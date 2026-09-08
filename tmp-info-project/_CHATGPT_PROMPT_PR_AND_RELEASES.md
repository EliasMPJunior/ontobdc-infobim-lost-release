# Prompt ChatGPT: Gerar PRs → Master + Releases (Títulos + Notes)

Este é um prompt em 2 FASES. **Execute SOMENTE a FASE 1 agora.**
Guarde o trabalho de FASE 2 em memória / rascunho e **não a gere até eu avisar explicitamente** com a mensagem
`Fase 2: gerar releases — todos os PRs aprovados`.

---

## Contexto do Monorepo (5 pacotes Python, 5 versões)

O diretório de trabalho `/Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC`
é um **monorepo com 5 repositórios Git independentes (subdiretórios)**, cada um com sua PR própria para `master`
e sua Release própria.

| Pasta (repositório)  | Branch de versão (head ATUAL a ser mergeado) | Tag versão anterior (para diff) | Nome da release → |
|---|---|---|---|
| `./brasidatacenter/`   | `v0.6`  | `0.5.0`     | `v0.6.0`  |
| `./develop/`           | `v0.2`  | `v0.2.0`    | `v0.2.0`  |
| `./infobim/`           | `v0.6`  | `v0.5.3`    | `v0.6.0`  |
| `./ontobdc/`           | `v0.17` | `v0.16.4`   | `v0.17.0` |
| `./presentation/`      | `v0.4`  | `v0.3.1`    | `v0.4.0`  |

**Ordem de merge (importante, pois infobim/develop/presentation dependem de ontobdc; todos dependem de brasidatacenter):**
1. brasidatacenter  (`v0.6`  → `master`)
2. ontobdc           (`v0.17` → `master`)
3. presentation      (`v0.4`  → `master`)
4. develop           (`v0.2`  → `master`)
5. infobim           (`v0.6`  → `master`)

---

## ⚙️ Como obter o conteúdo real (você DEVE fazer isso em seu ambiente)

Para CADA repositório `$dir` na tabela acima, execute:

```bash
cd "$dir"
# 1) Confirmar branch atual = branch de versão
git checkout vX.Y            # (branch na tabela)
git branch --show-current
# 2) Confirmar base da PR = master
git fetch origin master
# 3) Resumo (stat) do que será incluído nesta PR
git diff --stat master...HEAD
# 4) Lista de commits a serem mergeados
git log --oneline master...HEAD
# 5) Diffs detalhados se precisar justificar algo no PR body
git diff master...HEAD -- src/ tests/ docs/ pyproject.toml CHANGELOG.md
```

**Não invente conteúdo.** Se houver 0 diff de master...HEAD em develop (parece, pois branch v0.2 e tag v0.2.0
coincidem em master), então descreva a PR como "No-op release alignment / tag cut" e não gere release notes
falsas.

---

## 📋 Diffs reais já extraídos para OntoBDC v0.17 e InfoBIM v0.6 (use como referência)

### Repositório `ontobdc/` — versão `v0.17.0` (branch `v0.17`)

**Pontos ALTOS (highlights) NÃO NEGLIGENCIÁVEIS que a PR body e release notes DEVEM mencionar:**

1.  **Novo contrato `CapabilityMetadata.log_message` + single-point log em `CapabilityExecutor.execute`**
    -   `log_message["info"][lang]` = frase humanizada em VERBO PASSADO (happy-path, nível INFO)
    -   `log_message["debug_entry"][lang]` = frase humanizada em VERBO GERÚNDIO / presente contínuo,
        prefixada automaticamente com `[STARTED]` em cinza (nível DEBUG), disparado **antes** da capability rodar
    -   `log_message["debug_exception"][lang]` e `log_message["debug_<tipo_excecao_snake_case>"][lang]`
        = frases específicas por família de exceção; fallback 100% garantido = `str(exc)`
    -   Nenhuma capability deve mais escrever `logger.info(...)` / `logger.debug(...)` dentro de `execute()`.
