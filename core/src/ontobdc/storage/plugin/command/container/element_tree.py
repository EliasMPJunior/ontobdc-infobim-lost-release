import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from rdflib import Graph, Literal, URIRef

from ontobdc.cli.domain.exception.command import CliCommandArgumentException
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.context.plugin.parameter.element import ElementIdStrategy
from ontobdc.shared.facade.port.command import CliCommandPort
from ontobdc.shared.facade.request.command import CliCommandRequest
from ontobdc.shared.facade.response.command import CommandResponse, TreeCommandResponse
from ontobdc.storage.adapter.bootstrap import get_dataset_storage_file_path
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy


class StorageContainerElementTreeCommand(CliCommandPort):
    """Show one resolved Element's RDF properties as a tree."""

    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="container_element_tree",
        logical_component="storage",
        description="Visualize one storage element's properties as a tree.",
        arguments=[
            {
                "accepts": ["--container-id", "--container"],
                "valued": True,
                "description": "Select a registered container by ID or filesystem path.",
                "usage": "ontobdc storage --container <id-or-path> --element <GlobalId>",
            },
            {
                "accepts": ["--element"],
                "valued": True,
                "parameter": "element_id",
                "description": (
                    "Select one element by its GlobalId. Element ID and "
                    "GlobalId are the same value."
                ),
                "usage": "ontobdc storage --container <id-or-path> --element <GlobalId>",
            },
        ],
    )

    @staticmethod
    def _is_element_id(value: str) -> bool:
        stripped: str = str(value or "").strip()
        return bool(stripped) and not stripped.startswith("--")

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return (
            len(args) == 5
            and args[0] == "storage"
            and args[1] in {"--container-id", "--container"}
            and bool(str(args[2]).strip())
            and args[3] == "--element"
            and StorageContainerElementTreeCommand._is_element_id(args[4])
        )

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request
        self._container_id: str = ""
        self._container_path: Optional[Path] = None
        self._element_id: str = ""
        self._element_uri: str = ""
        self._element_dataset_path: Optional[Path] = None
        self._element_title: str = ""

    def check(self) -> bool:
        command_args: List[str] = self._request.command_args
        if not (
            len(command_args) == 4
            and command_args[0] in {"--container-id", "--container"}
            and command_args[2] == "--element"
        ):
            return False

        container_selector: str = command_args[1].strip()
        element_id: str = command_args[3].strip()
        if not container_selector or not self._is_element_id(element_id):
            return False

        container_parameter: str = (
            "container_id"
            if command_args[0] == "--container-id"
            else "container"
        )
        self._request.context.set_parameter_value(
            container_parameter,
            container_selector,
        )
        self._request.context.set_parameter_value("element_id", element_id)

        ContainerIdStrategy().execute(self._request.context)
        self._container_id = str(
            self._request.context.get_parameter_value("container_id") or ""
        ).strip()
        container_path: str = str(
            self._request.context.get_parameter_value("container_path") or ""
        ).strip()
        if not self._container_id or not container_path:
            raise CliCommandArgumentException(
                f"Invalid container selector: {container_selector}"
            )
        self._container_path = Path(container_path).expanduser().resolve()

        ElementIdStrategy().execute(self._request.context)
        self._element_id = str(
            self._request.context.get_parameter_value("element_id") or ""
        ).strip()
        self._element_uri = str(
            self._request.context.get_parameter_value("element_uri") or ""
        ).strip()
        dataset_path: str = str(
            self._request.context.get_parameter_value(
                "element_dataset_path"
            )
            or ""
        ).strip()
        if not self._element_uri or not dataset_path:
            raise CliCommandArgumentException(
                f"Element is not registered in this container: {self._element_id}"
            )
        self._element_dataset_path = Path(dataset_path).expanduser().resolve()

        element_instance: Any = self._request.context.get_parameter_value(
            "element_instance"
        )
        if isinstance(element_instance, dict):
            self._element_title = str(
                element_instance.get("title") or ""
            ).strip()
        return True

    def run(self) -> CommandResponse:
        if self._element_dataset_path is None:
            raise CliCommandArgumentException(
                f"Element is not registered in this container: {self._element_id}"
            )

        dataset_storage_file: Path = get_dataset_storage_file_path(
            self._element_dataset_path
        )
        graph: Graph = Graph()
        try:
            graph.parse(str(dataset_storage_file), format="turtle")
        except Exception as exc:
            raise CliCommandArgumentException(
                f"Could not read Element dataset metadata: {dataset_storage_file}"
            ) from exc

        subject: URIRef = URIRef(self._element_uri)
        predicate_objects = list(graph.predicate_objects(subject))
        if not predicate_objects:
            raise CliCommandArgumentException(
                f"Resolved Element subject is not present in dataset metadata: "
                f"{self._element_uri}"
            )

        root_name: str = (
            f"{self._element_id} — {self._element_title}"
            if self._element_title
            else self._element_id
        )

        children: List[Dict[str, Any]] = []
        for predicate, obj in predicate_objects:
            label: str = self._qname_local(graph, predicate)
            value_text: str = self._object_text(graph, obj)
            children.append(
                {
                    "name": f"{label.upper()}: {value_text}",
                    "kind": "property",
                    "children": [],
                }
            )
        children.sort(key=lambda node: str(node["name"]).lower())

        tree: Dict[str, Any] = {
            "name": root_name,
            "kind": "root",
            "children": children,
        }

        return TreeCommandResponse(
            title="Storage Element",
            description=(
                f"Tree view of element {self._element_id} in container "
                f"{self._container_id}."
            ),
            content={"tree": tree},
        )

    _AUTO_PREFIX_RE = re.compile(r"^ns\d+$")

    @classmethod
    def _qname_local(cls, graph: Graph, predicate: URIRef) -> str:
        try:
            qname: str = graph.namespace_manager.qname(predicate)
        except Exception:
            return cls._local_name(predicate)
        return qname.split(":", 1)[1] if ":" in qname else qname

    @classmethod
    def _object_text(cls, graph: Graph, obj: Any) -> str:
        if isinstance(obj, Literal):
            return str(obj).strip()
        if isinstance(obj, URIRef):
            return cls._qname_or_local(graph, obj)
        return str(obj)

    @classmethod
    def _qname_or_local(cls, graph: Graph, uri: URIRef) -> str:
        try:
            qname: str = graph.namespace_manager.qname(uri)
        except Exception:
            return cls._local_name(uri)
        prefix: str = qname.split(":", 1)[0] if ":" in qname else ""
        if cls._AUTO_PREFIX_RE.match(prefix):
            return cls._local_name(uri)
        return qname

    @staticmethod
    def _local_name(value: Any) -> str:
        raw_value: str = str(value or "").strip()
        if "#" in raw_value:
            return raw_value.rsplit("#", 1)[-1].strip()
        return raw_value.rstrip("/").rsplit("/", 1)[-1].strip()
