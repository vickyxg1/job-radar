
# Config do perfil "dev" — vaga de desenvolvimento Frontend/Full Stack
# (React, Angular, Next.js, Node.js, TypeScript), o currículo real de quem
# roda este projeto hoje. Separado de config.py (Dados/BI) pelo mesmo
# motivo de config_intl.py: são dois propósitos de busca diferentes, cada
# um com seu próprio cargo/cidade/termo — misturar forçaria os dois a usar
# a mesma whitelist de cidade e o mesmo vocabulário de cargo.
#
# Credenciais do Telegram e caminho do banco são os MESMOS do projeto
# principal (mesmo bot, mesmo jobs.db — dedup por link não tem risco de
# colisão entre perfis).
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DB_PATH  # noqa: F401

# Cargo forte: título que só existe mesmo em vaga de desenvolvimento
# frontend/full stack, sem possibilidade real de ser outra área (mobile,
# backend puro Java/PHP/.NET, QA, etc.).
KEYWORDS_CARGO_FORTE_DEV = [
    "Desenvolvedor Frontend",
    "Desenvolvedora Frontend",
    "Desenvolvedor Front-end",
    "Desenvolvedora Front-end",
    "Frontend Developer",
    "Front-end Developer",
    "Desenvolvedor React",
    "Desenvolvedora React",
    "React Developer",
    "Desenvolvedor Angular",
    "Desenvolvedora Angular",
    "Angular Developer",
    "Desenvolvedor Full Stack",
    "Desenvolvedora Full Stack",
    "Full Stack Developer",
    "Fullstack Developer",
    "Desenvolvedor Node",
    "Desenvolvedora Node",
    "Node.js Developer",
    "Node Developer",
    "Desenvolvedor JavaScript",
    "Desenvolvedora JavaScript",
    "JavaScript Developer",
    "Desenvolvedor TypeScript",
    "Desenvolvedora TypeScript",
    "TypeScript Developer",
    "Frontend Engineer",
    "Full Stack Engineer",
]

# Cargo ambíguo: título usado em vaga que não tem nada a ver com o perfil
# (Desenvolvedor Mobile, Desenvolvedor Java backend puro, Desenvolvedor
# .NET, Engenheiro de Software Embarcado...). Só conta como match se o
# título TAMBÉM tiver um QUALIFICADORES_DEV junto — mesmo mecanismo de
# KEYWORDS_CARGO_AMBIGUO em config.py.
KEYWORDS_CARGO_AMBIGUO_DEV = [
    "Desenvolvedor",
    "Desenvolvedora",
    "Developer",
    "Programador",
    "Programadora",
    "Software Engineer",
    "Engenheiro de Software",
    "Engenheira de Software",
]

# Termo que precisa aparecer junto no título quando o cargo é ambíguo, pra
# confirmar que é vaga de front-end/full stack JS e não de outra stack.
QUALIFICADORES_DEV = [
    "react",
    "angular",
    "node",
    "next",
    "javascript",
    "typescript",
    "frontend",
    "front-end",
    "front end",
    "web",
    "full stack",
    "fullstack",
]

# Ferramenta que aparece como núcleo do título ("React - Pleno", "Angular
# Sênior"). Só conta como match se o título TAMBÉM tiver uma palavra de
# cargo — espelho de FERRAMENTAS_TITULO/QUALIFICADORES_CARGO em config.py,
# mas com polaridade invertida: lá "desenvolvedor/developer/engenheiro"
# ficam FORA de propósito (pra manter vaga de dev fora do radar de dados);
# aqui são exatamente as palavras que confirmam que a vaga é deste perfil.
FERRAMENTAS_TITULO_DEV = ["React", "Angular", "Node.js", "Next.js"]

QUALIFICADORES_CARGO_DEV = [
    "desenvolvedor",
    "desenvolvedora",
    "developer",
    "engenheiro",
    "engenheira",
    "engineer",
    "programador",
    "programadora",
]

KEYWORDS_DEV = KEYWORDS_CARGO_FORTE_DEV + KEYWORDS_CARGO_AMBIGUO_DEV

# Mesma derivação automática de config.py (TERMOS_CARGO): toda keyword de
# propósito também vira termo de busca, sem manter duas listas divergentes
# à mão. TERMOS_CARGO_EXTRA_DEV cobre termo mais amplo que a keyword exata
# (a keyword em si é mais restrita, de propósito, pro filtro de título).
TERMOS_CARGO_EXTRA_DEV = [
    "react",
    "angular",
    "node.js",
    "next.js",
    "typescript",
    "front-end",
    "full stack",
]

TERMOS_BUSCA_DEV = sorted(set(k.lower() for k in KEYWORDS_DEV) | set(TERMOS_CARGO_EXTRA_DEV))

TERMOS_POR_CICLO_DEV = 10

# Cidade presencial/híbrida aceita — só a cidade real de quem roda este
# perfil (Uberlândia-MG), diferente da whitelist do perfil Dados (Nordeste,
# outra pessoa). "Remoto" é a porta de entrada da regra de modalidade
# remota (ver _FLAGS_REMOTO em job.py), não uma cidade de verdade.
CIDADES_DEV = ["Remoto", "Uberlândia"]

# Toggle único: liga/desliga o eixo de vaga remota fora do Brasil (LinkedIn
# location + mercado aceito) numa penada só. Currículo lista inglês
# "Profissional" (não fluente) — mercado americano/europeu de vaga JS é
# real, mas não medido ainda quanto de ruído (vaga que na prática exige
# inglês fluente em entrevista) esse eixo traz. Desligar aqui volta o
# perfil pra só Brasil (presencial Uberlândia + remoto Brasil) sem mexer
# em mais nada.
ATIVAR_REMOTO_INTERNACIONAL_DEV = True

# Mesmo padrão de LOCATIONS_LINKEDIN_REMOTO_APENAS em config.py: passada
# SÓ remota (f_WT=2) nesses países — não faz sentido buscar presencial num
# país onde quem roda este perfil não mora. Nomes em inglês (ao contrário
# da lista do perfil Dados, que usa nome em português) porque são mercados
# novos, sem teste ao vivo confirmado contra o endpoint do LinkedIn ainda —
# ajustar a grafia se algum não resolver.
LOCATIONS_LINKEDIN_REMOTO_APENAS_DEV = (
    ["United States", "United Kingdom", "Canada", "Germany", "Ireland", "Netherlands"]
    if ATIVAR_REMOTO_INTERNACIONAL_DEV
    else []
)

# Mercado aceito pra vaga remota COM escopo geográfico declarado no texto
# (ver extrair_escopo_remoto em job.py) — lista do QUE ACEITAR, separada da
# lista de ONDE BUSCAR acima (mesma separação de propósito que
# LOCATIONS_INTL vs. MERCADOS_REMOTO_ACEITOS_INTL em config_intl.py).
MERCADOS_REMOTO_ACEITOS_DEV = ["Brasil"] + (
    ["Estados Unidos", "Reino Unido", "Canadá", "Alemanha", "Irlanda", "Holanda", "Europa", "EMEA"]
    if ATIVAR_REMOTO_INTERNACIONAL_DEV
    else []
)
