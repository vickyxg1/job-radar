
import time

import requests

from core.job import Job
from core.logger import get_logger
from scrapers.base import BaseScraper

logger = get_logger()

API_URL = "https://freehire.me/api/v1/jobs/search"
PAGE_SIZE = 100
# Poll de rotina, não backfill: o dedup por link já existe entre ciclos
# (ver Job.id em core/job.py), então não precisa varrer milhares de vaga
# por execução — só as mais novas de cada ciclo (sort=posted_at) já bastam
# pra pegar o que entrou desde o ciclo anterior.
MAX_JOBS = 300
DELAY_S = 0.5
CATEGORIES = "frontend,fullstack,software_engineering"
# Geografia é um único grupo OR na API (ver docs/API.md do freehire,
# clonado em Projetos/Pessoal/freehire) — um request só já cobre tudo.
# global/latam: remoto sem restrição de país, aceito de qualquer lugar
# (inclusive Brasil). eu/uk/north_america: resto da lista aceita pelo
# perfil dev quando ATIVAR_REMOTO_INTERNACIONAL_DEV está ligado (Estados
# Unidos, Reino Unido, Canadá, Alemanha, Irlanda, Holanda, Europa, EMEA —
# ver MERCADOS_REMOTO_ACEITOS_DEV em core/config_dev.py). mena/africa/
# apac/cis ficam de fora por não estarem nessa lista.
REGIONS = "global,latam,eu,uk,north_america"

# Austrália é o único país do APAC aceito (decisão do usuário, 2026-09-24)
# — ligar `regions=apac` inteiro traria Ásia inteira (China/Índia/Japão/
# Singapura...) só pra depois o filtro geográfico jogar tudo fora, gastando
# request à toa. `countries` faz OR com `regions` (mesmo grupo de geografia
# — ver docs/API.md), então um país específico entra sem precisar abrir a
# região inteira.
COUNTRIES = "AU"

# `reality.class` (fresh/stale/likely-evergreen) marca postagem que já pode
# estar morta/vaga fantasma. Exclui só "stale" (postagem confirmada velha
# demais) — mantém "likely-evergreen" (empresa que recruta contínuo pro
# mesmo cargo continua sendo vaga de verdade, só sem data recente).
REALITY_OK = "fresh,likely-evergreen"

# Recrutadora/agência terceirizada é ruído medido no perfil BR (ver
# core/perfis.py, comentário de _SCRAPERS_BR) — mesmo motivo aqui. Lista
# (não string com vírgula): a doc da API só exemplifica `_exclude` com UM
# valor por vez — `requests` repete a chave pra cada item da lista
# (`company_type_exclude=outstaff&company_type_exclude=agency`), que é o
# formato "repeat" documentado como válido pra qualquer facet.
COMPANY_TYPE_EXCLUDE = ["outstaff", "agency"]

# Coleções da própria API que batem a EMPRESA (não o texto da vaga) contra
# um registro oficial de patrocinador de visto — GOV.UK (Skilled Worker),
# USCIS (histórico H-1B, últimos 5 anos fiscais) e IND (Holanda). Cobre o
# caso "a vaga não fala nada de sponsorship, mas a empresa já patrocinou/
# está licenciada" — diferente de `enrichment.visa_sponsorship` abaixo (LLM
# sobre o texto da vaga, fica null quando a vaga não fala nada, não resolve
# esse caso). Ressalva do próprio freehire: a licença é da empresa, não é
# compromisso de patrocinar ESSA vaga — por isso vira nota informativa, não
# filtro nem pontuação. Só cobre US/UK/Holanda; Alemanha/Irlanda/Canadá não
# têm registro público equivalente.
_ROTULOS_COLECAO_SPONSOR = {
    "uk-skilled-worker-sponsor": "🇬🇧 patrocinador licenciado (registro GOV.UK)",
    "us-h1b-sponsor": "🇺🇸 histórico de patrocínio H-1B (USCIS)",
    "nl-recognised-sponsor": "🇳🇱 patrocinador reconhecido (registro IND)",
}


def _nota_sponsor(raw: dict) -> list[str]:
    """Linhas sobre a EMPRESA (registro oficial) — ver comentário acima."""
    colecoes = raw.get("collections") or []
    rotulos = [_ROTULOS_COLECAO_SPONSOR[c] for c in colecoes if c in _ROTULOS_COLECAO_SPONSOR]
    if not rotulos:
        return []
    return ["🏢 Empresa pode patrocinar visto: " + "; ".join(rotulos)]


