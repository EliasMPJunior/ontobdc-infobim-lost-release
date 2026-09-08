from abc import ABC, abstractmethod

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.response.command import CommandResponse


class EntityPageGenerationDataTransitionHandlerPort(ABC):
    @abstractmethod
    def __init__(self, context: CliContextPort) -> None:
        ...

    @abstractmethod
    def execute(self) -> CommandResponse:
        ...
