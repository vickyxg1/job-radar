# JobRadar — Resumo e Análise de Expansão para Outras Áreas

Documento de análise, sem alteração de código. Gerado em 2026-08-18.

---

## 1. Resumo do projeto

**JobRadar** é um monitor automatizado de vagas de Dados/BI. Roda via GitHub
Actions (cron a cada 3h), sem servidor próprio, custo R$ 0. Varre 8 fontes,
filtra por cargo/cidade/mercado/idioma, pontua relevância (0–10) e notifica
no Telegram — individual para vaga de alta relevância, resumo diário
ranqueado para o resto.

### Arquitetura

- **`main.py`** — motor único. Um `ciclo_de_busca(perfil)` roda os scrapers
  do perfil em paralelo (ThreadPoolExecutor), filtra, deduplica, notifica e
  salva. Dois perfis hoje: `brasil` e `internacional`, escolhidos via
  `--perfil` na linha de comando. Antes eram dois scripts quase idênticos
  (`main.py` + `main_intl.py`); foram unificados num motor + dado
  (`core/perfis.py`), porque a lógica de execução é igual entre mercados —
  só cargo/cidade/termo/fonte diverge.
- **`core/perfis.py`** — define `Perfil` (dataclass): fontes, regras de
  filtro, termos de busca, rodízio, eixo secundário (ex: Ibéria). Cada
  perfil roda de forma isolada (chaves de metadados com sufixo próprio),
  mesmo compartilhando o mesmo `jobs.db`.
- **`core/config.py` / `core/config_intl.py`** — dado puro: cargos aceitos,
  cidades, ferramentas, termos de busca, pesos. Nenhuma lógica aqui.
- **`core/job.py`** — o motor de decisão: `Job`, `RegrasFiltro`,
  `combina_com()` (filtro) e `pontuar_relevancia()` (score). Inclui parsing
  bem elaborado de escopo geográfico de vaga remota (ex: distinguir
  "Remote — US only" de "Remote — Brazil", ou sigla de UF brasileira vs.
  estado americano que colide, tipo "AL"/"MA"/"PA").
- **`scrapers/`** — um módulo por fonte: LinkedIn, Gupy, Indeed, Catho,
  GeekHunter, 99Jobs, Solides, WeWorkRemotely (+ variantes internacionais).
  Cada scraper só faz *buscar_vagas()* com Playwright e devolve `Job`s crus
  — o filtro/score é sempre externo, em `core/job.py`.
- **`database/database.py`** — SQLite versionado no próprio Git (histórico
  de dedup *é* o commit). Guarda vaga vista, fila de digest, metadados de
  rodízio.
- **`notifier/telegram.py`** — notificação individual, digest diário,
  callback de feedback 👍/👎.
- **73 testes automatizados**, rodando em CI a cada push — cada um
  documentando um bug real já corrigido (não cenário hipotético).

### Engenharia notável

- **Filtro de 3 níveis de confiança**: cargo forte (inequívoco) passa
  sozinho; cargo ambíguo (ex: "Business Analyst" — existe em qualquer área)
  só conta com qualificador de dados junto no título; ferramenta (ex:
  "Power BI") só conta com palavra de cargo junto. Nada aprova por
  keyword solta.
- **Score sem ML**: 5 sinais com peso calibrado contra o histórico real do
  banco (cargo, ferramenta, senioridade, mercado, idioma) — não chutado.
- **Rodízio de termos de busca** (`TERMOS_POR_CICLO`): a lista de termos
  cresce, mas o custo por ciclo não — cada ciclo cobre um bloco, avança e
  guarda o offset no próprio banco. É o mecanismo que evita que expandir
  escopo (mais termos) exploda o tempo de execução.
- **Resiliente por medição, não por design abstrato**: cada regra do
  código carrega comentário "MEDIDO" citando o bug real e o log que provou
  o problema (ex: digest nunca enviado, banco perdido ao mover pasta,
  vaga americana passando como remota pro Brasil).

