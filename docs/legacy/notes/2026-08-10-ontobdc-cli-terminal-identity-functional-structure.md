# Estrutura funcional do `cli` e da identidade visual de terminal (message boxes)

**Data:** 10 de agosto de 2026
**Escopo:** o que `ontobdc/src/ontobdc/cli` faz, em que ordem, e como a resposta final de um comando vira algo visível no terminal — com foco em message boxes, por pedido explícito — seguido de uma proposta de estratégia (§9) para unificar os dois sistemas de renderização hoje coexistindo em um único caminho consistente. Complementa os levantamentos anteriores sobre [pastas](2026-08-10-ontobdc-directory-structure-survey.md), [storage](2026-08-10-ontobdc-storage-module-functional-structure.md) e [view](2026-08-10-ontobdc-view-module-functional-structure.md).
**Fontes:** leitura direta de `ontobdc/src/ontobdc/cli/**` e das peças de `ontobdc/src/ontobdc/view` que a CLI consome para desenhar suas respostas (`view/adapter/response.py`, `view/plugin/render/rich/layout.py`, `view/domain/model/table.py`, `view/domain/port/layout.py`, `view/component/logo`, `view/component/surface`); confirmação cruzada com `ontobdc/CHANGELOG.md`.
**Nota metodológica:** onde o código e a documentação/CHANGELOG parecem divergir, este documento registra a divergência como observação (§6), sem presumir qual lado está "certo" — conforme `AGENTS.md` §3 ("When the code and documentation disagree, do not silently choose one. State the conflict").

---

## 1. O que `cli/` possui

`cli/` é o ponto de entrada do pacote (`ontobdc.cli:main`, declarado em `pyproject.toml`), responsável por: parsear argumentos, descobrir e resolver o comando pedido, aplicar estratégias de parâmetro, checar pré-condições de saúde, executar o comando, e desenhar a `CommandResponse` resultante em um dos três formatos (`rich`, `json`, `html`).

O contexto de execução (`CliContextAdapter`, `adapter/context.py`) não é um objeto solto em memória — é, ele mesmo, um grafo RDF sob o namespace `urn:ontobdc:context/`, persistido como `context.ttl` dentro de `.__ontobdc__/` (o mesmo arquivo que o módulo `storage` trata como parte de seu próprio ciclo de vida — ver o documento sobre `storage`, §1). CLI e storage compartilham literalmente o mesmo artefato de contexto.

---

## 2. Duas gerações de arquitetura de comando, lado a lado

`adapter/command.py` declara isso explicitamente no próprio docstring da classe que hoje faz a ponte entre as duas:

> *"Small adapter layer for future command-style CLI execution. The current `ontobdc.cli.__init__.py` still contains the **legacy** dispatch flow, so this adapter must be safe to call before that logic runs."*

Ou seja: `CliCommandRunAdapter` (mais novo, com `check()` por **nível de saúde** — §5) já existe e já é usado por `main()`, mas o próprio `__init__.py` ainda carrega, no mesmo arquivo, boa parte da lógica de parsing/parâmetros "à moda antiga" (`_apply_explicit_parameter_values`, `_resolve_required_parameter_names` — funções de módulo, não métodos de uma classe testável isoladamente). Isso não é um julgamento de qualidade — é uma transição de arquitetura em andamento, e o código a nomeia como tal. É o mesmo padrão de débito técnico *declarado* já visto em `view/plugin/capability/hardcoded.py` (documento sobre `view`, §2.1).

---

## 3. A quinta máquina de prontidão: `CliInitProcessState`

Segue exatamente o mecanismo genérico (Evaluator + Handler + statechart YAML + Capability + Check/Hotfix) descrito em detalhe no documento sobre `storage` §2 — aqui aplicado ao comando `ontobdc init`:

| Ordem | Estado | O que significa | Capability |
|---|---|---|---|
| 1 | `ONTOBDC_DIRECTORY_READY` | o diretório alvo contém `.__ontobdc__` | `transformation_to_ontobdc_directory_ready.py` |
| 2 | `ENGINE_READY` | o engine configurado está disponível na config do projeto | `transformation_to_engine_ready.py` |
| 3 | `STORAGE_INDEX_HEALTHY` | `storage.ttl` existe e está conforme os checks de bootstrap | `transformation_to_storage_index_healthy.py` |
| 4 | `EXECUTION_CONTEXT_HEALTHY` | `context.ttl` existe e está conforme os checks de bootstrap | `transformation_to_execution_context_healthy.py` |
| 5 | `CONFIG_ADAPTER_READY` (final) | `config.yaml` existe e está conforme o contrato de bootstrap | `transformation_to_config_adapter_ready.py` |

