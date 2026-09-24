"""Classificador de sponsorship de visto — item 6 do roadmap
(Pessoal/ROADMAP-freehire-para-job-radar.md). Portado do Job-hunter
(src/services/jobs/sponsorshipDetector.js), que por sua vez veio do projeto
uk (src/config/sponsorshipPatterns.ts) — mesma lógica nos 3 projetos agora.

Padrões batem uma CLÁUSULA, nunca "sponsor" solto: "executive sponsor",
"event sponsorship", "sponsored ads" continuam 'unclear' de propósito.

Prioridade: EXPLICIT_NO > CONDITIONAL > POSITIVE > IMPLICIT_NO. Uma frase
direta sobre sponsorship vence um requisito genérico de "autorizado a
trabalhar" — "visa sponsorship available" não vira 'no' por causa de
boilerplate jurídico em outro trecho do anúncio.

Só inglês — mesma limitação assumida no original (`ponytail:` lá). Sem uso
real ainda em português/alemão/francês; adiciona padrão quando aparecer
caso de verdade.

BLOQUEIO CONHECIDO (ver roadmap, item 6): job-radar historicamente só
guarda metadado de card de busca (título/empresa/local), nunca o texto
completo do anúncio — `Job.descricao` é campo novo, vazio por padrão,
preenchido só onde o scraper já visita a página da vaga (ver
scrapers/weworkremotely_intl.py, primeira fonte a fazer isso, item 6 do
roadmap). Sem `descricao`, `detect_sponsorship("")` sempre devolve
'unclear' — comportamento correto (sem texto, não tem o que ler), não bug.
"""

import re

_NEG_VERBS_ALT = r"do(?:es)?\s+not|don't|doesn't|will\s+not|won't|would\s+not|cannot|can\s*not|can't"
_NEG_VERBS = rf"(?:{_NEG_VERBS_ALT})"

# Faixa ampla de emoji (blocos "Emoji"/"Supplemental Symbols and Pictographs"
# + símbolos comuns) — ver comentário em _POSITIVE sobre por que isso
# substitui `\p{Extended_Pictographic}` sem precisar da lib `regex`.
_EMOJI = r"[\U0001F000-\U0001FFFF☀-➿⬀-⯿]"

_EXPLICIT_NO = [
    r"\bno\s+(?:visa\s+|work\s+)?sponsorship\b",
    r"\bwithout\s+(?:the\s+need\s+for\s+|requiring\s+|needing\s+)?(?:current\s+or\s+future\s+)?(?:visa\s+|employer\s+|company\s+)?sponsorship\b",
    # "(visa) sponsorship is not available" — mas "not available for all roles" é condicional
    r"\b(?:visa\s+)?sponsorship\s+(?:is\s+)?(?:not\s+(?:currently\s+)?(?:available|offered|provided)|unavailable)\b(?!\s+for\s+(?:all|every)\s+roles?)",
    r"\bvisa\s*(?:sponsorship)?\s*[:\-]\s*(?:not\s+available|none|n/a|no)\b",
    rf"\b{_NEG_VERBS}\s+(?:currently\s+|anticipate\s+)?(?:offer|provid(?:e|ing)|sponsor|support|assist\s+with|consider)\b[^.!?\n]{{0,50}}\b(?:sponsor(?:ship|ing)?|visas?|work\s+permits?)\b",
    rf"\b(?:{_NEG_VERBS_ALT}|unable\s+to|not\s+(?:currently\s+)?able\s+to)\s+sponsor\b",
    r"\b(?:unable|not\s+(?:currently\s+)?able|not\s+in\s+a\s+position)\s+to\s+(?:offer|provide|sponsor|support|assist\s+with|consider|accept)\b[^.!?\n]{0,60}\b(?:sponsor(?:ship|ing)?|visas?|work\s+permits?)\b",
    r"\bnot\s+(?:currently\s+)?sponsoring\b",
    r"\bnot\s+eligible\s+for\s+(?:\w+\s+)?(?:visa\s+)?sponsorship\b",
    r"\bnot\s+a\s+(?:licensed|registered|licenced)\s+sponsor\b",
    r"\bsponsorship\b[^.!?\n]{0,40}\bwill\s+not\s+be\s+accepted\b",
    r"\bdoes\s+not\s+meet\s+the\s+minimum\s+requirements\b[^.!?\n]{0,80}\bsponsor\b",
]

