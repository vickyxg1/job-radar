"""_montar_vaga (scrapers/weworkremotely_intl.py) — a única parte deste
scraper que não depende de Playwright/rede, então a única testável sem
mock de browser. Cobre a integração nova do item 6 do roadmap:
Job.descricao + nota_extra a partir do core.sponsorship."""

from scrapers.weworkremotely_intl import WeWorkRemotelyIntlScraper


def _item(**overrides):
    base = {
        "titulo": "Senior Backend Engineer", "empresa": "Acme", "sede": "San Francisco, US",
        "link": "https://weworkremotely.com/remote-jobs/acme-senior-backend-engineer",
        "publicado_em": "",
    }
    base.update(overrides)
    return base


def _montar(**overrides):
    return WeWorkRemotelyIntlScraper(termos_busca=[])._montar_vaga(_item(**overrides))


def test_campos_basicos_mapeados_certo():
    vaga = _montar()
    assert vaga.titulo == "Senior Backend Engineer"
    assert vaga.empresa == "Acme"
    assert vaga.local == "San Francisco, US"  # sede vira local, ver comentário de escopo_indefinido em job.py
    assert vaga.site == "We Work Remotely"
    assert vaga.modalidade == "Remoto"
    assert vaga.escopo_indefinido is True


def test_sem_descricao_capturada_fica_sem_nota_e_sem_descricao():
    vaga = _montar(descricao="")
    assert vaga.descricao == ""
    assert vaga.nota_extra == ""


def test_descricao_unclear_nao_gera_nota():
    vaga = _montar(descricao="We are hiring a backend engineer to join our platform team.")
    assert vaga.descricao != ""
    assert vaga.nota_extra == ""


def test_descricao_com_sponsorship_explicito_gera_nota_com_evidencia():
    vaga = _montar(descricao="We are a licensed sponsor and offer visa sponsorship for this role.")
    assert vaga.nota_extra.startswith("✅")
    assert "sponsor" in vaga.nota_extra.lower()


def test_descricao_sem_sponsorship_gera_nota_de_alerta():
    vaga = _montar(descricao="Applicants must be authorized to work in the United States.")
    assert vaga.nota_extra.startswith("❌")


def test_descricao_condicional_gera_nota_propria():
    vaga = _montar(descricao="Sponsorship will be considered on a case-by-case basis.")
    assert vaga.nota_extra.startswith("⚠️")
