from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.plugin.builder.ifc_work_schedule.gantt_runtime_source import (
    GanttScriptAdapter,
)
from ontobdc_view.shared.adapter.vendor import VENDOR_SHEET_JS_NAME


_GANTT_TAB_MOUNT_SOURCE = r'''(function () {
  "use strict";

  function mountGanttTab() {
    const card = document.querySelector(".onto-page-body");
    const gantt = card && card.querySelector(".gantt-container");
    if (!card || !gantt) return;
    if (card.querySelector('[data-schedule-dimension-tab="gantt"]')) return;

    let tablist = card.querySelector(".schedule-dimension-tabs");
    if (!tablist) {
      tablist = document.createElement("div");
      tablist.className = "schedule-dimension-tabs";
      tablist.setAttribute("role", "tablist");
      tablist.setAttribute("aria-label", "Schedule views");
      card.insertBefore(tablist, gantt);
    }

    let panels = card.querySelector(".schedule-dimension-panels");
    if (!panels) {
      panels = document.createElement("div");
      panels.className = "schedule-dimension-panels";
      card.insertBefore(panels, gantt);
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "schedule-dimension-tab is-active";
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", "true");
    button.setAttribute("aria-controls", "schedule-dimension-panel-gantt");
    button.setAttribute("data-schedule-dimension-tab", "gantt");
    button.textContent = "Gantt";

    const panel = document.createElement("section");
    panel.className = "schedule-dimension-panel";
    panel.id = "schedule-dimension-panel-gantt";
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("data-schedule-dimension-panel", "gantt");
    panel.appendChild(gantt);

    tablist.insertBefore(button, tablist.firstChild);
    panels.insertBefore(panel, panels.firstChild);

    const tabs = [...tablist.querySelectorAll("[data-schedule-dimension-tab]")];
    const pagePanels = [...panels.querySelectorAll("[data-schedule-dimension-panel]")];

    function activate(selected) {
      for (const tab of tabs) {
        const active = tab.dataset.scheduleDimensionTab === selected;
        tab.classList.toggle("is-active", active);
        tab.setAttribute("aria-selected", String(active));
      }
      for (const candidate of pagePanels) {
        candidate.hidden = candidate.dataset.scheduleDimensionPanel !== selected;
      }
      if (selected === "gantt") {
        try { window.dispatchEvent(new Event("resize")); } catch (error) {}
      }
    }

    for (const tab of tabs) {
      tab.addEventListener("click", () => activate(tab.dataset.scheduleDimensionTab));
    }
    activate("gantt");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountGanttTab, { once: true });
  } else {
    mountGanttTab();
  }
})();
'''


class _IfcWorkScheduleGanttScriptCapability(TransformationCapability):
    SCRIPT_NAME = ""
    RESULTING_STATE = ""

    def label(self, lang: str = "en") -> str:
        return self.METADATA.name

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        path = self._target_path(context)
        if not path.is_file():
            return False
        try:
            return path.read_text(encoding="utf-8") == self._source()
        except OSError:
            return False

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        path = self._target_path(context)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._source(), encoding="utf-8")
        return {
            "resulting_state": self.RESULTING_STATE,
            "generated_script_path": str(path),
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    def _source(self) -> str:
        if self.SCRIPT_NAME == "gantt_tab_mount":
            return _GANTT_TAB_MOUNT_SOURCE
        return GanttScriptAdapter().script_source(self.SCRIPT_NAME)

    def _target_path(self, context: CliContextPort) -> Path:
        container_path = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_path:
            raise ValueError("The container path was not resolved.")
        return (
            Path(container_path).expanduser().resolve()
            / ".__ontobdc__"
            / "asset"
            / "ifc_work_schedule_view"
            / f"{self.SCRIPT_NAME}.js"
        )


class IfcWorkScheduleVendorSheetJsAssetGeneratedCapability(
    _IfcWorkScheduleGanttScriptCapability
):
    SCRIPT_NAME = VENDOR_SHEET_JS_NAME
    RESULTING_STATE = "__vendor_sheet_js_asset_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_vendor_sheet_js_asset_generated",
        version="1.0.0",
        name="IfcWorkSchedule Vendor Sheet JS Asset Generated",
        description="Write the stable Gantt SheetJS runtime asset for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "sheetjs"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule SheetJS asset was generated."}},
    )


class IfcWorkScheduleI18nScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "i18n_apply"
    RESULTING_STATE = "__i18n_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_i18n_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule I18n Script Generated",
        description="Write the stable Gantt i18n runtime for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "i18n"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule i18n script was generated."}},
    )


class IfcWorkScheduleGraphReaderScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "graph_reader"
    RESULTING_STATE = "__graph_reader_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_graph_reader_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Graph Reader Script Generated",
        description="Write the stable Gantt JSON-LD graph reader for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "json-ld"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule graph reader was generated."}},
    )


class IfcWorkScheduleContainerConnectionScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "container_connection"
    RESULTING_STATE = "__container_connection_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_container_connection_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Container Connection Script Generated",
        description="Write the stable Gantt container connection runtime for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "container"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule container connection script was generated."}},
    )


class IfcWorkScheduleConnectionStateScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "connection_state"
    RESULTING_STATE = "__connection_state_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_connection_state_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Connection State Script Generated",
        description="Write the stable Gantt connection-state runtime for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "connection"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule connection-state script was generated."}},
    )


class IfcWorkScheduleChromeControlsScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "chrome_controls"
    RESULTING_STATE = "__chrome_controls_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_chrome_controls_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Chrome Controls Script Generated",
        description="Write the stable Gantt chrome-controls runtime for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "chrome"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule chrome-controls script was generated."}},
    )


class IfcWorkSchedulePyodideRuntimeScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "pyodide_runtime"
    RESULTING_STATE = "__pyodide_runtime_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_pyodide_runtime_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Pyodide Runtime Script Generated",
        description="Write the stable Gantt SheetJS/Pyodide workbook runtime for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "pyodide"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule workbook runtime was generated."}},
    )


class IfcWorkScheduleTaskTableTimelineScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "task_table_timeline"
    RESULTING_STATE = "__task_table_timeline_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_task_table_timeline_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Task Table Timeline Script Generated",
        description="Write the stable Gantt task-table and timeline renderer for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "timeline"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule task timeline script was generated."}},
    )


class IfcWorkScheduleDependencyArrowsScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "dependency_arrows"
    RESULTING_STATE = "__dependency_arrows_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_dependency_arrows_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Dependency Arrows Script Generated",
        description="Write the stable Gantt dependency-arrow renderer for the IfcWorkSchedule Page.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "dependency"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule dependency-arrow script was generated."}},
    )


class IfcWorkScheduleGanttTabMountScriptGeneratedCapability(_IfcWorkScheduleGanttScriptCapability):
    SCRIPT_NAME = "gantt_tab_mount"
    RESULTING_STATE = "__gantt_tab_mount_script_generated__"
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.ifc_work_schedule_gantt_tab_mount_script_generated",
        version="1.0.0",
        name="IfcWorkSchedule Gantt Tab Mount Script Generated",
        description="Mount the restored Gantt inside the Gantt tab of the single IfcWorkSchedule card.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "gantt", "tab"],
        supported_languages=["en", "pt-br"],
        log_message={"info": {"en": "The IfcWorkSchedule Gantt tab mount script was generated."}},
    )
