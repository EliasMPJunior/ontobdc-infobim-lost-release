import re
from typing import Any

from ontobdc_dev.testing.domain.exception import TestExecutionError
from ontobdc_dev.testing.domain.model.context import ExecutionContext

_PLACEHOLDER_PATTERN = re.compile(r"\$\{context\.([a-zA-Z0-9_]+)\}")


def substitute(value: Any, context: ExecutionContext) -> Any:
    """Resolve `${context.<name>}` placeholders in strings, dicts, and lists.

    Raises `TestExecutionError` for a placeholder with no matching context
    value instead of silently substituting an empty string, so a missing
    `--param` surfaces as an observation/action error rather than a
    misleading pass or fail (semantic-test-orchestrator.md, 8.4).
    """

    if isinstance(value, str):
        return _substitute_string(value, context)

    if isinstance(value, dict):
        return {key: substitute(item, context) for key, item in value.items()}

    if isinstance(value, list):
        return [substitute(item, context) for item in value]

    return value


def _substitute_string(value: str, context: ExecutionContext) -> str:
    def _replace(match: "re.Match[str]") -> str:
        key: str = match.group(1)
        resolved: str = context.get(key)
        if resolved is None:
            raise TestExecutionError(
                f"Missing context value for '${{context.{key}}}'. "
                "Provide it with --param "
                f"{key}=<value>."
            )
        return resolved

    return _PLACEHOLDER_PATTERN.sub(_replace, value)
