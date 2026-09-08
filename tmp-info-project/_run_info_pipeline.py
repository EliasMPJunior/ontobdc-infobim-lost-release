"""Script manual: roda as 5 InfoBIM Project transformation capabilities na ordem,
usando InLineLogger com threshold DEBUG, exatamente como o CLI faria com
--log-level DEBUG.

Output esperado:
  5x [STARTED] cinza (debug_entry humanizado cada capability)
  5x ▶ INFO (info.en humanizado cada capability)
  0x EXCEPTION (caminho feliz)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

# Garantir path do ontobdc + infobim src
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ontobdc" / "src"))
sys.path.insert(0, str(ROOT / "infobim" / "src"))

from ontobdc.cli.adapter.context import CliContextAdapter  # type: ignore
from ontobdc.cli.adapter.logger import InLineLogger  # type: ignore
from ontobdc.cli.domain.model.command import CliCommandMetadata  # type: ignore
from ontobdc.cli.domain.model.logger import LogLevel, LogStrategyConfig  # type: ignore
from ontobdc.cli.domain.request.command import CliCommandRequest  # type: ignore
from ontobdc.shared.adapter.capability import CapabilityExecutor  # type: ignore
from ontobdc.shared.facade.adapter.logger import (  # type: ignore
    clear_active_log_repository,
    set_active_log_repository,
)
from infobim.project.plugin.capability.transformation.ifc_project_facade_ready import (  # type: ignore
    IfcProjectFacadeReadyCapability,
)
from infobim.project.plugin.capability.transformation.ifc_project_ready import (  # type: ignore
    IfcProjectReadyCapability,
)
from infobim.project.plugin.capability.transformation.ontobdc_container_ready import (  # type: ignore
    OntoBDCContainerReadyCapability,
)
from infobim.project.plugin.capability.transformation.project_dataset_ready import (  # type: ignore
    ProjectDatasetReadyCapability,
)
from infobim.project.plugin.capability.transformation.project_ready import (  # type: ignore
    ProjectReadyCapability,
)

CONTAINER_PATH: Path = Path(__file__).resolve().parent


def build_logger_debug() -> InLineLogger:
    """InLineLogger com threshold DEBUG + registrado no broker global (ordem correta)."""
    logger = InLineLogger()
    _ = LogStrategyConfig(log_level=LogLevel.DEBUG, log_repository=logger)
    set_active_log_repository(logger)
    return logger


def build_context(container_path: Path) -> CliContextAdapter:
    request = CliCommandRequest(
        logical_component="project",
        component_action="project_ready_pipeline_test",
        command_args=[],
        context=CliContextAdapter(root_path=container_path),
        metadata=CliCommandMetadata(id="info_project_ready_pipeline_test"),
    )
    ctx = request.context
    ctx.set_parameter_value("container_path", str(container_path))
    ctx.set_parameter_value("language", "en")
    ctx.root_path = container_path  # type: ignore[attr-defined]
    return ctx


def main() -> int:
    logger = build_logger_debug()
    try:
        ctx = build_context(CONTAINER_PATH)

        pipeline: List[object] = [
            OntoBDCContainerReadyCapability(),
            ProjectDatasetReadyCapability(),
            IfcProjectReadyCapability(),
            IfcProjectFacadeReadyCapability(),
            ProjectReadyCapability(),
        ]

        print(
            "\n========= InfoBIM Project Ready Pipeline — DEBUG threshold =========",
            file=sys.stderr,
        )
        for i, capability in enumerate(pipeline, start=1):
            cls_name = capability.__class__.__name__
            try:
                result = CapabilityExecutor.execute(capability, ctx)  # type: ignore[arg-type]
                ok_keys = list(result.keys()) if isinstance(result, dict) else []
                print(
                    f"#{i} OK   {cls_name:40s}  result_keys={ok_keys}",
                    file=sys.stderr,
                )
            except Exception as exc:
                print(
                    f"#{i} FAIL {cls_name:40s}  {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                import traceback

                traceback.print_exc()
                return 1

        print(
            "========= Pipeline completed successfully =========",
            file=sys.stderr,
        )
        return 0
    finally:
        clear_active_log_repository()


if __name__ == "__main__":
    raise SystemExit(main())
