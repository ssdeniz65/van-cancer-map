"""Ham Excel'den toplulaştırılmış veri üretir.

Kullanım:
    python scripts/prep.py data/raw/VANKANSER-1.xlsx

Çıktılar:
    data/aggregated.json  -> haritanın kullandığı küp (ilçe × cinsiyet × 5 yıllık yaş grubu × yıl × tür → vaka)
    data/ilce_ozet.csv     -> ilçe bazında özet (vaka, nüfus, ham hız, en sık türler)

Ham veri (hasta düzeyinde kayıtlar) repoya girmez; data/raw/ .gitignore'dadır.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# TÜİK ADNKS 2017 (kadın, erkek) — İŞKUR Van İl İşgücü Piyasası Raporu 2017, Tablo 1
# MERKEZ = İpekyolu + Tuşba
POP_2017 = {
    "MERKEZ": (150028 + 75610, 150768 + 81107),
    "ERCİŞ": (83666, 89405),
    "EDREMİT": (62141, 62234),
    "ÖZALP": (32690, 33805),
    "BAŞKALE": (25027, 26946),
    "ÇALDIRAN": (30853, 32750),
    "MURADİYE": (24547, 26168),
    "GÜRPINAR": (17267, 17888),
    "GEVAŞ": (13880, 13683),
    "ÇATAK": (9909, 10787),
    "SARAY": (10086, 10886),
    "BAHÇESARAY": (7363, 7395),
}
PERIOD = (2013, 2018)


def tr_upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def main(xlsx: str) -> None:
    d = pd.read_excel(xlsx)
    d["İLÇE"] = d["İLÇE"].astype(str).str.strip().map(tr_upper)
    d["TOPOLOJİ"] = d["TOPOLOJİ"].astype(str).str.strip().str.lower()
    d["yil"] = pd.to_datetime(d["TARİH"]).dt.year
    d["sex"] = (d["CİNSİYET"].str.upper() == "ERKEK").astype(int)  # 0 kadın, 1 erkek
    d["agebin"] = (d["YAŞ"].clip(upper=90) // 5 * 5).astype(int)  # 0,5,...,90 (90 = 90+)

    unknown = set(d["İLÇE"]) - set(POP_2017)
    if unknown:
        raise SystemExit(f"Nüfusu tanımsız ilçe(ler): {unknown}")

    districts = d["İLÇE"].value_counts().index.tolist()
    types = d["TOPOLOJİ"].value_counts().index.tolist()

    cube = (
        d.groupby(["İLÇE", "sex", "agebin", "yil", "TOPOLOJİ"]).size().reset_index(name="n")
    )
    rows = [
        [districts.index(r["İLÇE"]), int(r["sex"]), int(r["agebin"]), int(r["yil"]),
         types.index(r["TOPOLOJİ"]), int(r["n"])]
        for _, r in cube.iterrows()
    ]
    out = {"districts": districts, "types": types,
           "fields": ["district", "sex", "agebin", "year", "type", "n"], "cube": rows}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/aggregated.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    years = PERIOD[1] - PERIOD[0] + 1
    per = d[d["yil"].between(*PERIOD)]
    summ = []
    for name in districts:
        sub = d[d["İLÇE"] == name]
        pop = sum(POP_2017[name])
        top = sub["TOPOLOJİ"].value_counts().head(3)
        summ.append({
            "ilce": name,
            "nufus_2017": pop,
            "vaka": len(sub),
            "vaka_2013_2018": int((per["İLÇE"] == name).sum()),
            "ham_hiz_100bin_yil": round((per["İLÇE"] == name).sum() / (pop * years) * 1e5, 1),
            "kadin": int((sub["sex"] == 0).sum()),
            "erkek": int((sub["sex"] == 1).sum()),
            "en_sik_3_tur": "; ".join(f"{t} ({n})" for t, n in top.items()),
        })
    pd.DataFrame(summ).to_csv(ROOT / "data/ilce_ozet.csv", index=False, encoding="utf-8-sig")
    print(f"{len(d)} kayıt → {len(rows)} küp hücresi; {len(districts)} ilçe, {len(types)} tür")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
