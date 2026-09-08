from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ontobdc_view.page.plugin.builder.ifc_work_schedule.ifc_work_schedule_script_generation import (
    generate_ifc_work_schedule_scripts,
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


def test_statechart_generates_complete_gantt_runtime(tmp_path: Path) -> None:
    context = FakeCliContext({"container_path": str(tmp_path)})

    written_paths = generate_ifc_work_schedule_scripts(context)

    asset_directory = (
        tmp_path / ".__ontobdc__" / "asset" / "ifc_work_schedule_view"
    )
    expected_names = [
        "xlsx-0.18.5.full.min.js",
        "i18n_apply.js",
        "graph_reader.js",
        "container_connection.js",
        "connection_state.js",
        "chrome_controls.js",
        "pyodide_runtime.js",
        "task_table_timeline.js",
        "dependency_arrows.js",
        "gantt_tab_mount.js",
    ]
    expected_paths = [asset_directory / name for name in expected_names]

    assert written_paths == [str(path) for path in expected_paths]
    assert all(path.is_file() for path in expected_paths)
    assert "OntoBDCGanttViewRuntime" in (
        asset_directory / "graph_reader.js"
    ).read_text(encoding="utf-8")
    assert "gantt-tbody" in (
        asset_directory / "task_table_timeline.js"
    ).read_text(encoding="utf-8")

    mount_source = (asset_directory / "gantt_tab_mount.js").read_text(
        encoding="utf-8"
    )
    assert 'data-schedule-dimension-tab", "gantt"' in mount_source
    assert 'panel.appendChild(gantt)' in mount_source
    assert 'activate("gantt")' in mount_source
