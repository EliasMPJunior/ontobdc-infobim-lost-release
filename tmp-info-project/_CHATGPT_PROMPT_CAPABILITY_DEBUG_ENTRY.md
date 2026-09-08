# Prompt ChatGPT — Cadastrar `debug_entry` (e famílias `debug_exception` / `debug_*`) em TODAS as Capabilities Restantes

> Use este prompt **exatamente como está** sempre que precisar cadastrar frases humanizadas de `debug_entry["en"]` (e opcionalmente `debug_exception`, `debug_<tipo_exception_snake_case>`) em capabilities do OntoBDC / InfoBIM que **ainda não** tenham. Baseado no padrão das 11 capabilities `view/plugin/capability/transformation/*.py` do OntoBDC (já prontas).

---

## 1. Contexto / O que é o `log_message`

O contrato `CapabilityMetadata.log_message` é um dicionário **aninhado** do tipo:
```python
log_message: Dict[str, Dict[str, str]]
```

*   **Nível 1 = evento:** o nome do evento de log.
    *   Obrigatório já existe quase sempre = `"info"` → (disparado depois do sucesso happy-path, nível INFO).
    *   **Evento que você VAI CADASTRAR HOJE = `"debug_entry"`** → (disparado ANTES do `capability.execute(context)`, nível DEBUG, prefixado automaticamente com `[STARTED]` cinza).
    *   Opcionais (se a capability tiver exceções específicas conhecidas): `"debug_exception"`, `"debug_value_error"`, `"debug_type_error"`, `"debug_<qualquer_classe_exception_em_snake_case>"`.
*   **Nível 2 = idioma:** por enquanto **só cadastrar `"en"`**. (pt-BR fica para depois).

---

## 2. Regras OBRIGATÓRIAS (não quebre)

1.  **NÃO TOCAR NO MÉTODO `execute()` NEM EM QUALQUER OUTRO LUGAR DA CAPABILITY.** O log é disparado **100% automaticamente** pelo `CapabilityExecutor.execute()` — a capability é só um dado declarativo no metadata. NENHUMA linha nova fora do dicionário `log_message` no `CapabilityMetadata`.
2.  **Use o `info["en"]` que JÁ EXISTE como BASE.** A frase do `debug_entry["en"]` é **o VERBO da mesma etapa**, só que **no PRESENTE CONTÍNUO / GERÚNDIO** (ação em andamento) enquanto o `info["en"]` é **no PASSADO** (ação concluída). Exemplo de regra de transformação de frase:
    *   info.en = **"Minimal offline HTML Presentation Surface document was created."** (passado, concluído)
    *   debug_entry.en → **"Creating the minimal offline HTML Presentation Surface document."** (mesmos objetos, mesmo tom, só troca verbo para gerúndio em início)
    *   info.en = **"Presentation data was matched to compatible Component definitions and support envelopes."**
    *   debug_entry.en → **"Matching presentation data against compatible Component definitions and support envelopes."**
3.  **Tom da frase:** igual a `info["en"]` existente. **NÃO invente substantivos novos, não adicione informação nova, não invente contexto técnico extra (a menos que não exista info.en, aí use o `.description` ou o `.label()` da capability como base).** Apenas converta TEMPO VERBAL do passado para o gerúndio de ação começando.
4.  **Não use prefixos como "[DEBUG...]" ou "[CAPABILITY...]"** na frase. O prefixo (se houver, como `[STARTED]`) é inserido **pelo logger**, não no metadata. No metadata fica apenas a mensagem natural humana.
5.  **Ordem do `log_message`:** mantenha `"info"` PRIMEIRO e `"debug_entry"` LOGO DEPOIS (logo abaixo do info, no mesmo dict). Se já houver outras chaves, append no final.
6.  **Sempre inglês (`"en"`) por enquanto**, mesmo que a capability declare `supported_languages=["pt-br", "en"]`. Não cadastre pt-BR agora.
7.  **Se já tiver `debug_entry["en"]` existente** NÃO MEXA.
8.  **Se a capability NÃO for família side-effecting:** Ou seja, se ela herdar `QueryCapability` ou for `QueryCapabilityPort` → **NÃO cadastre debug_entry nem info (info já não tem para query anyway)**. O debug só roda para TransformationCapability e TransactionCapability (herdam de `TransformationCapability` ou `TransactionCapability`). Verifique o nome da classe ou herança antes.
9.  **Capabilities que são filhas (subclass) de uma capability base OntoBDC:** Ex.: `InfoBIMSurfaceMatchedCapability(SurfaceMatchedCapability)`. Se elas **NÃO definem o próprio `METADATA` (reescrevem)** → NÃO cadastre (herdam o `log_message` do pai, que já tem). **Só cadastre se a subclasse redefinir seu próprio atributo `METADATA = CapabilityMetadata(...)`.**