def _nota_enrichment_visto(raw: dict) -> list[str]:
    """Linha sobre o que a VAGA em si declara (extração LLM sobre o texto,
    `internal/ai/enrich` no freehire) — `None`/ausente quando o anúncio não
    fala nada (mesma limitação epistêmica do classificador por regex do
    Job-hunter: sem clone nenhum, não inventa)."""
    visto = (raw.get("enrichment") or {}).get("visa_sponsorship")
    if visto is True:
        return ["✅ Vaga declara sponsorship de visto"]
    if visto is False:
        return ["❌ Vaga declara que NÃO oferece sponsorship de visto"]
    return []


def _nota_extra(raw: dict) -> str:
    linhas = _nota_enrichment_visto(raw) + _nota_sponsor(raw)
    return "\n".join(linhas)


class FreehireScraper(BaseScraper):
    """Busca vaga 100% remota de dev (frontend/fullstack/software
    engineering) no catálogo aberto do freehire (freehire.me/api/v1) —
    API JSON sem chave, sem precisar de Playwright.

    Só entra no perfil "dev": o outro uso do freehire — vaga presencial/
    híbrida no exterior com sponsorship declarado, já portado pro
    Job-hunter em src/scrapers/apis/freehire.js — não tem como passar no
    filtro deste projeto. RegrasFiltro só aceita presencial/híbrido em
    CIDADES_DEV (só Uberlândia), e o freehire não lista vaga de
    Uberlândia; portar esse eixo exigiria o conceito de "presencial no
    exterior com visto" no motor de filtro, que este projeto não tem —
    fora de escopo aqui.

    Ignora `termos_busca` de propósito: o filtro de categoria da própria
    API (CATEGORIES) já restringe a vaga de dev sem precisar de um
    request por termo do rodízio — ao contrário dos outros scrapers, aqui
    um request só já cobre tudo.
    """

    def __init__(self, termos_busca: list[str]):
        self.termos_busca = termos_busca  # não usado — ver docstring

    def buscar_vagas(self) -> list[Job]:
        vagas: list[Job] = []
        vistos: set[str] = set()

        for offset in range(0, MAX_JOBS, PAGE_SIZE):
            try:
                pagina = self._buscar_pagina(offset)
            except Exception as e:
                logger.error(f"[Freehire] Erro na página offset={offset}: {e}")
                break

            linhas = pagina.get("data") or []
            if not linhas:
                break

            for raw in linhas:
                slug = raw.get("public_slug")
                if not slug or slug in vistos:
                    continue
                vistos.add(slug)
                vaga = self._normalizar(raw)
                if vaga:
                    vagas.append(vaga)

            total = (pagina.get("meta") or {}).get("total", 0)
            if len(linhas) < PAGE_SIZE or offset + PAGE_SIZE >= total:
                break
            time.sleep(DELAY_S)

        logger.info(f"[Freehire] {len(vagas)} vaga(s) encontrada(s) no total")
        return vagas

    def _buscar_pagina(self, offset: int) -> dict:
        params = {
            "category": CATEGORIES,
            "work_mode": "remote",
            "regions": REGIONS,
            "countries": COUNTRIES,
            "reality": REALITY_OK,
            "company_type_exclude": COMPANY_TYPE_EXCLUDE,
            "sort": "posted_at",
            "order": "desc",
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        resposta = requests.get(
            API_URL, params=params,
            headers={"User-Agent": "JobRadar/1.0 (local job monitor)"},
            timeout=20,
        )
        resposta.raise_for_status()
        return resposta.json()

    @staticmethod
    def _normalizar(raw: dict) -> "Job | None":
        titulo = (raw.get("title") or "").strip()
        empresa = (raw.get("company") or "").strip()
        link = (raw.get("url") or "").strip()
        if not (titulo and empresa and link):
            return None

        # `location` já vem no formato "Remote — EU"/"Remote — Brazil" que
        # extrair_escopo_remoto (core/job.py) sabe ler — mesmo padrão já
        # confirmado ao vivo pro LinkedIn/WeWorkRemotely. Sem local nenhum
        # (vaga 100% global, sem país associado), cai em "Remoto" puro,
        # que o mesmo parser trata como sem restrição geográfica.
        local = (raw.get("location") or "").strip() or "Remoto"

        return Job(
            titulo=titulo,
            empresa=empresa,
            local=local,
            link=link,
            site="freehire",
            publicado_em=(raw.get("posted_at") or ""),
            modalidade="Remoto",
            nota_extra=_nota_extra(raw),
        )
