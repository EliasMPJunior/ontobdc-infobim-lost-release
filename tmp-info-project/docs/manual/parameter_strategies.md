# Manual de Parameter Strategies do OntoBDC

Este documento descreve como o motor de parâmetros dinâmicos do OntoBDC
descobre, carrega, seleciona e executa *Parameter Strategies* — o passo de
pré-processamento que roda ANTES do `command.run()` para transformar
argumentos de CLI crus (`--container urn:...`) em chaves canônicas dentro
do `CliContextPort` (ex: `container_id`, `container_path`).

## 1. Conceitos

| Termo | Definição |
| :--- | :--- |
| **Parameter Strategy** | Uma classe concreta que implementa `CliContextStrategyPort` e declara um `ParameterMetadata` com um `name` canônico (ex: `container_id`). Lê um valor, resolve fallbacks opcionais e grava as chaves finais no `CliContextPort`. |
| **Parameter Loader** | [ParameterLoader](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/shared/adapter/loader.py#L354-L435) — orquestra a descoberta física de estratégias dentro da árvore de pacotes. |
| **Parameter Validation Orchestrator** | [CliParameterValidationOrchestrator](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/cli/__init__.py#L96-L294) — une os três estágios de pipeline (binding explícito → matching → execução) antes de delegar para `command.check()`. |
| **Porta marcadora (marker port)** | Interfaces vazias (`LoggerAwarePort`, `PromptChoiceAwarePort`, `PromptRawTextAwarePort`) usadas para IoC: o orchestrador injeta callbacks específicos apenas nas estratégias que declaram suportá-los. |

---

## 2. Estágio 0 — Região crítica de binding explícito (flags do shell)

Antes de qualquer Parameter Strategy rodar, o orchestrador grava no
`CliContextPort` os valores de **flags longas valoradas** declaradas no
`METADATA.arguments` do comando (ex: `--container urn:...`). O nome da chave
é derivado por convenção:

```
tira os dois primeiros traços (--) → troca "-" por "_" (snake_case)
--container     → container
--container-id  → container_id
--root-dir      → root_dir
```

Arquivo de referência: [apply_explicit_parameter_values](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/cli/__init__.py#L163-L216)

> ⚠️ **Apenas flags longas** (`--foo value`) são processadas nesta etapa.
> Flags curtas (`-c value`) e sintaxe com `=` (`--foo=value`) **não** são
> suportadas hoje. Se você passar só a flag sem valor (`--container` sem
> URN), o binding é pulado silenciosamente.

---

## 3. Estágio 1 — Descoberta e carregamento (ParameterLoader)

A descoberta é física, por **convenção de diretório**: o
[ParameterLoader.get_all("parameter")](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/shared/adapter/loader.py#L375-L435)
itera por **TODOS os pacotes** instalados que seguem a estrutura do
OntoBDC (`ontobdc`, `infobim`, `infobim_view` etc.) e varre a sub-árvore:

```
{RAIZ_PACOTE}/<dominio>/plugin/parameter/**/*.py
```

Regras do carregamento:

1.  Cada módulo Python é importado dinamicamente com `importlib.import_module`.
2.  Cada classe do módulo é inspecionada com `inspect.getmembers`.
3.  Só entram na lista de estratégias candidatas as classes que:
    - **Herdam** de `CliContextStrategyPort`;
    - **NÃO são** a própria classe abstrata `CliContextStrategyPort`;
    - O módulo consegue ser importado sem exceção.
4.  Cada classe aprovada é **instanciada imediatamente** (`obj()`) — a lista
    retornada por `get_all()` contém *instâncias prontas para uso*, não
    tipos/classe.

### Erros de import agora são avisados (antes eram silenciosos!)

Antes da refatoração de 2026-08-16, qualquer exceção de import
(`SyntaxError`, `ImportError`, `TypeError` na inicialização etc.) era
**totalmente engolida** com um `except Exception: continue` nu. Isso
significava que uma Strategy com bug de import simplesmente **sumia do
mapa**, sem que ninguém ficasse sabendo.

Hoje o `ParameterLoader` emite um **WARNING** descrebendo: (a) o nome do
módulo que quebrou, (b) o tipo da exceção, (c) a mensagem original da
exceção. O logger é passado pelo `CliParameterValidationOrchestrator` e o
default cai em `NullLogRepository` quando não há logger configurado.
Exemplos de mensagens de warning:

```
ParameterLoader: skipping plugin domain package 'ontobdc.storage.plugin'
(ImportError: cannot import name 'Faltando' from 'ontobdc.shared.foo')

ParameterLoader: skipping resource package 'infobim.view.plugin.parameter'
inside 'infobim.view.plugin' (ImportError: bad magic number in 'infobim.calc')

ParameterLoader: discarding strategy module
'ontxbdc.context.plugin.parameter.language' —
SyntaxError: invalid syntax (language.py, line 42)
```

---

## 4. Estágio 2 — Matching (quais strategies realmente executam?)

O carregamento do Estágio 1 retorna **TODAS as strategies encontradas no
monorepo**. Porém, para uma strategy realmente rodar para um comando
específico, o seu `METADATA.name` **PRECISA** pertencer ao conjunto de
nomes de parâmetro que o próprio comando declarou.

### Como o conjunto "required_parameter_names" é calculado?

O método
[resolve_required_parameter_names](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/cli/__init__.py#L219-L256)
lê o `METADATA.arguments` do comando, filtra apenas entradas com
`valued == True`, e aplica a mesma regra de kebab-case → snake_case do
Estágio 0. Exemplo para um comando storage `--container --update`:

```
METADATA.arguments[0].accepts = ["--container-id", "--container"]  → {container_id, container}
METADATA.arguments[1].accepts = ["--update"]                       → SEM valued, ignorado

required_parameter_names = {"container_id", "container"}
```

### Como o matching individual funciona?

Para cada strategy candidata, o orchestrador chama
[resolve_parameter_name](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/cli/__init__.py#L258-L270)
que extrai `strategy.METADATA.name` e valida:

- Se `name` **não é uma string** → pula.
- Se `name.strip()` for vazio → pula.
- Se `name ∉ required_parameter_names` → **PULA SEM AVISO NENHUM**.

> ⚠️ **Ponto de dor mais importante de todo o pipeline**:
> **Se você criou uma Parameter Strategy e ela parece "não ser chamada",
> 99% das vezes é porque o comando que você está executando NÃO declarou
> uma flag longa valorada que mapeie para o `METADATA.name` da strategy.**
> Apenas a existência da strategy no diretório não garante execução.

---

## 5. Estágio 3 — Configuração (injeção de portas marcadoras)

Strategies que herdam de interfaces marcadoras recebem injeção de callbacks
pelo método
[configure_parameter_strategy](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/cli/__init__.py#L271-L290)
antes de `execute()` rodar:

| Porta | Callback injetado | Para quê |
| :--- | :--- | :--- |
| `LoggerAwarePort` | `set_log_strategy(LogStrategyConfig(...))` | Logar INFO / WARNING / ERROR durante resolução de fallback. |
| `PromptChoiceAwarePort` | `set_prompt_choice(prompt_choice)` | Pedir ao usuário para escolher entre múltiplos containers registrados quando o selector é ambíguo. |
| `PromptRawTextAwarePort` | `set_prompt_raw_text(prompt_raw_text)` | Pedir input textual livre pro usuário quando um path é obrigatório mas não informado. |

Strategies que não implementam essas portas simplesmente não recebem a
injeção — não há erro nem warning.

---

## 6. Estágio 4 — Execução (strategy.execute(context))

Finalmente, a strategy selecionada roda `.execute(context)`. O contrato esperado:

### 6.1 Responsabilidades de uma Strategy bem-comportada

1.  **Prioriza valor explícito do Estágio 0.** Se `context.has_parameter("container")` retornar `True`, usa esse selector primeiro — o usuário digitou.
2.  **Procura fallbacks determinísticos.** Para container: storage.ttl global → diretório atual via `.__ontobdc__/container.ttl` → CWD se registrado no índice.
3.  **Sempre grava chaves CANÔNICAS no context.** A `ContainerIdStrategy`, por exemplo, nunca devolve `container` (nome da flag): ela **sempre** grava `container_id` (id canônico) e `container_path` (path resolvido para Path absoluto). Isso garante que os comandos só leiam chaves estáveis, não variantes de flags.
4.  **Em caso de falha na resolução, apaga (clear), não deixa velho.** A `ContainerIdStrategy` chama `context.delete_parameter("container_id")` e `context.delete_parameter("container_path")` em `_clear()`. Isso evita que um valor de uma execução anterior (contexto reaproveitado) "contamine" o comando atual.
5.  **Não crasha em caso de selector inválido.** Deve limpar e retornar normalmente. Erros levantados durante `execute()` propagam para o topo como falha de execução do comando, diferente de erros de import do Estágio 1 (que são warnings).

### 6.2 Exemplo completo: ContainerIdStrategy

Referência: [ContainerIdStrategy.execute](file:///Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC/ontobdc/src/ontobdc/storage/plugin/parameter/container.py#L65-L130)

1.  **Leitura do raw_args:** Primeiro verifica `context.raw_args` (quando executando do CLI real) para saber se o usuário passou `--container-id` ou `--container`.
2.  **Matching por ID:** Se `--container-id` foi passado → procura registro em `storage.ttl` com ID exato via `_find_by_id()`.
3.  **Matching por ID OU path:** Se `--container` foi passado → primeiro tenta match por ID (URN lógico ou UUID sintético). Se não achar, tenta match por path (Path absoluto ou relativo ao CWD) usando `_find_by_path()`, que dá prioridade ao path mais específico (mais segmentos) quando há múltiplos matches (ex: container A contém container B).
4.  **Fallback de CWD:** Nenhuma flag explícita? → tenta `Path(os.getcwd())` como path de container, depois tenta `_find_from_current_container()` que procura por `.__ontobdc__/container.ttl` na árvore de pais.
5.  **Bind ou Clear:** Qualquer caminho de sucesso chama `_bind(context, container_id, container_path)` escrevendo as chaves canônicas. Falha total chama `_clear(context)` para não deixar valor velho.

---

## 7. Checklist de Troubleshooting — "Minha strategy não executa!"

Quando a Parameter Strategy parece ser "ignorada", percorra TUDO nesta
ordem antes de abrir debugging:

| Passo | Verificação | Onde olhar |
| :--- | :--- | :--- |
| 1 | Arquivo `.py` está em `<dominio>/plugin/parameter/`? | Estrutura de pastas do seu pacote. |
| 2 | Classe herda de `CliContextStrategyPort` (e não é abstrata)? | Arquivo `.py` da strategy. |
| 3 | `METADATA.name` está preenchido com string não-vazia? | `ParameterMetadata(name="...")` da classe. |
| 4 | **O comando em execução declara** uma flag valorada longa que mapeie para esse `name`? (ex: name=`container_id` → comando precisa de `--container-id` com `valued=True` em METADATA.arguments) | `METADATA.arguments` do comando que você está rodando. |
| 5 | Rodou com log WARNING ativado? Existe alguma mensagem de `ParameterLoader: discarding strategy module`? | `StandardConsoleLogger` no CLI. |
| 6 | A strategy está crashando dentro do `execute()` e o traceback está sendo suprimido pelo handler de exceção do pipeline de comandos? | Roda com `PYTHONDEVMODE=1` ou habilita `print()` temporário dentro de execute. |

Se **todos** os 6 passos forem OK, a strategy **vai** executar. Se ainda
assim não rodar, provavelmente o comando que você esperava não foi o que
foi roteado no `accepts()` (verifique `len(args)`, shape das flags — ex:
o bug que ocorreu em 2026-08-15 no `storage --container <URN>` onde
`StorageUpdateCommand` só aceitava `len(args)==4` com `--update` no final,
nunca `len(args)==3` sem o update).

---

## 8. Exemplo prático completo

Cenário:
```bash
$ ontobdc storage --container urn:uuid:c04c187f-4358-4399-9c76-11c8088203e2
```

O que acontece em cada estágio:

| Estágio | Resultado |
| :--- | :--- |
| **Routing** (`command.accepts(args)`) | `StorageUpdateCommand.accepts()` → retorna `True` porque `args[0] == "storage"` / `args[1] == "--container"` / `len(args) == 3` / `args[2].strip()` não vazio. |
| **Estágio 0** (explicit binding) | `apply_explicit_parameter_values` grava `context["container"] = "urn:uuid:c04c..."`. |
| **Estágio 1** (discovery) | `ParameterLoader.get_all()` instancia 2 strategies: `ContainerIdStrategy(name="container_id")`, `ImportFromStrategy(name="import_from")`. 0 warnings de import. |
| **Estágio 2** (required_parameter_names) | `METADATA.arguments` do StorageUpdateCommand: `{"container_id", "container"}`. **Matches:** `ContainerIdStrategy` (name `container_id` ∈ conjunto). **Pula:** `ImportFromStrategy` (name `import_from` ∉ conjunto). |
| **Estágio 3** (config) | `ContainerIdStrategy` implementa `LoggerAwarePort` + `PromptChoiceAwarePort` → recebe os 2 callbacks. |
| **Estágio 4** (execute) | `.execute(context)` detecta `--container` no raw_args, chama `_find_by_id()` em containers registrados → acha `urn:uuid:c04c...` → `_bind()` grava `container_id = urn:uuid:c04c...` e `container_path = /abs/path/do/container`. |
| **Final** (`command.check()`) | Lê `context.container_path`, confirma que existe, chama state machine (`ContainerUpdateStateTransitionHandler`) → `__container_healthy__ → ... → __container_html_view_updated__`. |

---

## 9. Mudanças notáveis (changelog)

- **2026-08-16 (hoje):** Encapsulado todo o pipeline de parameter binding
  na classe `CliParameterValidationOrchestrator`. Adicionado **WARNINGS de
  logger** no `ParameterLoader` para exceções de import que antes eram
  silenciosamente engolidas.
- **2026-08-15:** Migração de toda a pilha de Surface/Terminal para TSR
  compartilhado — o contexto de parâmetros `container_path`/`dataset_path`
  agora também é consumido pelo pipeline HTML de geração de view.