IDs de capability seguem a mesma convenção dos outros módulos: `org.ontobdc.cli.plugin.capability.transformation.target.<estado>`. Diferente de `storage`, só dois dos cinco estados têm par `check/hotfix` dedicado em `plugin/check/` (`has_valid_config_file`, `has_valid_engine`) — os outros três (`ontobdc_directory_ready`, `storage_index_healthy`, `execution_context_healthy`) não têm diretório de check próprio dentro de `cli/plugin/check/`, o que sugere que sua verificação está embutida na própria capability ou é delegada a checks de outro módulo (o mesmo tipo de reaproveitamento cross-módulo documentado para `container_healthy` em `storage`/`view`) — vale confirmar ao tocar neste pipeline.

---

## 4. O fluxo de `main()`, passo a passo

```text
sys.argv
  → _parse_incoming_args()          # remove --json/--rich/--html/--silent/-s da lista de args do comando
  → decide render_type               # 'rich' (padrão) | 'json' se --json | 'html' se --html
  → decide silent                     # --silent ou -s
  → decide logger                      # NullLogRepository (json) | InLineLogger (rich) | StandardConsoleLogger (html/outro)
  → CliCommandRunAdapter.make(...)      # resolve qual CliCommandPort concreto vai rodar
  → _check_command(...)                  # aplica parameter strategies exigidas + roda .check()
  → liga prompt_choice/prompt_raw_text/log_strategy se o comando os declarar (via Port markers)
  → cli_command_run.run() -> CommandResponse
  → _render_response(response, logger, render_type)   # se not silent
  → sys.exit(0)
```

Qualquer exceção não tratada em qualquer etapa acima é capturada no nível mais alto e vira uma `ExceptionCommandResponse(title="Run", description="Command execution failed.", content={"error": str(e)})`, ainda renderizada no mesmo formato pedido, com `sys.exit(1)`.

`_check_command` é o mecanismo de resolução de parâmetro em duas fases: primeiro aplica valores explícitos vindos de flags (`--algo valor` → `context.set_parameter_value("algo", valor)`), depois roda toda `ParameterStrategy` descoberta cujo nome bate com um argumento `valued` e obrigatório declarado no `METADATA` do comando — e só então chama `cli_command_run.check()`, levantando `CliCommandArgumentException` se falhar.

---

## 5. Health checks: uma checagem diferente das máquinas de prontidão

`adapter/health.py` define um mecanismo paralelo às máquinas de estado do §3: `CliCommandHealthPort` com dois níveis registrados em `CliCommandRunAdapter.check()`:

- **nível 0 — `NoHealthCheckAdapter`**: sempre `True`. Usado para comandos que precisam rodar mesmo sem projeto inicializado (`_PROJECT_ROOT_OPTIONAL_COMMANDS = {"dev"}`).
- **nível 1 — `CliBootstrapHealthAdapter`** (padrão): confirma que a raiz do projeto está configurada antes de deixar qualquer comando prosseguir.

A distinção importa: as máquinas de `storage`/`view`/`cli` (§3 e os documentos irmãos) avaliam **o estado de um artefato específico** (um container, uma Surface, o `.__ontobdc__` do projeto). O health check aqui é mais primitivo — "existe sequer um projeto onde rodar isso?" — e roda antes de qualquer máquina de estado ter chance de avaliar coisa alguma.

---

## 6. Duas identidades visuais distintas para dois momentos diferentes

Vale separar, porque o código separa: a identidade visual do **log incremental** (o que aparece enquanto um comando ainda está rodando) é outro sistema, com outra paleta, do que a identidade visual da **resposta final**.

### 6.1 Log incremental — `print_log.sh`

Em modo `rich`, o logger ativo é `InLineLogger` (`adapter/logger.py`), que não formata nada em Python: ele invoca, via `subprocess`, um script chamado `cli/adapter/print_log.sh` (empacotado pela regra `"cli/*.sh"` de `pyproject.toml`) — que, apesar da extensão `.sh`, é um script Python (`#!/usr/bin/env python3`, chamado explicitamente com `sys.executable`, então o shebang nem chega a ser usado). Esse script define sua própria paleta ANSI por nível:

