from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

from ontobdc_dev.inspect.adapter.python_source import PythonSourceArchitectureAdapter
from ontobdc_dev.inspect.plugin.command.free_functions import (
    DevArchitectureFreeFunctionsCommand,
)


class TestPythonSourceArchitectureAdapter:
    def test_finds_module_and_nested_free_functions(self, tmp_path: Path) -> None:
        source_path: Path = tmp_path / "sample.py"
        source_path.write_text(
            "def outer():\n"
            "    def inner():\n"
            "        return 1\n"
            "    return inner()\n",
            encoding="utf-8",
        )

        findings = PythonSourceArchitectureAdapter().free_functions(tmp_path)

        assert [finding["name"] for finding in findings] == ["outer", "inner"]

    def test_ignores_methods_and_functions_nested_below_classes(self, tmp_path: Path) -> None:
        source_path: Path = tmp_path / "sample.py"
        source_path.write_text(
            "class Example:\n"
            "    def method(self):\n"
            "        def local():\n"
            "            return 1\n"
            "        return local()\n",
            encoding="utf-8",
        )

        findings = PythonSourceArchitectureAdapter().free_functions(tmp_path)

        assert findings == []

    def test_finds_async_free_function(self, tmp_path: Path) -> None:
        source_path: Path = tmp_path / "sample.py"
        source_path.write_text(
            "async def run():\n"
            "    return None\n",
            encoding="utf-8",
        )

        findings = PythonSourceArchitectureAdapter().free_functions(tmp_path)

        assert len(findings) == 1
        assert findings[0]["name"] == "run"
        assert findings[0]["kind"] == "async-function"


class TestDevArchitectureFreeFunctionsCommand:
    def test_scans_only_the_ontobdc_script_dir(self, tmp_path: Path) -> None:
        script_dir: Path = tmp_path / "ontobdc"
        script_dir.mkdir()

        class ScannerStub:
            def __init__(self) -> None:
                self.paths: List[Path] = []

            def free_functions(self, path: Path) -> List[Any]:
                self.paths.append(path)
                return [{"name": "main"}]

        request: Any = SimpleNamespace(
            command_args=["inspect", "--free-functions"],
            context=SimpleNamespace(
                get_parameter_value=lambda name: None,
            ),
        )
        command: DevArchitectureFreeFunctionsCommand = (
            DevArchitectureFreeFunctionsCommand(request)
        )
        scanner: ScannerStub = ScannerStub()
        command._scanner = scanner
        command._config_adapter = SimpleNamespace(script_dir=script_dir)

        response = command.run()

        assert scanner.paths == [script_dir]
        assert response.content == {
            "count": 1,
            "path": str(script_dir),
            "functions": [{"name": "main"}],
        }

    def test_scans_only_the_selected_module(self, tmp_path: Path) -> None:
        script_dir: Path = tmp_path / "ontobdc"
        module_dir: Path = script_dir / "storage"
        module_dir.mkdir(parents=True)

        class ScannerStub:
            def __init__(self) -> None:
                self.paths: List[Path] = []

            def free_functions(self, path: Path) -> List[Any]:
                self.paths.append(path)
                return []

        request: Any = SimpleNamespace(
            command_args=[
                "inspect",
                "--free-functions",
                "--module",
                "storage",
            ],
            context=SimpleNamespace(
                get_parameter_value=lambda name: "storage",
            ),
        )
        command: DevArchitectureFreeFunctionsCommand = (
            DevArchitectureFreeFunctionsCommand(request)
        )
        scanner: ScannerStub = ScannerStub()
        command._scanner = scanner
        command._config_adapter = SimpleNamespace(script_dir=script_dir)

        response = command.run()

        assert scanner.paths == [module_dir]
        assert response.content["path"] == str(module_dir)
