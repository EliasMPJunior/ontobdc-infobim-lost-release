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


def test_workstream_emits_a_global_event_after_a_successful_field_write() -> None:
    """Editing one field no longer asks for a full Surface regeneration.

    It used to: every saved cell wrote the regeneration request and the whole
    Surface was rebuilt for one value. A field change is now persisted as a
    Global Event the Surface replays over its snapshot, which is why the
    regeneration request is reserved for structural change (see the test
    below, and the Gantt one after it, both unchanged).
    """
    source = WorkStreamScriptAdapter().script_source("pyodide_runtime")
    assert 'scheduleSurfaceRegeneration("workstream_field:' not in source
    # Both write paths — SheetJS and Pyodide+openpyxl — go through the one
    # producer, after the write has completed.
    # Calls, not the definition, which also mentions the name.
    assert source.count("await emitWorkStreamFieldEvent(") == 2
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
