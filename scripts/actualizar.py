"""Actualiza docs/data/externos.json con fuentes públicas.

Corre en GitHub Actions cada semana. Usa solo la librería estándar de Python.
Si una fuente falla, conserva el dato anterior y deja un aviso.
"""
import csv
import datetime as dt
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SALIDA = ROOT / "docs" / "data" / "externos.json"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

try:
    anterior = json.loads(SALIDA.read_text(encoding="utf-8"))
except Exception:
    anterior = {"fuentes": {}}

out = {
    "actualizado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "fuentes": dict(anterior.get("fuentes", {})),
    "avisos": [],
}


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "laboratorio-demanda", **(headers or {})})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8-sig"))


# --- INEGI DENUE: número de tiendas por estado ---
tok = os.environ.get("DENUE_TOKEN", "").strip()
if not tok:
    out["avisos"].append("DENUE: falta el secreto DENUE_TOKEN; se conserva el dato anterior.")
else:
    try:
        acts = ",".join(CFG["denue_actividades"])
        areas = ",".join(f"{i:02d}" for i in range(1, 33))
        data = get_json(f"https://www.inegi.org.mx/app/api/denue/v1/consulta/Cuantificar/{acts}/{areas}/0/{tok}")
        sumas = {}
        for r in data:
            ag = str(r.get("AG", "")).strip().zfill(2)[:2]
            total = int(float(str(r.get("Total") or 0).replace(",", "")))
            sumas[ag] = sumas.get(ag, 0) + total
        filas = [{"estado": int(k), "tiendas": v, "actividad": acts} for k, v in sorted(sumas.items()) if k.isdigit() and 1 <= int(k) <= 32]
        if len(filas) < 30:
            raise ValueError(f"solo llegaron {len(filas)} estados")
        out["fuentes"]["tiendas"] = {"fuente": "INEGI DENUE", "rows": filas}
        print(f"DENUE: {sum(sumas.values()):,} tiendas en {len(filas)} estados")
    except Exception as e:
        out["avisos"].append(f"DENUE: no se pudo actualizar ({e}); se conserva el dato anterior.")

# --- Banxico SIE: gasto con tarjeta nacional ---
btok = os.environ.get("BANXICO_TOKEN", "").strip()
series = [s.strip() for s in CFG.get("banxico_series", []) if s.strip()]
if not series:
    out["avisos"].append("Banxico: no hay claves de serie en config.json.")
elif not btok:
    out["avisos"].append("Banxico: falta el secreto BANXICO_TOKEN; se conserva el dato anterior.")
else:
    try:
        fin = dt.date.today()
        ini = fin.replace(year=fin.year - int(CFG.get("banxico_anios", 3)))
        url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{','.join(series)}/datos/{ini}/{fin}"
        data = get_json(url, {"Bmx-Token": btok, "Accept": "application/json"})
        por_fecha = {}
        for s in data["bmx"]["series"]:
            for d in s.get("datos", []) or []:
                try:
                    v = float(str(d["dato"]).replace(",", ""))
                except ValueError:
                    continue
                por_fecha[d["fecha"]] = por_fecha.get(d["fecha"], 0.0) + v
        if not por_fecha:
            raise ValueError("la serie llegó vacía")
        out["fuentes"]["gastoNacional"] = {"fuente": "Banxico SIE", "rows": [{"fecha": f, "valor": v} for f, v in por_fecha.items()]}
        print(f"Banxico: {len(por_fecha)} observaciones")
    except Exception as e:
        out["avisos"].append(f"Banxico: no se pudo actualizar ({e}); se conserva el dato anterior.")

# --- Archivos manuales (fuentes sin API) ---
MANUALES = {
    "poblacion.csv": ("poblacion", "Censo / ENIGH"),
    "gasto_estatal.csv": ("gastoEstatal", "BBVA Research"),
    "clima.csv": ("clima", "SMN"),
}
for nombre, (tipo, fuente) in MANUALES.items():
    p = ROOT / "datos_manuales" / nombre
    if not p.exists():
        continue
    with p.open(encoding="utf-8-sig", newline="") as f:
        filas = [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]
    if filas:
        out["fuentes"][tipo] = {"fuente": fuente, "rows": filas}
        print(f"{nombre}: {len(filas)} filas")
    elif tipo in out["fuentes"]:
        del out["fuentes"][tipo]

SALIDA.parent.mkdir(parents=True, exist_ok=True)
SALIDA.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
for a in out["avisos"]:
    print("AVISO:", a)
