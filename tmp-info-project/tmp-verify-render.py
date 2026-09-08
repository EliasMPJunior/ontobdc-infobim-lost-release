from __future__ import annotations

import re
from typing import List

from ontobdc_view.page.adapter.container import (
    IFC_WORK_SCHEDULE_RUNTIME,
    WORK_STREAM_RUNTIME,
    PageRuntimeOptions,
    chrome_controls_source,
    connection_state_source,
    container_connection_source,
)

SOURCES: List[object] = [
    container_connection_source,
    connection_state_source,
    chrome_controls_source,
]
RUNTIMES: List[PageRuntimeOptions] = [WORK_STREAM_RUNTIME, IFC_WORK_SCHEDULE_RUNTIME]

all_ok: bool = True
for source in SOURCES:
    source_fn = getattr(source, "__call__", source)
    source_name = getattr(source, "__name__", str(source))
    for options in RUNTIMES:
        rendered: str = source_fn(options)
        leftover: List[str] = re.findall(r"__[A-Z_]+__", rendered)
        if leftover:
            print(
                "FAIL: "
                + source_name
                + " / "
                + options.resource_name
                + ": leftover placeholders = "
                + repr(leftover)
            )
            all_ok = False
        if source_name == "container_connection_source":
            if "readDatapackageOrNull" not in rendered:
                print(
                    "FAIL: "
                    + source_name
                    + " / "
                    + options.resource_name
                    + ": readDatapackageOrNull helper not found in output"
                )
                all_ok = False
            if "datapackageFromHandle" not in rendered:
                print(
                    "FAIL: "
                    + source_name
                    + " / "
                    + options.resource_name
                    + ": datapackageFromHandle helper not found in output"
                )
                all_ok = False

ws: str = container_connection_source(WORK_STREAM_RUNTIME)
gantt: str = container_connection_source(IFC_WORK_SCHEDULE_RUNTIME)
if 'const WORK_STREAM_RESOURCE_NAME = "work_stream";' not in ws:
    print("FAIL: WorkStream resource literal not found")
    all_ok = False
if 'const WORK_STREAM_RESOURCE_NAME = "ifc_work_schedule";' not in gantt:
    print("FAIL: Gantt resource literal not found")
    all_ok = False

if all_ok:
    print("ALL RENDER CHECKS PASSED")
