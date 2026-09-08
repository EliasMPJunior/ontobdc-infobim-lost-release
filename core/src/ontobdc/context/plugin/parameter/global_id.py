from typing import Any

from ontobdc.context.adapter.instance import ContainerEntityInstanceRepository
from ontobdc.shared.domain.model.parameter import ParameterMetadata
from ontobdc.shared.domain.port.parameter import ParameterPort
from ontobdc.shared.facade.port.context import CliContextPort, CliContextStrategyPort


def resolve_entity_by_global_id(
    *, container_path: str, entity: str, global_id: str
) -> dict[str, Any]:
    """Resolve exactly one projected entity instance by canonical GlobalId."""
    return ContainerEntityInstanceRepository(
        container_path=container_path,
        entity=entity,
    ).get_instance(global_id)


class EntityGlobalIdStrategy(ParameterPort, CliContextStrategyPort):
    """Resolve GlobalId as Element identity and, when requested, Entity data."""

    METADATA = ParameterMetadata(
        id="org.ontobdc.domain.context.parameter.global-id",
        version="0.17.0",
        name="global_id",
        description="Resolve exactly one Element and optional Entity instance by GlobalId.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        python_type=str,
    )

    def execute(self, context: CliContextPort) -> CliContextPort:
        global_id = str(context.get_parameter_value("global_id") or "").strip()
        if not global_id:
            raise ValueError("--global-id is required.")
        context.set_parameter_value("global_id", global_id)
        context.set_parameter_value("element_id", global_id)

        container_path = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_path:
            return context

        element_repository = ContainerEntityInstanceRepository(
            container_path=container_path,
        )
        element = element_repository.get_element(global_id)
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

        entity = str(context.get_parameter_value("entity") or "").strip()
        if entity:
            context.set_parameter_value(
                "entity_instance",
                ContainerEntityInstanceRepository(
                    container_path=container_path,
                    entity=entity,
                ).get_instance(global_id),
            )
        return context
