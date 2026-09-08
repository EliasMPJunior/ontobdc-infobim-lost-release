import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/Users/eliasmpjunior/Brasidata/07_Engenharia_e_Tecnologia/06_Solucoes_Reutilizaveis/OntoBDC")
INFObim_BIN = ROOT / ".venv" / "bin" / "infobim"

result = subprocess.run(
    [str(INFObim_BIN), "view", "--project", "3GqWHHIVfD_uF$f$TSbZi6"],
    capture_output=True,
    text=True,
    cwd=str(ROOT),
    timeout=180,
    env={
        **__import__("os").environ,
        "VIRTUAL_ENV": str(ROOT / ".venv"),
        "PATH": f"{ROOT / '.venv' / 'bin'}:{__import__('os').environ.get('PATH', '')}",
    },
)
print("stdout tail:")
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.stderr:
    print("stderr tail:")
    print(result.stderr[-1200:] if len(result.stderr) > 1200 else result.stderr)
print(f"exit code: {result.returncode}")
assert result.returncode == 0, f"comando infobim view falhou: {result.returncode}"

# Encontrar index.html gerado
project_root = ROOT / "feature" / "3GqWHHIVfD_uF$f$TSbZi6"
view_output = None
for cand in project_root.rglob("index.html"):
    text = cand.read_text(errors="ignore")
    if "const BRAND" in text:
        view_output = cand
        break
if view_output is None:
    print("ERROR: nenhum index.html com const BRAND encontrado em ", project_root)
    raise SystemExit(1)
print(f"HTML: {view_output}")
html = view_output.read_text()
m = re.search(r"const BRAND = (\{.*?\});\s*\n", html, re.S)
if not m:
    print("ERROR: const BRAND não encontrado no HTML")
    raise SystemExit(2)
brand_raw = m.group(1)
try:
    brand = json.loads(brand_raw)
except json.JSONDecodeError:
    import ast
    brand = ast.literal_eval(brand_raw)

print(f"\n=== VALIDAÇÃO FINAL BRAND NO HTML ===")
print(f"  name         : {brand.get('name')!r}")
print(f"  slogan       : {brand.get('slogan')!r}")
mark_len = len(brand.get("mark_svg", ""))
logo_len = len(brand.get("logotype_svg", ""))
print(f"  mark_svg len : {mark_len}")
print(f"  logotype len : {logo_len}")
mark = brand.get("mark_svg", "")
logo = brand.get("logotype_svg", "")
tem_circulo_placeholder = "<circle" in mark and len(mark) < 10000 and "InfoBIMBrand" not in mark
tem_onto_texto = "OntoBDC</text>" in logo
tem_infobim_root = "InfoBIMBrand" in mark[:300]
print(f"  marca é círculo velho placeholder?: {tem_circulo_placeholder}")
print(f"  logotipo tem 'OntoBDC</text>' (placeholder velho)?: {tem_onto_texto}")
print(f"  marca tem InfoBIMBrand header?: {tem_infobim_root}")
print()
ok = (
    brand.get("name") == "InfoBIM"
    and mark_len >= 5000
    and logo_len >= 25000
    and not tem_circulo_placeholder
    and not tem_onto_texto
)
print(f"✅ Validação passa? {ok}")
assert ok, "Validação falhou: regressão na logo InfoBIM"
