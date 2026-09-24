"""Testes da camada de notificação (notifier/telegram.py) que não dependem
de rede — parsing de callback_data e montagem de teclado inline, a parte
nova do fluxo de feedback 👍/👎 (ver processar_feedback_pendente).

Chamada de rede de verdade (sendMessage/getUpdates/answerCallbackQuery)
não é testável aqui: o sandbox não alcança api.telegram.org (proxy do
ambiente bloqueia, já diagnosticado nesta sessão). O que é função pura —
_parsear_callback_data e _teclado_feedback — é testado isolado, sem mock
nenhum.
"""

import pytest

from core.job import Job
from notifier.telegram import _linha_mercado, _linha_match_skills, _parsear_callback_data, _teclado_feedback

_ID_EXEMPLO = "d41d8cd98f00b204e9800998ecf8427e"  # md5 de exemplo, 32 chars

CASOS_PARSE_CALLBACK = [
    ("positivo-formato-valido", f"fb|1|{_ID_EXEMPLO}", (_ID_EXEMPLO, "positivo")),
    ("negativo-formato-valido", f"fb|0|{_ID_EXEMPLO}", (_ID_EXEMPLO, "negativo")),
    # Botão de confirmação (substitui o teclado original depois de
    # registrado) não deve ser reprocessado como voto novo.
    ("botao-confirmacao-nao-e-voto", "fb|ok|-", None),
    # Direção fora de 1/0.
    ("direcao-invalida", f"fb|2|{_ID_EXEMPLO}", None),
    # Prefixo errado (callback_data de outro bot/projeto, teoricamente).
    ("prefixo-errado", f"xx|1|{_ID_EXEMPLO}", None),
    # Formato sem as 3 partes esperadas.
    ("sem_partes_suficientes", "fb|1", None),
    ("partes_demais", f"fb|1|{_ID_EXEMPLO}|extra", None),
    ("string_vazia", "", None),
]


@pytest.mark.parametrize(
    "nome,data,esperado",
    CASOS_PARSE_CALLBACK,
    ids=[c[0] for c in CASOS_PARSE_CALLBACK],
)
def test_parsear_callback_data(nome, data, esperado):
    assert _parsear_callback_data(data) == esperado


def test_teclado_feedback_estrutura():
    teclado = _teclado_feedback(_ID_EXEMPLO)
    linha = teclado["inline_keyboard"][0]
    assert len(linha) == 2
    assert linha[0]["callback_data"] == f"fb|1|{_ID_EXEMPLO}"
    assert linha[1]["callback_data"] == f"fb|0|{_ID_EXEMPLO}"


def _vaga(titulo="Desenvolvedor React Pleno", descricao=""):
    return Job(titulo=titulo, empresa="Acme", local="Remoto", link="https://x.com/1", site="Teste", descricao=descricao)


def test_match_skills_so_aparece_no_perfil_dev():
    vaga = _vaga()
    assert _linha_match_skills(vaga, "dev") != ""
    assert _linha_match_skills(vaga, "brasil") == ""
    assert _linha_match_skills(vaga, "internacional") == ""
    assert _linha_match_skills(vaga, "") == ""


def test_match_skills_some_quando_nenhuma_skill_bate():
    vaga = _vaga(titulo="Analista de Suporte N1")
    assert _linha_match_skills(vaga, "dev") == ""


def test_match_skills_mostra_percentual_e_skills_batidas():
    vaga = _vaga(titulo="Desenvolvedor React e TypeScript")
    linha = _linha_match_skills(vaga, "dev")
    assert "%" in linha
    assert "react" in linha
    assert "typescript" in linha


def test_mercado_aparece_quando_escopo_declarado():
    vaga = Job(titulo="React Developer", empresa="Acme", local="Remote — UK", link="https://x.com/1", site="Teste", modalidade="Remoto")
    assert "Reino Unido" in _linha_mercado(vaga)


def test_mercado_reconhece_australia():
    vaga = Job(titulo="React Developer", empresa="Acme", local="Remote — Australia", link="https://x.com/2", site="Teste", modalidade="Remoto")
    assert "Austrália" in _linha_mercado(vaga)


def test_mercado_some_sem_escopo_declarado():
    # Remoto "puro", sem país/região no texto — nada pra badge mostrar.
    vaga = Job(titulo="React Developer", empresa="Acme", local="Remoto", link="https://x.com/3", site="Teste", modalidade="Remoto")
    assert _linha_mercado(vaga) == ""


def test_mercado_some_quando_vaga_nao_e_remota():
    vaga = Job(titulo="React Developer", empresa="Acme", local="Uberlândia, MG", link="https://x.com/4", site="Teste", modalidade="Presencial")
    assert _linha_mercado(vaga) == ""


def test_mercado_mostra_mais_de_um_pais_quando_declarado():
    vaga = Job(titulo="React Developer", empresa="Acme", local="Remote - LATAM + Brazil", link="https://x.com/5", site="Teste", modalidade="Remoto")
    linha = _linha_mercado(vaga)
    assert "Brasil" in linha
    assert "LATAM" in linha


def test_match_skills_usa_titulo_mais_descricao():
    # Nenhuma skill no título, mas a descrição (só existe em fonte que
    # visita a página da vaga — ver item 6) menciona a stack.
    vaga = _vaga(titulo="Engenheiro de Software Pleno", descricao="Trabalhamos com Node.js e Angular no dia a dia.")
    linha = _linha_match_skills(vaga, "dev")
    assert "node" in linha
    assert "angular" in linha


def test_teclado_feedback_callback_data_dentro_do_limite_do_telegram():
    # Limite real da API: callback_data <= 64 bytes.
    teclado = _teclado_feedback(_ID_EXEMPLO)
    for botao in teclado["inline_keyboard"][0]:
        assert len(botao["callback_data"].encode("utf-8")) <= 64


def test_ida_e_volta_teclado_para_parser():
    # O que _teclado_feedback gera, _parsear_callback_data tem que
    # entender de volta — as duas funções são as duas pontas do mesmo
    # contrato (callback_data), então uma mudar sem a outra é exatamente o
    # tipo de bug que só aparece em produção sem esse teste.
    teclado = _teclado_feedback(_ID_EXEMPLO)
    botao_positivo, botao_negativo = teclado["inline_keyboard"][0]

    assert _parsear_callback_data(botao_positivo["callback_data"]) == (_ID_EXEMPLO, "positivo")
    assert _parsear_callback_data(botao_negativo["callback_data"]) == (_ID_EXEMPLO, "negativo")
