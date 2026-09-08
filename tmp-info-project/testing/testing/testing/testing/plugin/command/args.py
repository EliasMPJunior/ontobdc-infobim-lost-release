from typing import Dict, List, Optional


def flag_value(tokens: List[str], flag: str) -> Optional[str]:
    """Return the value following `flag` in `tokens`, or `None` if absent."""

    if flag not in tokens:
        return None

    value_index: int = tokens.index(flag) + 1
    if value_index >= len(tokens):
        return None

    return tokens[value_index]


def collect_params(tokens: List[str]) -> Dict[str, str]:
    """Collect every repeated `--param key=value` occurrence in `tokens`."""

    values: Dict[str, str] = {}
    for index, token in enumerate(tokens):
        if token != "--param":
            continue

        if index + 1 >= len(tokens):
            raise ValueError("--param requires a 'key=value' value.")

        raw_value: str = tokens[index + 1]
        key, separator, value = raw_value.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"Invalid --param value: {raw_value!r}. Expected 'key=value'.")

        values[key.strip()] = value

    return values
