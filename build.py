"""Haritayı tek dosyalık index.html olarak üretir.

Kullanım:
    python build.py

Girdiler: template.html, aggregated.json, provinces.json, lakes.json (hepsi repo kökünde)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> None:
    html = read("template.html")
    for marker, rel in {
        "/*DATA*/": "aggregated.json",
        "/*PROV*/": "provinces.json",
        "/*LAKES*/": "lakes.json",
    }.items():
        if html.count(marker) != 1:
            raise SystemExit(f"Şablonda {marker} işareti bulunamadı")
        html = html.replace(marker, read(rel).strip())
    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"{out.relative_to(ROOT)} yazıldı ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
