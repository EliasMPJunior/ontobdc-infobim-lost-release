# Estrutura funcional do módulo `view` (`ontobdc/src/ontobdc/view`)

**Data:** 10 de agosto de 2026
**Escopo:** o que o módulo `view` faz, em que ordem, o que cada peça produz e o que verifica — não apenas a taxonomia de pastas (já coberta em [2026-08-10-ontobdc-directory-structure-survey.md](2026-08-10-ontobdc-directory-structure-survey.md)).
**Fontes:** leitura direta de `domain/machine/*.py`, `domain/machine/*.yaml`, `domain/port/*.py`, `adapter/*.py`, `component/**`, `plugin/**` em `ontobdc/src/ontobdc/view`; comparação com `ontobdc/docs/2026-08-08-interface-presentation-layer-report.md` e com o documento irmão sobre `storage`.

---

## 1. Três responsabilidades coexistindo sob um único módulo

`view` acumula, hoje, três funções que valem a pena distinguir explicitamente porque usam mecanismos e até vocabulários diferentes:

1. **Geração de view legada de container** (`ContainerViewProcessState`) — dashboard/publicação em HTML via templates Jinja2, decompondo dados de datasets em facades serializadas como JSON-LD. É explicitamente chamada de "legacy" no próprio código (`domain/machine/state.py`: *"States inferred from the **legacy** container view artefacts"*).
2. **Geração de Presentation Surface offline** (`SurfaceGenerationProcessState`) — a materialização, do lado servidor/Python, do modelo dDock/PresentationLayer/Tile descrito em `ontobdc/docs/2026-08-08-interface-presentation-layer-report.md`. É o pipeline mais novo e mais rico do módulo (§3 e §4).
3. **Renderização de resposta para host terminal/CLI** (`component/`, `plugin/render/rich/`) — o mesmo problema de "pegar uma resposta semântica e desenhá-la" resolvido para um host completamente diferente (ANSI/terminal em vez de navegador). Ver §5.

As três compartilham o mesmo mecanismo genérico de máquina de estado descrito no documento sobre `storage` (evaluator + handler + statechart YAML + capability + check), mas só as duas primeiras o usam de fato — a terceira (§5) é um problema de renderização síncrona, sem processo cumulativo.

---

## 2. As duas máquinas de estado de geração de HTML

### 2.1 `ContainerViewProcessState` — view legada (5 estados)

| Ordem | Estado | O que significa | Capability |
|---|---|---|---|
| 1 | `DATA_GATHERED` | dados usados pela view legada foram materializados (compartilhado com o pipeline de Surface, §2.2) | `data_gathered.py` |
| 2 | `HARDCODED` | operações de geração ainda não formalizadas foram executadas | `hardcoded.py` |
| 3 | `FACADES_SERIALIZED` | todo dataset foi materializado por sua facade; contratos e instâncias serializados como JSON-LD e embutidos na view | `facades_serialized.py` |
| 4 | `DATASET_VIEWS_GENERATED` | páginas de WorkStream/IfcWorkSchedule declaradas pelos datasets foram renderizadas de templates Jinja | `dataset_views_generated.py` |
| 5 | `GENERATED` (final) | a representação de view legada solicitada foi gerada | `generated.py` |

**`hardcoded.py` merece destaque à parte.** Não é só um nome descritivo — é uma zona de débito técnico *deliberadamente contida e documentada*, com o próprio docstring do arquivo funcionando como um contrato de saída:

> *"HARDCODED is the temporary consolidation state for view-generation operations that still live outside the official publication and dashboard flow. It is deliberately a holding area: once an operation receives an official adapter, capability, data contract, and tests, that operation must leave this module."*

O docstring ainda lista as operações hoje exclusivas desse módulo (ler `views/public.yaml`, renderizar `template/index.html.jinja`, extrair `IfcSite.RefLatitude/RefLongitude`, converter `IfcCompoundPlaneAngleMeasure`, entre outras) — ou seja, o próprio código documenta o que ainda precisa ser "oficializado" e por quê. Isso é o oposto do débito técnico silencioso que `AGENTS.md` proíbe implicitamente (§14: "create silent legacy fallbacks"): aqui o fallback existe, mas é explícito, nomeado e rastreável.

### 2.2 `SurfaceGenerationProcessState` — Presentation Surface offline (11 estados)

