"""Normalização do scraper freehire — só a lógica pura (sem rede)."""

from core.perfis import PERFIL_DEV
from scrapers.freehire import COUNTRIES, FreehireScraper


def _raw(**overrides):
    base = {
        "public_slug": "senior-frontend-engineer-acme-1a2b",
        "title": "Senior Frontend Engineer",
        "company": "Acme",
        "url": "https://boards.greenhouse.io/acme/jobs/123",
        "location": "Remote — EU",
        "posted_at": "2026-06-18T00:00:00Z",
    }
    base.update(overrides)
    return base


def test_normaliza_campos_basicos():
    vaga = FreehireScraper._normalizar(_raw())
    assert vaga.titulo == "Senior Frontend Engineer"
    assert vaga.empresa == "Acme"
    assert vaga.link == "https://boards.greenhouse.io/acme/jobs/123"
    assert vaga.site == "freehire"
    assert vaga.modalidade == "Remoto"
    assert vaga.local == "Remote — EU"
    assert vaga.publicado_em == "2026-06-18T00:00:00Z"


def test_sem_local_cai_pra_remoto_puro():
    assert FreehireScraper._normalizar(_raw(location="")).local == "Remoto"


def test_sem_titulo_empresa_ou_link_descarta():
    assert FreehireScraper._normalizar(_raw(title="")) is None
    assert FreehireScraper._normalizar(_raw(company="")) is None
    assert FreehireScraper._normalizar(_raw(url="")) is None


def test_escopo_remoto_reconhece_localizacao_da_api():
    """Contrato entre este scraper e core/job.py: o formato real da API
    ("Remote — EU") precisa ser reconhecido pelo parser de escopo, senão a
    vaga é rejeitada mesmo com "Europa" na lista aceita do perfil dev."""
    vaga = FreehireScraper._normalizar(_raw())
    assert vaga.escopo_remoto == {"Europa"}


def test_query_pede_australia_via_countries_nao_regiao_apac_inteira():
    """Decisão do usuário (2026-09-24): só Austrália do APAC, não a região
    inteira (evita trazer Ásia inteira só pra filtrar tudo fora depois)."""
    assert COUNTRIES == "AU"


def test_escopo_remoto_reconhece_australia_por_extenso_e_por_sigla():
    vaga_extenso = FreehireScraper._normalizar(_raw(location="Remote — Australia"))
    vaga_sigla = FreehireScraper._normalizar(_raw(location="Remote — AU"))
    assert vaga_extenso.escopo_remoto == {"Austrália"}
    assert vaga_sigla.escopo_remoto == {"Austrália"}


def test_vaga_remota_australiana_passa_no_filtro_do_perfil_dev():
    vaga = FreehireScraper._normalizar(_raw(location="Remote — Australia"))
    assert vaga.combina_com(PERFIL_DEV.regras)


def test_empresa_patrocinadora_conhecida_vira_nota():
    vaga = FreehireScraper._normalizar(_raw(collections=["yc", "us-h1b-sponsor"]))
    assert "🇺🇸 histórico de patrocínio H-1B (USCIS)" in vaga.nota_extra
    assert "yc" not in vaga.nota_extra  # coleção sem rótulo de sponsor não aparece


def test_multiplas_colecoes_de_sponsor_juntam_na_mesma_nota():
    vaga = FreehireScraper._normalizar(_raw(collections=["uk-skilled-worker-sponsor", "nl-recognised-sponsor"]))
    assert "GOV.UK" in vaga.nota_extra
    assert "IND" in vaga.nota_extra


def test_sem_colecao_de_sponsor_nota_fica_vazia():
    assert FreehireScraper._normalizar(_raw(collections=["yc", "unicorn"])).nota_extra == ""
    assert FreehireScraper._normalizar(_raw()).nota_extra == ""


def test_vaga_declara_sponsorship_no_texto():
    vaga = FreehireScraper._normalizar(_raw(enrichment={"visa_sponsorship": True}))
    assert "✅" in vaga.nota_extra
    assert "NÃO" not in vaga.nota_extra


def test_vaga_declara_que_nao_oferece_sponsorship():
    vaga = FreehireScraper._normalizar(_raw(enrichment={"visa_sponsorship": False}))
    assert "❌" in vaga.nota_extra
    assert "NÃO" in vaga.nota_extra


def test_enrichment_ausente_ou_sem_campo_nao_gera_nota():
    assert FreehireScraper._normalizar(_raw()).nota_extra == ""
    assert FreehireScraper._normalizar(_raw(enrichment={})).nota_extra == ""
    assert FreehireScraper._normalizar(_raw(enrichment={"visa_sponsorship": None})).nota_extra == ""


def test_enrichment_e_colecao_de_sponsor_juntam_na_mesma_nota():
    vaga = FreehireScraper._normalizar(_raw(
        enrichment={"visa_sponsorship": True},
        collections=["us-h1b-sponsor"],
    ))
    assert "✅" in vaga.nota_extra
    assert "USCIS" in vaga.nota_extra
