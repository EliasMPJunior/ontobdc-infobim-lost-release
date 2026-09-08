"""The surface statechart and the state enum must agree: a state added to one
and not the other leaves generation stuck mid-pipeline at runtime."""
from pathlib import Path

import pytest

from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc.view.adapter.surface.machine import _capability_type_for_state
from ontobdc.view.domain.machine.surface_state import SurfaceGenerationProcessState

STATECHART = (
    Path(__file__).resolve().parents[4]
    / "src/ontobdc/view/domain/machine/standard_surface_html.yaml"
)


class RecordingHandler:
    """Accepts every transition the chart proposes and records the order."""

    def __init__(self):
        self.performed = []
        self._state = SurfaceGenerationProcessState.UNDEFINED

    @property
    def current_state(self):
        return self._state

    @property
    def state_sequence(self):
        return list(SurfaceGenerationProcessState)

    def can_transit_to(self, to_state):
        sequence = self.state_sequence
        return sequence.index(self._state) + 1 == sequence.index(to_state)

    def perform_state_transition(self, to_state):
        self.performed.append(to_state)
        self._state = to_state

    def validate_state_transition(self, from_state, to_state):
        return bool(self.performed) and self.performed[-1] is to_state

    def bind_active_state(self, state):
        self._state = state


class NullLogger:
    def log_info(self, *args, **kwargs): ...
    def log_warning(self, *args, **kwargs): ...
    def log_error(self, *args, **kwargs): ...
    def log_debug(self, *args, **kwargs): ...


@pytest.fixture
def walked_states():
    handler = RecordingHandler()
    StateWorkerAdapter(
        state_adapter=SurfaceGenerationProcessState,
        state_context_name="SurfaceGenerationProcessStatePort",
        handler=handler,
        logger=NullLogger(),
        statechart_file_path=STATECHART,
    ).work()
    return handler.performed


def test_statechart_walks_every_declared_state_in_order(walked_states):
    assert walked_states == list(SurfaceGenerationProcessState)[1:]


def test_parameters_are_ensured_between_assembly_and_packaging(walked_states):
    assembled = walked_states.index(SurfaceGenerationProcessState.SURFACE_ASSEMBLED)
    ensured = walked_states.index(
        SurfaceGenerationProcessState.SURFACE_PARAMETERS_ENSURED
    )
    packaged = walked_states.index(SurfaceGenerationProcessState.SURFACE_PACKAGED)
    assert assembled < ensured < packaged


@pytest.mark.parametrize(
    "state",
    [
        state
        for state in SurfaceGenerationProcessState
        if state is not SurfaceGenerationProcessState.UNDEFINED
    ],
    ids=lambda state: state.name,
)
def test_every_state_resolves_to_a_registered_capability(state):
    assert _capability_type_for_state(state) is not None


@pytest.mark.parametrize(
    "state",
    list(SurfaceGenerationProcessState),
    ids=lambda state: state.name,
)
def test_every_state_is_labelled_in_both_catalogs(state):
    assert state.label("en") != state.value
    assert state.label("pt-br") != state.value
    assert state.description("en")
    assert state.description("pt-br")
