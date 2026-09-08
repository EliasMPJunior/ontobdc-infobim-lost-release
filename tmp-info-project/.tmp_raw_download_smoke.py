from pathlib import Path
import tempfile
from ontobdc.view.plugin.capability.transformation.surface_branded import (
    SurfaceBrandedCapability,
    _PRODUCT_SPECS,
    _iter_urls,
)
import infobim  # noqa: F401 -- side-effect: registers infobim

SPEC = _PRODUCT_SPECS["infobim"]
for role, k in (("brand", "brand_urls"), ("logotype", "logotype_urls")):
    urls = _iter_urls(SPEC[k])
    print(f"== {role}: testando _download_raw com {len(urls)} URLs ==")
    try:
        payload, source = SurfaceBrandedCapability._download_raw(urls)
        print(f"  OK: {len(payload)} bytes from {source}")
        print(f"  <svg no payload? {b'<svg' in payload[:512].lower()}")
    except Exception as exc:
        print(f"  FAIL: {type(exc).__name__}: {exc}")

print()
print("== Teste 3-tier com paths vazios (força download) ==")
with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
    container = Path(t1)
    workspace = Path(t2)
    relative = Path(".__infobim__") / "assets" / "InfoBIMLogotype.svg"
    urls = _iter_urls(SPEC["logotype_urls"])
    try:
        path, src = SurfaceBrandedCapability._resolve_svg(
            container_root=container,
            workspace_root=workspace,
            relative_path=relative,
            candidate_urls=urls,
        )
        print(f"  path resolvido: {path}")
        print(f"  source        : {src}")
        print(f"  arquivo existe: {path.is_file()}")
        print(f"  tamanho       : {path.stat().st_size}")
        print(f"  começa com <svg: {b'<svg' in path.read_bytes()[:512].lower()}")
    except Exception as exc:
        print(f"  FAIL: {type(exc).__name__}: {exc}")
