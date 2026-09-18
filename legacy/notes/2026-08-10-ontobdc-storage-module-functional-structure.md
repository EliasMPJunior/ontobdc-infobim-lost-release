# Estrutura funcional do módulo `storage` (`ontobdc/src/ontobdc/storage`)

**Data:** 10 de agosto de 2026
**Escopo:** o que o módulo `storage` faz, em que ordem, o que cada peça produz e o que verifica — não apenas a taxonomia de pastas (já coberta em [2026-08-10-ontobdc-directory-structure-survey.md](2026-08-10-ontobdc-directory-structure-survey.md)).
**Fontes:** leitura direta de `domain/machine/*.py`, `domain/machine/*.yaml`, `domain/port/*.py`, `adapter/*.py`, `plugin/**` em `ontobdc/src/ontobdc/storage`, e de `ontobdc/src/ontobdc/shared/adapter/capability.py`.

---

## 1. O que o módulo possui

`storage` é o dono da persistência de containers e datasets do OntoBDC — grafos RDF/Turtle que seguem simultaneamente a ontologia ISO 21597 ("Container", prefixo `ct`) e a ontologia própria do OntoBDC (prefixo `obdc`, `http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#`). O estado local do projeto vive num diretório marcador oculto, `.__ontobdc__/` (constante `MARKER_DIR_NAME`/`ONTOBDC_DIRECTORY_NAME` em `adapter/repository.py` e `adapter/bootstrap.py`), contendo:

- `storage.ttl` — índice de storage local (`STORAGE_IDENTIFIER = "urn:ontobdc:storage/local"`);
- `context.ttl` — contexto de execução ativo (qual container/dataset está selecionado);
- `container.ttl` / `dataset.ttl` — metadados por objeto;
- `ro-crate-metadata.json` — compatibilidade com RO-Crate.

Isso confirma, na prática, a regra de `AGENTS.md` §7: "Treat the hidden `.__ontobdc__` structure as runtime metadata, not an arbitrary cache."

---

## 2. O mecanismo genérico: Evaluator + Handler + Statechart + Capability + Check/Hotfix

Todo fluxo com ciclo de vida em `storage` segue exatamente o mesmo esqueleto, declarado como contrato em `domain/port/machine.py` (e, para o attach, em `domain/port/attach_machine.py`):

```text
<X>StateEvaluatorPort
    .evaluate(context, ...) -> <X>ProcessStatePort
        # infere o estado atual a partir dos artefatos reais em disco —
        # nunca a partir de uma flag separada que possa dessincronizar

<X>StateTransitionHandlerPort
    .current_state          # o que a evaluator observou agora
    .state_sequence          # a sequência-alvo completa, ordenada
    .can_transit_to(to)        # a próxima transição é permitida?
    .perform_state_transition(to)  # executa a Capability daquele estado-alvo
    .validate_state_transition(from, to)  # confirma que o novo estado foi de fato alcançado
    .execute()                   # roda o processo do estado atual até o fim (ou até falhar)
```

Cada processo tem, além do enum Python (`domain/machine/*.py`) e da implementação concreta (`adapter/machine.py`, `adapter/attach_machine.py`), um **statechart declarativo em YAML** (`domain/machine/standard_*.yaml`, executado via `sismic`) que expressa a mesma sequência como estados-e-transições com guardas e contratos:

```yaml
- name: identity_resolved
  transitions:
    - target: container_metadata_attached
      guard: handler.can_transit_to(to_state = ...CONTAINER_METADATA_ATTACHED)
      action: handler.perform_state_transition(to_state = ...CONTAINER_METADATA_ATTACHED)
      contract:
        - after: handler.validate_state_transition(from_state = ...IDENTITY_RESOLVED, to_state = ...CONTAINER_METADATA_ATTACHED)
```
*(`domain/machine/standard_container_attach.yaml`, trecho real.)*

