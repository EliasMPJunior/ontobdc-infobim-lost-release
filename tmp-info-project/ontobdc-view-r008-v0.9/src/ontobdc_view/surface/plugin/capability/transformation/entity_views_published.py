"""Publish generated Entity Page JSON-LD payloads as standalone HTML."""

import json
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.script import EntityPageScriptGeneratorLoader
from ontobdc_view.page.adapter.template import EntityPageTemplateAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import (
    SurfaceGenerationProcessState,
)


class EntityViewsPublishedCapability(TransformationCapability):
    """Render every generated Entity Page JSON-LD artifact through Jinja."""

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "entity_views_published"
        ),
        version="1.0.0",
        name="Entity Views Published",
        description=(
            "Publish standalone detail pages for entities supported by "
            "ontobdc_view Page renderers."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "surface", "html", "page", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Entity view publication completed.",
            },
            "debug_entry": {
                "en": "Publishing standalone entity detail pages.",
            },
        },
    )

    def __init__(
        self,
        script_generator_loader: Optional[
            EntityPageScriptGeneratorLoader
        ] = None,
        template_adapter: Optional[EntityPageTemplateAdapter] = None,
    ) -> None:
        self._script_generator_loader = (
            script_generator_loader or EntityPageScriptGeneratorLoader()
        )
        self._template_adapter = template_adapter or EntityPageTemplateAdapter()

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.ENTITY_VIEWS_PUBLISHED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.ENTITY_VIEWS_PUBLISHED.description(
            lang
        )

    def check(self, context: CliContextPort) -> bool:
        sources = self._jsonld_paths(context)
        return bool(sources) and all(
            source.with_suffix(".html").is_file() for source in sources
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        language = str(
            context.get_parameter_value("language") or "en"
        ).strip() or "en"
        published_paths: List[str] = []
        future_source: Dict[Future[Path], Path] = {}
        source_paths = self._jsonld_paths(context)

        with ThreadPoolExecutor() as executor:
            for source_path in source_paths:
                future = executor.submit(
                    self._publish_view,
                    source_path,
                    language,
                )
                future_source[future] = source_path

            for future in as_completed(future_source):
                published_paths.append(str(future.result()))

        published_paths.sort()
        script_paths: List[str] = []
        for view_directory in sorted(
            {source.parent.name for source in source_paths}
        ):
            generator = self._script_generator_loader.get(view_directory)
            if generator is not None:
                script_paths.extend(generator(context))

        return {
            "resulting_state": (
                SurfaceGenerationProcessState.ENTITY_VIEWS_PUBLISHED
            ),
            "published_view_count": len(published_paths),
            "published_view_paths": published_paths,
            "generated_script_paths": script_paths,
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    def _publish_view(self, source_path: Path, language: str) -> Path:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        target_path = source_path.with_suffix(".html")
        target_path.write_text(
            self._template_adapter.render(
                view_directory=source_path.parent.name,
                payload=payload,
                language=language,
            ),
            encoding="utf-8",
        )
        return target_path

    @classmethod
    def _jsonld_paths(cls, context: CliContextPort) -> List[Path]:
        container_path = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_path:
            raise ValueError("The container path was not resolved.")

        view_directory = (
            Path(container_path).expanduser().resolve()
            / ".__ontobdc__"
            / "view"
        )
        if not view_directory.is_dir():
            return []
        return sorted(view_directory.rglob("*.jsonld"))
