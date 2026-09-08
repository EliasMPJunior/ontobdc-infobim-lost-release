# Levantamento da estrutura de pastas do `ontobdc/`

**Data:** 10 de agosto de 2026
**Escopo:** o submódulo `ontobdc` (pacote Python `ontobdc`, "Ontology-Based Datasets & Containers"), na branch de desenvolvimento ativa (`v0.14`, conforme `AGENTS.md`).
**Fontes:** listagem direta do diretório (`find`), `ontobdc/AGENTS.md` §4 ("Repository architecture"), `ontobdc/README.md`, `ontobdc/pyproject.toml`, `ontobdc/CHANGELOG.md`.
**Método:** inspeção estrutural — não é uma auditoria de código nem uma revisão de correção. O objetivo é registrar *por que* cada divisão lógica existe, não apenas *o que* ela contém.

---

## 1. Nível raiz

```text
ontobdc/
├── AGENTS.md          # contrato de trabalho para agentes de IA (arquitetura, regras, definição de "pronto")
├── CHANGELOG.md        # histórico de mudanças por versão, incluindo breaking changes explícitas
├── LICENSE
├── README.md            # contrato público do produto (anotações tipadas, editor, workspace, Subject Page)
├── docs/                    # documentação interna do próprio pacote (não confundir com o ./docs do workspace)
├── lab/                        # protótipos desacoplados do pacote instalável
├── pyproject.toml                # identidade do pacote, dependências, entry point, regras de package-data
├── reinstall.sh / reinstall.ps1    # bootstrap de ambiente de desenvolvimento (bash + PowerShell)
├── src/ontobdc/                       # o pacote em si
└── tests/                                # espelha src/ontobdc — é tratado como parte da especificação
```

Valor semântico do nível raiz: separa **identidade do pacote** (`pyproject.toml`, `LICENSE`, `README.md`), **regras de trabalho** (`AGENTS.md`), **histórico versionado** (`CHANGELOG.md`), **implementação** (`src/`), **verificação** (`tests/`), **documentação de suporte** (`docs/`) e **experimentação** (`lab/`) em compartimentos que não se misturam. Um agente ou desenvolvedor novo consegue responder "onde eu leio a regra?", "onde está o código?", "onde está a prova de que funciona?" e "onde eu posso quebrar coisas sem consequência?" só pela posição do arquivo, sem abrir nada.

`reinstall.sh`/`reinstall.ps1` existirem em paralelo (mesmo roteiro, duas linguagens de shell) é um sinal estrutural próprio: o projeto trata Windows como cenário de primeira classe, não como afterthought — o que `AGENTS.md` §10 também declara explicitamente ("Account for Windows paths and PowerShell usage as first-class scenarios").

---

## 2. O padrão arquitetural de `src/ontobdc/<módulo>/`

`AGENTS.md` §4 é a fonte de verdade explícita e vale citar por inteiro, porque toda a árvore de `src/` é a aplicação literal desta regra:

> - `domain/`: models, value objects, requests, responses, exceptions, and ports;
> - `facade/`: stable contracts exposed across logical components;
> - `adapter/`: concrete implementations of ports and external integration;
> - `plugin/`: dynamically discovered commands, capabilities, checks, hotfixes, renderers, and parameter strategies;
> - `shared/`: cross-cutting contracts and reusable infrastructure;

Cada "módulo lógico" (`cli`, `context`, `dev`, `entity`, `shared`, `storage`, `view`) repete um subconjunto dessas camadas conforme sua maturidade — nenhum módulo tem as cinco completas, e isso é informativo por si (ver §4).

### 2.1 `domain/` — o que o código *significa*, sem depender de como é executado

Contém modelos (`model/`), portas/interfaces (`port/`), requisições e respostas (`request/`, `response/`), exceções (`exception/`) e, em vários módulos, máquinas de estado (`machine/`). Exemplo: `storage/domain/port/repository.py` declara o contrato de um repositório de containers sem saber se ele será implementado em disco local, ZIP ou outro meio.

Regra de dependência (`AGENTS.md` §4): **domain não importa adapter, UI, filesystem ou plugin concreto.** Isso é o que torna o domínio testável isoladamente e o que impede que uma decisão de infraestrutura (ex.: "os containers ficam em disco") vaze para dentro da definição de "o que é um container".

A presença recorrente de `domain/machine/` (`cli/domain/machine/state.py`, `storage/domain/machine/state.py` + `attach_state.py`, `view/domain/machine/state.py` + `surface_state.py`, `context/domain/machine/document_import_state.py` + `learning_state.py`) mostra que fluxos com ciclo de vida (execução de comando, anexação de container, geração de surface, importação de documento, aprendizado) são modelados explicitamente como **máquinas de estado versionadas no domínio**, não como sequências implícitas de `if`s espalhados pelo código de aplicação. O projeto depende da biblioteca `sismic` (ver `pyproject.toml`) precisamente para isso.

