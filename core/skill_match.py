"""Cobertura de skill determinística — item 7 do roadmap
(Pessoal/ROADMAP-freehire-para-job-radar.md). Réplica local de
`GET /jobs/{slug}/match` do freehire (coverage de skill sem LLM), que exige
conta freehire + API key (cota free 3/dia) e só funciona pra vaga DO
freehire — inviável pra um cron rodando sobre vaga de qualquer fonte.

Substring com borda de palavra sobre TÍTULO (+ descrição, quando a fonte
tem — ver Job.descricao em core/job.py) contra uma lista de skill fixa, não
perfil de currículo de verdade — mais simples, sem cadastro nenhum.
"""

import re
import unicodedata

# Lista própria, não derivada de QUALIFICADORES_DEV (core/config_dev.py) —
# aquela serve outro propósito (confirmar cargo ambíguo no TÍTULO) e mistura
# sinônimo de CARGO/ÁREA (frontend, web, full stack) com tecnologia de
# verdade; usar como "skill" inflaria a cobertura à toa. Extraída dos 3
# currículos reais da usuária (2026-09-24) — 6 originais (react/angular/
# node/next/javascript/typescript) + 5 confirmados como stack de verdade
# nos 3 PDFs (tailwind, jest, supabase, oauth, vite). Descartado da lista:
# python/pandas (projeto secundário, não stack principal), docker (só
# "conceitos" numa das 3 versões, claim fraco), git/github/api/scrum/agile
# (universal demais, zero poder de diferenciação).
SKILLS_DEV = [
    "react", "angular", "node", "next", "javascript", "typescript",
    "tailwind", "jest", "supabase", "oauth", "vite",
]


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


def _bate(skill: str, texto_norm: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", texto_norm) is not None


def calcular_match(texto: str, skills: list[str] = SKILLS_DEV) -> dict:
    """{"cobertura_percent": int, "batidas": [...], "ausentes": [...]} —
    skills vazia devolve 0% sem dividir por zero."""
    if not skills:
        return {"cobertura_percent": 0, "batidas": [], "ausentes": []}

    texto_norm = _normalizar(texto or "")
    batidas = [s for s in skills if _bate(s, texto_norm)]
    ausentes = [s for s in skills if s not in batidas]
    cobertura = round(100 * len(batidas) / len(skills))
    return {"cobertura_percent": cobertura, "batidas": batidas, "ausentes": ausentes}
