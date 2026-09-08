# Orquestrador Semântico de Testes do OntoBDC

**Status:** proposta de arquitetura e plano de implementação  
**Repositório-alvo:** `ontobdc-dev`  
**Versão inicial do manifesto:** `ontobdc.org/testing/v1alpha1`  
**Público principal:** manutenção do OntoBDC, implementação do boilerplate e criação de testes para todos os `check.py` e `hotfix.py`

---

## 1. Decisão arquitetural

O `ontobdc-dev` deverá oferecer um **orquestrador semântico de testes**: um runtime declarativo capaz de carregar manifestos YAML, observar estados reais do sistema, resolver ações necessárias, montar um plano executável, executar checks e hotfixes, verificar transições, coletar evidências e produzir um veredito reproduzível.

A ideia central é generalizar o padrão que já existe no OntoBDC:

```text
check
→ caso o estado não esteja satisfeito, hotfix
→ recheck
→ estado resultante
→ transição validada
```

O novo runtime não substituirá `pytest`. Ele deverá:

1. descrever em YAML **o comportamento do sistema**;
2. adaptar `check.py`, `hotfix.py` e capabilities existentes;
3. gerar instâncias concretas de testes e planos de execução;
4. executar essas instâncias em ambientes isolados;
5. registrar estados anteriores e posteriores;
6. usar o `check` como fonte autoritativa para confirmar o estado;
7. permitir que `pytest` teste o próprio runtime e, quando útil, invoque os manifestos.

O resultado esperado é uma camada acima dos testes unitários tradicionais: um mecanismo de testes orientado a estado, com rastreabilidade explícita entre requisito técnico, check, hotfix, capability, transição, evidência e veredito.

---

## 2. Escopo

### 2.1 Incluído na primeira implementação

- carregamento de manifestos YAML;
- validação estrutural e semântica dos manifestos;
- registro de estados, ações, casos, fluxos e suítes;
- adaptação de funções Python existentes;
- adaptação do padrão `check.py`/`hotfix.py`;
- composição e encadeamento de ações;
- planejamento por dependências de estado;
- execução explícita de fluxos ordenados;
- parametrização de casos;
- fixtures de diretório e arquivos;
- mutações controladas para criar cenários inválidos;
- snapshots antes e depois;
- evidências de filesystem, RDF, stdout, stderr e códigos de saída;
- resultados em JSON e JUnit XML;
- CLI `ontobdc-dev test ...`;
- inventário e cobertura de todos os checks e hotfixes encontrados no workspace;
- criação dos casos iniciais para todos os checks e hotfixes existentes.

### 2.2 Fora do primeiro boilerplate

- interface gráfica;
- execução distribuída;
- paralelismo entre repositórios;
- geração automática por LLM;
- linguagem de consulta semântica completa para o catálogo;
- substituição dos testes unitários existentes;
- execução destrutiva em dados reais;
- inferência automática de todas as precondições a partir do código Python.

Esses itens poderão ser adicionados depois. A primeira versão precisa ser determinística, auditável e simples de depurar.

---

## 3. Fundamento no código atual

O boilerplate deve partir da arquitetura já existente, não criar uma ilha paralela.

Hoje, os checks do OntoBDC normalmente:

- recebem parâmetros simples;
- observam arquivos, grafos ou contexto;
- retornam `0` quando o estado está satisfeito;
- retornam valor diferente de zero quando não está satisfeito ou ocorreu erro.

Os hotfixes normalmente:

- recebem o mesmo contexto do check;
- tentam produzir ou reparar o estado;
- retornam `0` quando a operação foi executada sem erro;
- não devem ser considerados suficientes por si mesmos: o estado precisa ser confirmado por novo check.

As capabilities de transformação já implementam o padrão:

```text
check atual
→ hotfix quando necessário
→ check posterior
→ erro se o estado continuar inválido
→ retorno de resulting_state
```

As máquinas de estado existentes já possuem:

- enumerações de estados;
- avaliadores do estado observado;
- handlers de transição;
- capabilities por estado-alvo;
- statecharts YAML;
- contratos posteriores às transições.

O orquestrador deve reutilizar esses conceitos:

| Conceito existente | Conceito no orquestrador |
|---|---|
| `check.py` | `StateObserver` / probe de estado |
| `hotfix.py` | `RepairAction` |
| capability | implementação de `TestAction` |
| enum de processo | vocabulário de estados do domínio |
| statechart YAML | fonte de fluxos e transições esperadas |
| `StateWorkerAdapter` | referência para o executor/planner |
| contrato `after` | assertiva posterior / estado garantido |
| `resulting_state` | efeito declarado e posteriormente observado |

---

## 4. Terminologia canônica

A nomenclatura abaixo deve ser usada no código, nos manifestos e nos relatórios.

### 4.1 `TestCatalog`

Catálogo carregado pelo runtime. É o resultado da composição de um ou mais arquivos YAML.

Contém definições de estados, ações, casos, fluxos, suítes, fixtures e políticas.

### 4.2 `StateDefinition`

Definição verificável de uma condição do sistema.

Exemplos:

- `storage.container.directory.ready`;
- `storage.container.metadata.ready`;
- `storage.container.index.ready`;
- `storage.container.manifest.synced`.

Um estado não é apenas uma string ou fase nominal. Ele deve possuir um observador capaz de determinar se está:

- satisfeito;
- não satisfeito;
- impossível de observar por erro.