Cada nome de estado-alvo corresponde a **exatamente um arquivo** em `plugin/capability/transformation/<nome_do_estado>.py` (a ação que produz aquele estado) e, na maioria dos casos, a **um diretório** em `plugin/check/is_<algo>/` com `check.py` (verifica se o estado foi alcançado) e `hotfix.py` (corrige quando não foi). O ID de cada capability segue a convenção `org.ontobdc.storage.plugin.capability.transformation.target.<nome_do_estado>` (ex.: `.../target.directory_ready`).

As capabilities são tipadas em três famílias, por `shared/domain/port/capability.py`:

| Tipo | Contrato declarado | Uso típico em `storage` |
|---|---|---|
| `QueryCapability` | "designed to query information without side effects" | não observado em uso direto neste módulo |
| `TransformationCapability` | "designed to transform data structures" | passos simples de criação (`directory_ready`, `container_metadata_ready`, ...) |
| `TransactionCapability` | "modifies state or performs transactions" | passos com maior risco/efeito colateral coordenado |

---

## 3. As quatro máquinas de estado concretas

### 3.1 `ContainerCreateProcessState` — criar um container novo (`ontobdc ct_create`)

| Ordem | Estado | O que significa | Capability |
|---|---|---|---|
| 1 | `DIRECTORY_READY` | diretório-alvo existe e está pronto | `directory_ready.py` |
| 2 | `CONTAINER_METADATA_READY` | `container.ttl` existe e descreve um data container válido, sem exigir datasets | `container_metadata_ready.py` |
| 3 | `CONTAINER_STORAGE_INDEX_READY` | a entrada do container em `storage.ttl` está sincronizada com o `container.ttl` | `container_storage_index_ready.py` |
| 4 | `CONTAINER_MANIFEST_SYNCED` | o manifesto lista todos os arquivos do container, exceto diretórios de marker/dataset | `container_manifest_synced.py` |

Estado de erro dedicado: `INVALID_PATH` (o caminho alvo já é um arquivo existente).

### 3.2 `DatasetCreateProcessState` — criar um dataset dentro de um container (`ontobdc ds_create`)

| Ordem | Estado | O que significa | Capability |
|---|---|---|---|
| 1 | `DIRECTORY_READY` | mesmo arquivo `directory_ready.py` reaproveitado do pipeline de container | `directory_ready.py` (compartilhado) |
| 2 | `DATASET_METADATA_READY` | `dataset.ttl` existe e contém uma descrição válida do dataset | `dataset_metadata_ready.py` |
| 3 | `DATASET_CONTAINER_INDEX_READY` | o `container.ttl` contém a entrada do dataset e está sincronizado com `dataset.ttl` | `dataset_container_index_ready.py` |

O reaproveitamento de `directory_ready.py` entre os dois pipelines (em vez de duplicar a lógica "crie um diretório e confira que não é um arquivo") é o mesmo tipo de disciplina que `AGENTS.md` §10 pede ("Do not add dead compatibility branches... duplicate implementations").

### 3.3 `ContainerUpdateProcessState` — atualizar um container já registrado (`StorageUpdateCommand`)

| Ordem | Estado | O que significa | Capability |
|---|---|---|---|
| 1 | `CONTAINER_HEALTHY` | o container satisfaz seus requisitos estruturais/semânticos | `container_healthy.py` |
| 2 | `CONTAINER_CLEANED` | artefatos obsoletos/órfãos foram removidos | `container_cleaned.py` |
| 3 | `CONTAINER_DATAPACKAGE_UPDATED` | `datapackage.json` foi resincronizado | `container_datapackage_updated.py` |
| 4 | `CONTAINER_RO_CRATE_UPDATED` | `ro-crate-metadata.json` foi resincronizado | `container_ro_crate_updated.py` |
| 5 | `CONTAINER_HTML_VIEW_UPDATED` | a view HTML publicada foi regenerada | `container_html_view_updated.py` |
| 6 | `CONTAINER_UPDATED` | estado final — todas as sub-atualizações acima estão consistentes entre si | *(sem arquivo de capability próprio — ver observação abaixo)* |

