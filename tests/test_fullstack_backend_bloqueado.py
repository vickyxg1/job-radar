"""backend_fullstack_bloqueado (core/job.py + core/config_dev.py) —
decisão do usuário (2026-09-24): perfil front-end-first, full stack só
interessa pareado com Go/Java/Node. Vaga full stack que nomeia
explicitamente OUTRO backend no título é rejeitada; sem backend nomeado,
continua passando (sem sinal, sem base pra rejeitar)."""

from core.job import Job
from core.perfis import PERFIL_DEV


def _vaga(titulo, local="Remoto", modalidade="Remoto", descricao=""):
    return Job(titulo=titulo, empresa="Empresa Teste", local=local,
               link=f"https://exemplo.com/{abs(hash(titulo))}",
               site="Teste", modalidade=modalidade, descricao=descricao)


def test_fullstack_com_backend_permitido_passa():
    for titulo in [
        "Desenvolvedor Full Stack (React + Node.js)",
        "Full Stack Developer (Angular + Go)",
        "Full Stack Developer (Angular + Java)",
        "Desenvolvedor Full Stack React e Node",
    ]:
        assert _vaga(titulo).combina_com(PERFIL_DEV.regras), titulo


def test_fullstack_com_backend_bloqueado_e_rejeitado():
    for titulo in [
        "Desenvolvedor Full Stack (Python/Django)",
        "Full Stack Developer (PHP/Laravel)",
        "Full Stack .NET Developer",
        "Desenvolvedor Full Stack C#",
        "Fullstack Ruby on Rails Developer",
    ]:
        assert not _vaga(titulo).combina_com(PERFIL_DEV.regras), titulo


def test_fullstack_sem_backend_nomeado_continua_passando():
    """Sem sinal explícito de backend, sem base pra rejeitar."""
    assert _vaga("Desenvolvedor Full Stack").combina_com(PERFIL_DEV.regras)
    assert _vaga("Full Stack Developer Pleno").combina_com(PERFIL_DEV.regras)


def test_backend_bloqueado_so_derruba_quando_titulo_e_fullstack():
    """Vaga puramente front-end (sem "full stack" no título) não é afetada
    mesmo se a descrição mencionar um backend bloqueado à toa (ex: projeto
    que integra com um serviço Python que não é o backend da vaga)."""
    vaga = _vaga("Desenvolvedor Frontend React", descricao="Integra com um serviço interno escrito em Python.")
    assert vaga.combina_com(PERFIL_DEV.regras)


def test_checa_titulo_e_descricao():
    """Backend bloqueado só no corpo da descrição (não no título) também
    derruba, quando a fonte tem descrição — ver Job.descricao."""
    vaga = _vaga("Desenvolvedor Full Stack", descricao="Stack: React no front, Django no backend.")
    assert not vaga.combina_com(PERFIL_DEV.regras)


def test_perfil_sem_a_regra_configurada_nao_e_afetado():
    """None (default) preserva o comportamento de antes — usado por
    quem não configurou isso (perfil BR/Internacional)."""
    from core.job import RegrasFiltro
    regras_sem_checagem = RegrasFiltro(
        keywords_forte=["Full Stack"], keywords_ambiguo=[], qualificadores_dados=[],
        ferramentas_titulo=[], qualificadores_cargo=[], cidades=["Remoto"],
    )
    vaga = _vaga("Full Stack Python Developer")
    assert vaga.combina_com(regras_sem_checagem)