| Nível | Cor | Ícone |
|---|---|---|
| `INFO` | azul | `▶` |
| `WARN`/`WARNING` | amarelo | `⚠️` |
| `ERROR` | vermelho | `❌` |
| `DEBUG` | ciano | `▶` |
| `SUCCESS` | verde | `✔` |
| `NOTICE` | ciano | `▶` |
| *(outro)* | branco | `•` |

Cada linha de log leva também um timestamp `HH:MM:SS`. Em modo `json`, o logger vira `NullLogRepository` (silencioso — a saída deve ser JSON puro, sem ruído de log misturado, exatamente como `AGENTS.md` §6 exige: "maintain JSON output as machine-readable JSON without human logging noise").

### 6.2 Prompts interativos — `old_terminal.py`

`prompt_choice`/`prompt_raw_text` (usados quando um comando implementa `PromptChoiceAwarePort`/`PromptRawTextAwarePort`) vivem em um arquivo chamado `adapter/old_terminal.py` e usam `rich.Panel`/`Group`/`Text` para desenhar o menu de escolha. "Old" é só o nome do arquivo — é o caminho vivo, ativamente conectado em `main()`; não há um `new_terminal.py` substituindo-o hoje.

### 6.3 A resposta final — dois sistemas coexistindo no código-fonte

É aqui que a pergunta do usuário ("message boxes") tem uma resposta em duas partes, porque **dois sistemas de renderização de resposta existem no repositório e nenhum é interno ao outro.**

#### 6.3.1 O que `main()` de fato invoca em modo `rich`: logo + markdown + JSON

`_render_rich_response` usa `ResponseAnsiInformationAdapterLoader` (`cli/adapter/loader.py`), que escaneia `cli/adapter/response.py` por classes que implementam `ResponseAnsiInformationAdapterPort` (`accepts`/`render`), escolhe a mais específica por distância na MRO da resposta, e a invoca. As implementações concretas hoje (`cli/adapter/response.py`):

| Adapter | Aceita | Comportamento |
|---|---|---|
| `LogoResponseAnsiInformationAdapter` | `CommandResponse` (genérico, fallback) | logo ASCII + `# título` + descrição + bloco `json` |
| `HelpResponseAnsiInformationAdapter` | `HelpCommandResponse` | idem (herda o comportamento base) |
| `ListResponseAnsiInformationAdapter` | `ListCommandResponse` | se `content` tiver uma chave `"rows"`, desenha uma tabela `rich.Table.grid` (rótulo colorido com a cor RGB do próprio logo, valor em texto simples) em vez do bloco JSON |
| `MarkdownResponseAnsiInformationAdapter` | `WelcomeCommandResponse` | logo + o campo `content["hero"]` como markdown solto |

Todos usam `LogoComponent` (`view/component/logo/python.py`, `pyfiglet`, texto "Onto" + "BDC" em duas cores) e `TerminalSurface` (`view/component/surface/python.py`) para medir a largura real do terminal e quebrar linha corretamente — a mesma dupla Component/Surface descrita no documento sobre `view` §3, aqui a serviço da resposta de comando, não do prompt.

**Não há bordas, não há `>_`, não há badge colorido de tipo neste caminho.** É logo grande + texto solto + um bloco de código JSON.

#### 6.3.2 O sistema de message box: `RichMessageBoxLayout`

Existe, em paralelo, um segundo sistema completo — mais elaborado visualmente e o que o `CHANGELOG.md` descreve em detalhe nas entradas mais recentes ("Unreleased"). É este:

```text
CommandResponse
    ↓
ResponseMessageBoxAdapterPort.map()   # decide o QUÊ: title_type, color, title, content, subtitle, footer
    ↓
MessageBoxLayoutData                    # contrato estável entre as duas pontas (view/domain/port/layout.py)
    ↓
RichMessageBoxLayout.render()             # decide o COMO: bordas, largura, quebra de linha, tabela
    ↓
string ANSI final
```

Quatro adapters concretos (`view/adapter/response.py`), cada um fixando `title_type`/`color`:

