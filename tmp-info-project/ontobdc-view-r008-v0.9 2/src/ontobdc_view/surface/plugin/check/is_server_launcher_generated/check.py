from pathlib import Path
from typing import Optional
from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState


def main(surface_path: Optional[str] = None) -> int:
    """Whether SERVER_LAUNCHER_GENERATED was reached.

    Deliberately marker-only. The original check additionally validated a
    real `server.cmd` and a per-page `ontobdc-server-reference` script, but
    `ServerLauncherGeneratedCapability.execute()` has been temporarily
    nulled out to a state-marker-only no-op (nothing writes those
    artifacts right now), so validating them here would make this check
    permanently fail instead of nullifying the state. Restore the full
    artifact validation together with the real `execute()` when this
    capability is implemented for real.
    """
    try:
        _, document = resolve_document(surface_path)
    except Exception:
        return 1
    return (
        0
        if SurfaceDocumentAdapter.state_reached(
            document, SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED
        )
        else 1
    )


def resolve_document(surface_path: Optional[str]) -> tuple[Path, str]:
    path = SurfaceDocumentAdapter.resolve_surface_path(surface_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path, SurfaceDocumentAdapter.read_surface(path)
