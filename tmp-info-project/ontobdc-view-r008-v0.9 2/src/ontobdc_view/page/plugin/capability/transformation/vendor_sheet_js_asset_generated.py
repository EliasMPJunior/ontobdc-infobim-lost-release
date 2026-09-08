from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.script import PageScriptAssetAdapter
from ontobdc_view.shared.adapter.vendor import VENDOR_SHEET_JS_NAME


class VendorSheetJsAssetGeneratedCapability(TransformationCapability):
    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "vendor_sheet_js_asset_generated"
        ),
        version="1.0.0",
        name="Vendor Sheet JS Asset Generated",
        description="Publish the builder's vendored SheetJS library.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "sheetjs", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {"en": "The Page SheetJS asset was generated."},
            "debug_entry": {"en": "Generating the Page SheetJS asset."},
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Vendor Sheet JS Asset Generated"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return PageScriptAssetAdapter.check(context, VENDOR_SHEET_JS_NAME)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        path = PageScriptAssetAdapter.write(context, VENDOR_SHEET_JS_NAME)
        return {
            "resulting_state": "__vendor_sheet_js_asset_generated__",
            "generated_script_path": str(path),
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