### Estado atual (do README)

| Item | Valor |
|---|---|
| Vagas processadas (7–15 ago) | 1.052 |
| Concentração numa única fonte (LinkedIn) | 89,5% |
| Testes automatizados | 73 |
| Fontes monitoradas | 8 |
| Frequência | a cada 3h |
| Custo | R$ 0 |

O próprio README trata a concentração em LinkedIn como risco medido, não
ignorado — o endpoint não é oficial e pode bloquear.

---

## 2. Expandir para outras áreas (não-dados) — é viável?

**Sim, e a arquitetura já foi desenhada pra isso**, mesmo que hoje só
existam dois perfis de *mercado* (Brasil/Internacional), não de *área*.

### O que já é reaproveitável sem tocar

- `Perfil` (dataclass) já separa tudo que muda por contexto: cargo aceito,
  cidade, termo de busca, fonte, regra de idioma. Um perfil novo (ex:
  "Dev", "Suporte/Administrativo") seguiria o mesmo padrão que já existe
  entre Brasil e Internacional — motor único, dado novo.
- Os scrapers (LinkedIn, Gupy, Indeed, Catho, GeekHunter, 99Jobs, Solides)
  não são hardcoded pra dados: recebem `termos_busca` como parâmetro e
  devolvem qualquer vaga que o termo encontrar no site. Trocar o termo já
  muda a área coberta.
- `RegrasFiltro` (3 níveis de confiança) e `pontuar_relevancia()` (5
  sinais) são genéricos — não fazem nenhuma suposição de domínio de dados
  no código, só nas *listas* passadas (`KEYWORDS_CARGO_FORTE` etc.).

### O que é 100% hardcoded pra dados/BI hoje

- `KEYWORDS_CARGO_FORTE`, `KEYWORDS_CARGO_AMBIGUO`, `QUALIFICADORES_DADOS`,
  `FERRAMENTAS_TITULO`, `TERMOS_BUSCA` em `core/config.py` — tudo cargo,
  ferramenta e termo de dados/BI.
- Isso é exatamente o "dado" que teria que ser reescrito por área nova —
  não a lógica.

### Custo real de expandir: cobertura, não código

O ponto de atenção não é "dá pra programar" (dá, e a base já foi pensada
pra isso) — é o **rodízio de termos**. Cada termo novo de busca dilui a
frequência de cobertura dos que já existem, porque `TERMOS_POR_CICLO` é
fixo por perfil. Duas formas de lidar com isso, sem inventar nada:

1. **Perfil isolado** (ex: `--perfil dev`, rodando em paralelo ao `brasil`
   na mesma execução do workflow) — mesmo padrão que já existe hoje entre
   `brasil` e `internacional`. Não dilui o rodízio de dados, mas soma custo
   de execução (mais scrapers rodando por ciclo).
2. **Mesmo perfil, termos misturados** — mais simples, mas cada termo novo
   de outra área compete pelo mesmo bloco de rodízio, atrasando a cobertura
   de dados. Só faz sentido se a área nova for pequena/complementar.

Dado que o rodízio + fontes já são o gargalo medido (89,5% de concentração
numa fonte só), a opção 1 (perfil isolado) é a que não arrisca piorar a
cobertura do que já funciona.

---

## 3. O que aproveitar do outro projeto (Job-hunter)

`C:\Users\Vicky\Desktop\Projetos\Pessoal\Job-hunter` — Node/Express, app
local (não automação headless), objetivo bem mais amplo: coletar vaga,
gerar currículo/cover letter adaptado via IA (multi-provider), gerar PDF,
dashboard, histórico por empresa. Documentado em `docs/01-PRD.md` a
`03-ROADMAP.md`, com 17 sprints planejados.

### Estado (por que "não funciona tão bem")