| Adapter | `title_type` | `color` | Observação |
|---|---|---|---|
| `CommandResponseMessageBoxAdapter` | `"OntoBDC"` | `GRAY` | caso genérico |
| `ExceptionCommandResponseMessageBoxAdapter` | `"ERROR"` | `RED` | acrescenta seções `DETAILS`/`TRACEBACK` ao conteúdo |
| `HelpCommandResponseMessageBoxAdapter` | `"OntoBDC"` | `GRAY` | |
| `ListCommandResponseMessageBoxAdapter` | `"OntoBDC"` | `CYAN` | |

**A anatomia visual da caixa** (`RichMessageBoxLayout`, `view/plugin/render/rich/layout.py`):

```text
╭──────────────────────────────────────────╮
│ >_ OntoBDC  Título da resposta            │   ← badge + título (linha 1)
│                                            │   ← linha em branco
│ (linhas de conteúdo, cinza, com wrap)      │
│                                            │
│ Field       Value                          │   ← tabela, se o conteúdo for "harmonioso"
│ chave       valor                           │
╰─ rodapé opcional ──────────────────────────╯
```

- Bordas com caracteres de desenho de caixa (`╭─╮│╰╯`), cor da borda = cor resolvida do `color` da resposta.
- O badge `>_ <title_type>` é sempre **negrito**; fica **azul fixo quando `title_type == "OntoBDC"`**, senão usa a cor do próprio tipo de resposta (vermelho para `ERROR`) — é exatamente o `>_ OntoBDC ...` / `>_ ERROR ...` que o `CHANGELOG.md` documenta na entrada sobre remoção do prefixo redundante "OntoBDC" dos títulos (a entrada explica que o badge já mostra "OntoBDC" uma vez, então repeti-lo no campo `title` virava `>_ OntoBDC OntoBDC Run` — daí a limpeza).
- Rodapé, quando existe, não é uma linha extra: fica **embutido na própria borda inferior** (`╰─ footer ──╯`).
- Conteúdo passa por um parser de markdown-lite próprio (não usa a lib `rich` para isso, é regex própria): `#`/`##` viram linha isolada + linha em branco; `###`/`####+` viram `texto:`/`  texto:`; `-`/`*`/`+` viram `• texto` com indentação; `**negrito**` e `` `código` `` são **removidos** (não convertidos para ANSI bold — a ênfase original se perde, vira texto plano).
- **Detecção de tabela "harmoniosa"** (a feature mais recente do `CHANGELOG.md`): em `view/adapter/response.py`, `_is_harmonious_record` (dict raso, todo-escalar) vira tabela de duas colunas `Field`/`Value`; `_is_harmonious_table` (lista não vazia de dicts com exatamente as mesmas chaves, todos os valores escalares) vira tabela multi-coluna. Qualquer coisa fora desse formato (tipos mistos, chaves diferentes por item, valores aninhados) cai de volta para a lista com marcadores recursiva (`_format_markdown_block`/`_format_dict_block`/`_format_list_block`), com uma heurística de "chave preferida" (`repository`, `name`, `id`, `title`, `file`, `path`, `branch`) para decidir qual campo vira a primeira linha de um item de lista.
- A tabela detectada não vira `rich.Table` nem HTML — vira um **bloco de texto opaco com marcadores privados** (`view/domain/model/table.py`): `encode_table()` serializa cabeçalho/linhas usando `\x1f` (separador de campo ASCII) entre `\x02TABLE\x02`/`\x02/TABLE\x02`, embutido dentro da própria string `content` de `MessageBoxLayoutData`. Só `RichMessageBoxLayout` (via `split_segments()`) sabe abrir esses marcadores de volta em `TableSegment` e desenhar colunas alinhadas — o próprio código comenta que é *"a private convention... not a public content format"*. O motivo declarado é que só o renderer conhece a largura real do terminal para decidir a largura de cada coluna (`_fit_column_widths`, que encolhe colunas proporcionalmente até caber, preservando a primeira coluna em negrito branco e as demais em cinza).

---

## 7. Observação: os dois sistemas de resposta coexistem, mas só um está com fio ligado

Isto é uma constatação de leitura de código, não uma crítica: `grep` por instanciação real (não apenas `import`) de `RichMessageBoxLayout(`, `ResponseMessageBoxAdapterLoader(` e `MessageBoxLayoutData(` em todo `src/` mostra que essas três classes **só aparecem construídas dentro dos próprios arquivos que as definem** (`view/plugin/render/rich/layout.py`, `view/adapter/loader.py`, `view/adapter/response.py`). Nenhum teste em `tests/` as referencia.

