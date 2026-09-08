from __future__ import annotations

from pathlib import Path
from typing import ClassVar, List, Tuple

import pytest
from playwright.sync_api import Page, expect

from ontobdc_view.component.adapter.preview import (
    CASES,
    TilePreviewCase,
    TileStandaloneHtmlBuilder,
)


class TestStandaloneTiles:
    CASES: ClassVar[Tuple[TilePreviewCase, ...]] = CASES

    @pytest.mark.parametrize(
        "case",
        CASES,
        ids=tuple(case.tag for case in CASES),
    )
    def test_tile_renders_alone_in_temporary_html(
        self,
        case: TilePreviewCase,
        page: Page,
        tmp_path: Path,
        request: pytest.FixtureRequest,
    ) -> None:
        repository_root: Path = Path(__file__).resolve().parents[2]
        builder = TileStandaloneHtmlBuilder(repository_root)
        if not builder.is_migrated(case.tag):
            pytest.skip(
                f"{case.tag} has not been migrated out of old/ yet -- "
                "old/ is not tested."
            )
        theme: str = str(request.config.getoption("--theme"))
        html_path: Path = builder.write(
            case=case,
            theme=theme,
            output_path=tmp_path / f"{case.tag}.html",
        )
        page_errors: List[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        page.goto(
            f"{html_path.as_uri()}?lang=en&theme={theme}",
            wait_until="load",
        )
        page.wait_for_function(
            "tag => Boolean(customElements.get(tag))",
            arg=case.tag,
        )

        tile = page.locator(case.tag)
        expect(tile).to_have_count(1)
        expect(tile).to_be_visible()
        bounding_box = tile.bounding_box()
        assert bounding_box is not None
        assert bounding_box["width"] > 0
        assert bounding_box["height"] > 0
        assert page.locator("#tile-preview > *").count() == 1
        assert page_errors == []
