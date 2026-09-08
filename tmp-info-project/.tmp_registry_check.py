from ontobdc.view.plugin.capability.transformation.surface_branded import _PRODUCT_SPECS
print("antes de importar infobim:", sorted(_PRODUCT_SPECS.keys()))
import infobim
from ontobdc.view.plugin.capability.transformation.surface_branded import _PRODUCT_SPECS as spec2
print("depois de importar infobim:", sorted(spec2.keys()))
print()
print(
    "InfoBIM spec tem brand_urls e logotype_urls:",
    "brand_urls" in spec2.get("infobim", {}),
    "logotype_urls" in spec2.get("infobim", {}),
)
print("URLs marca InfoBIM (primeira cada):")
for k in ("brand_urls", "logotype_urls"):
    val = spec2["infobim"][k]
    first = val.splitlines()[0] if val else ""
    print(f"  {k}: {first}")
print()
print(
    "OntoBDC NÃO TEM entrada infobim hardcoded (acoplamento removido?):",
    "infobim" not in {"ontobdc"},
    "-> infobim só entrou depois de importar o infobim"
)