### 2.2 `facade/` — fronteira estável entre componentes lógicos

Só existe hoje em `shared/facade/` (`port/`, `request/`, `response/`, `exception/`, `adapter/`). É a camada que os outros módulos (`cli`, `context`, `storage`, `view`) atravessam quando precisam conversar entre si sem se acoplar às implementações internas uns dos outros — por exemplo, `shared/facade/port/container.py` e `shared/facade/port/dataset.py` são o vocabulário comum que qualquer módulo usa para falar de "container" ou "dataset" sem importar `storage/domain/model` diretamente.

Valor semântico: é a única camada com "estável" no próprio nome do contrato do `AGENTS.md` — o resto do sistema pode mudar por baixo dela sem quebrar quem a consome.

### 2.3 `adapter/` — onde a decisão concreta mora

Implementações reais dos `port`s do domínio e integrações externas. Ex.: `storage/adapter/repository.py` implementa o `port` declarado em `storage/domain/port/repository.py`; `storage/adapter/attach_machine.py` executa a máquina de estado declarada em `storage/domain/machine/attach_state.py`.

Regra de dependência: **adapters implementam ports; ports não importam adapters** — a seta de dependência aponta sempre do concreto para o abstrato, nunca o contrário. Isso é o que permite, em tese, trocar a implementação de armazenamento sem tocar no domínio ou nos plugins que o consomem.

### 2.4 `plugin/` — o sistema de descoberta dinâmica, e sua própria sub-taxonomia

É a camada mais estruturalmente elaborada do repositório. `AGENTS.md` §5 descreve descoberta dinâmica por varredura de diretórios como `plugin/capability`, `plugin/command`, `plugin/parameter` — e a árvore real confirma cinco sub-espécies recorrentes:

| Subpasta | Papel | Exemplo real |
|---|---|---|
| `plugin/command/` | comandos expostos na CLI | `storage/plugin/command/container/attach.py` |
| `plugin/capability/` | unidades de comportamento/transformação que o runtime pode executar | `storage/plugin/capability/transformation/container_healthy.py` |
| `plugin/check/<nome>/` | pré-condição verificável, sempre em subpasta própria | `storage/plugin/check/is_container_metadata_ready/check.py` |
| `plugin/parameter/` | estratégias de resolução de argumento | `context/plugin/parameter/entity.py` |
| `plugin/render/` | estratégias de renderização de resposta | `view/plugin/render/rich/layout.py` |

**Padrão `check/` + `hotfix.py`.** A maioria das pastas `plugin/check/<is_x_ready>/` traz dois arquivos: `check.py` (a verificação) e `hotfix.py` (a correção automática quando a verificação falha) — por exemplo `storage/plugin/check/is_container_manifest_synced/{check.py,hotfix.py}`. Isso não é coincidência de nomenclatura: é um mecanismo de **auto-remediação declarativa** — o sistema não apenas detecta que um container não está pronto, ele sabe como consertá-lo, e as duas responsabilidades (diagnosticar vs. corrigir) ficam em arquivos separados e simetricamente nomeados dentro da mesma pasta.

**Padrão `capability/transformation/*_ready.py` / `*_<particípio>.py`.** Em `context`, `storage` e `view`, as capabilities dentro de `plugin/capability/transformation/` são nomeadas sistematicamente no particípio passado — `container_attached`, `container_cleaned`, `directory_ready`, `identity_resolved`, `storage_index_attached`, `surface_assembled`, `surface_enriched`, `surface_validated`, `vectors_loaded`. O nome de cada arquivo é literalmente um **estado alcançado**, não uma ação imperativa (`attach_container`, `clean_container`). Combinado com o par `check`/`hotfix` acima, isso desenha um runtime organizado como um **grafo de prontidão**: cada capability leva o sistema de um estado para o próximo estado nomeado, e cada check verifica se aquele estado foi de fato alcançado antes de prosseguir — um padrão estrutural muito mais próximo de um *reconciliation loop* (ao estilo de um controlador declarativo) do que de uma sequência linear de funções.

Nota de consistência: em `cli/plugin/capability/` esse mesmo vocabulário aparece **achatado no nome do arquivo** em vez de aninhado em `transformation/` — `transformation_to_engine_ready.py`, `transformation_to_storage_index_healthy.py` — mesma convenção semântica (particípio = estado-alvo), organização física ligeiramente diferente por módulo.

### 2.5 `shared/` — o que é genuinamente transversal, não uma gaveta de miscelânea