**Observação:** `CONTAINER_UPDATED` não tem um `container_updated.py` correspondente em `plugin/capability/transformation/`. É consistente com ele ser um estado **composto**: alcançado quando os cinco passos anteriores já validaram individualmente, sem exigir uma transformação própria adicional — mas vale confirmar essa leitura ao tocar neste pipeline, já que é a única lacuna desse tipo entre as quatro máquinas de `storage`.

`CONTAINER_HEALTHY` é notável porque **não é exclusivo deste pipeline**: é a mesma capability que o módulo `view` reaproveita para iniciar seu próprio pipeline de Surface (ver §6).

### 3.4 `ContainerAttachProcessState` — anexar um container importado ao root local (`StorageAttachCommand`)

É a máquina mais rica do módulo — a única que expõe seis estados de falha nomeados além do caminho feliz, e a única cujos passos são implementados por seis arquivos de adapter dedicados em vez de um por capability:

| Ordem | Estado (caminho feliz) | O que significa |
|---|---|---|
| 1 | `CONTAINER_INSPECTED` | container e datasets importados foram inspecionados sem alterar metadados |
| 2 | `IDENTITY_RESOLVED` | identidades e localizações locais de destino foram calculadas e checadas por conflito |
| 3 | `CONTAINER_METADATA_ATTACHED` | o grafo de metadados do container passa a usar a identidade/localização de destino |
| 4 | `DATASETS_ATTACHED` | todo grafo de dataset e o índice de datasets no container usam as identidades de destino |
| 5 | `STORAGE_INDEX_ATTACHED` | o índice de storage local contém a entrada canônica copiada do container anexado |
| 6 | `CONTEXT_ATTACHED` | o contexto de execução aponta para o container anexado, sem seletor de update obsoleto |
| 7 | `CONTAINER_ATTACHED` (final) | container, datasets, índice e contexto estão mutuamente consistentes |

Estados de falha nomeados: `INVALID_CONTAINER_PATH`, `INVALID_CONTAINER_GRAPH`, `IDENTITY_CONFLICT`, `DATASET_ATTACH_FAILED`, `STORAGE_INDEX_ATTACH_FAILED`, `ATTACH_ROLLBACK_FAILED`.

A implementação é decomposta em seis arquivos de responsabilidade única sob `adapter/`, e não em um arquivo por estado:

- `attachment_graph.py` — operações RDF de baixo nível (carregar grafo, reescrever sujeitos, exigir literal/URI);
- `attachment_plan.py` — calcula o **plano** de identidades/localizações de destino a partir do grafo importado;
- `attachment_metadata.py` — aplica o plano ao grafo de metadados e de datasets (usa `attachment_graph.py`);
- `attachment_context.py` — orquestra a sequência completa (`attach_context`), decide quando está `is_container_attached`/`is_context_attached`;
- `attachment_transaction.py` — tira um snapshot do contexto antes de mexer em qualquer coisa e sabe restaurá-lo (`snapshot_context`, `restore_attachment`, `discard_attachment_backup`) — a rede de segurança contra falha no meio do attach;
- `attachment_error.py` — mapeia **cada tipo de exceção diretamente a um estado de falha do enum**:

```python
class InvalidContainerPathError(ContainerAttachError):
    state = ContainerAttachProcessState.INVALID_CONTAINER_PATH
```

Esse último ponto é a peça que fecha o mecanismo: uma exceção de domínio não é apenas "algo deu errado", ela **é** uma transição de estado — o handler sabe exatamente em qual estado de falha o processo parou só pelo tipo da exceção capturada, sem precisar de um `if isinstance(...)` espalhado pela orquestração.

---

## 4. Checks que não pertencem a nenhuma das quatro máquinas nomeadas