---

## 3. Exemplos Padrão (usar de referência)

### Exemplo A: `SurfaceInitializedCapability` (TransformationCapability)

**ANTES (se não tivesse `debug_entry` ainda):**
```python
METADATA = CapabilityMetadata(
    id="org.ontobdc.view.plugin.capability.transformation.target.surface_initialized",
    version="1.0.0",
    name="Surface Initialized",
    description="Create the minimal offline HTML Presentation Surface document.",
    tags=["view", "surface", "html", "transformation"],
    log_message={
        "info": {
            "en": "Minimal offline HTML Presentation Surface document was created.",
        },
    },
)
```

**DEPOIS (você cadastrou `debug_entry`):**
```python
METADATA = CapabilityMetadata(
    id="org.ontobdc.view.plugin.capability.transformation.target.surface_initialized",
    version="1.0.0",
    name="Surface Initialized",
    description="Create the minimal offline HTML Presentation Surface document.",
    tags=["view", "surface", "html", "transformation"],
    log_message={
        "info": {
            "en": "Minimal offline HTML Presentation Surface document was created.",
        },
        "debug_entry": {
            "en": "Creating the minimal offline HTML Presentation Surface document.",
        },
    },
)
```

### Exemplo B: `DataGatheredCapability` (TransformationCapability)

**DEPOIS (você cadastrou):**
```python
log_message = {
    "info": {
        "en": "Presentation source data was materialized as the DATA_GATHERED JSON-LD ETL state artifact.",
    },
    "debug_entry": {
        "en": "Materializing presentation source data into the DATA_GATHERED JSON-LD ETL state artifact.",
    },
}
```

---

## 4. Chaves opcionais de DEBUG (cadastrar SOMENTE se fizer sentido para a capability)

Use essas chaves **apenas quando a capability tiver exceções específicas muito frequentes / conhecidas** (não precisa cadastrar para todas — o default fallback é `str(exc)` automaticamente, nunca fica vazio):

| Chave (nível 1)              | O que dispara                         |
|-------------------------------|---------------------------------------|
| `"debug_exception"`           | Fallback genérico — qualquer exception, nível DEBUG. **Não precisa cadastrar quase nunca** (fallback default `str(exc)` já funciona). |
| `"debug_value_error"`         | Exception do tipo `ValueError` (ex: formato inválido de container_id). Tipo de exception → snake_case: `ValueError → debug_value_error`, `TypeError → debug_type_error`, `CapabilityExecutionError → debug_capability_execution_error`, `HTTPError → debug_http_error`. Exemplo de uso: `"debug_value_error": {"en": "Matcher refused: surface data missing required fields."}` |

---

## 5. Como executar: varredura

Varra TODOS os arquivos de capability que ainda não tiver `debug_entry["en"]` dentro de:
1.  Primeiro `ontobdc/src/ontobdc/**/plugin/capability/**/*.py` (todos os pacotes OntoBDC: storage, facade, context, registry, view etc. — menos as 11 de `view/plugin/capability/transformation/` que já estão prontas)
2.  Depois `infobim/src/infobim/**/plugin/capability/**/*.py` (todas as capabilities InfoBIM: view, project, ifc, element, context etc.) — exceto `base.py` se for só classe base.
3.  **Apenas capabilities que herdam explicitamente de `TransformationCapability` ou `TransactionCapability`**. (Se herdar de `QueryCapability` → pular.)
4.  Execute de forma determinística: ordem alfabética de paths. 1 capability = 1 edição mínima (só o dict metadata).
5.  **NO FINAL**, rode `python -m py_compile <arquivo>` para cada arquivo editado (garantir que não estragou sintaxe de Python).
