#!/usr/bin/env python3
"""Aggiorna prices.json con i prezzi benzina (Euro-Super 95, EUR/litro).

Fonti gratuite:
 - Italia: open data MIMIT (giornaliero) -> media nazionale benzina self service
 - Paesi UE: fuel-prices.eu (tabella settimanale dal Bollettino Petrolifero UE)
 - Norvegia e Svizzera: nessuna fonte gratuita affidabile -> restano gli ultimi
   valori presenti in prices.json (correggili a mano nel sito quando serve).

Se una fonte non risponde, i valori precedenti vengono mantenuti:
il sito non resta mai senza dati.

Dipendenze: requests
"""
import csv
import datetime
import io
import json
import os
import re

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "prices.json")   # prices.json nella root del repo
UA = {"User-Agent": "caponord-prezzi (github action)"}


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"prices": {}}


data = load()
prices = dict(data.get("prices", {}))     # partiamo dai valori esistenti
sources = {}


def set_price(code, val, src):
    try:
        val = float(val)
    except Exception:
        return False
    if 0.5 < val < 4.0:
        prices[code] = round(val, 3)
        sources[code] = src
        print(f"  {code}: {val:.3f} EUR/L  ({src})")
        return True
    return False


# ---------------------------------------------------------------------------
# ITALIA — MIMIT, prezzi comunicati alle 8 (delimitatore "|", non ";")
# colonne: idImpianto | descCarburante | prezzo | isSelf | dtComu
# ---------------------------------------------------------------------------
MIMIT_URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
it_done = False
print("Italia (MIMIT)…")
try:
    r = requests.get(MIMIT_URL, timeout=120, headers=UA)
    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    tot = 0.0
    n = 0
    for row in csv.reader(io.StringIO(r.text), delimiter="|"):
        # salta intestazioni e righe corte
        if len(row) < 4:
            continue
        if row[1].strip().lower() == "benzina" and row[3].strip() == "1":
            try:
                v = float(row[2].replace(",", "."))
            except ValueError:
                continue
            if 1.0 < v < 3.0:          # scarta refusi/valori impossibili
                tot += v
                n += 1
    if n > 1000:
        it_done = set_price("IT", tot / n, f"MIMIT media su {n} impianti self")
    else:
        print(f"  IT: solo {n} righe valide (attese >1000): mantengo il valore precedente")
except Exception as e:
    print("  IT: fonte non raggiungibile:", e)


# ---------------------------------------------------------------------------
# PAESI UE — fuel-prices.eu, tabella "| Country | Petrol (€/L) | Diesel |"
# (dati dal Bollettino Petrolifero settimanale della Commissione Europea)
# ---------------------------------------------------------------------------
EU_URL = "https://www.fuel-prices.eu/weekly/llms.txt"
NAME2CODE = {
    "italy": "IT", "germany": "DE", "denmark": "DK", "sweden": "SE",
    "finland": "FI", "estonia": "EE", "latvia": "LV", "lithuania": "LT",
    "poland": "PL",
}
EU_WANTED = {"DE", "DK", "SE", "FI", "EE", "LV", "LT", "PL"}
print("Paesi UE (fuel-prices.eu)…")
try:
    r = requests.get(EU_URL, timeout=60, headers=UA)
    r.raise_for_status()
    table = {}
    for line in r.text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name = cells[0].lower().replace("*", "").replace("**", "").strip()
        code = NAME2CODE.get(name)
        if not code:
            continue
        m = re.search(r"[\d]+[.,]\d+", cells[1])   # es. "€1.910"
        if m:
            table[code] = float(m.group(0).replace(",", "."))
    for code in EU_WANTED:
        if code in table:
            set_price(code, table[code], "Bollettino UE via fuel-prices.eu")
    # Italia di riserva: solo se MIMIT non ha risposto
    if not it_done and "IT" in table:
        set_price("IT", table["IT"], "fuel-prices.eu (riserva, MIMIT KO)")
    if not table:
        print("  UE: tabella non riconosciuta, mantengo i valori precedenti")
except Exception as e:
    print("  UE: fonte non raggiungibile:", e)


# ---------------------------------------------------------------------------
# Norvegia e Svizzera: nessuna fonte automatica gratuita.
# Restano i valori già presenti in prices.json (nessuna azione = li conserviamo).
# ---------------------------------------------------------------------------
for code in ("NO", "CH"):
    if code in prices and code not in sources:
        sources[code] = data.get("sources", {}).get(code, "manuale (sito)")


# ---------------------------------------------------------------------------
# salva
# ---------------------------------------------------------------------------
out = {
    "updated": datetime.date.today().isoformat(),
    "prices": prices,
    "sources": sources or data.get("sources", {}),
    "note": ("Benzina 95 in EUR/L, tasse incluse. IT: MIMIT giornaliero; "
             "UE: Bollettino settimanale via fuel-prices.eu; "
             "NO e CH senza fonte automatica gratuita: correggili a mano nel sito."),
}
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("Salvato prices.json:", out["updated"], "-", len(prices), "paesi")