_CONDITIONAL = [
    r"\bsponsorship\s+may\s+be\s+(?:available|considered|possible|offered)\b",
    r"\bsponsorship\b[^.!?\n]{0,40}\bin\s+(?:very\s+)?limited\s+circumstances\b",
    r"\bsubject\s+to\s+sponsorship\s+eligibility\b",
    r"\bnot\s+all\s+roles\s+are\s+eligible\s+for\s+sponsorship\b",
    r"\bsponsorship\s+(?:will\s+be\s+)?considered\s+on\s+a\s+case[- ]by[- ]case\s+basis\b",
    r"\bdepending\s+on\s+(?:the\s+)?(?:role|circumstances|eligibility)\b[^.!?\n]{0,40}sponsorship\b",
    r"\bsponsorship\s+(?:is\s+)?not\s+available\s+for\s+(?:all|every)\s+roles?\b",
    r"\bsponsorship\s+will\s+only\s+be\s+considered\s+where\b",
    r"\bsponsorship\s+(?:is\s+)?(?:available|offered)\s+(?:only\s+)?for\s+(?:certain|select|some|eligible|exceptional|qualified)\b",
]

_POSITIVE = [
    r"\b(?:visa\s+|work\s+(?:permit\s+|visa\s+)?|immigration\s+)?sponsorship\s+(?:is\s+)?(?:available|offered|provided)\b",
    r"\bvisa\s*:\s*(?:sponsorship\s+)?(?:available|yes|offered)\b",
    r"\bwe\s+(?:can\s+|will\s+|are\s+able\s+to\s+|are\s+happy\s+to\s+)?(?:offer|provide|sponsor|support|assist\s+with)\s+(?:(?:with\s+)?(?:visa|work\s+permit|immigration)s?(?:\s+(?:sponsorship|support|assistance|relocation))?|sponsorship)\b",
    r"\bwelcome\s+applications?\s+from\s+candidates?\s+requiring\s+sponsorship\b",
    r"\bthis\s+role\s+is\s+eligible\s+for\s+(?:\w+\s+)?(?:visa\s+)?sponsorship\b",
    r"\beligible\s+for\s+(?:a\s+)?certificate\s+of\s+sponsorship\b",
    r"\bwe\s+are\s+a\s+(?:licensed|registered|licenced)\s+sponsor\b",
    r"\b(?:does\s+)?meets?\s+the\s+minimum\s+requirements\b[^.!?\n]{0,80}\bto\s+sponsor\b",
    # Item de lista com bullet ascii ("• Visa sponsorship") — só confia na
    # frase nua quando é item de lista de verdade (início de linha), nunca
    # dentro de prosa corrida (ver docstring do módulo).
    r"(?:^|\n)\s*[-•*·▪●]\s*(?:visa|work\s+permit)\s+(?:sponsorship|support|assistance)\s*(?=\n|$)",
    # Item de lista com emoji ("🌎 visa sponsorship") — sem âncora de linha
    # de propósito: diferente do bullet ascii, emoji quase nunca aparece
    # por coincidência antes dessa frase específica em prosa corrida, então
    # o risco de falso positivo é baixo o bastante pra não precisar da
    # âncora (mesma escolha do original em JS). `\p{Extended_Pictographic}`
    # do JS exigiria a lib `regex` (não está nas dependências) — Python
    # `re` já lida com codepoint astral nativamente, então uma faixa
    # explícita de emoji cobre o mesmo caso sem dependência nova.
    rf"{_EMOJI}️?\s*(?:visa|work\s+permit)\s+(?:sponsorship|support|assistance)\b",
]

