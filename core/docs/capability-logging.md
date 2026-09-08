# Capability success logging (`CapabilityMetadata.log_message`)

Every side-effecting capability can announce its own success with a single
INFO log line — no logging code required in `execute()`. Declare the
message once, per language, on the capability's own `METADATA`, and the
shared executor emits it automatically after a successful run.

## Where it lives

- **Declaration**: `CapabilityMetadata.log_message` (`ontobdc.shared.domain.model.capability`) — `Dict[str, Dict[str, str]]`, outer key is the log level (currently only `"info"` is wired), inner key is a language tag (`"en"`, `"pt-br"`, ...).
- **Trigger**: `CapabilityExecutor.execute()` (`ontobdc.shared.adapter.capability`) — calls `CapabilityLoggingSupport._log_capability_success(...)` right after `capability.execute(context)` returns *without raising*.

## Who gets it

Only side-effecting capabilities are eligible:

- `TransformationCapabilityPort` and `TransactionCapabilityPort` → logged.
- `QueryCapabilityPort` → **silent on purpose**. Reads are deterministic and often run in bulk (multi-lookup pipelines); logging every one would drown real signal in noise.

If the capability raises, this mechanism never fires — failure reporting stays the job of the existing exception channels (the CLI's error box, state-machine retries, hotfix logs).

## Message resolution order

For each successful run, the executor picks the message in this order:

1. `log_message["info"][context.language]` — capability-specific, language-specific text you declared.
2. `log_message["info"]["en"]` — same dict, English fallback, when the active language has no entry.
3. A generic built-in template — guaranteed fallback so the line is never empty: `"<Transaction|Transformation> capability completed successfully. Capability: <ClassName>. Id: <capability id>. Output keys: [...]."`.

So declaring `log_message` is optional — every side-effecting capability already logs *something* on success. Declaring it just replaces the generic sentence with a message that actually makes sense to a human reading the terminal.

## Where the logger comes from

You never pass a logger in — `CapabilityLoggingSupport._lazy_get_logger()` resolves one by walking five channels, in order, and using the first one it finds:

1. **CLI broker** — the exact logger `ontobdc.cli.__init__.main()` registered via `set_active_log_repository(logger)`, already configured with the user's `--log-level`. This is the fast path every real CLI invocation hits.
2. `capability._log_strategy.log_repository` — set on capabilities that implement `LoggerAwarePort` directly.
3. **State-machine owner chain** — walks `_owner` / `_handler` / `_parent` / `_machine` starting from `context`, looking for something carrying a `_logger`. This is how a capability invoked from inside a `*StateTransitionHandler.perform_state_transition()` picks up that handler's logger without either side wiring anything explicitly.
4. `context`/capability "bag" attributes (`_logger`, `log_repository`, `logger`) set by programmatic callers.
5. A fresh `StandardConsoleLogger()` as the last resort, so a bare programmatic `CapabilityExecutor.execute(...)` call (no CLI, no handler) still gets a working logger.

Every channel is guarded — if logging infrastructure is missing entirely, the resolver just returns `None` and the executor skips logging silently. A capability can never fail *because* logging failed.

## It obeys `--log-level` like everything else

The resolved logger's `log_info(message)` still goes through the normal `LogLevelPolicy` threshold check. The default threshold is `NOTICE`, which is *stricter* than `INFO` — so **these messages are silent by default** and only show up when the user runs with `--log-level info` (or a more verbose level). This is not a bug or an oversight: it is the same rule every other log line in the CLI follows, INFO messages included.

## Constraint: the message is static text, not a template

`log_message["info"][lang]` is looked up and used **verbatim** — there is no `.format()`/interpolation step. This is fine (and clean) when the message doesn't need to embed per-run data:

```python
# ontobdc/run/plugin/capability/transformation/language_defined.py
METADATA = CapabilityMetadata(
    ...
    log_message={
        "info": {
            "en": "The run's language was set.",
            "pt-br": "O idioma da execucao foi definido.",
        },
    },
)
```

`LanguageDefinedCapability` never writes a logging call — `CapabilityExecutor` emits "The run's language was set." on its own after `execute()` returns successfully.

### Embedding per-run data without writing a logging call

`log_message["info"][lang]` is looked up and used **verbatim** — there is no `.format()`/interpolation step, so the dict above can't say *which* value was set. But `capability.metadata` (the thing `CapabilityLoggingSupport` actually reads `log_message` from) is just a Python `@property` — `Capability.metadata` returns `self.METADATA` by default, and nothing stops a subclass from overriding it to build a fresh `CapabilityMetadata` on the fly. Since the executor always reads `capability.metadata` *after* `execute()` has already run, `execute()` can stash whatever it captured on `self`, and the overridden `metadata` property can splice that value into a copy of `log_message`:

```python
# ontobdc/run/plugin/capability/transformation/language_defined.py
class LanguageDefinedCapability(TransformationCapability):
    METADATA = CapabilityMetadata(...)  # no log_message declared here

    def __init__(self) -> None:
        self._resolved_language: Optional[str] = None

    @property
    def metadata(self) -> CapabilityMetadata:
        if self._resolved_language is None:
            return self.METADATA  # execute() hasn't run yet
        return self.METADATA.model_copy(
            update={
                "log_message": {
                    "info": {
                        "en": f"The run's language was set to '{self._resolved_language}'.",
                        "pt-br": f"O idioma da execucao foi definido como '{self._resolved_language}'.",
                    },
                },
            },
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        language = ...  # resolve it
        self._resolved_language = language
        return {"language": language, ...}
```

Still zero calls to a logger anywhere in this file — `CapabilityExecutor` is the only thing that ever calls `log_info(...)`. This is the pattern to reach for whenever the message needs a captured value, not a manual `logger.log_info(...)` call inside `execute()`: it keeps the *timing* declarative (still happens exactly once, after a successful run, through the same 5-channel resolution and `--log-level` threshold) while letting the *content* be dynamic. `ontobdc/run/plugin/capability/transformation/received.py` follows the identical shape to embed the captured prompt text.

This only works because `execute()` runs strictly before the executor reads `metadata` — a capability that needs to log something *before* or *during* its own `execute()` (rather than describing what it just finished) is the one real case left for calling the logger directly, via `ontobdc.shared.facade.adapter.logger.get_active_log_repository()`.

## Debug-level counterpart

The same class also emits a **DEBUG** line right before `execute()` runs (`_log_capability_debug_entry`) and on exception (`_log_capability_debug_exception`), using the identical 5-channel logger resolution but `log_debug`/`LogLevel.DEBUG` instead of `log_info`/`LogLevel.INFORMATIONAL`. Nothing to declare for that — it always fires (subject to `--log-level debug`), independent of `log_message`.

## Worked example

```python
# ontobdc/storage/plugin/capability/transformation/container_cleaned.py
class ContainerCleanedCapability(TransactionCapability):
    METADATA = CapabilityMetadata(
        ...
        log_message={
            "info": {
                "en": (
                    "Configured temporary files were removed from the "
                    "container workspace before metadata synchronization."
                ),
            },
        },
    )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        ...  # no logging code anywhere in here
        return {"resulting_state": ..., "removed_files": ...}
```

Run any command that reaches this capability with `--log-level info` and the line appears on its own, with zero logging code inside `execute()`.