2.  **Correção do bug CLI InfoBIM (NullLogRepository hardcoded)**
    -   Antes: `infobim/cli/__init__.py` criava `logger = NullLogRepository()` hardcoded → `--log-level DEBUG`
        nunca funcionava e capability logs nunca apareciam no InfoBIM.
    -   Depois: segue exatamente o mesmo padrão de `ontobdc/cli/__init__.py` — cria `InLineLogger()`,
        aplica `LogStrategyConfig(log_level=DEBUG, log_repository=logger)` para setar threshold,
        só depois chama `set_active_log_repository(logger)`, faz `clear_active_log_repository()` no `finally`.
3.  **Centralização de cores ANSI SGR (eliminação de duplicação hardcoded)**
    -   Novo módulo single-purpose: `ontobdc.shared.adapter.terminal_color` com RESET, GRAY (Bright Black
        `\033[90m` — mesmo SGR do timestamp do InLineLogger), 14 cores 4-bit, estilos BOLD/DIM,
        helpers `rgb_fg(r,g,b)` / `rgb_bg(r,g,b)`, regex centralizado `ANSI_ESCAPE_REGEX`.
    -   4 arquivos refatorados: `cli/adapter/logger.py`, `cli/adapter/surface_renderer.py`,
        `shared/adapter/logo.py`, `shared/adapter/capability.py` — pararam de hardcodar `\033[90m` / `\033[0m`.
4.  **`debug_entry["en"]` humanizado já cadastrado em 11 OntoBDC view transformation capabilities + 1 CLI
    `ConfigAdapterReadyCapability` (TransactionCapability) + 5 InfoBIM project transformation capabilities.**
5.  **Novo componente terminal-only `onto-logo-tile-terminal` é terminal-only (não tem JS embed).**
    Ver InfoBIM abaixo.
6.  **Pipeline novo CLI global `--log-level` global flag (antes só INFO default; agora suporta DEBUG / NOTICE etc).**
7.  **Arquivo docs/manual/parameter_strategies.md novo (228 linhas) documentando Parameter Strategy flow.**
8.  **Storage `--container` bare selector fix (sem --update era rejeitado).**
9.  **Refatoração storage attachment: pacote `storage/adapter/attachment/` modularizado com context.py,
    error.py, graph.py, machine.py, metadata.py, plan.py, transaction.py em vez de arquivos planos.**
10. **Novo `storage/adapter/identifier.py` com UUID4 estável (antes usava path-derived urn).**
11. **Context `--graph` agora lista agrupada por subject (netext layout) — antes graph node-link.**
12. **Shared Terminal Surface Renderer pipeline novo (tabelas, spans, widgets) unificado entre OntoBDC e InfoBIM.**

**Diff stat de referência (v0.16.4 → HEAD):** 94 files changed; ver rodapé do prompt para estatística detalhada.

### Repositório `infobim/` — versão `v0.6.0` (branch `v0.6`)

**Pontos ALTOS (highlights) NÃO NEGLIGENCIÁVEIS:**

1.  **Fix do crash `infobim view project → ontobdc-view did not provide component source: onto-logo-tile-terminal`**
    -   **Causa raiz (não workaround):** `InfoBIMComponentSourceAdapter.scripts()` carregava **TODOS** os components
        registrados no `ComponentLoader().get_all()` shared, incluindo o `onto-logo-tile-terminal` que é um widget
        **TERMINAL-ONLY** (fez parte do unificado shared terminal surface renderer — não tem JS para embedar na
        surface HTML offline). Quando `ontobdc_view.component_source("onto-logo-tile-terminal")` retornava vazio,
        um `raise ValueError` genérico quebrava todo `infobim view project`.
    -   **Fix correto:** a loop em `InfoBIMComponentSourceAdapter.scripts()` agora **pula** opcionalmente qualquer tag
        que retorne source vazio **MENOS** a tag obrigatória `"onto-presentation-surface"` (runtime cliente que todo
        tile precisa — se essa faltar, ainda raise como packaging error de verdade).
2.  **CLI InfoBIM agora respeita `--log-level DEBUG` (vide bug NullLogRepository hardcoded corrigido).**
    -   Capability `debug_entry` aparece agora: `[HH:MM:SS] ▶ DEBUG [STARTED] <frase humanizada gerúndio>`
        + depois `▶ INFO <frase humanizada passado>` para cada transformation/transaction capability.
