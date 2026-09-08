from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.script import PageScriptAssetAdapter


I18N_SCRIPT_NAME = "i18n_apply"


class I18nScriptGeneratedCapability(TransformationCapability):
    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "i18n_script_generated"
        ),
        version="1.0.0",
        name="I18n Script Generated",
        description="Publish the entity builder's UI translation script.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "i18n", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {"en": "The Page i18n script was generated."},
            "debug_entry": {"en": "Generating the Page i18n script."},
        },
    )

    def label(self, lang: str = "en") -> str:
        return "I18n Script Generated"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return PageScriptAssetAdapter.check(context, I18N_SCRIPT_NAME)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        path = PageScriptAssetAdapter.write(context, I18N_SCRIPT_NAME)
        return {
            "resulting_state": "__i18n_script_generated__",
            "generated_script_path": str(path),
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