`shared/` é o único módulo que acumula `domain/`, `facade/` **e** `adapter/` **e** `plugin/` ao mesmo tempo — reflexo de ser o módulo mais atravessado por todos os outros (config, capability, ontology, resolver, worker, loader). `AGENTS.md` §4 é explícito sobre o risco que essa pasta corre: *"Do not move feature-specific logic into `shared` merely to avoid choosing a bounded context."* A pasta só se justifica estruturalmente enquanto for disciplinada a conter contratos e infraestrutura de fato cross-cutting (ex.: `shared/adapter/config.py`, `shared/domain/model/capability.py`) e não virar um dumping ground.

---

## 3. Os módulos lógicos e sua maturidade relativa

| Módulo | Camadas presentes | O que possui semanticamente |
|---|---|---|
| `cli/` | domain, adapter, plugin | ponto de entrada (`ontobdc.cli:main`), execução de comando, resposta estruturada, logging, modos de renderização (rich/JSON/HTML) |
| `context/` | domain (parcial), adapter, plugin | acesso semântico a entidades/instâncias, importação de documentos, aprendizado, vetorização — o "entendimento" do conteúdo |
| `storage/` | domain, adapter, plugin | containers, datasets, manifests, índices, anexação — a camada mais rica em capabilities/checks, refletindo que persistência confiável é o núcleo de risco do produto |
| `view/` | domain, adapter, plugin, component, asset | geração de HTML, componentes reutilizáveis, pipeline de "surface" (ver §2.4), assets de navegador |
| `shared/` | domain, facade, adapter, plugin | contratos cross-cutting; config, ontologia, capability, resolver — ver §2.5 |
| `entity/` | plugin (só `command/create.py`) | módulo ainda fino/emergente — só expõe um comando, sem `domain`/`adapter` próprios ainda |
| `dev/` | plugin (só `command/proxy.py`) | ferramentas de desenvolvimento interno, deliberadamente mínimo — não é superfície de produto |

A assimetria é informativa: `storage/` e `view/` concentram a maior parte da complexidade estrutural (mais checks, mais capabilities, sub-taxonomias próprias como `component/` e `asset/`), enquanto `entity/` e `dev/` são módulos ainda finos — provavelmente extraídos recentemente de outro lugar ou ainda em formação, sem terem "ganhado" `domain/`/`adapter/` próprios.

### 3.1 `view/component/` — um terceiro tipo de unidade, distinto de `adapter` e `plugin`

`view/component/logo/` e `view/component/surface/` (cada um com um `python.py`) são geradores de representação reutilizáveis — não são portas de domínio nem plugins descobertos dinamicamente, são blocos de montagem que o `view/adapter/` e o `view/plugin/` compõem para produzir a saída final. É a mesma distinção **Tile (unidade espacial) vs. Component (unidade de UI encapsulada)** documentada em `ontobdc/docs/2026-08-08-interface-presentation-layer-report.md` e prototipada em `ontobdc/lab/presentation-tile/index.html` — aqui aparecendo do lado Python/servidor da mesma ideia.

### 3.2 Duas famílias de assets dentro de `view/`

- `view/asset/image/` — estáticos genéricos e compartilhados (logo, favicon), sem dono específico dentro de `view`.
- `view/plugin/asset/{css,js}/annotation/` e `.../workstream/` — CSS/JS específicos de plugins concretos (o editor/workspace de anotações descrito no `README.md`, e o board de WorkStream), fisicamente colocalizados com o plugin que os possui, não centralizados numa pasta `static/` genérica.

Essa divisão é a mesma regra de encapsulamento aplicada a dois níveis: ativos que pertencem à *view como um todo* ficam em `view/asset/`; ativos que pertencem a *um plugin específico da view* ficam dentro daquele plugin. `AGENTS.md` §9 reforça que esses assets devem continuar sendo JavaScript puro, compatível com `file://`, sem framework/bundler — a estrutura de pastas plana (sem `node_modules`, sem build step) é consequência direta dessa regra.

---

## 4. `lab/` — prototipagem deliberadamente fora do pacote instalável

`lab/presentation-tile/index.html` é um protótipo standalone (`onto-tile` / `presentation-surface`, Custom Elements + Shadow DOM) que **não está sob `src/ontobdc/`** e portanto não é empacotado nem versionado como contrato do produto. Seu valor semântico é justamente esse isolamento: é o espaço legítimo para validar uma ideia de interface (aqui, o contrato de negociação `TilePresentationRequest` descrito no relatório de 08/08) antes dela — se aprovada — migrar para dentro da árvore de pacote real (`view/plugin/asset/` ou equivalente) e passar a herdar as regras de `AGENTS.md` (testes, package-data, compatibilidade).

---

## 5. `tests/` como espelho e especificação

