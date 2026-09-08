from typing import Any, Dict

from ontobdc.cli.domain.port.context import (
    CliContextPort,
    CliContextStrategyPort,
)
from ontobdc.context.adapter.container_instance import (
    ContainerEntityInstanceRepository,
)
from ontobdc.shared.domain.model.parameter import ParameterMetadata
from ontobdc.shared.domain.port.parameter import ParameterPort
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy


class ElementIdStrategy(ParameterPort, CliContextStrategyPort):
    """Resolve one Element by its canonical GlobalId inside a Container."""

    METADATA = ParameterMetadata(
        id="org.ontobdc.domain.context.capability.incoming.element",
        version="0.2.0",
        name="element_id",
        description=(
            "Resolve --element <GlobalId> to exactly one Element in the "
            "selected Container. Element ID and GlobalId are the same value."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        python_type=str,
    )

    def execute(self, context: CliContextPort) -> CliContextPort:
        global_id: str = str(
            context.get_parameter_value("element_id")
            or context.get_parameter_value("element")
            or context.get_parameter_value("global_id")
            or ""
        ).strip()
        if not global_id:
            raise ValueError("Element GlobalId is required.")

        context.set_parameter_value("element_id", global_id)
        context.set_parameter_value("global_id", global_id)
        context.set_parameter_value("element", global_id)

        container_path: str = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_path:
            ContainerIdStrategy().execute(context)
            container_path = str(
                context.get_parameter_value("container_path") or ""
            ).strip()
        if not container_path:
            raise ValueError(
                "Element resolution requires a selected Container."
            )

        element: Dict[str, Any] = ContainerEntityInstanceRepository(
            container_path=container_path,
        ).get_element(global_id)

        context.set_parameter_value("element_instance", element)
        context.set_parameter_value(
            "element_uri",
            str(element.get("iri") or "").strip(),
        )
        context.set_parameter_value(
            "element_dataset_path",
            str(element.get("dataset_path") or "").strip(),
        )
        context.set_parameter_value(
            "element_entity_uri",
            str(element.get("entity_uri") or "").strip(),
        )
        return context
