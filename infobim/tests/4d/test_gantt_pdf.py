"""The 4D domain exports the container's mapped schedule as a real PDF."""

from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from openpyxl import Workbook

from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.shared.adapter.capability import CapabilityExecutor

pdf_adapter = importlib.import_module("infobim.4d.adapter.gantt_pdf")
pdf_capability = importlib.import_module(
    "infobim.4d.plugin.capability.transformation.gantt_pdf"
)
pdf_command = importlib.import_module("infobim.4d.plugin.command.pdf")

ScheduleGanttPdfExporter = pdf_adapter.ScheduleGanttPdfExporter
FourDGanttPdfCapability = pdf_capability.FourDGanttPdfCapability
FourDGanttPdfCommand = pdf_command.FourDGanttPdfCommand


def build_container(root: Path, *, one_workbook_resource: bool = False) -> Path:
    marker: Path = root / ".__ontobdc__"
    document: Path = root / "payload" / "document"
    marker.mkdir(parents=True)
    document.mkdir(parents=True)
    workbook_path: Path = document / "ifc_work_schedule.xlsx"

    sheets: Dict[str, Any] = {
        "IfcWorkSchedule": (["GlobalId", "Name"], [["WS-1", "Obra"]]),
        "IfcTask": (
            ["GlobalId", "Identification", "Name", "TaskTime", "IsMilestone"],
            [
                ["T-2", "1.10", "Concretagem", "TT-2", False],
                ["T-1", "1.2", "Escavacao", "TT-1", False],
            ],
        ),
        "IfcTaskTime": (
            [
                "GlobalId",
                "ScheduleStart",
                "ScheduleFinish",
                "PercentComplete",
            ],
            [
                ["TT-2", datetime(2026, 9, 5), datetime(2026, 9, 9), 25],
                ["TT-1", datetime(2026, 9, 1), datetime(2026, 9, 4), 100],
            ],
        ),
        "IfcRelSequence": (["GlobalId"], []),
    }

    workbook = Workbook()
    workbook.remove(workbook.active)
    resources: List[Dict[str, Any]] = []
    for entity, (header, rows) in sheets.items():
        worksheet = workbook.create_sheet(entity)
        worksheet.append(header)
        for row in rows:
            worksheet.append(row)
        resources.append(
            {
                "name": entity.lower(),
                "entityIdentifier": entity,
                "path": "../payload/document/ifc_work_schedule.xlsx",
                "dialect": {"excel": {"sheet": entity}},
            }
        )
    workbook.save(workbook_path)
    workbook.close()
    declared_resources = resources[:1] if one_workbook_resource else resources
    (marker / "datapackage.json").write_text(
        json.dumps({"resources": declared_resources}), encoding="utf-8"
    )
    return root


def test_exporter_joins_task_time_and_orders_wbs(tmp_path: Path) -> None:
    container = build_container(tmp_path / "container")
    workbook_path = container / "payload/document/ifc_work_schedule.xlsx"

    tasks = ScheduleGanttPdfExporter(workbook_path).tasks()

    assert [task.identification for task in tasks] == ["1.2", "1.10"]
    assert tasks[0].completion == 100
    assert tasks[0].start == datetime(2026, 9, 1)


def test_capability_resolves_datapackage_and_writes_pdf(tmp_path: Path) -> None:
    container = build_container(
        tmp_path / "container", one_workbook_resource=True
    )
    output = tmp_path / "exports" / "gantt.pdf"
    context = CliContextAdapter([])
    context.set_parameter_value("container_path", str(container))
    context.set_parameter_value("pdf_path", str(output))

    result = CapabilityExecutor.execute(FourDGanttPdfCapability(), context)

    assert result["task_count"] == 2
    assert Path(result["pdf_path"]) == output
    assert output.read_bytes().startswith(b"%PDF")


def test_pdf_command_uses_the_4d_public_domain(tmp_path: Path) -> None:
    container = build_container(tmp_path / "container")
    output = tmp_path / "gantt.pdf"
    raw_args = ["4d", "--pdf", "--container", str(container), "-o", str(output)]
    assert FourDGanttPdfCommand.accepts(raw_args)

    request_args = raw_args[1:]
    context = CliContextAdapter(request_args)
    command = FourDGanttPdfCommand(
        CliCommandRequest(
            logical_component="4d",
            component_action="4d_gantt_pdf",
            command_args=request_args,
            context=context,
        )
    )
    assert command.check()
    response = command.run()

    assert response.content["pdf_path"] == str(output)
    assert output.is_file()


def test_schedule_is_not_the_public_domain_anymore() -> None:
    assert FourDGanttPdfCommand.accepts(["4d", "--pdf"])
    assert not FourDGanttPdfCommand.accepts(["schedule", "--pdf"])