3.  **5 capabilities InfoBIM project (`transformation/`) já com `debug_entry["en"]` cadastrado:**
    -   `OntoBDCContainerReadyCapability` — *Creating or validating the project path as an OntoBDC container…*
    -   `ProjectDatasetReadyCapability` — *Creating or validating the reserved InfoBIM project EntityDataset…*
    -   `IfcProjectReadyCapability` — *Creating or validating the editable IfcProject instance and its XLSX…*
    -   `IfcProjectFacadeReadyCapability` — *Constructing the IFC project facade from the IFC file header…*
    -   `ProjectReadyCapability` — *Validating the complete InfoBIM project contract…*
4.  **Pacote NOVO `infobim.element` (414 linhas parameter adapter + 4 comandos):**
    -   `element set-parameter`, `set-parameter-all`, `unset-parameter`, `unset-all-parameters`
    -   254 testes novos (test_parameter + test_commands).
5.  **i18n refatorado para shared central adapter (arquivos de locale em `view/adapter/i18n/locale/*.yaml`).**
6.  **Project tile JS component atualizado com file-size + i18n placeholders.**
7.  **Shared Terminal Surface Renderer unificado (mesmo pipeline do OntoBDC para CLI frame `>_ InfoBIM`).**

**Diff stat de referência (v0.5.3 → HEAD):** 41 files changed, 1781 insertions(+), 87 deletions(-).

---

# FASE 1 — Gerar 5 PRs (uma por pacote) para `master`.

**Para CADA repositório da tabela, gere UM bloco de PR com a seguinte estrutura EXATA. Se o diff
master...HEAD for ZERO (como pode ser develop v0.2), escreva explicitamente "No-op PR: tag alignment
release cut / nenhuma alteração de código nova" em vez de inventar mudanças.**

Use **Commits Semânticos em INGLÊS** em títulos de PR e headings de release notes.

---

### Modelo de PR (copiar este modelo 5 vezes, uma por pacote)

```markdown
# PR #<NÚMERO_AUTOMATICO_POR_REPO>: <TÍTULO_SEMÂNTICO>

**Repositório:** `<nome-do-repo>` | **Branch head:** `vX.Y` → **Branch base:** `master`  
**Versão que sai:** `<tag release>` | **Comparação (diff base):** `git diff <tag_anterior>...HEAD`  
**Requer aprovação / merge de:** `<repo que deve ser mergeado ANTES, se houver dependência>` (ex: infobim requer ontobdc)

## Resumo (Summary)

1-3 frases curtas em INGLÊS explicando o que esta PR entrega. Não use jargão.

## Principais mudanças (Highlights) — bullet points em INGLÊS

-   **feat|fix|refactor|docs|test|chore:** `<descrição curta>`
-   Repetir para cada ponto alto (use os listados acima para OntoBDC v0.17 / InfoBIM v0.6)

## Principais arquivos / locais impactados

-   `path/do/arquivo.py#L1-L10` — o que mudou
-   Repetir para cada arquivo de top 5 mais impactado

## Testagem realizada (Testing)

Preencha com o que foi provado em sandbox para OntoBDC v0.17 / InfoBIM v0.6 (abaixo).
Para brasidatacenter / develop / presentation **não invente testes**: escreva
"Testing required from maintainer — no sandbox evidence available for this repo."

Provas reais já executadas (OntoBDC v0.17):
-   `_prove_config_adapter_started.py` executou com sucesso e produziu:
    `[HH:MM:SS] ▶ DEBUG [STARTED] Creating or validating the CLI bootstrap configuration file so the shared ConfigDataAdapter can be used downstream.`
    seguido de `▶ INFO Configuration bootstrap file was created or validated and is ready for CLI initialization.`
-   `ontobdc view project --project-id ... --log-level DEBUG` pipeline executou com 11 capabilities exibindo
    prefixo cinza `[STARTED]` + INFO humanizado, em `tmp-info-project/`.