_IMPLICIT_NO = [
    r"\b(?:must|need\s+to|required\s+to|should)\s+(?:already\s+)?(?:be\s+|have\s+)?(?:legally\s+)?(?:authori[sz]ed|eligible|entitled|permitted)\s+to\s+(?:work|be\s+employed)\b",
    r"\b(?:must|need\s+to)\s+(?:already\s+)?(?:have|possess|hold)\s+(?:the\s+)?(?:legal\s+|existing\s+|valid\s+|current\s+|pre-existing\s+)?right\s+to\s+work\b",
    r"\bpre-existing\s+right\s+to\s+work\b",
    r"\bright\s+to\s+(?:live\s+and\s+)?work\s+in\s+the\s+uk\s+independently\b",
    r"\b(?:must\s+be|need\s+to\s+be)\s+(?:a\s+)?(?:u\.?s\.?|united\s+states)\s+citizens?\b",
    r"^\s*(?:[-•*]\s*)?be\s+a\s+(?:u\.?s\.?|united\s+states)\s+citizen\b",
    r"\bcitizenship\s+(?:and\s+residency\s+[^.!?\n]{0,30})?(?:is\s+)?required\b",
    r"\bmust\s+hold\s+citizenship\b",
]

# Compilados uma vez (i = case-insensitive sempre; m = multiline só nesta
# regra — é a única que usa ^ pra "início de QUALQUER linha", não só do
# texto inteiro; as regras de item de lista acima resolvem isso sozinhas
# escrevendo `(?:^|\n)` por extenso, sem precisar da flag).
_MULTILINE_PATTERNS = {
    r"^\s*(?:[-•*]\s*)?be\s+a\s+(?:u\.?s\.?|united\s+states)\s+citizen\b",
}


def _compile(patterns):
    return [
        re.compile(p, re.IGNORECASE | (re.MULTILINE if p in _MULTILINE_PATTERNS else 0))
        for p in patterns
    ]


_RULES = [
    (_compile(_EXPLICIT_NO), "explicit_no"),
    (_compile(_CONDITIONAL), "conditional"),
    (_compile(_POSITIVE), "explicit_yes"),
    (_compile(_IMPLICIT_NO), "explicit_no"),
]


def _to_text(descricao: str) -> str:
    """Normaliza pontuação de abreviação que cortaria a frase-evidência no
    meio ("e.g." -> "eg") e HTML básico, caso a fonte um dia passe HTML cru
    em vez do texto já renderizado que Playwright's inner_text() devolve."""
    texto = str(descricao or "")
    texto = re.sub(r"<\s*li\b[^>]*>", "\n• ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<\s*(?:br|/p|/li|/div|/h\d|/tr)\b[^>]*>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = (
        texto.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        .replace("&nbsp;", " ").replace("&quot;", '"')
    )
    texto = re.sub(r"\be\.g\.", "eg", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bi\.e\.", "ie", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bu\.s\.(?=\W|$)", "US", texto, flags=re.IGNORECASE)
    return re.sub(r"[ \t]+", " ", texto)


def _extrair_evidencia(texto: str, match: "re.Match") -> str:
    """Frase inteira ao redor do match; se a "frase" for um bloco sem
    pontuação (lista de benefício sem ponto final), cai num recorte
    centrado no match."""
    inicio, fim = match.start(), match.end()

    candidatos_inicio = [
        texto.rfind(c, 0, inicio) for c in (".", "\n", "!", "?")
    ]
    s_inicio = max(candidatos_inicio) + 1

    candidatos_fim = [i for i in (texto.find(c, fim) for c in (".", "\n", "!", "?")) if i >= 0]
    s_fim = min(candidatos_fim) + 1 if candidatos_fim else len(texto)

    de = max(s_inicio, inicio - 120)
    ate = min(s_fim, fim + 120)
    recorte = texto[de:ate]
    recorte = re.sub(r"\s+", " ", recorte).strip()
    return ("..." if de > s_inicio else "") + recorte + ("..." if ate < s_fim else "")


def detect_sponsorship(descricao: str) -> dict:
    """{"status": "explicit_yes"|"conditional"|"explicit_no"|"unclear",
    "evidence": str|None} — mesma assinatura de detectSponsorship() no
    Job-hunter (sponsorshipDetector.js), só que em snake_case."""
    texto = _to_text(descricao)
    for padroes, status in _RULES:
        for padrao in padroes:
            match = padrao.search(texto)
            if match:
                return {"status": status, "evidence": _extrair_evidencia(texto, match)}
    return {"status": "unclear", "evidence": None}
