from ontobdc_view.page.adapter.container import (
    IFC_WORK_SCHEDULE_RUNTIME,
    WORK_STREAM_RUNTIME,
    connection_state_source,
)
from ontobdc_view.page.adapter.gantt_script import GanttScriptAdapter
from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter


def test_both_pages_can_request_background_surface_regeneration() -> None:
    for runtime in (WORK_STREAM_RUNTIME, IFC_WORK_SCHEDULE_RUNTIME):
        source = connection_state_source(runtime)
        assert '"surface-regeneration.request.json"' in source
        assert 'getDirectoryHandle(".__ontobdc__", {' in source
        assert "requestSurfaceRegeneration" in source
        assert "scheduleSurfaceRegeneration" in source


def test_workstream_requests_regeneration_after_a_successful_field_write() -> None:
    source = WorkStreamScriptAdapter().script_source("pyodide_runtime")
    assert source.count('scheduleSurfaceRegeneration("workstream_field:" + column)') == 2
    assert "await _sheetJsWriteWorkStreamCell" in source
    assert "await syncMountedFilesystem" in source


def test_schedule_requests_regeneration_after_every_workbook_mutation() -> None:
    source = GanttScriptAdapter().script_source("pyodide_runtime")
    for reason in (
        "ifc_work_schedule_task_time",
        "ifc_work_schedule_task",
        "ifc_work_schedule_metadata",
        "ifc_work_schedule_task_created",
        "ifc_work_schedule_task_deleted",
    ):
        assert f'scheduleSurfaceRegeneration("{reason}")' in source