`cli/__init__.py` importa `ResponseMessageBoxAdapterLoader`, `ResponseMessageBoxAdapterPort` e `RichMessageBoxLayout` no topo do arquivo (linhas 18–20) — mas nenhuma das três é usada em `main()` nem em nenhuma função auxiliar do módulo. O mesmo vale para `RichMessageBoxLayout` e `ExceptionCommandResponseMessageBoxAdapter`, importados em `cli/adapter/response.py` mas não referenciados no corpo de nenhuma classe ali (confirmado por leitura completa do arquivo). O caminho que `_render_rich_response` de fato executa é o do §6.3.1 (`ResponseAnsiInformationAdapterLoader`, um port e um loader diferentes, só coincidentemente parecidos em nome).

Adicionalmente, `_render_html_response` hoje é `print(response)` — o que imprime o JSON de `CommandResponse.__str__()`, não HTML. Isso está em tensão direta com o próprio docstring de `_render_response` ("Supports JSON, rich, and HTML rendering") e com `AGENTS.md` §6, que lista "render modes: rich, JSON, and HTML" como comportamento a preservar.

Não é possível, só pela leitura estática, saber se o sistema de message box é código novo ainda não conectado, um caminho alternativo pensado para outro consumidor (por exemplo, um host que não seja a função `main()` deste arquivo), ou está no meio de uma migração que vai substituir o caminho do §6.3.1. O próprio `CHANGELOG.md` trata a feature de detecção de tabela "harmoniosa" como trabalho corrente ("Unreleased"), o que é consistente com uma integração em andamento. Vale confirmar isso diretamente com quem está desenvolvendo antes de assumir qualquer uma das duas hipóteses.

---

## 8. Síntese

`cli/` está, por seu próprio código-fonte, em transição arquitetural declarada (`CliCommandRunAdapter` novo, dispatch "legacy" ainda presente em `__init__.py`) — e essa mesma transição parece se repetir, sem estar nomeada da mesma forma explícita, na camada de identidade visual da resposta: o caminho realmente executado hoje em modo `rich` é simples (logo ASCII + markdown solto + JSON), enquanto um segundo sistema bem mais elaborado — bordas, badge `>_ <tipo>`, cores por tipo de resposta, detecção automática de tabela "harmoniosa" via convenção privada de marcadores — existe pronto no código e é descrito em detalhe no `CHANGELOG.md`, mas não está, hoje, alcançável a partir de `ontobdc.cli:main`. As duas identidades visuais que *estão* de fato ligadas (log incremental via `print_log.sh` e prompts via `old_terminal.py`) têm paletas e mecanismos próprios, independentes tanto uma da outra quanto dos dois sistemas de resposta final.

---

## 9. Proposta de estratégia: unificar a resposta final do terminal

Objetivo: uma única identidade visual "lisa" — sem costura visível entre tipos de comando, sem dois sistemas concorrentes no código-fonte, sem modo de renderização que minta sobre o que faz. A proposta abaixo é sequenciada em passos pequenos e reversíveis, cada um deixando o repositório num estado íntegro (nenhum passo depende de terminar o seguinte para não quebrar nada), coerente com a exigência de `AGENTS.md` §13 de "make the smallest coherent change" e §2 de não misturar limpeza oportunista com mudança funcional.

### 9.1 Decisão de fundo: qual sistema vira o único

**Recomendação: o sistema de message box (`RichMessageBoxLayout` + `ResponseMessageBoxAdapterPort`) vira o caminho único de `rich`, e o caminho de logo+markdown+JSON (`ResponseAnsiInformationAdapterPort`, `cli/adapter/response.py`) é aposentado.**

Motivos observáveis no próprio código, não preferência estética:

