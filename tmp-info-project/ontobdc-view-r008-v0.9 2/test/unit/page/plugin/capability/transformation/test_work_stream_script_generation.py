from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ontobdc_view.page.plugin.builder.work_stream.work_stream_script_generation import (
    generate_work_stream_scripts,
)


class FakeCliContext:
    raw_args: List[str] = []
    unprocessed_args: List[str] = []
    is_capability_targeted = False
    target_capability_id = None
    root_path = ""
    language = "en"

    def __init__(self, values: Dict[str, Any]) -> None:
        self.values = values

    def has_parameter(self, key: str) -> bool:
        return key in self.values

    def get_parameter_value(self, key: str) -> Any:
        return self.values.get(key)

    def set_parameter_value(self, key: str, value: Any) -> None:
        self.values[key] = value

    def delete_parameter(self, key: str) -> None:
        self.values.pop(key, None)

    def clear_parameters(self, keys: List[str]) -> None:
        for key in keys:
            self.delete_parameter(key)

    def reload(self) -> None:
        pass


def test_statechart_generates_sheetjs_then_entity_i18n(tmp_path: Path) -> None:
    context = FakeCliContext({"container_path": str(tmp_path)})

    written_paths = generate_work_stream_scripts(context)

    view_directory = (
        tmp_path / ".__ontobdc__" / "view" / "work_stream"
    )
    sheetjs_path = view_directory / "xlsx-0.18.5.full.min.js"
    i18n_path = view_directory / "i18n_apply.js"
    assert written_paths == [str(sheetjs_path), str(i18n_path)]
    assert "xlsx.js" in sheetjs_path.read_text(encoding="utf-8")
    i18n_source = i18n_path.read_text(encoding="utf-8")
    assert "OntoBDCWorkStreamViewRuntime" in i18n_source
    assert "OntoBDCGanttViewRuntime" not in i18n_source
    # The machine supplies its builder/view dynamically to the generic
    # capabilities, so their postconditions are evaluated inside the machine's
    # isolated context rather than against this parent context.
    assert sheetjs_path.is_file()
    assert i18n_path.is_file()