### 4.3 `StateObserver`

Adaptador que observa um `StateDefinition`.

Na primeira versão, deve suportar:

- chamada de função Python;
- subprocesso;
- existência/ausência de arquivo;
- hash de arquivo ou diretório;
- consulta RDF;
- comparação de conteúdo textual ou JSON.

O observador não modifica o sistema.

### 4.4 `StateSnapshot`

Registro imutável do estado observado em um instante.

Deve conter:

- identificador da execução;
- estado observado;
- status da observação;
- horário;
- parâmetros resolvidos;
- evidências;
- detalhes normalizados;
- erro, quando houver.

### 4.5 `TestAction`

Operação executável conhecida pelo orquestrador.

Uma ação pode ser implementada por:

- capability do OntoBDC;
- função Python;
- `hotfix.py`;
- comando subprocess;
- ação interna do runtime, como copiar fixture ou aplicar mutação.

A ação declara:

- estados exigidos (`requires`);
- estados que pretende produzir (`ensures`);
- efeitos colaterais;
- política de idempotência;
- parâmetros;
- timeout;
- mecanismo de execução.

`ensures` é uma intenção declarada. O estado só é confirmado após reobservação.

### 4.6 `RepairAction`

Especialização semântica de `TestAction` cujo objetivo é reparar um estado não satisfeito.

Todo `hotfix.py` deve ser exposto como `RepairAction`.

### 4.7 `TestCase`

Especificação reutilizável de um comportamento a testar.

Um caso declara:

- fixture inicial;
- condições dadas;
- ação principal;
- estados esperados;
- invariantes que não podem ser violados;
- dados e parâmetros;
- mutações preparatórias;
- política de limpeza.

O `TestCase` é definição, portanto não possui `passed` ou `failed`.

### 4.8 `TestCaseInstance`

Instância concreta gerada a partir de um `TestCase` e de um conjunto de parâmetros.

Exemplo:

```text
TestCase: reparar identidade do container
TestCaseInstance:
  container_name = techcenter-doc
  original_id = urn:ontobdc:storage/local/old-root/labsea
```

### 4.9 `TestFlow`

Sequência explicitamente ordenada de passos quando a própria ordem é parte do comportamento testado.

Uma suíte não representa ordem. Um fluxo representa.

### 4.10 `TestSuite`

Seleção lógica de casos e fluxos.

Pode selecionar por:

- identificadores;
- tags;
- componente;
- risco;
- tipo (`check`, `hotfix`, `state-machine`, `smoke`, `regression`);
- status do manifesto.

### 4.11 `ExecutionPlan`

Plano concreto e imutável compilado pelo runtime.

É um DAG ou uma sequência resolvida contendo:

- preparação;
- ações;
- checkpoints;
- observações;
- assertivas;
- limpeza;
- dependências;
- parâmetros finais.

### 4.12 `TestRun`

Execução concreta de um `ExecutionPlan`.

### 4.13 `StepRun`

Execução concreta de um passo do plano.

### 4.14 `ActualResult`

Resultado bruto observado durante uma execução: retorno, stdout, stderr, exceção, arquivo criado, triples RDF etc.

### 4.15 `AssertionResult`

Resultado de uma comparação ou assertiva específica.

### 4.16 `TestVerdict`

Classificação final de uma instância:

- `passed`;
- `failed`;
- `error`;
- `blocked`;
- `skipped`;
- `inconclusive`.

### 4.17 `TestEvidence`

Artefato que sustenta a observação ou o veredito:

- snapshot de diretório;
- hash;
- log;
- stdout/stderr;
- arquivo Turtle;
- diff RDF;
- diff textual;
- JSON serializado;
- traceback;
- plano resolvido.

---

## 5. Separação obrigatória entre estados

Não usar uma única propriedade `status` para tudo.

### 5.1 Estado do sistema

Exemplo:

```text
storage.container.metadata.ready
```

É observado por um check.

### 5.2 Estado operacional da execução

Valores:

```text
pending
planning
ready
running
cleaning
completed
aborted
```

### 5.3 Resultado de uma ação

Valores:

```text
succeeded
failed
error
noop
timed_out
```

### 5.4 Veredito do teste

Valores:

```text
passed
failed
error
blocked
skipped
inconclusive
```

Essa separação impede ambiguidades como “o teste está `ready`”: não fica claro se o sistema está pronto, o plano está pronto ou o teste passou.

---

## 6. Semântica de `check` e `hotfix`

### 6.1 O check é autoritativo

O resultado do hotfix não prova que o estado foi alcançado.

Regra obrigatória:

```text
antes: check
ação: hotfix
depois: check
veredito: derivado do check posterior e das invariantes
```

### 6.2 Normalização dos códigos de saída

Os checks atuais não são completamente uniformes. O manifesto deve permitir mapear códigos.

Padrão recomendado:

| Código | Interpretação |
|---:|---|
| `0` | estado satisfeito |
| `1` | estado não satisfeito |
| `2` | erro de observação ou entrada inválida |
| outro | erro, salvo mapeamento explícito |

O adapter deverá produzir:

```python
class ObservationStatus(str, Enum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    ERROR = "error"
```

O hotfix deverá produzir um `ActionOutcome`, porém o estado final será definido pelo recheck.

### 6.3 Idempotência

Todo hotfix deve possuir teste de idempotência.

Há duas formas aceitáveis:

