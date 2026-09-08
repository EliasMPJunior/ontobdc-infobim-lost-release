"""Tests for the shared ``I18nCatalogLoader`` adapter.

The annotation UI's translated labels now live under the ``ontobdc_view``
package (presentation layer). This suite reuses the view's locale files so
the loader contract keeps working against real YAML content instead of a
fake fixture.
"""

from __future__ import annotations

from typing import Dict, Tuple

from ontobdc.shared.adapter.i18n import (
    I18nCatalogLoader,
    LocaleCatalog,
    FullCatalog,
)


_VIEW_LOADER: I18nCatalogLoader = I18nCatalogLoader(
    package_name="ontobdc_view",
    resource_path=("component", "adapter", "i18n", "locale"),
)
_VIEW_LOCALES: Tuple[str, ...] = _VIEW_LOADER.supported_locales


def test_supported_locales_default() -> None:
    assert set(_VIEW_LOCALES) == {"en", "pt-BR", "pt-PT", "es"}
    assert I18nCatalogLoader.DEFAULT_LOCALE == "en"


def test_full_catalog_has_every_locale() -> None:
    catalog: FullCatalog = _VIEW_LOADER.full_catalog()
    assert set(catalog.keys()) == set(_VIEW_LOCALES)


def test_every_locale_has_the_same_keys_in_annotation_namespace() -> None:
    catalog: FullCatalog = _VIEW_LOADER.full_catalog()
    default = I18nCatalogLoader.DEFAULT_LOCALE
    base_keys = set(catalog[default]["annotation"].keys())
    for locale in _VIEW_LOCALES:
        keys = set(catalog[locale]["annotation"].keys())
        assert keys == base_keys, f"locale '{locale}' keys {keys} != {base_keys}"


def test_category_labels_and_tool_labels_are_nested_dicts_per_locale() -> None:
    annotation: LocaleCatalog = _VIEW_LOADER.catalog_for_namespace("annotation")
    for locale in _VIEW_LOCALES:
        assert set(annotation[locale]["categoryLabels"].keys()) == {
            "NoteAnnotation",
            "IssueAnnotation",
            "ClassificationAnnotation",
            "LocationAnnotation",
            "RecordAnnotation",
        }
        assert set(annotation[locale]["toolLabels"].keys()) == {
            "select",
            "point",
            "multiple-points",
            "bounding-box",
            "clear",
        }


def test_pt_br_and_pt_pt_are_distinct() -> None:
    merged_view: I18nCatalogLoader = I18nCatalogLoader(
        package_name="ontobdc_view",
        merge_common_namespace=True,
        fallback_namespace="common",
    )
    annotation = merged_view.catalog_for_namespace("annotation")
    assert annotation["pt-BR"]["timeline"] == "Linha do tempo"
    assert annotation["pt-PT"]["timeline"] == "Linha temporal"
    assert annotation["pt-BR"]["timeline"] != annotation["pt-PT"]["timeline"]


def test_merge_common_adds_shared_keys_to_namespace() -> None:
    merged_view: I18nCatalogLoader = I18nCatalogLoader(
        package_name="ontobdc_view",
        merge_common_namespace=True,
        fallback_namespace="common",
    )
    merged: LocaleCatalog = merged_view.catalog_for_namespace("language_tile")
    for locale in _VIEW_LOCALES:
        assert "open" in merged[locale], "common.open must be present in merge"
        assert "selectLanguage" in merged[locale], "language_tile key must be present"


def test_fallback_namespace_applies_for_unknown_namespace() -> None:
    merged_view: I18nCatalogLoader = I18nCatalogLoader(
        package_name="ontobdc_view",
        merge_common_namespace=True,
        fallback_namespace="common",
    )
    merged = merged_view.catalog_for_namespace("this-namespace-does-not-exist")
    expected_catalog: FullCatalog = merged_view.full_catalog()
    for locale in _VIEW_LOCALES:
        assert merged[locale] == expected_catalog[locale]["common"]


def test_plain_loader_returns_empty_dict_for_unknown_namespace() -> None:
    plain: I18nCatalogLoader = I18nCatalogLoader(package_name="infobim")
    result: LocaleCatalog = plain.catalog_for_namespace("definitely-does-not-exist")
    for locale in plain.supported_locales:
        assert result[locale] == {}
