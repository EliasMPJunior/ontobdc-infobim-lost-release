
import os
import sys
import subprocess
from pathlib import Path
from importlib.util import find_spec
from importlib.machinery import ModuleSpec
from typing import Dict, Iterable, List, NoReturn, Optional


class OntoBDCExtraModuleResolver:

    def __init__(self, module: str) -> None:
        self._module: str = module
        self._environment: Dict[str, str] = {}
        self._module_src_path: Optional[Path] = None
        self._load()

    @property
    def module_name(self) -> str:
        return f"ontobdc_{self._module}"

    def exec_module_cli(self, forwarded_args: List[str], platform_name: Optional[str] = None) -> NoReturn:
        execution_arguments: List[str] = [
            sys.executable,
            "-m",
            self.module_name,
            *forwarded_args,
        ]

        resolved_platform_name: str = (
            os.name if platform_name is None else platform_name
        )

        if resolved_platform_name == "nt":
            completed_process: subprocess.CompletedProcess[bytes] = (
                subprocess.run(
                    execution_arguments,
                    env=self._environment,
                    check=False,
                )
            )
            raise SystemExit(completed_process.returncode)

        os.execvpe(sys.executable, execution_arguments, self._environment)

    def _resolve_module_src_path(self) -> Optional[Path]:
        try:
            module_spec: Optional[ModuleSpec] = find_spec(self.module_name)
        except (AttributeError, ImportError, ValueError):
            return None

        if module_spec is None:
            return None

        package_location_candidates: Iterable[str] = (
            module_spec.submodule_search_locations or []
        )

        package_location: str
        for package_location in package_location_candidates:
            package_path: Path = Path(package_location).expanduser().resolve()
            if self._is_valid_module_path(package_path):
                return package_path.parent

        if module_spec.origin is None:
            return None

        origin_package_path: Path = (
            Path(module_spec.origin).expanduser().resolve().parent
        )

        if self._is_valid_module_path(origin_package_path):
            return origin_package_path.parent

        return None

    def _path_entries(self, environment: Dict[str, str]) -> List[str]:
        python_path_entries: List[str] = []
        current_python_path: str = str(
            environment.get("PYTHONPATH") or ""
        )
        python_path_entry: str
        for python_path_entry in current_python_path.split(os.pathsep):
            normalized_entry: str = python_path_entry.strip()
            if normalized_entry:
                python_path_entries.append(normalized_entry)

        return python_path_entries

    def _load(self) -> NoReturn:
        view_src_path: Optional[Path] = self._resolve_module_src_path()

        if view_src_path is None:
            current_directory: Path = Path.cwd().resolve()
            raise ModuleNotFoundError(
                "Unable to locate the ontobdc-view package. Install "
                "ontobdc-view in the active Python environment or place its "
                "checkout below a nearby workspace root. Current working "
                f"directory: {current_directory}"
            )

        environment: Dict[str, str] = dict(os.environ)

        python_path_entries: List[str] = self._path_entries(environment)
        view_src_path_text: str = str(view_src_path)
        if view_src_path_text not in python_path_entries:
            python_path_entries.insert(0, view_src_path_text)
        environment["PYTHONPATH"] = os.pathsep.join(python_path_entries)

        self._environment = environment
        self._module_src_path = view_src_path

    def _is_valid_module_path(self, package_path: Path) -> bool:
        return (
            package_path.is_dir()
            and package_path.name == self.module_name
            and (package_path / "__main__.py").is_file()
        )

    # def _exec_view_cli(
    #     self,
    #     execution_arguments: List[str],
    #     environment: Dict[str, str],
    #     ,
    # ) -> NoReturn:

    # def _resolve_checkout_view_src_path(self) -> Optional[Path]:
    #     search_roots: List[Path] = []
    #     base_path: Path
    #     for base_path in (
    #         Path.cwd().resolve(),
    #         Path(__file__).resolve().parent,
    #     ):
    #         candidate_root: Path
    #         for candidate_root in (base_path, *base_path.parents):
    #             if candidate_root in search_roots:
    #                 continue
    #             search_roots.append(candidate_root)

    #     search_root: Path
    #     for search_root in search_roots:
    #         view_root_candidates: List[Path] = [
    #             search_root,
    #             search_root / "ontobdc-view",
    #         ]
    #         view_root: Path
    #         for view_root in view_root_candidates:
    #             view_src_path: Path = view_root / "src"
    #             if self._is_valid_view_src_path(view_src_path):
    #                 return view_src_path.resolve()

    #     return None

    # def _is_valid_view_src_path(self, view_src_path: Path) -> bool:
    #     return self._is_valid_view_package_path(
    #         view_src_path / self.module_name
    #     )