`AGENTS.md` §4 declara `tests/` como parte da especificação, não como um apêndice de verificação. A árvore confirma isso na prática: `tests/context/adapter/test_entity_catalog.py` espelha `src/ontobdc/context/adapter/entity_catalog.py`; `tests/view/component/logo/test_python.py` espelha `src/ontobdc/view/component/logo/python.py`; `tests/view/plugin/capability/test_workstream_schedule_relations.py` espelha a capability homônima. A regra implícita de nomenclatura (`test_<nome_do_módulo>.py` no mesmo caminho relativo) é o que permite a um agente (humano ou IA) localizar o teste de qualquer arquivo de produção sem precisar de um índice separado — o caminho já é o índice.

Cobertura hoje é parcial e desigual entre módulos (ex.: `storage/` tem dezenas de capabilities e checks mas nenhum arquivo espelhado ainda em `tests/storage/`), o que é consistente com `storage/` ser, pela contagem de arquivos, o módulo mais jovem/em maior mudança ativa dos dois mais complexos.

---

## 6. `docs/` interno ao pacote vs. `./docs` do workspace

Vale registrar a distinção, já que os dois se chamam `docs/` e convivem no mesmo workspace:

- **`ontobdc/docs/`** (interno ao pacote): hoje só dois arquivos — `2026-08-08-interface-presentation-layer-report.md` (o relatório do modelo de interface dDock/PresentationLayer/Tile) e `test_foundation.md` (fundamentos conceituais de o que é um "projeto de testes"). É documentação de arquitetura/produto específica do runtime OntoBDC.
- **`./docs`** (raiz do workspace, submódulo `ontobdc-doc`, onde este próprio arquivo vive): notas de conversas de domínio datadas (`notes/domain-conversations/`), histórico (`history/`), e documentos de produto adjacentes (`attention-surface.md`). É o espaço de registro do workspace como um todo, não apenas do pacote `ontobdc`.

Nenhuma das duas é redundante com a outra: `ontobdc/docs/` documenta o pacote para quem trabalha dentro dele; `./docs` documenta o raciocínio e o histórico do produto/negócio ao redor de todos os submódulos (`ontobdc`, `presentation`, `mobile`, `my-desktop`, `brasidatacenter`).

---

## 7. Observações e tensões estruturais

- **`pyproject.toml` referencia diretórios que não existem hoje na árvore.** As regras de `package-data` incluem `"core/**"`, `"module/**"`, `"prompt/**"`, `"check/*.sh"`, `"check/*.json"`, `"check/infra/*/*.sh"`, `"entity/*.sh"`, `"run/*.sh"` — nenhum desses caminhos (`core/`, `module/`, `prompt/`, `run/`, `check/` na raiz do pacote) existe em `src/ontobdc/` hoje. Isso é um sinal de **drift entre a configuração de empacotamento e a árvore atual**: ou são resquícios de uma estrutura anterior à consolidação em `domain/facade/adapter/plugin/shared` descrita em `AGENTS.md` §4, ou são preparação antecipada para módulos ainda não criados. `AGENTS.md` §12 é explícito que "a feature that disappears from the wheel is not done" — o inverso (regras de wheel para pastas que não existem) não quebra nada, mas é ruído de manutenção que vale confirmar na próxima limpeza de packaging.
- **`entity/` e `dev/` são módulos de uma camada só.** Isso não é necessariamente um problema — pode ser exatamente o estágio certo de maturidade para o que cada um faz hoje —, mas é a diferença estrutural mais visível em relação aos módulos "completos" (`storage`, `view`, `context`) e útil de acompanhar: se `entity/` crescer, é esperado que ganhe `domain/` e `adapter/` próprios em vez de continuar dependendo implicitamente de `shared/`.
- **A convenção de nomenclatura por particípio passado em `plugin/capability/transformation/` não é aplicada uniformemente** (nível de aninhamento difere entre `cli/` e os demais módulos — ver §2.4). Não é um erro, mas é uma inconsistência estrutural pequena entre módulos que, de resto, seguem a mesma convenção arquitetural com bastante disciplina.

---

## 8. Síntese

A árvore de `ontobdc/` implementa, de forma consistente e deliberada, uma arquitetura hexagonal (ports & adapters) com um sistema de plugins descoberto dinamicamente por cima dela. As fronteiras (`domain` não conhece `adapter`; `adapter` implementa `domain`; `plugin` compõe os dois; `shared` só existe para o que é realmente transversal) não são apenas uma convenção de nomes — são reforçadas por uma regra de dependência explícita em `AGENTS.md` §4 e por um mecanismo real de descoberta (`AGENTS.md` §5) que só encontra um plugin se ele estiver no lugar certo. O resultado prático mais distintivo é o par `check/hotfix` combinado com a nomenclatura de capabilities como estados-alvo: o runtime não é uma sequência de comandos, é um grafo de prontidão que se autodiagnostica e se autocorrige módulo a módulo (`storage`, `context`, `view`) antes de expor uma operação como disponível.
