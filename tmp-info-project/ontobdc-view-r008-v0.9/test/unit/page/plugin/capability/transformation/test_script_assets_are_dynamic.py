from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ontobdc_view.page.adapter.context import (
    PageScriptGenerationContextAdapter,
)
from ontobdc_view.page.plugin.capability.transformation.i18n_script_generated import (
    I18nScriptGeneratedCapability,
)
from ontobdc_view.page.plugin.capability.transformation.graph_reader_script_generated import (
    GraphReaderScriptGeneratedCapability,
)
from ontobdc_view.page.plugin.capability.transformation.vendor_sheet_js_asset_generated import (
    VendorSheetJsAssetGeneratedCapability,
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


def test_generic_capabilities_use_the_builder_and_view_from_context(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    package = tmp_path / "custom_entity_builder"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "xlsx-0.18.5.full.min.js").write_text(
        "// custom SheetJS",
        encoding="utf-8",
    )
    (package / "i18n_apply.js").write_text(
        "// custom i18n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    parent = FakeCliContext({"container_path": str(tmp_path / "container")})
    context = PageScriptGenerationContextAdapter(
        parent,
        builder_package="custom_entity_builder",
        view_directory="custom_entity",
    )

    sheet_result = VendorSheetJsAssetGeneratedCapability().execute(context)
    i18n_result = I18nScriptGeneratedCapability().execute(context)

    target = (
        tmp_path / "container" / ".__ontobdc__" / "view" / "custom_entity"
    )
    assert Path(sheet_result["generated_script_path"]) == (
        target / "xlsx-0.18.5.full.min.js"
    )
    assert Path(i18n_result["generated_script_path"]) == (
        target / "i18n_apply.js"
    )
    assert (target / "xlsx-0.18.5.full.min.js").read_text(
        encoding="utf-8"
    ) == "// custom SheetJS"
    assert (target / "i18n_apply.js").read_text(
        encoding="utf-8"
    ) == "// custom i18n"


def test_graph_reader_capability_is_a_stub(tmp_path: Path) -> None:
    context = FakeCliContext({"container_path": str(tmp_path)})

    capability = GraphReaderScriptGeneratedCapability()

    assert capability.check(context) is False
    assert capability.execute(context) == {
        "resulting_state": "__graph_reader_script_generated__"
    }
    assert not list(tmp_path.rglob("graph_reader.js"))
