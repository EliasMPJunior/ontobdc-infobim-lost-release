from pathlib import Path
from typing import Any, Dict, List, Optional

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, RDF, XSD

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.storage.adapter.attachment.graph import (
    AttachmentGraphNamespaceBootstrap,
)
from ontobdc.storage.adapter.attachment.context import AttachmentContextManager
from ontobdc.storage.adapter.attachment.metadata import (
    AttachmentMetadataService,
)
from ontobdc.storage.adapter.attachment.plan import AttachmentPlanConstants


class FakeContext(CliContextPort):
    def __init__(self, root_path: Path, parameters: Dict[str, Any]) -> None:
        self._root_path: Path = root_path
        self._parameters: Dict[str, Any] = parameters

    @property
    def raw_args(self) -> List[str]:
        return []

    @property
    def unprocessed_args(self) -> List[str]:
        return []

    @property
    def is_capability_targeted(self) -> bool:
        return False

    @property
    def target_capability_id(self) -> Optional[str]:
        return None

    @property
    def root_path(self) -> str:
        return str(self._root_path)

    @property
    def language(self) -> Optional[str]:
        return None

    def has_parameter(self, param_key: str) -> bool:
        return param_key in self._parameters

    def get_parameter_value(self, param_key: str) -> Any:
        return self._parameters.get(param_key)

    def set_parameter_value(self, param_key: str, param_value: Any) -> None:
        self._parameters[param_key] = param_value

    def delete_parameter(self, param_key: str) -> None:
        self._parameters.pop(param_key, None)

    def clear_parameters(self, param_keys: List[str]) -> None:
        for param_key in param_keys:
            self.delete_parameter(param_key)

    def reload(self) -> None:
        return None


class TestAttachmentMetadataService:
    def test_attaches_iso_container_description_and_creation_date(
        self,
        tmp_path: Path,
    ) -> None:
        AttachmentGraphNamespaceBootstrap.initialize()
        ct: Namespace = AttachmentGraphNamespaceBootstrap.CT
        obdc: Namespace = AttachmentGraphNamespaceBootstrap.OBDC
        container_subject: URIRef = URIRef("urn:ontobdc:storage/local/example")
        container_file: Path = tmp_path / "container.ttl"
        storage_file: Path = tmp_path / "storage.ttl"
        container_graph: Graph = Graph()
        container_graph.add((container_subject, RDF.type, obdc.DataContainer))
        container_graph.add(
            (container_subject, DCTERMS.identifier, Literal(str(container_subject)))
        )
        container_graph.add(
            (container_subject, DCTERMS.title, Literal("Example container"))
        )
        container_graph.add(
            (container_subject, ct.description, Literal("Example description"))
        )
        container_graph.add(
            (
                container_subject,
                ct.creationDate,
                Literal("2026-08-19T03:35:28+00:00", datatype=XSD.dateTime),
            )
        )
        container_graph.add(
            (container_subject, PROV.atLocation, URIRef(tmp_path.as_uri()))
        )
        container_graph.serialize(str(container_file), format="turtle")
        Graph().serialize(str(storage_file), format="turtle")
        attachment_plan: Dict[str, Any] = {
            "root_path": str(tmp_path),
            "container_path": str(tmp_path),
            "container_file": str(container_file),
            "storage_file": str(storage_file),
            "source_container_subject": str(container_subject),
            "source_container_id": str(container_subject),
            "source_container_location": tmp_path.as_uri(),
            "target_container_subject": str(container_subject),
            "target_container_id": str(container_subject),
            "target_container_location": tmp_path.as_uri(),
            "context_snapshot": {},
            "datasets": [],
        }
        context: FakeContext = FakeContext(
            tmp_path,
            {
                AttachmentPlanConstants.ATTACH_PLAN_PARAMETER: attachment_plan,
                "container_path": str(tmp_path),
            },
        )

        AttachmentMetadataService(context).attach_container_metadata()

        attached_storage_graph: Graph = Graph().parse(
            str(storage_file),
            format="turtle",
        )
        assert list(
            attached_storage_graph.objects(container_subject, ct.description)
        ) == [Literal("Example description")]
        assert [
            str(value)
            for value in attached_storage_graph.objects(
                container_subject,
                ct.creationDate,
            )
        ] == ["2026-08-19T03:35:28+00:00"]
        assert AttachmentMetadataService._is_storage_index_attached_core(
            attached_storage_graph,
            attached_storage_graph,
        )

        storage_without_container: Graph = Graph()

        assert not AttachmentMetadataService._is_storage_index_attached_core(
            attached_storage_graph,
            storage_without_container,
        )

        AttachmentContextManager(context).complete_attachment()

        assert AttachmentContextManager(context).is_container_attached()
        assert context.get_parameter_value(
            AttachmentPlanConstants.ATTACH_FINALIZED_PARAMETER
        ) == str(tmp_path.resolve())
