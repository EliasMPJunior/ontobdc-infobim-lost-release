"""The Listener plugin contract.

A Listener is the architectural correlate of a Command: a discovered
plugin that receives an occurrence and produces a response, rather than a
CLI verb that receives arguments. It follows the same conventions every
other OntoBDC plugin resource follows --

* it lives under ``<domain>/plugin/<resource>/``, here
  ``ontobdc_web_dock/dock/plugin/listener/``;
* it declares a class-level ``METADATA`` carrying the same fields
  ``CapabilityMetadata`` / ``CliCommandMetadata`` carry;
* it is found by walking that package, never by an import list.

``ListenerMetadata`` is a ``dataclass`` rather than a
``pydantic.BaseModel`` only because this contract executes inside
Pyodide, where pydantic is not part of the runtime. The field set is
deliberately the same so a Listener's metadata reads identically to a
Capability's.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ListenerMetadata:
    id: str
    version: str
    name: str
    description: str
    author: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    log_message: Dict[str, Dict[str, str]] = field(default_factory=dict)


class ListenerPort:
    """What every dDock Listener plugin implements.

    Not a Command in disguise: a Command's contract is
    ``accepts(args) -> check() -> run()``; a Listener's is
    ``listens_to() -> handle(envelope)``. There is no ``check()`` step --
    a Listener never validates an argument vector, it reacts to an
    occurrence that already happened.
    """

    METADATA: ListenerMetadata

    def listens_to(self) -> str:
        """The occurrence family this Listener answers for."""
        raise NotImplementedError

    def handle(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Answer one occurrence envelope with a dDock response."""
        raise NotImplementedError