1. **idempotência estrutural:** executar duas vezes gera o mesmo conteúdo normalizado;
2. **idempotência semântica:** o conteúdo pode mudar em metadados não essenciais, mas o grafo ou estado semântico permanece equivalente.

O manifesto deve declarar qual modalidade é exigida.

### 6.4 Preservação

Um hotfix deve provar que não destrói informação não relacionada.

Cada caso de hotfix deve declarar invariantes, por exemplo:

- título existente é preservado;
- descrição existente é preservada;
- data de criação existente é preservada;
- relações com datasets são preservadas;
- diretório não é renomeado;
- sujeitos antigos deixam de existir apenas quando explicitamente substituídos;
- arquivos fora do escopo não são modificados.

### 6.5 Falha segura

Quando o hotfix falhar:

- não deve deixar arquivo parcial sem indicação;
- deve preservar o original ou usar escrita atômica;
- deve registrar a exceção;
- deve permitir reproduzir o erro;
- o recheck deve continuar falhando;
- o veredito deve ser `error` ou `failed`, conforme a causa.

---

## 7. Modelo dos manifestos YAML

### 7.1 Cabeçalho comum

Todos os documentos devem usar:

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: StateDefinition
metadata:
  name: storage.container.metadata.ready
  title: Container metadata ready
  description: >
    The container metadata file exists and contains a valid container identity,
    semantic metadata and location.
  tags:
    - storage
    - container
    - metadata
spec: {}
```

Regras:

- `apiVersion` obrigatório;
- `kind` obrigatório;
- `metadata.name` obrigatório e único no catálogo;
- nomes canônicos em minúsculas, separados por ponto;
- títulos são humanos e podem mudar;
- IDs não devem conter versão de release;
- campos desconhecidos devem gerar erro na primeira versão;
- documentos podem ser separados por `---`;
- imports devem ser determinísticos.

### 7.2 Kinds iniciais

- `StateDefinition`;
- `TestAction`;
- `FixtureDefinition`;
- `TestCase`;
- `TestFlow`;
- `TestSuite`;
- `TestPolicy`.

### 7.3 Exemplo de estado baseado em check Python

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: StateDefinition
metadata:
  name: storage.container.metadata.ready
  title: Container metadata ready
  tags: [storage, container, metadata, check]
spec:
  observer:
    type: python-call
    target: ontobdc.storage.plugin.check.is_container_metadata_ready.check:main
    arguments:
      container_path: "${context.container_path}"
      root_path: "${context.root_path}"
    result:
      satisfiedWhen:
        exitCode: [0]
      unsatisfiedWhen:
        exitCode: [1]
      errorWhen:
        exitCode: [2]
      otherwise: error
  evidence:
    include:
      - "${context.container_path}/.__ontobdc__/container.ttl"
```

### 7.4 Exemplo de hotfix como ação

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: TestAction
metadata:
  name: storage.container.metadata.repair
  title: Repair container metadata
  tags: [storage, container, metadata, hotfix]
spec:
  role: repair
  executor:
    type: python-call
    target: ontobdc.storage.plugin.check.is_container_metadata_ready.hotfix:main
    arguments:
      container_path: "${context.container_path}"
      root_path: "${context.root_path}"
    result:
      succeededWhen:
        exitCode: [0]
      failedWhen:
        exitCode: [1]
      otherwise: error
  requires:
    - state: storage.container.directory.ready
  ensures:
    - state: storage.container.metadata.ready
  verification:
    mode: reobserve
    states:
      - storage.container.metadata.ready
  behavior:
    idempotency: semantic
    destructive: false
    retryable: false
  effects:
    write:
      - "${context.container_path}/.__ontobdc__/container.ttl"
```

### 7.5 Exemplo de capability como ação

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: TestAction
metadata:
  name: storage.container.metadata.ensure
  title: Ensure container metadata through capability
  tags: [storage, container, capability]
spec:
  role: transition
  executor:
    type: capability
    capabilityId: org.ontobdc.storage.plugin.capability.transformation.target.container_metadata_ready
  requires:
    - state: storage.container.directory.ready
  ensures:
    - state: storage.container.metadata.ready
  verification:
    mode: reobserve
```

### 7.6 Exemplo de fixture

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: FixtureDefinition
metadata:
  name: storage.container.metadata.legacy-identity
  title: Container with legacy identity
spec:
  sandbox:
    layout:
      - directory: my-desktop/techcenter-doc/.__ontobdc__
      - file:
          path: my-desktop/techcenter-doc/.__ontobdc__/container.ttl
          from: fixtures/storage/container-metadata/legacy-identity.ttl
  context:
    root_path: "${sandbox}/my-desktop"
    container_path: "${sandbox}/my-desktop/techcenter-doc"
```

### 7.7 Exemplo de caso de hotfix

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: TestCase
metadata:
  name: storage.container.metadata.hotfix.repairs-legacy-identity
  title: Hotfix repairs container identity without renaming the directory
  tags: [storage, container, metadata, hotfix, regression]
spec:
  fixture:
    ref: storage.container.metadata.legacy-identity

  given:
    states:
      - not: storage.container.metadata.ready

  when:
    action: storage.container.metadata.repair

  then:
    states:
      - storage.container.metadata.ready

  invariants:
    rdf:
      - file: "${context.container_path}/.__ontobdc__/container.ttl"
        preserve:
          predicates:
            - dcterms:title
            - ct:description
            - ct:creationDate
            - obdc:hasEntityDataset
            - obdc:belongsToDataContainer
    filesystem:
      - directoryNameUnchanged: "${context.container_path}"

  evidence:
    before:
      - "${context.container_path}/.__ontobdc__/container.ttl"
    after:
      - "${context.container_path}/.__ontobdc__/container.ttl"

  cleanup:
    mode: always
```

