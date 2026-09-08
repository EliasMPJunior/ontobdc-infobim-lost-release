from pathlib import Path
from typing import Any, Dict, List

from ontobdc_dev.testing.adapter.yaml_loader import load_documents
from ontobdc_dev.testing.domain.exception import TestManifestError
from ontobdc_dev.testing.domain.model.action import TestAction
from ontobdc_dev.testing.domain.model.metadata import ManifestMetadata
from ontobdc_dev.testing.domain.model.state import StateDefinition

_SUPPORTED_API_VERSION: str = "ontobdc.org/testing/v1alpha1"
_SUPPORTED_KINDS: frozenset = frozenset({"StateDefinition", "TestAction"})


class TestCatalog:
    """Composition of one or more manifests (semantic-test-orchestrator.md, 4.1).

    Only the `StateDefinition` and `TestAction` kinds are supported; the
    remaining kinds listed in 7.2 (`FixtureDefinition`, `TestCase`,
    `TestFlow`, `TestSuite`, `TestPolicy`) belong to the fixture/sandbox and
    planning phases and are not part of this slice.
    """

    def __init__(self) -> None:
        self._states: Dict[str, StateDefinition] = {}
        self._actions: Dict[str, TestAction] = {}

    @property
    def states(self) -> Dict[str, StateDefinition]:
        return dict(self._states)

    @property
    def actions(self) -> Dict[str, TestAction]:
        return dict(self._actions)

    def add_state(self, state: StateDefinition, source: str) -> None:
        if state.name in self._states:
            raise TestManifestError(
                f"Duplicate StateDefinition '{state.name}' in {source}."
            )
        self._states[state.name] = state

    def add_action(self, action: TestAction, source: str) -> None:
        if action.name in self._actions:
            raise TestManifestError(
                f"Duplicate TestAction '{action.name}' in {source}."
            )
        self._actions[action.name] = action

    def get_state(self, name: str) -> StateDefinition:
        state: Any = self._states.get(name)
        if state is None:
            raise TestManifestError(f"Unknown state '{name}'.")

        return state

    def get_action(self, name: str) -> TestAction:
        action: Any = self._actions.get(name)
        if action is None:
            raise TestManifestError(f"Unknown action '{name}'.")

        return action


class TestCatalogLoader:
    """Loads and validates a `TestCatalog` from a manifest file or directory.

    Structural and semantic validation (semantic-test-orchestrator.md, 20)
    is done directly against the parsed dict rather than through a JSON
    Schema (`schema/v1alpha1/*.schema.json` in 18 is not implemented in
    this slice): required fields, known `kind`, unique names, and existing
    state references are checked; unrecognized extra fields (`behavior`,
    `effects`, `planning`, `evidence`, ...) are accepted but ignored.
    """

    def load(self, path: Path) -> TestCatalog:
        catalog: TestCatalog = TestCatalog()
        for document in load_documents(path):
            self._ingest(document, catalog)

        self._validate_references(catalog)
        return catalog

    def _ingest(self, document: Dict[str, Any], catalog: TestCatalog) -> None:
        source: str = str(document.get("_source_path", "<unknown>"))
        api_version: Any = document.get("apiVersion")
        if api_version != _SUPPORTED_API_VERSION:
            raise TestManifestError(
                f"Unsupported apiVersion '{api_version}' in {source}; "
                f"expected '{_SUPPORTED_API_VERSION}'."
            )

        kind: Any = document.get("kind")
        if kind not in _SUPPORTED_KINDS:
            raise TestManifestError(
                f"Unsupported kind '{kind}' in {source}; expected one of "
                f"{sorted(_SUPPORTED_KINDS)}."
            )

        metadata: ManifestMetadata = self._parse_metadata(document, source)
        spec: Dict[str, Any] = document.get("spec") or {}

        if kind == "StateDefinition":
            catalog.add_state(self._parse_state(metadata, spec, source), source)
        else:
            catalog.add_action(self._parse_action(metadata, spec, source), source)

    def _parse_metadata(self, document: Dict[str, Any], source: str) -> ManifestMetadata:
        raw_metadata: Any = document.get("metadata")
        if not isinstance(raw_metadata, dict) or not str(raw_metadata.get("name", "")).strip():
            raise TestManifestError(f"Manifest in {source} is missing 'metadata.name'.")

        return ManifestMetadata(
            name=str(raw_metadata["name"]).strip(),
            title=str(raw_metadata.get("title", "")),
            description=str(raw_metadata.get("description", "")),
            tags=[str(tag) for tag in (raw_metadata.get("tags") or [])],
        )

    def _parse_state(
        self,
        metadata: ManifestMetadata,
        spec: Dict[str, Any],
        source: str,
    ) -> StateDefinition:
        observer: Any = spec.get("observer")
        expression: Any = spec.get("expression")
        if bool(observer) == bool(expression):
            raise TestManifestError(
                f"StateDefinition '{metadata.name}' in {source} must declare "
                "exactly one of 'observer' or 'expression'."
            )

        return StateDefinition(metadata=metadata, observer=observer, expression=expression)

    def _parse_action(
        self,
        metadata: ManifestMetadata,
        spec: Dict[str, Any],
        source: str,
    ) -> TestAction:
        executor: Any = spec.get("executor")
        if not isinstance(executor, dict):
            raise TestManifestError(
                f"TestAction '{metadata.name}' in {source} is missing 'executor'."
            )

        requires: List[str] = self._parse_state_references(spec.get("requires"))
        ensures: List[str] = self._parse_state_references(spec.get("ensures"))
        verification: Dict[str, Any] = spec.get("verification") or {}
        verification_states: List[str] = [
            str(state_name) for state_name in (verification.get("states") or [])
        ] or list(ensures)

        if not verification_states:
            raise TestManifestError(
                f"TestAction '{metadata.name}' in {source} declares no 'ensures' "
                "or 'verification.states' to reobserve after execution."
            )

        return TestAction(
            metadata=metadata,
            role=str(spec.get("role", "transition")),
            executor=executor,
            requires=requires,
            ensures=ensures,
            verification_states=verification_states,
        )

    def _parse_state_references(self, raw_references: Any) -> List[str]:
        return [
            str(reference["state"])
            for reference in (raw_references or [])
            if isinstance(reference, dict) and "state" in reference
        ]

    def _validate_references(self, catalog: TestCatalog) -> None:
        for action in catalog.actions.values():
            referenced_names: List[str] = [
                *action.requires,
                *action.ensures,
                *action.verification_states,
            ]
            for state_name in referenced_names:
                if state_name not in catalog.states:
                    raise TestManifestError(
                        f"TestAction '{action.name}' references unknown state "
                        f"'{state_name}'."
                    )

        for state in catalog.states.values():
            if state.expression is None:
                continue

            for state_name in self._referenced_state_names(state.expression):
                if state_name not in catalog.states:
                    raise TestManifestError(
                        f"StateDefinition '{state.name}' references unknown state "
                        f"'{state_name}' in its composite expression."
                    )

    def _referenced_state_names(self, expression: Dict[str, Any]) -> List[str]:
        if "not" in expression:
            return [str(expression["not"])]

        for operator in ("all", "any"):
            if operator in expression:
                return [str(state_name) for state_name in expression[operator]]

        return []
