from pathlib import Path
from typing import Any, Dict, List

import pytest

from ontobdc_dev.inspect.plugin.parameter import module
from ontobdc_dev.inspect.plugin.parameter.module import ModuleStrategy


class ContextStub:
    def __init__(self, value: Any) -> None:
        self.raw_args: List[str] = []
        self._parameters: Dict[str, Any] = {"module": value}

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters.get(name)

    def delete_parameter(self, name: str) -> None:
        self._parameters.pop(name, None)

    def set_parameter_value(self, name: str, value: Any) -> None:
        self._parameters[name] = value


class TestModuleStrategy:
    def test_resolves_an_existing_top_level_module(
        self,
        tmp_path: Path,
        monkeypatch: Any,
    ) -> None:
        script_dir: Path = tmp_path / "ontobdc"
        (script_dir / "storage").mkdir(parents=True)
        monkeypatch.setattr(
            module,
            "UnsetProjectRootConfigDataAdapter",
            lambda: type("Config", (), {"script_dir": script_dir})(),
        )
        context: ContextStub = ContextStub(" storage ")

        ModuleStrategy().execute(context)

        assert context.get_parameter_value("module") == "storage"

    def test_rejects_an_unknown_module(
        self,
        tmp_path: Path,
        monkeypatch: Any,
    ) -> None:
        script_dir: Path = tmp_path / "ontobdc"
        script_dir.mkdir()
        monkeypatch.setattr(
            module,
            "UnsetProjectRootConfigDataAdapter",
            lambda: type("Config", (), {"script_dir": script_dir})(),
        )

        with pytest.raises(ValueError, match="does not exist"):
            ModuleStrategy().execute(ContextStub("unknown"))

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(ValueError, match="top-level Python module"):
            ModuleStrategy().execute(ContextStub("../storage"))