### 7.8 Parametrização

```yaml
spec:
  matrix:
    missingField:
      - identifier
      - title
      - description
      - creationDate
      - location
  fixture:
    ref: storage.container.metadata.valid
  prepare:
    mutations:
      - rdf.remove:
          file: "${context.container_path}/.__ontobdc__/container.ttl"
          predicateFromParameter: "${matrix.missingField}"
```

O compilador gera um `TestCaseInstance` para cada combinação.

### 7.9 Fluxo explícito

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: TestFlow
metadata:
  name: storage.container.create.lifecycle
  title: Complete container creation lifecycle
spec:
  fixture:
    ref: storage.empty-workspace

  steps:
    - id: directory
      action: storage.container.directory.ensure
      checkpoint:
        states:
          - storage.container.directory.ready

    - id: metadata
      action: storage.container.metadata.ensure
      checkpoint:
        states:
          - storage.container.metadata.ready

    - id: index
      action: storage.container.index.ensure
      checkpoint:
        states:
          - storage.container.index.ready

    - id: manifest
      action: storage.container.manifest.ensure
      checkpoint:
        states:
          - storage.container.manifest.synced
```

### 7.10 Suíte

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: TestSuite
metadata:
  name: storage.checks-and-hotfixes
  title: Storage checks and hotfixes
spec:
  include:
    tags:
      all:
        - storage
      any:
        - check
        - hotfix
  policies:
    isolation: per-case
    failFast: false
    cleanup: always
    requireEvidence: true
```

---

## 8. Estados simples, compostos e negativos

### 8.1 Estado simples

Observado por uma única probe.

```yaml
spec:
  observer:
    type: filesystem
    exists: "${context.container_path}"
    kind: directory
```

### 8.2 Estado composto

Combina outros estados:

```yaml
apiVersion: ontobdc.org/testing/v1alpha1
kind: StateDefinition
metadata:
  name: storage.container.healthy
spec:
  expression:
    all:
      - storage.container.metadata.ready
      - storage.container.index.ready
      - storage.container.manifest.synced
```

Operadores iniciais:

- `all`;
- `any`;
- `not`.

### 8.3 Estados negativos

Estados negativos devem ser expressos como negação no caso ou em expressão composta, não como uma proliferação de classes `...invalid`, salvo quando a invalidez for um estado de domínio real.

Preferir:

```yaml
given:
  states:
    - not: storage.container.metadata.ready
```

Em vez de criar automaticamente:

```text
storage.container.metadata.invalid
```

### 8.4 Estado impossível de observar

Erro de parsing, permissão ou assinatura incorreta não significa “estado não satisfeito”. Significa `ObservationStatus.ERROR`, e o teste deve terminar como `error`, não `failed`.

---

## 9. Planner semântico

### 9.1 Objetivo

Dado:

- estados iniciais observados;
- estados exigidos;
- ações registradas;
- efeitos declarados;
- políticas;
- ação principal do caso;

o planner deve produzir um `ExecutionPlan`.

### 9.2 Regras

1. observar o ambiente antes de planejar;
2. não executar ação para estado já satisfeito, salvo quando o caso exige exercitá-la;
3. resolver precondições recursivamente;
4. detectar ciclos;
5. rejeitar produtores ambíguos sem política de seleção;
6. não confiar em `ensures` sem reobservação;
7. inserir checkpoints após ações;
8. inserir snapshots conforme política;
9. manter ordem explícita de `TestFlow`;
10. produzir um plano serializável e estável.

### 9.3 Seleção entre múltiplos produtores

Uma ação pode ter:

```yaml
planning:
  priority: 100
  cost: 10
  preferred: true
```

Ordem inicial de decisão:

1. produtor explicitamente indicado no caso;
2. produtor marcado como `preferred`;
3. maior `priority`;
4. menor `cost`;
5. erro de ambiguidade se ainda houver empate.

### 9.4 Plano imutável

O plano compilado deve ser salvo antes da execução e possuir hash.

Mudanças dinâmicas durante a execução devem ser registradas como eventos, nunca sobrescrever silenciosamente o plano original.

### 9.5 Explicabilidade

Comando obrigatório:

```bash
ontobdc-dev test explain --case <id>
```

Deve explicar:

- estado-alvo;
- estado atual;
- precondições;
- ação escolhida;
- alternativas rejeitadas;
- checkpoints;
- invariantes;
- razão de cada passo.

---

## 10. Ciclo de execução

Para cada `TestCaseInstance`:

1. carregar catálogo;
2. validar schema;
3. resolver imports;
4. registrar estados e ações;
5. criar sandbox;
6. materializar fixture;
7. resolver contexto e parâmetros;
8. observar estados iniciais;
9. aplicar mutações de preparação;
10. observar novamente o `given`;
11. compilar o plano;
12. salvar `plan.json`;
13. capturar snapshot anterior;
14. executar setup;
15. executar ação principal ou fluxo;
16. capturar stdout, stderr, retorno e exceções;
17. reobservar estados esperados;
18. avaliar invariantes;
19. capturar snapshot posterior;
20. produzir assertivas;
21. calcular o veredito;
22. executar cleanup;
23. salvar relatório e evidências.

