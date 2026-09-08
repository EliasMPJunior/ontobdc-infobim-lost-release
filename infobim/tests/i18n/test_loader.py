"""i18n locale catalog tests for InfoBIM's own view Tiles."""

from __future__ import annotations

from infobim.view.adapter.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, catalog_for_namespace, full_catalog


def test_supported_locales():
    assert set(SUPPORTED_LOCALES) == {"en", "pt-BR", "pt-PT", "es"}
    assert DEFAULT_LOCALE == "en"


def test_full_catalog_has_every_locale():
    catalog = full_catalog()
    assert set(catalog.keys()) == set(SUPPORTED_LOCALES)


def test_every_locale_has_the_same_keys_per_namespace():
    catalog = full_catalog()
    namespaces = set()
    for locale_catalog in catalog.values():
        namespaces |= set(locale_catalog.keys())

    for namespace in namespaces:
        base_keys = set(catalog[DEFAULT_LOCALE].get(namespace, {}).keys())
        for locale in SUPPORTED_LOCALES:
            keys = set(catalog[locale].get(namespace, {}).keys())
            assert keys == base_keys, (
                f"locale '{locale}' namespace '{namespace}' keys {keys} "
                f"!= default-locale keys {base_keys}"
            )


def test_project_tile_pt_br_and_pt_pt_are_distinct():
    catalog = catalog_for_namespace("project_tile")
    assert catalog["pt-BR"]["indexedFilesLabel"] == "Arquivos indexados"
    assert catalog["pt-PT"]["indexedFilesLabel"] == "Ficheiros indexados"
