from importlib.resources import files
from pathlib import Path

import ontobdc_view.component.adapter.source as component_source
from infobim.view.adapter.component import InfoBIMComponentSourceAdapter


def test_infobim_brand_assets_are_package_resources() -> None:
    assets = files("infobim").joinpath("view", "plugin", "asset", "image")

    png = assets.joinpath("InfoBIMBrand.png").read_bytes()
    brand_svg = assets.joinpath("InfoBIMBrand.svg").read_text(encoding="utf-8")
    logotype_svg = assets.joinpath("InfoBIMLogotype.svg").read_text(encoding="utf-8")

    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in brand_svg[:512].lower()
    assert "<svg" in logotype_svg[:512].lower()


def test_infobim_surface_embeds_packaged_brand_without_network(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / ".__infobim__").mkdir()
    monkeypatch.setattr(component_source, "_candidate_brand_roots", lambda _: [tmp_path])

    scripts = InfoBIMComponentSourceAdapter().scripts(root_path=str(tmp_path))
    logo_source = next(
        source
        for source in scripts
        if 'customElements.define("onto-logo-tile"' in source
    )

    assert '"name":"InfoBIM"' in logo_source
    assert "InfoBIMBrand.svg" not in logo_source
    assert "<svg" in logo_source