O cleanup deve rodar em bloco equivalente a `finally`, respeitando política `always`, `on-success`, `on-failure` ou `never`.

---

## 11. Test oracle

O oráculo é a combinação de:

- estados esperados;
- resultados esperados da ação;
- invariantes;
- ausência de erros;
- políticas da suíte.

O veredito deve obedecer:

### `passed`

- ação concluída de forma aceitável;
- todos os estados esperados satisfeitos;
- todas as invariantes satisfeitas;
- nenhuma observação em erro.

### `failed`

- comportamento observado é válido tecnicamente, porém não corresponde ao esperado;
- check posterior continua não satisfeito;
- invariante foi violada.

### `error`

- exceção inesperada;
- manifesto inválido detectado apenas em runtime;
- erro ao observar;
- fixture não pôde ser criada;
- cleanup crítico falhou;
- timeout.

### `blocked`

- dependência externa indisponível;
- precondição não atingível;
- produtor necessário ausente.

### `skipped`

- exclusão explícita por política, plataforma ou marcador.

### `inconclusive`

- execução ocorreu, mas evidência insuficiente para veredito.

---

## 12. Evidências e diretório de execução

Estrutura recomendada:

```text
.ontobdc-dev/
└── test-runs/
    └── <run-id>/
        ├── manifest.lock.yaml
        ├── catalog.json
        ├── plan.json
        ├── context.json
        ├── events.jsonl
        ├── summary.json
        ├── junit.xml
        ├── logs/
        │   ├── runner.log
        │   └── steps/
        ├── states/
        │   ├── before.json
        │   ├── checkpoints/
        │   └── after.json
        ├── evidence/
        │   ├── before/
        │   ├── after/
        │   └── diffs/
        └── sandbox/
```

Requisitos:

- `manifest.lock.yaml` contém os manifests efetivamente usados e seus hashes;
- `events.jsonl` é append-only;
- arquivos de evidência possuem hash SHA-256;
- caminhos absolutos sensíveis devem ser normalizados nos relatórios;
- o sandbox pode ser preservado em caso de falha com `--keep-sandbox`;
- o run deve registrar versão Python, sistema operacional, branch e commit dos repositórios envolvidos.

---

## 13. Fixtures e mutações

### 13.1 Fixture

Uma fixture representa o estado inicial reproduzível.

Pode ser criada por:

- template de diretório;
- cópia de arquivos;
- geração programática;
- chamada de capability;
- referência a snapshot versionado.

### 13.2 Mutação

Mutações criam cenários inválidos sem duplicar dezenas de fixtures.

Adapters iniciais:

- `filesystem.remove`;
- `filesystem.rename`;
- `filesystem.write`;
- `filesystem.chmod` quando suportado;
- `rdf.add`;
- `rdf.remove`;
- `rdf.replace-subject`;
- `json.set`;
- `text.replace`.

Toda mutação deve:

- ser declarativa;
- produzir evidência;
- ficar restrita ao sandbox;
- ser reversível por descarte do sandbox.

### 13.3 Proibição

A primeira versão não deve executar mutações fora do sandbox, salvo opção explícita de desenvolvimento com confirmação e flag de risco. CI nunca deve habilitar isso.

---

## 14. Cobertura obrigatória para cada check e hotfix

O objetivo não é apenas “um teste por arquivo”. Cada check/hotfix deverá possuir uma matriz mínima.

### 14.1 Check sem hotfix

1. **positivo:** fixture válida → check satisfeito;
2. **negativo:** fixture inválida → check não satisfeito;
3. **erro de observação:** entrada impossível ou arquivo malformado → resultado `error`, quando distinguível;
4. **determinismo:** duas observações do mesmo snapshot produzem o mesmo status;
5. **não mutação:** hash do escopo permanece igual após o check.

### 14.2 Check com hotfix

Além dos anteriores:

1. **reparo:** inválido → hotfix → válido;
2. **recheck obrigatório:** hotfix `0` sem estado válido não pode passar;
3. **idempotência:** válido → hotfix → continua semanticamente equivalente;
4. **preservação:** dados não relacionados permanecem;
5. **falha segura:** erro não deixa corrupção parcial;
6. **limite de escopo:** hotfix não altera arquivos fora dos efeitos declarados;
7. **casos parciais:** cada requisito interno do check deve ser isoladamente violado;
8. **composição:** o estado reparado habilita a capability ou transição seguinte.

### 14.3 Máquina de estados

Para cada statechart:

1. estado inicial;
2. cada transição válida;
3. tentativa de transição inválida;
4. retomada a partir de estado intermediário;
5. no-op quando o estado já está satisfeito;
6. falha da capability;
7. check posterior não confirma o estado;
8. ciclo inexistente;
9. estado final correto;
10. lista de estados visitados coerente.

---

## 15. Inventário automático dos checks e hotfixes

Criar:

```bash
ontobdc-dev test inventory
```

O comando deve varrer os repositórios descobertos no workspace por:

```text
src/**/plugin/check/*/check.py
src/**/plugin/check/*/hotfix.py
```

Para cada item, registrar:

- repositório;
- componente;
- identificador do check;
- path;
- callable exportado;
- assinatura;
- presença de hotfix;
- capabilities que importam o check/hotfix;
- testes `pytest` existentes;
- manifesto semântico existente;
- status de cobertura.