Provas reais já executadas (InfoBIM v0.6):
-   `InfoBIMComponentSourceAdapter().scripts()` retornou 16 scripts com sucesso;
    `onto-logo-tile-terminal` skipado sem erro; `onto-presentation-surface` presente.
-   `infobim init --log-level DEBUG` mostrou `[18:16:21] ▶ INFO The system is healthy for bootstrap.`
    (timestamp cinza + nível INFO aparecendo = prova que NullLogRepository bug foi corrigido).

## Checklist de merge (preencha para cada PR)

-   [ ] `master` está atualizado localmente (`git pull origin master`)
-   [ ] `vX.Y` está atualizada em cima do `master` (`git merge --no-ff master` ou `git rebase master` quando aplicável)
-   [ ] `pytest` / `python -m compileall src/` passa no repo
-   [ ] `CHANGELOG.md` tem entrada para a versão `<tag release>` em heading `## [<tag>] - YYYY-MM-DD`
-   [ ] `pyproject.toml` / `__version__.py` reflete versão `<tag release>` (major/minor)
-   [ ] Nenhum arquivo do diretório `/Users/eliasmpjunior/infobim/deploy/ontobdc-stack/core` foi modificado (proibido)
-   [ ] Nenhum fallback não solicitado / workaround (Regra de projeto)
-   [ ] Tipagem explícita, imports no topo, PEP8 ordem Standard → Third → Local (Regras de projeto)
-   [ ] Todas as capabilities transformation/transaction adicionaram `debug_entry["en"]` + `info["en"]` em `METADATA.log_message`
        (NÃO escrevem `logger.info/debug` dentro de `execute()`) (Regra de projeto)
-   [ ] Cores ANSI usam `from ontobdc.shared.adapter.terminal_color import GRAY, RESET, ...` — não hardcodam `\033[90m` (Regra de projeto)

## Instrução para revisor (Reviewer guidance)

Foco do review: `<1-2 frases em INGLÊS>` — ex: "Focus review on root-cause fix in component source adapter; ensure only terminal-only components are skipped and onto-presentation-surface always raises on missing."
```

---

### Instrução específica para CADA uma das 5 PRs

1.  **PR (1/5) — brasidatacenter v0.6 → master.** Diff com `git diff 0.5.0...master...HEAD`. Se desconhecer o conteúdo,
    faça o diff real no ambiente primeiro.
2.  **PR (2/5) — ontobdc v0.17 → master.** Use os 12 highlights listados acima. **OBRA PRINCIPAL desta batch.**
    Título PR recomendado (Commits Semânticos INGLÊS):
    `feat(capability,cli): single-point humanized debug_entry/info logs; centralize ANSI colors; --log-level DEBUG pipeline`
3.  **PR (3/5) — presentation v0.4 → master.** Diff com `git diff v0.3.1...HEAD`.
4.  **PR (4/5) — develop v0.2 → master.** Diff com `git diff v0.2.0...HEAD`.
    Se diff = 0, escreva noop e checklist mínimo.
5.  **PR (5/5) — infobim v0.6 → master.** Use os 7 highlights acima. Depende de PR ontobdc v0.17 SER mergeado ANTES
    (pois InfoBIM consome novos contratos shared/CapabilityMetadata.log_message e terminal_color).
    Título PR recomendado:
    `fix(view,cli,element): skip terminal-only component tags in offline surface scripts; unlock --log-level DEBUG; add infobim.element parameter adapter + 4 commands`

---

# FASE 2 — (GUARDE. NÃO GERE AGORA. ESPERE MENSAGEM EXPLÍCITA.)

Quando eu enviar `Fase 2: gerar releases — todos os PRs aprovados`, gere 5 releases uma por repo
na **mesma ordem de merge**, cada um com:

### Modelo de Release (por pacote — 5 vezes)

```
Release title (no GitHub):   <nome-repo> <tag-release>
Tag:                         <tag-release> (release criada no commit mergeado master)
Target branch:               master
Prerelease:                  false
Generate release notes:      NÃO (usar o texto abaixo, escrito por você, em inglês, semântico)

## What's Changed (Heading obrigatório)

