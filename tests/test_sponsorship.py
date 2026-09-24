"""Classificador de sponsorship (core/sponsorship.py) — mesmo corpus real
usado em Job-hunter/src/services/jobs/sponsorshipDetector.test.js, portado
pra confirmar paridade entre os dois (ver item 6 do roadmap)."""

import pytest

from core.sponsorship import detect_sponsorship


def _check(expected, casos):
    for texto in casos:
        r = detect_sponsorship(texto)
        assert r["status"] == expected, f'esperava {expected}, veio {r["status"]} pra: "{texto}"'
        if expected != "unclear":
            assert r["evidence"], f'sem evidência pra: "{texto}"'


def test_explicit_no_frases_do_corpus_real():
    _check("explicit_no", [
        "Veeva does not provide sponsorship for employment visa status (e.g., H-1B, OPT, or TN status) for this employment position.",
        "Veeva Systems does not anticipate providing sponsorship for employment visa status for this employment position.",
        "Veeva is unable to provide sponsorship for employment visas for this position.",
        "This is a work anywhere role, however, you must already be based in and be eligible for employment in the EU, as Veeva does not sponsor employment visa or relocation processes.",
        "We are not sponsoring working visas, meaning you must already have the right to work full time in Germany.",
        "We do not provide visa assistance, and our cooperation model does not include the benefits typically offered with direct hire.",
        "Cannot provide sponsorship - must be able to work W2",
        "Compensation: $200k base competitive equity Visa: not available Company overview",
        "<li>Work Authorization: Qualified candidates must be legally authorized to be employed in the United States.</li>",
        "<li>Applicants must be authorized to work in the United States.</li>",
        "<li>Location: must be eligible to work in Ireland</li>",
        "<p><em>Due to government requirements, you must be a United States citizen to fill this position.</em></p>",
        "<li>be a US citizen</li>",
        "Citizenship is required due to federal compliance obligations",
        "We are unable to offer visa sponsorship for this role.",
        "Unfortunately, we are not in a position to offer visa sponsorship.",
        "Applications requiring sponsorship will not be accepted for this role.",
        "we are not a registered sponsor",
        "right to work without employer sponsorship",
        "we will not sponsor",
    ])


def test_conditional():
    _check("conditional", [
        "Company sponsorship may be available for eligible candidates applying for certain roles.",
        "Sponsorship is not available for all roles.",
        "We are only able to facilitate visa sponsorship in very limited circumstances.",
        "Sponsorship will be considered on a case-by-case basis.",
    ])


def test_explicit_yes_lista_de_beneficio_e_prosa():
    _check("explicit_yes", [
        "What we offer 💰 competitive salary 🧑‍⚕️ health insurance 🌎 visa sponsorship 🍼 parental leave",
        "<li>• 🪪 Visa sponsorship</li>",
        "<ul><li>Visa sponsorship</li><li>Health insurance</li></ul>",
        "Visa sponsorship is available!",
        "Work policy: full-time, 5 days/week in office (visa sponsorship available)",
        "We are a licensed sponsor and offer visa sponsorship for this role.",
        "We can provide visa support for the right candidate.",
    ])


def test_unclear_ruido_de_sponsor_visto_cidadania_nao_classifica():
    _check("unclear", [
        "",
        "Serve as an executive sponsor for strategic customers.",
        "Align with executives on business challenges and gain sponsorship for enterprise-wide deployments.",
        "Own the sponsorship strategy for flagship events and manage sponsored content.",
        "Trusted by leading organizations such as HPE, HSBC, Visa, and Oracle.",
        "100% sponsored medical, dental, and vision plans",
        "We do not discriminate on the basis of race, religion, national origin, citizenship, age or disability.",
        "Relocation assistance may be available.",
        "Sponsor banks, BIN sponsors and fintechs ecosystem.",
        "Konzeption von Retail Media Kampagnen (Sponsored Ads, DSP, CTV)",
        "For more information about visa sponsorship, see gov.uk.",
    ])


def test_prioridade_declaracao_explicita_vence_boilerplate_de_autorizacao():
    _check("explicit_yes", ["Visa sponsorship is available. Applicants must be authorized to work in the country of hire."])
    _check("explicit_no", ["Visa sponsorship is available for some of our roles. However, this role is not eligible for visa sponsorship."])
    _check("explicit_no", ["Sponsorship may be available for some posts, but we are not a registered sponsor for this one."])


def test_evidencia_e_um_recorte_legivel_nao_o_blob_inteiro():
    blob = "What we offer " + "perk " * 80 + "🌎 visa sponsorship " + "perk " * 80
    r = detect_sponsorship(blob)
    assert "visa sponsorship" in r["evidence"]
    assert len(r["evidence"]) < 320
