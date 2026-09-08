from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict

import ontobdc_web_dock
from brasidatacenter.resources import ontology_path
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy

from ontobdc_view.component.adapter.dock import (
    component_event_promoter_source,
    dock_runtime_module_names,
    presentation_event_policy,
)

# These tests verify the *shape* of the generated JavaScript bridge --
# correct embedding, the canonical DOM envelopes, absence of a parallel
# promotion table. They cannot execute the generated script (no JS runtime
# in this suite), so they are packaging evidence, not proof that the bridge
# actually queues, bootstraps Pyodide, or dispatches events in a browser.
# See docs/doc/03-architecture/event-promotion.md's "Testing guidelines"
# for the full evidence ladder; layer 4 (a real Playwright/Pyodide run)
# is what proves runtime behavior.

_POLICY_ASSIGNMENT_RE = re.compile(
    r"const PRESENTATION_EVENT_POLICY = (?P<payload>.*?);\n", re.DOTALL
)
_RUNTIME_ASSIGNMENT_RE = re.compile(
    r"const DOCK_RUNTIME_SOURCE = (?P<payload>.*?);\n", re.DOTALL
)
_BUNDLED_SOURCES_RE = re.compile(
    r'_ONTOBDC_DOCK_SOURCES = _json\.loads\(r"""(?P<payload>.*?)"""\)', re.DOTALL
)


class TestPresentationEventPolicy:
    def test_reads_the_real_packaged_turtle_document(self) -> None:
        expected_path = ontology_path("tool", "ontobdc", "abox", "presentation_event.ttl")
        expected = Path(str(expected_path)).read_text(encoding="utf-8")
        assert presentation_event_policy() == expected


class TestDockRuntimeModuleNames:
    def test_lists_the_real_ontobdc_web_dock_modules(self) -> None:
        names = dock_runtime_module_names()
        assert "bridge.py" in names
        assert "dock/adapter/policy.py" in names
        assert "dock/plugin/listener/presentation_event.py" in names

    def test_excludes_cache_artifacts_and_is_sorted(self) -> None:
        names = dock_runtime_module_names()
        assert not any("__pycache__" in name for name in names)
        assert names == sorted(names)


class TestComponentEventPromoterSource:
    def test_embeds_the_real_presentation_event_policy_verbatim(self) -> None:
        source = component_event_promoter_source()
        match = _POLICY_ASSIGNMENT_RE.search(source)
        assert match is not None
        embedded_policy = json.loads(match.group("payload"))
        assert embedded_policy == presentation_event_policy()

    def test_bundles_the_real_modules_with_matching_content_and_no_cache_artifacts(
        self,
    ) -> None:
        source = component_event_promoter_source()
        runtime_match = _RUNTIME_ASSIGNMENT_RE.search(source)
        assert runtime_match is not None
        installer_script = json.loads(runtime_match.group("payload"))

        sources_match = _BUNDLED_SOURCES_RE.search(installer_script)
        assert sources_match is not None
        bundled: Dict[str, str] = json.loads(sources_match.group("payload"))

        assert set(bundled) == set(dock_runtime_module_names())
        assert not any("__pycache__" in name for name in bundled)

        real_root = Path(str(ontobdc_web_dock.__file__)).parent
        real_bridge = (real_root / "bridge.py").read_text(encoding="utf-8")
        assert bundled["bridge.py"] == real_bridge

    def test_uses_only_the_canonical_component_and_shared_event_dom_envelopes(
        self,
    ) -> None:
        source = component_event_promoter_source()
        assert "const COMPONENT_EVENT_TYPE = 'ontobdc:component-event';" in source
        assert "const SHARED_EVENT_TYPE = 'ontobdc:shared-event';" in source

    def test_reads_the_semantic_occurrence_name_from_detail_event(self) -> None:
        source = component_event_promoter_source()
        assert 'const name = String(detail.event || "").trim();' in source

    def test_contains_no_hardcoded_promotion_table_outside_the_embedded_policy(
        self,
    ) -> None:
        source = component_event_promoter_source()
        without_policy = _POLICY_ASSIGNMENT_RE.sub("", source)
        without_embedded_payloads = _RUNTIME_ASSIGNMENT_RE.sub("", without_policy)

        policy = PromotionPolicy.from_turtle(presentation_event_policy())
        concrete_event_names = set(policy.component_event_names()) | set(
            policy.shared_event_names()
        )
        assert concrete_event_names, "the real policy must declare at least one event"
        for name in concrete_event_names:
            assert name not in without_embedded_payloads

    def test_dispatches_a_shared_event_for_every_target_carrying_provenance_fields(
        self,
    ) -> None:
        # Structural evidence only (see module docstring): confirms the
        # dispatch loop and detail shape exist in source, not that they run.
        source = component_event_promoter_source()
        assert "for (const target of targets) {" in source
        assert "dispatchSharedEvent(occurrence, answer, target);" in source
        assert "event: target.event," in source
        assert "eventIri: target.iri," in source
        assert "promotedFrom: answer.componentEvent," in source
        assert "promotedFromIri: answer.componentEventIri," in source
        assert "...(occurrence.envelope.detail || {})," in source

    def test_queues_occurrences_and_preserves_the_queue_on_bootstrap_failure(
        self,
    ) -> None:
        # Structural evidence only (see module docstring).
        source = component_event_promoter_source()
        assert "this.#pending.push(occurrence);" in source
        assert "while (this.#pending.length) {" in source
        assert (
            'catch (error) { log("drain: bootstrap failed, keeping queue", error); return; }'
            in source
        )