| Ordem | Estado | O que significa | Capability |
|---|---|---|---|
| 1 | `CONTAINER_HEALTHY` | container fonte satisfaz seus requisitos estruturais/semânticos | **reaproveitada de `storage`** (ver §2.3) |
| 2 | `IS_PUBLISHABLE` | container saudável tem descritor de publicação válido e recursos necessários | `is_publishable.py` |
| 3 | `DATA_GATHERED` | dados-fonte da apresentação materializados como artefato JSON-LD de estado | `data_gathered.py` (compartilhado com §2.1) |
| 4 | `SURFACE_INITIALIZED` | documento HTML offline mínimo e host da Presentation Surface existem | `surface_initialized.py` |
| 5 | `SURFACE_ENRICHED` | dados e metadados semânticos embutidos no HTML como JSON-LD | `surface_enriched.py` |
| 6 | `SURFACE_SET` | regiões da Surface e regras de apresentação declaradas, sem fixar geometria de viewport | `surface_set.py` |
| 7 | `SURFACE_MATCHED` | dados de apresentação correlacionados a definições de Tile compatíveis e seus envelopes de suporte | `surface_matched.py` |
| 8 | `SURFACE_ASSEMBLED` | regiões `operation`, `content` e `pinned` compostas com Tiles e restrições de layout de runtime | `surface_assembled.py` |
| 9 | `SURFACE_PACKAGED` | implementações de componente do navegador embutidas para execução offline | `surface_packaged.py` |
| 10 | `SURFACE_VALIDATED` (final) | a Surface HTML empacotada satisfaz os checks de geração offline | `surface_validated.py` |

`surface_base.py` não é um estado — é `SurfaceTransformationCapability`, a classe-base compartilhada por `surface_initialized/enriched/set/matched/assembled/packaged/validated`, com os helpers comuns `_path`/`_read`/`_write` sobre o arquivo HTML da Surface.

**Esta tabela é a contraparte server-side, linha a linha, do modelo descrito no relatório de interface.** Os nomes de estado 4–8 (`SURFACE_INITIALIZED`, `SURFACE_ENRICHED`, `SURFACE_SET`, `SURFACE_MATCHED`, `SURFACE_ASSEMBLED`) correspondem exatamente às regiões (`operation`/`content`/`pinned`), ao conceito de Tile e ao vocabulário de "matching"/negociação descritos em `ontobdc/docs/2026-08-08-interface-presentation-layer-report.md` §4. A geração de Surface não é uma reinterpretação livre daquele modelo — é a mesma cadeia conceitual (`Response → Agent → Bus → Bridge → Dock/dDock → PresentationLayer → Grid/Slot Engine → Tile → Component`) sendo *produzida*, passo a passo e validável, do lado do gerador Python, para consumo por um host navegador offline.

Confirmação concreta no código: `adapter/surface_document.py` manipula literalmente a tag do Custom Element publicado pelo pacote `presentation/`:

```python
SURFACE_TAG = "onto-presentation-surface"
```

### 2.3 Reaproveitamento cross-módulo: `CONTAINER_HEALTHY` vem de `storage`

O primeiro estado do pipeline de Surface não tem capability própria em `view/` — ele é resolvido por ID global apontando para a capability de `storage`:

```python
# ontobdc/src/ontobdc/view/adapter/surface_machine.py
_CAPABILITY_ID_BY_STATE = {
    SurfaceGenerationProcessState.CONTAINER_HEALTHY: (
        "org.ontobdc.storage.plugin.capability.transformation.target."
        "container_healthy"
    ),
    SurfaceGenerationProcessState.IS_PUBLISHABLE: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        "is_publishable"
    ),
    **{  # os oito estados de surface_* seguem o padrão automático pelo nome do estado
        state: f"org.ontobdc.view.plugin.capability.transformation.target.{state.value.strip('_')}"
        for state in SurfaceGenerationProcessState
        if state not in {..., SurfaceGenerationProcessState.CONTAINER_HEALTHY, ...}
    },
}
```

Uma Surface só pode começar a ser gerada para um container que `storage` já considera saudável — dependência de domínio expressa como dependência de capability publicada, resolvida em runtime via `CapabilityLoader().get(capability_id)`, nunca como import direto de `storage.adapter` dentro de `view`.

### 2.4 Ausência de `hotfix.py` em `view/plugin/check/`

Nenhum dos sete diretórios `plugin/check/is_surface_*/` (`initialized`, `enriched`, `set`, `matched`, `assembled`, `packaged`, `validated`) contém `hotfix.py`, ao contrário da maioria dos checks de `storage`. A leitura mais direta: o pipeline de Surface é **regenerado do zero a cada execução do comando `view`**, não é um estado persistente de longo prazo que faça sentido "consertar in-place" — se algo está errado, a correção é gerar de novo, não aplicar um hotfix cirúrgico sobre um HTML já publicado.

---

## 3. `component/` — a mesma distinção Tile/Component, só que no terminal

`view/component/logo/` e `view/component/surface/` implementam, em Python puro (sem HTML), a contraparte do mesmo par conceitual **Tile vs. Component** descrito no relatório de interface — mas para o host terminal, não navegador:

- `component/logo/python.py` (`LogoComponent`) — usa `pyfiglet` para desenhar o logo `OntoBDC` como ASCII art colorido no terminal.
- `component/surface/python.py` — `TerminalSurfaceSize` (colunas × linhas do terminal) e `TerminalSurfaceResizeEvent`, isto é, a mesma ideia de "capacidade de apresentação calculada a partir do espaço disponível" (`PresentationCapacity` do relatório, §4.7) aplicada a um terminal em vez de um `viewport` de navegador.