Saída:

```text
CHECK                              HOTFIX  MANIFEST  POS  NEG  REPAIR  IDEMPOTENCE
storage.container_metadata_ready   yes     yes       yes  yes  yes     yes
storage.container_manifest_synced  yes     no        no   no   no      no
...
```

Também deve gerar JSON para CI.

### 15.1 Scaffold

Criar:

```bash
ontobdc-dev test scaffold --from-checks
```

O scaffold deve:

- gerar IDs canônicos;
- criar `StateDefinition`;
- criar `RepairAction` quando houver hotfix;
- gerar esqueleto de casos;
- marcar campos não inferidos com `TODO`;
- nunca considerar manifesto gerado automaticamente como aprovado;
- usar `metadata.status: draft`.

---

## 16. Gate de cobertura

Criar:

```bash
ontobdc-dev test coverage --checks
```

Critérios:

- 100% dos checks inventariados possuem `StateDefinition`;
- 100% dos checks possuem caso positivo e negativo;
- 100% dos hotfixes possuem caso de reparo;
- 100% dos hotfixes possuem caso de idempotência;
- 100% dos hotfixes possuem ao menos uma invariante de preservação;
- nenhuma referência de manifesto está quebrada;
- nenhuma action declara `ensures` sem verificação posterior.

CI deverá falhar quando a cobertura ficar abaixo do exigido.

---

## 17. CLI inicial

```bash
ontobdc-dev test validate [PATH]
ontobdc-dev test inventory
ontobdc-dev test scaffold --from-checks
ontobdc-dev test list states|actions|cases|flows|suites
ontobdc-dev test plan --case <id>
ontobdc-dev test plan --suite <id>
ontobdc-dev test explain --case <id>
ontobdc-dev test run --case <id>
ontobdc-dev test run --suite <id>
ontobdc-dev test coverage --checks
ontobdc-dev test report <run-id>
```

Proxy no OntoBDC:

```bash
ontobdc dev test ...
```

Flags iniciais:

```text
--root-dir
--manifest
--param key=value
--tag
--exclude-tag
--dry-run
--keep-sandbox
--fail-fast
--output
--format text|json|junit
--verbosity
```

Códigos de saída da CLI:

| Código | Significado |
|---:|---|
| `0` | todos passaram |
| `1` | ao menos um `failed` |
| `2` | erro de configuração ou execução |
| `3` | bloqueado sem execução suficiente |
| `4` | manifesto inválido |

---

## 18. Estrutura do boilerplate no `ontobdc-dev`

```text
src/ontobdc_dev/testing/
├── __init__.py
├── domain/
│   ├── enum.py
│   ├── exception.py
│   ├── model/
│   │   ├── metadata.py
│   │   ├── state.py
│   │   ├── action.py
│   │   ├── fixture.py
│   │   ├── case.py
│   │   ├── flow.py
│   │   ├── suite.py
│   │   ├── plan.py
│   │   ├── run.py
│   │   ├── result.py
│   │   └── evidence.py
│   └── port/
│       ├── loader.py
│       ├── observer.py
│       ├── executor.py
│       ├── planner.py
│       ├── snapshot.py
│       └── reporter.py
├── application/
│   ├── catalog.py
│   ├── validator.py
│   ├── compiler.py
│   ├── planner.py
│   ├── runner.py
│   ├── oracle.py
│   ├── inventory.py
│   ├── coverage.py
│   └── reporter.py
├── adapter/
│   ├── yaml_loader.py
│   ├── schema_validator.py
│   ├── python_call.py
│   ├── subprocess.py
│   ├── capability.py
│   ├── filesystem.py
│   ├── rdf.py
│   ├── snapshot.py
│   ├── evidence.py
│   └── junit.py
├── plugin/
│   ├── observer/
│   │   ├── check.py
│   │   ├── filesystem.py
│   │   └── rdf.py
│   ├── action/
│   │   ├── hotfix.py
│   │   ├── capability.py
│   │   └── mutation.py
│   └── command/
│       ├── base.py
│       ├── validate.py
│       ├── inventory.py
│       ├── scaffold.py
│       ├── list.py
│       ├── plan.py
│       ├── explain.py
│       ├── run.py
│       ├── coverage.py
│       └── report.py
└── schema/
    └── v1alpha1/
        ├── common.schema.json
        ├── state.schema.json
        ├── action.schema.json
        ├── fixture.schema.json
        ├── case.schema.json
        ├── flow.schema.json
        └── suite.schema.json
```

Manifestos do workspace:

```text
tests/semantic/
├── catalog.yaml
├── states/
├── actions/
├── fixtures/
├── cases/
├── flows/
├── suites/
└── resources/
```

Os testes unitários do próprio orquestrador permanecem em:

```text
tests/testing/
```

---

## 19. Modelos de domínio mínimos

Usar `dataclasses` ou classes de domínio simples. Não passar dicionários crus entre camadas.

Interfaces mínimas:

```python
class StateObserverPort(Protocol):
    def observe(
        self,
        definition: StateDefinition,
        context: ExecutionContext,
    ) -> StateSnapshot:
        ...


class ActionExecutorPort(Protocol):
    def execute(
        self,
        action: TestAction,
        context: ExecutionContext,
    ) -> ActionResult:
        ...


class TestPlannerPort(Protocol):
    def compile_case(
        self,
        case: TestCaseInstance,
        catalog: TestCatalog,
        context: ExecutionContext,
    ) -> ExecutionPlan:
        ...


class TestRunnerPort(Protocol):
    def run(self, plan: ExecutionPlan) -> TestRun:
        ...
```