Dois checks em `plugin/check/` são precondições de infraestrutura, não passos de um pipeline de criação/attach/update:

- **`is_root_set`** — confirma que a configuração de root do projeto aponta para uma raiz de storage local válida (usa o mesmo `STORAGE_IDENTIFIER`). É a precondição mais básica: sem root definido, nenhuma das quatro máquinas acima consegue nem começar a avaliar seu estado.
- **`is_container_id_registered`** — resolve, a partir do ID informado, a localização do container correspondente no `storage.ttl` (`get_registered_container_location`). É usado diretamente por `StorageUpdateCommand` para descobrir *qual* container a máquina de update deve tratar antes de sequer instanciar o handler.

Ambos seguem o padrão `check.py` + `hotfix.py`.

---

## 5. Comandos CLI expostos

| Comando (arquivo) | Aciona | Componente `logical_component` |
|---|---|---|
| `ct_create` (`plugin/command/container/create.py`) | `ContainerCreateStateTransitionHandler.execute()` | `storage` |
| update (`plugin/command/container/update.py`) | `ContainerUpdateStateTransitionHandler.execute()`, após resolver o container via `is_container_id_registered` | `storage` |
| attach (`plugin/command/container/attach.py`) | `ContainerAttachStateTransitionHandler` + `attachment.py` (`ATTACH_PLAN_PARAMETER`, `ATTACH_COMPLETED_PARAMETER`, `ATTACH_ERROR_PARAMETER`) | `storage` |
| delete (`plugin/command/container/delete.py`) | remoção direta via `StorageGraphFileRepository`, fora do mecanismo de máquina de estado (é uma operação atômica, não um pipeline cumulativo) | `storage` |
| `ds_create` (`plugin/command/dataset/create.py`) | `DatasetCreateStateTransitionHandler.execute()` | `storage` |
| help (`plugin/command/help.py`), base (`plugin/command/base.py`) | listagem/roteamento de comandos do componente | `storage` |

Todo comando de criação/update/attach é, na prática, uma camada finíssima: ele resolve argumentos, instancia o `*StateTransitionHandler` correspondente e delega `.execute()`. A lógica de negócio não mora no comando — mora na máquina de estado e nas capabilities que ela invoca.

---

## 6. Reaproveitamento cross-módulo

O módulo `view` inicia seu próprio pipeline de geração de Surface (ver documento irmão sobre `view`) reaproveitando literalmente a capability `container_healthy` de `storage`, por ID global, via o mesmo `CapabilityLoader` de descoberta dinâmica — não por importação direta de código nem por duplicação:

```python
# ontobdc/src/ontobdc/view/adapter/surface_machine.py
_CAPABILITY_ID_BY_STATE = {
    SurfaceGenerationProcessState.CONTAINER_HEALTHY: (
        "org.ontobdc.storage.plugin.capability.transformation.target."
        "container_healthy"
    ),
    ...
}
```

Isso é a prova prática, em código, da regra de `AGENTS.md` §5 ("the class is discoverable without manual registration") e da separação de camadas do §4: `view` depende de uma **capability publicada por ID**, não de um import interno de `storage.adapter`.

---

## 7. Síntese

`storage` implementa quatro pipelines de prontidão cumulativa (criar container, criar dataset, atualizar container, anexar container) sobre o mesmo esqueleto genérico — evaluator que infere estado real, handler que decide a próxima transição permitida, statechart declarativo em YAML que documenta a sequência, uma capability por estado-alvo, e (na maioria dos casos) um par check/hotfix que verifica e corrige. O pipeline de attach é o mais elaborado por ser o de maior risco (importar identidade externa para dentro de um root local); é o único com estados de falha nomeados individualmente e com uma camada de transação (snapshot/restore) dedicada. O módulo expõe essa complexidade para fora através de comandos CLI deliberadamente finos, e expõe pelo menos uma capability (`container_healthy`) como um contrato público que outro módulo (`view`) consome sem acoplamento direto.
