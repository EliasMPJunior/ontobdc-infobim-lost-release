from __future__ import annotations

import importlib
import re
from importlib.resources import files
from pathlib import Path
from types import ModuleType
from typing import Callable, List, Optional, Tuple

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc_view.page.adapter.context import PageScriptGenerationContextAdapter


ScriptGenerator = Callable[[CliContextPort], List[str]]
_VIEW_DIRECTORY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class PageScriptAssetAdapter:
    """Copy a script from the active entity builder to its container view."""

    @classmethod
    def source(cls, context: CliContextPort, script_name: str) -> str:
        builder_package = PageScriptGenerationContextAdapter.builder_package(
            context
        )
        asset = files(builder_package).joinpath(f"{script_name}.js")
        try:
            return asset.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError) as error:
            raise ValueError(
                f"Script {script_name!r} was not found in Page builder "
                f"{builder_package!r}."
            ) from error

    @classmethod
    def target_path(
        cls,
        context: CliContextPort,
        script_name: str,
    ) -> Path:
        container_path = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_path:
            raise ValueError("The container path was not resolved.")
        view_directory = PageScriptGenerationContextAdapter.view_directory(
            context
        )
        if not _VIEW_DIRECTORY_PATTERN.fullmatch(view_directory):
            raise ValueError(
                f"Invalid Page view directory: {view_directory!r}."
            )
        return (
            Path(container_path).expanduser().resolve()
            / ".__ontobdc__"
            / "view"
            / view_directory
            / f"{script_name}.js"
        )

    @classmethod
    def write(cls, context: CliContextPort, script_name: str) -> Path:
        target_path = cls.target_path(context, script_name)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            cls.source(context, script_name),
            encoding="utf-8",
        )
        return target_path

    @classmethod
    def check(cls, context: CliContextPort, script_name: str) -> bool:
        target_path = cls.target_path(context, script_name)
        if not target_path.is_file():
            return False
        try:
            return target_path.read_text(
                encoding="utf-8"
            ) == cls.source(context, script_name)
        except OSError:
            return False


class EntityPageScriptGeneratorLoader:
    """Resolve a Page script generator from an entity view directory."""

    def __init__(
        self,
        root_packages: Tuple[str, ...] = ("ontobdc_view",),
    ) -> None:
        self._root_packages = root_packages

    def get(self, view_directory: str) -> Optional[ScriptGenerator]:
        if not _VIEW_DIRECTORY_PATTERN.fullmatch(view_directory):
            raise ValueError(
                f"Invalid Page view directory: {view_directory!r}."
            )
        function_name = f"generate_{view_directory}_scripts"
        matches: List[ScriptGenerator] = []
        for root_package in self._root_packages:
            module_name = (
                f"{root_package}.page.plugin.builder.{view_directory}."
                f"{view_directory}_script_generation"
            )
            module = self._import_optional(module_name)
            if module is None:
                continue
            generator = getattr(module, function_name, None)
            if callable(generator):
                matches.append(generator)

        if not matches:
            return None
        if len(matches) > 1:
            raise ValueError(
                f"More than one Page script generator was found for "
                f"{view_directory!r}."
            )
        return matches[0]

    @staticmethod
    def _import_optional(module_name: str) -> Optional[ModuleType]:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            missing_name = str(error.name or "")
            if missing_name and (
                module_name == missing_name
                or module_name.startswith(f"{missing_name}.")
            ):
                return None
            raise
