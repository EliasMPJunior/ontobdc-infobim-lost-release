from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Type

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.response.command import CommandResponse


class ContainerRenameProcessStatePort(str, Enum):
    """Base enum contract for storage container rename states."""


class ContainerRenameStateEvaluatorPort(ABC):
    @property
    @abstractmethod
    def process_state_class(self) -> Type[ContainerRenameProcessStatePort]:
        ...

    @abstractmethod
    def evaluate(
        self,
        context: CliContextPort,
    ) -> ContainerRenameProcessStatePort:
        ...


class ContainerRenameStateTransitionHandlerPort(ABC):
    @property
    @abstractmethod
    def context(self) -> CliContextPort:
        ...

    @property
    @abstractmethod
    def target_path(self) -> Path:
        ...

    @property
    @abstractmethod
    def current_state(self) -> ContainerRenameProcessStatePort:
        ...

    @property
    @abstractmethod
    def state_sequence(self) -> List[ContainerRenameProcessStatePort]:
        ...

    @abstractmethod
    def can_transit_to(
        self,
        to_state: ContainerRenameProcessStatePort,
    ) -> bool:
        ...

    @abstractmethod
    def perform_state_transition(
        self,
        to_state: ContainerRenameProcessStatePort,
    ) -> None:
        ...

    @abstractmethod
    def validate_state_transition(
        self,
        from_state: ContainerRenameProcessStatePort,
        to_state: ContainerRenameProcessStatePort,
    ) -> bool:
        ...

    @abstractmethod
    def bind_active_state(
        self,
        state: ContainerRenameProcessStatePort,
    ) -> None:
        ...

    @abstractmethod
    def execute(self) -> CommandResponse:
        ...