Objetos devem ser imutáveis sempre que possível, especialmente:

- definições carregadas;
- instâncias;
- plano;
- snapshots;
- resultados.

---

## 20. Validação dos manifestos

Duas etapas:

### 20.1 Validação estrutural

JSON Schema:

- campos obrigatórios;
- tipos;
- enums;
- formatos;
- rejeição de campos desconhecidos;
- validação por `kind`.

### 20.2 Validação semântica

- IDs únicos;
- referências existentes;
- ausência de ciclos entre estados e ações;
- parâmetros resolvíveis;
- action com executor conhecido;
- state com observer conhecido;
- `ensures` sempre verificável;
- suite não vazia;
- flow com IDs de step únicos;
- fixture restrita ao sandbox;
- efeito destrutivo explicitamente declarado;
- `TestCase` com ao menos uma expectativa;
- códigos de saída sem sobreposição.

O comando `validate` deve mostrar path YAML e linha/coluna quando possível.

---

## 21. Determinismo e reprodutibilidade

O mesmo catálogo, fixture, parâmetros e versões deve produzir o mesmo plano.

Registrar:

- hash dos manifestos;
- versão do `ontobdc-dev`;
- commit dos repositórios;
- versão Python;
- plataforma;
- timezone;
- locale relevante;
- parâmetros;
- seed aleatório.

Datas geradas por hotfixes podem impedir comparação byte a byte. Para esses casos:

- normalizar predicates voláteis;
- usar equivalência semântica;
- permitir máscaras de comparação;
- nunca ignorar campos voláteis sem declaração explícita.

---

## 22. Segurança operacional

- sandbox por padrão;
- proteção contra path traversal;
- resolução e validação de todos os paths;
- proibição de apagar fora do sandbox;
- timeout por ação;
- limite de tamanho das evidências;
- mascaramento de segredos;
- nenhum shell implícito em subprocessos;
- comandos como lista de argumentos;
- escrita atômica recomendada para hotfixes;
- opção destrutiva exigindo `--allow-destructive` e manifesto marcado.

---

## 23. Integração com `pytest`

O runtime e o catálogo serão testados por `pytest`.

Além disso, fornecer helper:

```python
def test_semantic_suite(semantic_runner):
    result = semantic_runner.run_suite("storage.checks-and-hotfixes")
    assert result.verdict == TestVerdict.PASSED
```

Também pode haver geração de parametrização:

```python
@pytest.mark.parametrize(
    "case_id",
    semantic_catalog.case_ids(tags=["smoke"]),
)
def test_semantic_case(semantic_runner, case_id):
    semantic_runner.assert_case(case_id)
```

O manifesto não deve esconder bugs do runtime. Adapters, planner, parser, oracle e reporter precisam de testes unitários tradicionais.

---

## 24. Plano de implementação

### Fase 0 — inventário e baseline

- implementar ou produzir manualmente o inventário inicial;
- listar todos os checks e hotfixes;
- identificar assinaturas e convenções de retorno;
- mapear capabilities e estados relacionados;
- registrar testes existentes;
- congelar baseline de cobertura.

**Saída:** `inventory.json` e tabela no PR.

### Fase 1 — domínio e loader

- modelos de domínio;
- enums;
- exceptions;
- loader YAML;
- composição de documentos;
- schemas `v1alpha1`;
- validação estrutural e semântica;
- comandos `validate` e `list`.

**Aceite:** exemplos válidos carregam; referências inválidas falham com mensagem útil.

### Fase 2 — observers e snapshots

- adapter `python-call`;
- adapter de check;
- filesystem;
- RDF;
- normalização de códigos;
- evidências;
- snapshot anterior/posterior.

**Aceite:** um check existente pode ser executado por manifesto sem wrapper específico.

### Fase 3 — actions e hotfixes

- adapter de função Python;
- adapter de hotfix;
- adapter de capability;
- timeout;
- captura de output;
- reobservação obrigatória;
- action result.

**Aceite:** caso real de `container_metadata_ready` executa `check → hotfix → recheck`.

### Fase 4 — fixtures, mutações e sandbox

- criação do sandbox;
- materialização de fixtures;
- mutações filesystem e RDF;
- cleanup;
- preservação opcional em falha.

**Aceite:** cenários positivo e negativo podem compartilhar fixture base.

### Fase 5 — compiler e planner

- expansão de matriz;
- `TestCaseInstance`;
- DAG de dependências;
- detecção de ciclo;
- escolha de produtores;
- plano serializado;
- `plan` e `explain`.

**Aceite:** planner alcança `container.metadata.ready` a partir de diretório preparado e explica a escolha.

### Fase 6 — runner e oracle

- lifecycle completo;
- eventos;
- checkpoints;
- invariantes;
- vereditos;
- fail-fast;
- resultados agregados.

**Aceite:** suíte executa vários casos isoladamente e agrega resultados corretamente.

### Fase 7 — inventory, scaffold e coverage

- varredura dos repositórios;
- correlação check/hotfix/capability/test;
- scaffold;
- relatório de cobertura;
- gate CI.

**Aceite:** qualquer novo check sem manifesto faz a cobertura falhar.

