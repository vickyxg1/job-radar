from core.skill_match import calcular_match, SKILLS_DEV


def test_skills_de_cargo_genericas_nao_entram_na_lista():
    for termo in ("frontend", "front-end", "front end", "web", "full stack", "fullstack"):
        assert termo not in SKILLS_DEV


def test_titulo_sem_nenhuma_skill_da_zero_por_cento():
    r = calcular_match("Analista de Suporte N1")
    assert r["cobertura_percent"] == 0
    assert r["batidas"] == []
    assert set(r["ausentes"]) == set(SKILLS_DEV)


def test_titulo_com_skill_unica_conta_certo():
    r = calcular_match("Desenvolvedor React Pleno")
    assert "react" in r["batidas"]
    assert r["cobertura_percent"] == round(100 / len(SKILLS_DEV))


def test_varias_skills_somam_na_cobertura():
    r = calcular_match("React, Node.js e TypeScript — full stack")
    assert set(r["batidas"]) >= {"react", "node", "typescript"}
    assert r["cobertura_percent"] == round(100 * len(r["batidas"]) / len(SKILLS_DEV))


def test_case_insensitive_e_sem_acento():
    r_maiuscula = calcular_match("REACT DEVELOPER")
    r_minuscula = calcular_match("react developer")
    assert r_maiuscula["batidas"] == r_minuscula["batidas"]


def test_borda_de_palavra_nao_casa_substring_solta():
    # "next" não deveria bater dentro de "nextera" (nome de empresa fictício)
    r = calcular_match("Backend Engineer at Nextera Solutions")
    assert "next" not in r["batidas"]


def test_texto_vazio_da_zero_por_cento():
    r = calcular_match("")
    assert r["cobertura_percent"] == 0
    assert r["batidas"] == []


def test_lista_de_skills_vazia_nao_divide_por_zero():
    r = calcular_match("React developer", skills=[])
    assert r == {"cobertura_percent": 0, "batidas": [], "ausentes": []}


def test_ausentes_e_batidas_sao_complementares():
    r = calcular_match("Angular Developer")
    assert set(r["batidas"]) | set(r["ausentes"]) == set(SKILLS_DEV)
    assert set(r["batidas"]) & set(r["ausentes"]) == set()
