from __future__ import annotations

from typing import Any, Dict
from unittest.mock import patch

import pytest

from ontobdc_view.surface.adapter.publication import SurfacePublicationAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.is_publishable import (
    IsPublishableCapability,
)


class TestIsPublishableCapability:
    def test_check_returns_true_when_container_is_publishable(self) -> None:
        capability = IsPublishableCapability()
        context: object = object()
        with patch.object(
            SurfacePublicationAdapter,
            "is_container_publishable",
            return_value=True,
        ) as mocked:
            result: bool = capability.check(context)
        assert result is True
        mocked.assert_called_once_with(context)

    def test_check_returns_false_when_container_is_not_publishable(self) -> None:
        capability = IsPublishableCapability()
        context: object = object()
        with patch.object(
            SurfacePublicationAdapter,
            "is_container_publishable",
            return_value=False,
        ) as mocked:
            result: bool = capability.check(context)
        assert result is False
        mocked.assert_called_once_with(context)

    def test_check_passes_context_through_unchanged(self) -> None:
        # Guards against a future change that wraps/copies context before
        # forwarding it to the adapter -- the adapter reads container_path
        # and root_path off this exact object, so identity must be preserved.
        capability = IsPublishableCapability()
        context: object = object()
        with patch.object(
            SurfacePublicationAdapter,
            "is_container_publishable",
            return_value=True,
        ) as mocked:
            capability.check(context)
        assert mocked.call_args.args == (context,)

    def test_execute_returns_adapter_result_with_resulting_state_added(self) -> None:
        adapter_result: Dict[str, Any] = {
            "container_path": "/fake/container",
            "container_id": "urn:container:fake",
            "datapackage_path": "/fake/container/datapackage.json",
            "resource_count": 3,
            "local_resource_count": 3,
            "added_resource_count": 0,
            "updated_resource_count": 0,
            "removed_resource_count": 0,
        }
        capability = IsPublishableCapability()
        context: object = object()
        with patch.object(
            SurfacePublicationAdapter,
            "ensure_publishable",
            # A fresh copy: execute() mutates the returned dict in place, and
            # the mock must not hand out the same object this test still
            # holds a reference to.
            return_value=dict(adapter_result),
        ) as mocked:
            result: Dict[str, Any] = capability.execute(context)
        assert result["resulting_state"] is SurfaceGenerationProcessState.IS_PUBLISHABLE
        for key, value in adapter_result.items():
            assert result[key] == value
        mocked.assert_called_once_with(context)

    def test_execute_propagates_exception_from_ensure_publishable(self) -> None:
        capability = IsPublishableCapability()
        context: object = object()
        with patch.object(
            SurfacePublicationAdapter,
            "ensure_publishable",
            side_effect=ValueError("bad container path"),
        ):
            with pytest.raises(ValueError, match="bad container path"):
                capability.execute(context)

    @pytest.mark.parametrize("publishable", [True, False])
    def test_is_satisfied_matches_check_result(self, publishable: bool) -> None:
        capability = IsPublishableCapability()
        context: object = object()
        with patch.object(
            SurfacePublicationAdapter,
            "is_container_publishable",
            return_value=publishable,
        ):
            result: bool = capability.is_satisfied(context)
        assert result is publishable

    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Is Publishable"), ("pt-br", "Publicavel")],
    )
    def test_label_delegates_to_process_state(
        self, lang: str, expected_label: str
    ) -> None:
        capability = IsPublishableCapability()
        assert capability.label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = IsPublishableCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.IS_PUBLISHABLE.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        # CapabilityLoader discovers capabilities by this exact id string --
        # a typo here breaks plugin registration silently, with no other
        # test in the suite catching it.
        assert IsPublishableCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target."
            "is_publishable"
        )