### Fase 8 — migração de todos os checks/hotfixes

Para cada check:

- estado;
- fixture;
- positivo;
- negativo;
- não mutação.

Para cada hotfix:

- action;
- reparo;
- recheck;
- idempotência;
- preservação;
- falha segura.

**Aceite:** 100% conforme seção de cobertura.

### Fase 9 — relatórios e documentação

- JSON;
- JUnit XML;
- resumo textual Rich;
- documentação de autoria;
- exemplos;
- guia de depuração.

---

## 25. Primeiro caso vertical obrigatório

Usar `is_container_metadata_ready` como implementação vertical de referência.

Casos mínimos:

1. container válido passa no check;
2. diretório inexistente falha no check;
3. `container.ttl` ausente falha;
4. Turtle malformado produz observação classificada;
5. múltiplos sujeitos `DataContainer` falham;
6. identificador antigo falha;
7. título ausente falha;
8. descrição ausente falha;
9. data de criação ausente falha;
10. localização errada falha;
11. hotfix cria metadata ausente;
12. hotfix reescreve identidade antiga;
13. hotfix preserva título existente;
14. hotfix preserva descrição existente;
15. hotfix preserva creationDate existente;
16. hotfix preserva relações com datasets;
17. hotfix não renomeia o diretório;
18. hotfix é semanticamente idempotente;
19. check posterior confirma o estado;
20. capability retorna o estado esperado;
21. falha do hotfix impede transição;
22. state machine retoma de `DIRECTORY_READY`;
23. state machine não refaz estado já satisfeito.

Esse caso vertical define o padrão para os demais.

---

## 26. Critérios de aceite do boilerplate

O boilerplate estará pronto quando:

- a CLI reconhecer `ontobdc-dev test`;
- manifests `v1alpha1` forem validados;
- um catálogo puder ser composto por múltiplos arquivos;
- checks existentes puderem ser observadores sem alteração de código;
- hotfixes existentes puderem ser ações sem alteração de código;
- capabilities puderem ser ações;
- planner produzir e salvar plano;
- runner usar sandbox;
- recheck for obrigatório;
- snapshots e evidências forem produzidos;
- vereditos estiverem separados de status operacionais;
- JUnit XML puder ser consumido por CI;
- inventory encontrar checks/hotfixes no workspace;
- coverage detectar ausência de manifests;
- o caso vertical de container metadata estiver completo;
- documentação explicar como adicionar um novo check/hotfix.

---

## 27. Definition of Done para cada novo check

Um novo check só está completo quando:

- possui ID canônico;
- possui `StateDefinition`;
- documenta códigos de retorno;
- não modifica o sistema;
- possui caso positivo;
- possui caso negativo;
- possui caso de erro quando aplicável;
- possui teste de não mutação;
- aparece no inventory;
- aparece como coberto;
- possui relação com capability ou fluxo, quando aplicável.

## 28. Definition of Done para cada novo hotfix

Um novo hotfix só está completo quando:

- possui `TestAction` com role `repair`;
- declara `requires`;
- declara `ensures`;
- declara efeitos de escrita;
- possui caso de reparo;
- possui recheck;
- possui idempotência;
- possui invariantes de preservação;
- possui caso de falha segura;
- não escreve fora do escopo;
- aparece no inventory;
- aparece como coberto.

---

## 29. Decisões que não devem ser revertidas silenciosamente

1. **Suíte agrupa; fluxo ordena.**
2. **Check observa; hotfix modifica.**
3. **Retorno do hotfix não comprova estado.**
4. **Todo efeito deve ser reobservado.**
5. **Estado do sistema, status do run e veredito são conceitos diferentes.**
6. **Manifesto é declarativo; executor é plugin.**
7. **Plano é compilado e persistido antes de executar.**
8. **Sandbox é o padrão.**
9. **Campos desconhecidos em YAML falham.**
10. **Novo check/hotfix sem cobertura deve quebrar o gate.**
11. **O runtime complementa, não substitui, `pytest`.**
12. **Termos específicos do OntoBDC devem ser documentados como extensão interna, não como nomenclatura normativa externa.**

---

## 30. Entregáveis esperados da implementação

- pacote `ontobdc_dev.testing`;
- schemas dos manifestos;
- CLI completa da primeira versão;
- catálogo de exemplo;
- caso vertical de container metadata;
- inventário de checks/hotfixes;
- manifests para todos os checks/hotfixes;
- fixtures correspondentes;
- suíte `checks-and-hotfixes`;
- gate de cobertura;
- relatório JUnit;
- documentação de autoria;
- documentação de depuração;
- testes unitários do parser, planner, runner, adapters e oracle.

---

## 31. Resultado arquitetural esperado

Ao final, o OntoBDC deverá ser capaz de expressar:

```text
estado observado
→ ação possível
→ precondições
→ efeitos pretendidos
→ plano de alcance
→ execução
→ novo estado observado
→ evidências
→ veredito
```

O mesmo vocabulário servirá para:

- testar checks isolados;
- testar hotfixes;
- testar capabilities;
- testar encadeamentos;
- testar máquinas de estado;
- testar regressões;
- validar releases;
- explicar por que o sistema considera um container, dataset ou contexto saudável.

Essa é a finalidade do orquestrador semântico: transformar a lógica implícita dispersa entre checks, hotfixes, capabilities, enums e statecharts em especificações executáveis, rastreáveis e verificáveis.
