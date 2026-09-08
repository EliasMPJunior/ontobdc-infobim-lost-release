import json
import re
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from ontobdc.view.domain.machine.surface_state import SurfaceGenerationProcessState
from ontobdc.view.plugin.check.surface_common import resolve_document, state_reached


SERVER_LAUNCHER_FILENAME = "server.cmd"
SERVER_REFERENCE_SCRIPT_ID = "ontobdc-server-reference"
DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 8080
DYNAMIC_PORT_MIN = 49152
DYNAMIC_PORT_MAX = 65535

_LAUNCHER_RE = re.compile(
    r"^ontobdc server --container \. --host (?P<host>\S+) --port (?P<port>\d+)$"
)
_SERVER_REFERENCE_RE = re.compile(
    rf"<script\b[^>]*\bid=[\"']{re.escape(SERVER_REFERENCE_SCRIPT_ID)}[\"'][^>]*>"
    rf"(?P<body>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_REFERENCE_JSON_RE = re.compile(
    r"const GENERATED = Object\.freeze\((?P<payload>\{.*?\})\);",
    re.DOTALL,
)


def launcher_lines(host: str, port: int) -> Tuple[str, ...]:
    return (
        "@echo off",
        'cd /d "%~dp0"',
        f"ontobdc server --container . --host {host} --port {int(port)}",
    )


def expected_launcher_text(host: str, port: int) -> str:
    return "\r\n".join(launcher_lines(host, port)) + "\r\n"


def read_launcher_reference(path: Path) -> Optional[Tuple[str, int]]:
    if not path.is_file():
        return None
    try:
        lines = tuple(path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return None
    if len(lines) != 3 or lines[:2] != launcher_lines(DEFAULT_SERVER_HOST, 1)[:2]:
        return None
    match = _LAUNCHER_RE.fullmatch(lines[2].strip())
    if match is None:
        return None
    try:
        port = int(match.group("port"))
    except ValueError:
        return None
    if not 1 <= port <= 65535:
        return None
    host = match.group("host").strip()
    if not host:
        return None
    return host, port


def generated_html_paths(surface: Path) -> Iterable[Path]:
    yielded = set()
    surface = surface.resolve()
    yielded.add(surface)
    yield surface

    marker = surface.parent / ".__ontobdc__"
    if not marker.is_dir():
        return
    for candidate in sorted(marker.rglob("*.html")):
        resolved = candidate.resolve()
        if resolved in yielded or not resolved.is_file():
            continue
        yielded.add(resolved)
        yield resolved


def extract_server_reference(document: str) -> Optional[Dict[str, object]]:
    script_match = _SERVER_REFERENCE_RE.search(document)
    if script_match is None:
        return None
    payload_match = _REFERENCE_JSON_RE.search(script_match.group("body"))
    if payload_match is None:
        return None
    try:
        payload = json.loads(payload_match.group("payload"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def main(surface_path: Optional[str] = None) -> int:
    try:
        surface, document = resolve_document(surface_path)
    except Exception:
        return 1

    if not state_reached(
        document,
        SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED,
    ):
        return 1

    launcher_path = surface.parent / SERVER_LAUNCHER_FILENAME
    reference = read_launcher_reference(launcher_path)
    if reference is None:
        return 1
    host, port = reference

    for html_path in generated_html_paths(surface):
        try:
            html = html_path.read_text(encoding="utf-8")
        except OSError:
            return 1
        server_reference = extract_server_reference(html)
        if server_reference is None:
            return 1
        if str(server_reference.get("host") or "") != host:
            return 1
        try:
            html_port = int(server_reference.get("port"))
        except (TypeError, ValueError):
            return 1
        if html_port != port:
            return 1

    return 0