### Breaking Changes — (se NENHUM, remover seção. Não invente breaking.)

### Features (`feat:` por categoria)
-   feat(<scope>): <descrição 1 linha inglês>

### Fixes (`fix:` por categoria)
-   fix(<scope>): <descrição 1 linha inglês>

### Refactors (`refactor:`)
-   refactor(<scope>): <descrição 1 linha inglês>

### Documentation / Tests / Build / CI
-   docs(...): ...
-   test(...): ...
-   chore(ci): ...

**Full Changelog:** `https://github.com/<ORG>/<REPO>/compare/<tag_anterior>...<tag_release>`
```

**Regras de release notes:**
-   Todas as linhas em INGLÊS. Nenhum português.
-   Escopo (`<scope>`) = `capability`, `cli`, `logger`, `terminal-color`, `view`, `project`, `element`,
    `storage`, `context`, `i18n`, `surface`, `ontology` etc.
-   Primeiro listar 2-4 destaques em **Highlights bullet points** (curto, human-friendly) ANTES do heading
    `What's Changed`.
-   NÃO mencionar trabalho futuro, só o que de fato foi entregue no diff da tag anterior até hoje.
-   No infobim v0.6.0: COLOCAR em primeiro nos Highlights a correção de causa raiz do `onto-logo-tile-terminal`
    e o desbloqueio do `--log-level DEBUG`.
-   No ontobdc v0.17.0: COLOCAR em primeiro nos Highlights o contrato `log_message` em `CapabilityMetadata`
    + `CapabilityExecutor.execute` single-point log + `[STARTED]` cinza humanizado + centralização de cores ANSI.
-   Se develop v0.2.0 for no-op, escrever `No code changes in this release: tag-alignment cut only.`
    em vez de inventar.

---

## Apêndice A: Diff stats referenciais copiados do git

### OntoBDC v0.16.4 → v0.17 (stat resumido)
```
.github/pypi-publish.yml                           |   30 -
.github/workflows/deploy-production.yml            |    3 +
AGENTS.md                                          |  170 +++
CHANGELOG.md                                       |   10 +
docs/2026-08-14-cli-command-reference.md           |   10 +-
docs/manual/parameter_strategies.md                |  228 ++++
docs/test_foundation.md                            |    4 +-
pyproject.toml                                     |   10 +-
src/ontobdc/cli/__init__.py                        |  696 +++++++---
src/ontobdc/cli/adapter/logger.py                  |  191 ++-
src/ontobdc/cli/adapter/machine.py                 |   10 +-
src/ontobdc/cli/adapter/response.py                |  149 ++-
src/ontobdc/cli/domain/model/logger.py             |   51 +-
src/ontobdc/cli/plugin/parameter/log_level.py      |  121 ++
src/ontobdc/shared/adapter/capability.py           |  785 ++++++++++-
src/ontobdc/shared/adapter/terminal_color.py       |  138 ++
src/ontobdc/shared/adapter/ontology.py             |  414 +++++-
src/ontobdc/storage/adapter/bootstrap.py           |  363 +++--
src/ontobdc/storage/adapter/identifier.py          |   36 +
src/ontobdc/storage/adapter/manifest.py            |  204 ++-
src/ontobdc/storage/adapter/attachment/* (9 arqs)  | ~1.800 linhas novas
(...)
94 arquivos modificados / criados / removidos no total.
```

### InfoBIM v0.5.3 → v0.6 (stat resumido)
```
41 files changed, 1781 insertions(+), 87 deletions(-)
src/infobim/cli/__init__.py                        | 254 +++++++++++--
src/infobim/element/adapter/parameter.py           | 414 +++++++++++++++++++++
src/infobim/element/plugin/command/* (4 commands)  | 334 ++++++++++++++
tests/element/ (2 test files novos)                | 259 ++++++++++
src/infobim/view/adapter/component.py              |  31 +-
src/infobim/view/adapter/i18n/* (novos locale)     | ~120 +
src/infobim/project/plugin/capability/transformation/* (5 capabilities) = cada um com log_message{ info, debug_entry }["en"] novo
```