- Todo o código data do mesmo dia (3–4 jun), sem commits depois — projeto
  parado no meio, não abandonado por decisão, aparenta ter sido um sprint
  único que não terminou.
- Chegou a implementar bem além do início: scrapers de API
  (`adzuna.js`, `remoteok.js`, `remotive.js`, `arbeitnow.js`, `gupy.js`),
  scraping via Playwright (`greenhouse.js`, `lever.js`, `linkedin.js`),
  scoring heurístico (`jobScoring.js`), worker de IA (`aiWorker.js`),
  auto-geração (`autoGenerator.js`) — ou seja, passou de boa parte do
  roadmap (~sprint 14–15 de 17).
- Mas o roadmap exige currículo adaptado + cover letter + PDF + multi-
  provider de IA + dashboard completo pra ser considerado "concluído" —
  escopo bem maior que o do JobRadar, e é exatamente esse tipo de escopo
  amplo (IA generativa, múltiplas integrações, front próprio) que
  historicamente trava projeto individual no meio.
- Não tem testes automatizados nem CI — diferença estrutural grande frente
  ao JobRadar (73 testes, CI a cada push). É provável que parte do "não
  funciona tão bem" seja regressão silenciosa sem cobertura pra pegar.

### O que É reaproveitável dali, especificamente

O achado útil não é o código (stacks diferentes: Python vs. Node), é a
**escolha de fontes** para cobrir vaga fora de dados:

- **Adzuna, RemoteOK, Remotive, Arbeitnow** — agregadores com API pública,
  cobrindo qualquer área/tech, sem depender de scraping frágil de portal
  (não têm o risco de bloqueio que o LinkedIn tem hoje no JobRadar).
- **Greenhouse, Lever** — ATS (sistema de recrutamento) usado por muita
  empresa de tecnologia; página de vaga é estruturada e estável, mais fácil
  de raspar de forma confiável que o card do LinkedIn.

Essas fontes são candidatas naturais a **scraper novo do JobRadar** (mesmo
padrão de `scrapers/base.py`) se a área de expansão escolhida for
tech/dev em geral — cobrem vaga de outra área nativamente, sem precisar de
scraping HTML: só muda o termo da query. Reduziria também a dependência de
LinkedIn (o risco medido no README).

### Comparação direta

| | JobRadar | Job-hunter |
|---|---|---|
| Escopo | Encontrar e notificar vaga | Encontrar, pontuar, gerar currículo/cover letter/PDF via IA |
| Estado | Em produção, medido | Parado no meio, 1 dia de código |
| Testes | 73, CI a cada push | Nenhum |
| Stack | Python + Playwright + SQLite | Node/Express + Playwright + SQLite + IA |
| Fontes | 8, majoritariamente scraping HTML | APIs (Adzuna/RemoteOK/Remotive/Arbeitnow) + ATS (Greenhouse/Lever) + LinkedIn |
| Base pra evoluir | Melhor — arquitetura testada e já pensada pra multi-perfil | Fraca sozinha, mas boa fonte de ideia de fonte/scraper |

---

## 4. Decisões em aberto (não decididas aqui, de propósito)

1. **Qual área expandir?** Dev/TI geral tem maior sobreposição de skill com
   quem já busca dados (SQL, Python) e é onde Greenhouse/Lever/Adzuna
   rendem melhor. Suporte/administrativo seria essencialmente cargo novo do
   zero, sem essas fontes ajudando tanto.
2. **Perfil isolado ou mesclado?** Perfil isolado (`--perfil <nova-area>`)
   não arrisca a cobertura de dados que já funciona; mesclado é mais
   simples de manter mas compete pelo mesmo rodízio de termos.
3. **Vale importar Adzuna/Arbeitnow/Greenhouse/Lever como scraper novo do
   JobRadar**, independente da área escolhida? Reduziria a dependência de
   89,5% numa fonte só, isso sozinho já é ganho mesmo sem mudar de área.