- é o sistema em que o `CHANGELOG.md` mostra investimento ativo e recente (detecção de tabela "harmoniosa", ajuste do badge de título) — indício de que é o caminho que o time já trata como o vigente conceitualmente, mesmo sem estar ligado a `main()`;
- já modela por design a diferença semântica entre tipos de resposta (`title_type`/`color` por adapter — `ERROR` em vermelho, listagem em ciano) enquanto o outro sistema distingue apenas `HelpCommandResponse`/`ListCommandResponse`/`WelcomeCommandResponse` por comportamento de conteúdo, não por identidade visual;
- o contrato `MessageBoxLayoutData → MessageBoxLayoutRendererPort` já foi desenhado para múltiplos renderers (é o mesmo princípio "`Command → Response semântico → Renderer`" do relatório de interface, `ontobdc/docs/2026-08-08-interface-presentation-layer-report.md`) — o que abre caminho direto para resolver a lacuna do `--html` (§9.5) sem inventar um contrato novo.

Esta é uma decisão de produto/arquitetura, não só técnica — o time deve confirmá-la antes de qualquer remoção de código; a leitura estática não decide sozinha se o sistema de message box foi abandonado ou é o destino pretendido (já registrado como incerteza em §7).

### 9.2 Reaproveitar, não descartar, o que o caminho atual faz bem

Duas peças do sistema hoje ligado (`cli/adapter/response.py`) valem a pena preservar, só que hospedadas dentro do sistema de message box em vez de ao lado dele:

- **O logo ASCII (`LogoComponent`) e a medição de largura (`TerminalSurface`)** não têm equivalente no sistema de message box hoje (`RichMessageBoxLayout` mede a largura do terminal sozinho, com seu próprio `shutil.get_terminal_size`, duplicando o que `TerminalSurface` já faz). Proposta: `RichMessageBoxLayout` passa a receber uma `TerminalSurface` injetada (o mesmo objeto que `LogoComponent` usa) em vez de chamar `shutil` diretamente — elimina uma segunda fonte de verdade para "quantas colunas tem este terminal" e reaproveita a mesma dupla Component/Surface documentada no levantamento de `view` (§3).
- **O banner do logo em si.** Proposta: o logo vira uma linha renderizada **uma vez por invocação do CLI**, acima da(s) caixa(s) — não dentro da borda de cada resposta. Isso também resolve de forma natural o caso do `WelcomeCommandResponse` (`content["hero"]`), que passa a ser só mais um conteúdo dentro de uma caixa `OntoBDC`/cinza como qualquer outro, sem precisar de um adapter dedicado só para desenhar markdown solto.

### 9.3 Unificar a paleta de cores/severidade numa única fonte

Hoje existem **três** tabelas de cor independentes, sem nada garantindo que concordem entre si:

1. `print_log.sh` — `INFO`/`WARN`/`ERROR`/`DEBUG`/`SUCCESS`/`NOTICE` com cor + ícone próprios;
2. `RichMessageBoxLayout.COLOR_MAP` — `RED`/`GREEN`/`YELLOW`/`CYAN`/`BLUE`/`WHITE`/`GRAY`/`INFO`;
3. o `color`/`title_type` fixado em cada `*MessageBoxAdapter` (`view/adapter/response.py`).

Proposta: extrair um módulo único de tokens semânticos de terminal (ex.: `ontobdc/shared/domain/model/terminal_palette.py`, ao lado dos outros modelos cross-cutting de `shared/` — ver o levantamento de pastas, §2.5) com um enum `TerminalSeverity` (`INFO`/`WARNING`/`ERROR`/`DEBUG`/`SUCCESS`/`NOTICE`/`NEUTRAL`) mapeado uma única vez para `(cor ANSI, ícone)`. `RichMessageBoxLayout`, os `*MessageBoxAdapter` e o substituto de `print_log.sh` (§9.4) passam a importar dessa fonte única. Resultado prático: uma mensagem de erro tem a **mesma** cor vermelha em um log incremental, num badge `>_ ERROR` e — se um dia existir — num equivalente HTML, porque os três leem do mesmo lugar.

Esse mesmo módulo é o lugar certo para decidir, de uma vez, a questão hoje inconsistente do texto em **negrito**: `RichMessageBoxLayout` remove `**negrito**`/`` `código` `` do markdown-lite em vez de convertê-los para ANSI bold (§6.3.2); vale decidir explicitamente se isso é intencional (simplicidade/legibilidade) ou uma lacuna a fechar, e registrar a decisão aqui.

### 9.4 Tirar o log incremental de um subprocesso

