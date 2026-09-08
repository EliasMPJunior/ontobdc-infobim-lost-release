from pathlib import Path
from typing import Any, Dict, List, Set, Type
from unittest.mock import Mock

from PIL import Image

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.loader import CapabilityLoader
from ontobdc.shared.adapter.draw import (
    DrawSourceStrategyLoader,
)
from ontobdc.shared.plugin.capability.logo_as_svg import (
    DrawLogoAsSvgCapability,
)
from ontobdc.shared.domain.model.draw import DrawSource
from ontobdc.shared.domain.port.draw import DrawSourceStrategyPort
from ontobdc.shared.plugin.strategy.draw.raster import (
    RasterDrawSourceStrategy,
)
from ontobdc.shared.plugin.strategy.draw.svg import (
    SvgDrawSourceStrategy,
)


def test_draw_source_strategies_are_auto_discovered() -> None:
    strategy_types: List[Type[DrawSourceStrategyPort]] = (
        DrawSourceStrategyLoader().get_all()
    )

    assert SvgDrawSourceStrategy in strategy_types
    assert RasterDrawSourceStrategy in strategy_types


def test_svg_strategy_resolves_source_from_content(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "logo.unknown"
    source_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 40"/>',
        encoding="utf-8",
    )

    strategy: DrawSourceStrategyPort = DrawSourceStrategyLoader().resolve(
        source_path
    )
    source: DrawSource = strategy.load(source_path)

    assert isinstance(strategy, SvgDrawSourceStrategy)
    assert source.source_format == "SVG"
    assert source.width == 80
    assert source.height == 40


def test_capability_draws_raster_logo_as_svg(tmp_path: Path) -> None:
    source_path: Path = tmp_path / "logo.data"
    target_path: Path = tmp_path / "output" / "logo.svg"
    image: Image.Image = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
    for x_coordinate in range(4, 28):
        for y_coordinate in range(4, 20):
            image.putpixel((x_coordinate, y_coordinate), (0, 180, 216, 255))
    image.save(source_path, format="PNG")

    context: Mock = Mock(spec=CliContextPort)
    context.get_parameter_value.side_effect = {
        "source_path": str(source_path),
        "target_path": str(target_path),
    }.get

    result: Dict[str, Any] = DrawLogoAsSvgCapability().execute(context)
    svg: str = target_path.read_text(encoding="utf-8")

    assert result["source_format"] == "PNG"
    assert result["source_strategy"] == "RasterDrawSourceStrategy"
    assert result["width"] == 32
    assert result["height"] == 24
    assert result["svg_path"] == str(target_path)
    assert "<svg" in svg
    assert "<path" in svg


def test_draw_logo_as_svg_capability_is_auto_discovered() -> None:
    capability_ids: Set[str] = {
        capability_type.METADATA.id
        for capability_type in CapabilityLoader().get_all()
    }

    assert DrawLogoAsSvgCapability.METADATA.id in capability_ids
