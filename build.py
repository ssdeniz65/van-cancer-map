"""Haritayı tek dosyalık docs/index.html olarak üretir.

Kullanım:
    python scripts/build.py

Girdiler: src/template.html, data/aggregated.json, geo/provinces.json, geo/lakes.json
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> None:
    html = read("src/template.html")
    for marker, rel in {
        "/*DATA*/": "data/aggregated.json",
        "/*PROV*/": "geo/provinces.json",
        "/*LAKES*/": "geo/lakes.json",
    }.items():
        if html.count(marker) != 1:
            raise SystemExit(f"Şablonda {marker} işareti bulunamadı")
        html = html.replace(marker, read(rel).strip())
    out = ROOT / "docs/index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{out.relative_to(ROOT)} yazıldı ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
