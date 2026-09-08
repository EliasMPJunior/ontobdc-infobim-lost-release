from functools import partial
from pathlib import Path
from typing import Callable, List, Optional

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.atomic_file import AtomicFileWriter
from ontobdc.storage.adapter.bootstrap import (
    StorageBootstrap,
    StorageNamespaceBootstrap,
)


class ContainerNameAdapter:
    """Read and update the canonical semantic name of one storage container."""

    def __init__(
        self,
        root_path: Path,
        container_path: Path,
        container_id: str,
    ) -> None:
        self._root_path: Path = root_path.expanduser().resolve()
        self._container_path: Path = container_path.expanduser().resolve()
        self._container_id: str = container_id.strip()
        self._metadata_path: Path = StorageBootstrap.get_container_storage_file_path(
            self._container_path
        )
        self._storage_index_path: Path = StorageBootstrap.get_storage_file_path(
            self._root_path
        )

    @classmethod
    def from_context(cls, context: CliContextPort) -> "ContainerNameAdapter":
        root_path: Path = Path(str(context.root_path)).expanduser().resolve()
        container_path: Path = Path(
            str(context.get_parameter_value("container_path"))
        ).expanduser().resolve()
        container_id: str = str(
            context.get_parameter_value("container_id")
        ).strip()
        return cls(
            root_path=root_path,
            container_path=container_path,
            container_id=container_id,
        )

    @property
    def container_id(self) -> str:
        return self._container_id

    @property
    def container_path(self) -> Path:
        return self._container_path

    def is_valid(self) -> bool:
        if not self._metadata_path.is_file():
            return False
        if not self._storage_index_path.is_file():
            return False

        metadata_graph: Graph = self._load_graph(self._metadata_path)
        storage_graph: Graph = self._load_graph(self._storage_index_path)
        return (
            self._resolve_container_subject(metadata_graph) is not None
            and self._resolve_container_subject(storage_graph) is not None
        )

    def metadata_title(self) -> Optional[str]:
        graph: Graph = self._load_graph(self._metadata_path)
        subject: URIRef = self._require_container_subject(graph)
        title: Optional[Literal] = self._single_title(graph, subject)
        if title is None:
            return None
        return str(title)

    def storage_index_matches_metadata(self) -> bool:
        metadata_graph: Graph = self._load_graph(self._metadata_path)
        metadata_subject: URIRef = self._require_container_subject(
            metadata_graph
        )
        metadata_title: Optional[Literal] = self._single_title(
            metadata_graph,
            metadata_subject,
        )
        if metadata_title is None:
            return False

        storage_graph: Graph = self._load_graph(self._storage_index_path)
        storage_subject: URIRef = self._require_container_subject(storage_graph)
        storage_title: Optional[Literal] = self._single_title(
            storage_graph,
            storage_subject,
        )
        return storage_title == metadata_title

    def rename_metadata(self, new_title: str) -> None:
        normalized_title: str = new_title.strip()
        if not normalized_title:
            raise ValueError("Container name cannot be empty.")

        graph: Graph = self._load_graph(self._metadata_path)
        subject: URIRef = self._require_container_subject(graph)
        existing_title: Optional[Literal] = self._single_title(graph, subject)
        replacement: Literal = self._replacement_literal(
            existing=existing_title,
            value=normalized_title,
        )

        graph.remove((subject, DCTERMS.title, None))
        graph.add((subject, DCTERMS.title, replacement))
        writer: Callable[[Path], None] = partial(self._write_graph, graph)
        AtomicFileWriter.write(self._metadata_path, writer)

    def rename_storage_index(self) -> None:
        metadata_graph: Graph = self._load_graph(self._metadata_path)
        metadata_subject: URIRef = self._require_container_subject(
            metadata_graph
        )
        metadata_title: Optional[Literal] = self._single_title(
            metadata_graph,
            metadata_subject,
        )
        if metadata_title is None:
            raise ValueError("Container metadata has no canonical title.")

        storage_graph: Graph = self._load_graph(self._storage_index_path)
        storage_subject: URIRef = self._require_container_subject(storage_graph)
        storage_graph.remove((storage_subject, DCTERMS.title, None))
        storage_graph.add((storage_subject, DCTERMS.title, metadata_title))

        writer: Callable[[Path], None] = partial(
            self._write_graph,
            storage_graph,
        )
        AtomicFileWriter.write(self._storage_index_path, writer)

    @staticmethod
    def _load_graph(file_path: Path) -> Graph:
        graph: Graph = Graph()
        graph.parse(str(file_path), format="turtle")
        return graph

    def _resolve_container_subject(self, graph: Graph) -> Optional[URIRef]:
        obdc = StorageNamespaceBootstrap.OBDC
        candidates: List[URIRef] = []
        for subject in graph.subjects(RDF.type, obdc.DataContainer):
            if not isinstance(subject, URIRef):
                continue
            identifiers: List[str] = [
                str(value).strip()
                for value in graph.objects(subject, DCTERMS.identifier)
                if str(value).strip()
            ]
            if identifiers == [self._container_id]:
                candidates.append(subject)

        if len(candidates) != 1:
            return None
        return candidates[0]

    def _require_container_subject(self, graph: Graph) -> URIRef:
        subject: Optional[URIRef] = self._resolve_container_subject(graph)
        if subject is None:
            raise ValueError(
                f"Container metadata is ambiguous for {self._container_id}."
            )
        return subject

    @staticmethod
    def _single_title(graph: Graph, subject: URIRef) -> Optional[Literal]:
        titles: List[Literal] = [
            value
            for value in graph.objects(subject, DCTERMS.title)
            if isinstance(value, Literal)
        ]
        if len(titles) != 1:
            return None
        return titles[0]

    @staticmethod
    def _replacement_literal(
        existing: Optional[Literal],
        value: str,
    ) -> Literal:
        if existing is None:
            return Literal(value)
        if existing.language:
            return Literal(value, lang=existing.language)
        if existing.datatype is not None:
            return Literal(value, datatype=existing.datatype)
        return Literal(value)

    @staticmethod
    def _write_graph(graph: Graph, destination: Path) -> None:
        serialized_graph: bytes = graph.serialize(
            format="turtle",
            encoding="utf-8",
        )
        destination.write_bytes(serialized_graph)