`InLineLogger` starta um processo Python novo (`subprocess.run([sys.executable, ...])`) a cada linha de log — sem necessidade, já que `print_log.sh` já é Python puro chamado explicitamente com `sys.executable` (o shebang `.sh` nunca é usado). Proposta: mover a lógica de `print_log.sh` para um módulo Python normal importável (`cli/adapter/log_format.py`, por exemplo) e chamá-lo em processo, sem `subprocess`. Ganhos: elimina o custo de spawn por linha de log, permite o mesmo módulo consumir a paleta única do §9.3 sem duplicar a tabela de cores, e remove a estranheza de um arquivo `.sh` cujo conteúdo é Python. Se houver uma razão deliberada para isolar essa saída num processo separado (ex.: isolamento de falhas de log em relação ao processo principal), ela deve ser confirmada antes desta mudança — não é óbvia a partir do código atual.

### 9.5 Fechar a lacuna do `--html`

Duas opções, em ordem de esforço:

- **Imediata e barata:** `_render_html_response` para de fingir sucesso. Levanta `NotImplementedError`/loga um erro específico em vez de imprimir JSON sob um nome que promete HTML — alinhado com `AGENTS.md` §15 ("errors are specific enough to diagnose") e com a regra geral de não simular sucesso. Isso pode ser feito **antes** e **independentemente** de qualquer decisão sobre §9.1.
- **Definitiva:** implementar `HtmlMessageBoxLayout(MessageBoxLayoutRendererPort)`, reaproveitando a mesma `MessageBoxLayoutData` que a caixa de terminal já consome (é exatamente o contrato para isso — `Response semântico → Renderer específico do target`, relatório de interface §6.1). Só faz sentido depois de §9.1 estar resolvido, senão duplica-se o problema de dois sistemas paralelos em mais um formato de saída.

### 9.6 Proteger a unificação com testes de caracterização

`AGENTS.md` §11 pede teste de "response rendering" para mudança de comando e "generation test... data binding" para mudança de view; nada disso existe hoje para nenhum dos dois sistemas de resposta (`tests/` não referencia `MessageBox` nem os adapters ANSI). Proposta de sequência segura:

1. **Antes de tocar em qualquer renderer**, escrever testes de caracterização que capturam a saída ANSI atual (com `ANSI_ESCAPE_PATTERN`/`_strip_ansi` como referência para uma variante "texto visível") para pelo menos um fixture de cada tipo de resposta (`CommandResponse`, `ExceptionCommandResponse` com e sem traceback, `HelpCommandResponse`, `ListCommandResponse` com e sem `"rows"`, `WelcomeCommandResponse`) — travando o comportamento de **ambos** os sistemas como estão hoje, para que a migração tenha uma base de comparação.
2. Ao ligar o sistema de message box em `_render_rich_response` (§9.1), atualizar esses testes para o novo formato esperado — a diferença entre o "antes" e o "depois" nos testes é, por si, a documentação da mudança visual.
3. Só remover `cli/adapter/response.py`/`ResponseAnsiInformationAdapterLoader` depois que os testes novos cobrirem os mesmos casos que os testes de caracterização cobriam.

### 9.7 Ordem de execução recomendada

```text
1. Testes de caracterização dos dois sistemas atuais (§9.6.1)     — sem mudar comportamento
2. --html para de mentir (§9.5, opção imediata)                    — sem mudar rich/json
3. Paleta única de severidade/cor (§9.3)                             — sem mudar comportamento visível
4. print_log.sh → módulo Python in-process (§9.4)                     — sem mudar comportamento visível
5. TerminalSurface injetado em RichMessageBoxLayout (§9.2)              — sem mudar comportamento visível
6. Ligar RichMessageBoxLayout em _render_rich_response (§9.1)            — MUDA a saída rich; testes do passo 2 do §9.6 cobrem isso
7. Banner de logo fora da caixa + aposentar o sistema ANSI antigo (§9.2)   — remove código morto
8. HtmlMessageBoxLayout (§9.5, opção definitiva)                            — fecha a lacuna do --html de verdade
9. Atualizar CHANGELOG.md e AGENTS.md/README onde citarem o comportamento antigo
```

Os passos 1–5 são preparação pura, sem alterar nenhum byte do que já é impresso no terminal hoje — só o passo 6 muda a saída visível de `ontobdc <comando>` sem flags, e é o único ponto da sequência que exige validação humana direta (rodar comandos reais e olhar o terminal), não só testes automatizados.