Isso é uma confirmação prática do **Talking Dinosaur Test** do relatório (§4.8: *"O dinossauro falante consegue interpretar isso de alguma forma coerente?"*): o mesmo vocabulário arquitetural (Component, Surface, capacidade calculada a partir do espaço disponível) se materializa tanto como `<onto-presentation-surface>` HTML/Shadow DOM (§2.2) quanto como dimensões de terminal ANSI — sem que um conheça a existência do outro.

---

## 4. Command → Response → Renderer: o princípio do relatório, implementado

O relatório de interface descreve, na Fase A do doc2, a separação:

> `Command → Response semântico (não sabe como desenhar) → Renderer específico do target → materialização concreta`

`view/adapter/response.py` + `view/domain/port/response.py` + `view/plugin/render/rich/layout.py` são exatamente essa cadeia, implementada para o host CLI/terminal:

- `ResponseMessageBoxAdapterPort` declara `accepts(response) -> bool` e `render(response, layout) -> str` — um adapter só entra em ação se `accepts()` reconhecer o tipo de `CommandResponse`.
- Quatro adapters concretos cobrem os tipos de resposta do CLI: `CommandResponseMessageBoxAdapter`, `ExceptionCommandResponseMessageBoxAdapter`, `HelpCommandResponseMessageBoxAdapter`, `ListCommandResponseMessageBoxAdapter` (`adapter/response.py`).
- `ResponseMessageBoxAdapterLoader` (`adapter/loader.py`) descobre, em runtime, qual adapter aceita uma resposta dada — o mesmo mecanismo de plugin discovery usado em todo o resto do projeto (`AGENTS.md` §5), aplicado à escolha de renderer.
- `RichMessageBoxLayout` (`plugin/render/rich/layout.py`) é o *Renderer* de fato: só ele sabe desenhar caixas ANSI coloridas e só ele decide como o conteúdo tabular vira colunas alinhadas, dado que só ele conhece a largura real do terminal (`shutil` para medir colunas).
- `domain/model/table.py` (`TableSegment`, `encode_table`/`split_segments`) é, no próprio comentário do código, *"a private convention between `view.adapter.response` ... and `view.plugin.render.rich.layout`"* para carregar dados tabulares dentro do texto da mensagem sem alterar o contrato público `MessageBoxLayoutData` — ou seja, o `Response` continua sem saber que vai virar uma tabela; só o par adapter/renderer sabe.

O mesmo par porta/adapter é reaproveitado para o output HTML: `MessageBoxLayoutRendererPort` (`domain/port/layout.py`) é implementado tanto pelo layout Rich (terminal) quanto, presumivelmente, por um layout HTML equivalente consumido pela geração de view — o ponto estrutural é que o `Command`/`Response` do `cli/` nunca precisa saber qual dos dois vai desenhá-lo.

---

## 5. Comando CLI e parâmetros expostos

| Comando/estratégia | Arquivo | Papel |
|---|---|---|
| `view` (`ContainerViewCommand`) | `plugin/command/view.py` | resolve o container, roda `SurfaceGenerationStateTransitionHandler.execute()` até o fim ou até o estado pedido, abre o resultado no navegador (`webbrowser`) |
| `ViewRepresentationStrategy` | `plugin/parameter/representation.py` | resolve a representação visual pedida — hoje `("html", "pdf")` |

Assim como em `storage`, o comando é uma camada fina: resolve argumentos e delega ao handler da máquina de estado.

---

## 6. Duas famílias de assets (resumo; detalhado no levantamento de pastas)

- `view/asset/image/` — estáticos genéricos da view como um todo (logo, favicon).
- `view/plugin/asset/{css,js}/annotation/` e `.../workstream/` — CSS/JS de plugins específicos (editor/workspace de anotações do `README.md` do pacote; board de WorkStream), colocalizados com o plugin dono, JavaScript puro compatível com `file://`, sem bundler (`AGENTS.md` §9).

---

## 7. Síntese

`view` é o módulo onde três problemas de "pegar dados/estado e torná-los perceptíveis" convivem sob o mesmo teto: uma geração de dashboard legada com débito técnico explicitamente contido (`hardcoded.py`), um pipeline novo de 10 estados que é a implementação server-side literal do modelo dDock/PresentationLayer/Tile do relatório de 08/08, e um sistema de renderização de resposta para terminal que usa exatamente o mesmo princípio (`Command → Response → Renderer`) e o mesmo vocabulário (`Component`, capacidade calculada por espaço disponível) só que para um host ANSI em vez de HTML. A dependência entre `view` e `storage` (a Surface só nasce de um container que `storage` já validou como saudável) é resolvida como consumo de capability publicada por ID, não como acoplamento de código — o mesmo padrão que sustenta toda a arquitetura de plugins descrita em `AGENTS.md`.
