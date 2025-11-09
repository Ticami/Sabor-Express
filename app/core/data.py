from __future__ import annotations

import csv
from io import StringIO
from typing import Dict, Iterable, List


CANON_COLS = ["id", "nome", "endereco", "latitude", "longitude", "selecionado"]

COL_SYNONYMS: Dict[str, Iterable[str]] = {
    "id": ["id", "codigo", "código", "idx"],
    "nome": ["nome", "cliente", "ponto", "name"],
    "endereco": ["endereco", "endereço", "address", "rua"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng", "long"],
    "selecionado": ["selecionado", "selecionar", "selected", "ativo"],
}


def _coerce_bool(v: str) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "t", "yes", "y", "sim"}


def _coerce_float(v: str):
    try:
        return float(v)
    except Exception:
        return None


def _coerce_int(v: str):
    try:
        return int(float(v))
    except Exception:
        return None


def read_points_csv(content: bytes | str) -> List[Dict]:
    if isinstance(content, bytes):
        text = content.decode("utf-8", errors="ignore")
    elif isinstance(content, str):
        text = content
    else:
        raise TypeError("Unsupported content type for CSV")

    f = StringIO(text)
    reader = csv.DictReader(f)
    lower_cols = {c.lower().strip(): c for c in reader.fieldnames or []}
    mapping: Dict[str, str] = {}
    for canon, synonyms in COL_SYNONYMS.items():
        for s in synonyms:
            if s in lower_cols:
                mapping[lower_cols[s]] = canon
                break

    rows: List[Dict] = []
    for raw in reader:
        row = {c: None for c in CANON_COLS}
        for k, v in raw.items():
            key = mapping.get(k, None)
            if key is None:
                continue
            row[key] = v
        row["id"] = _coerce_int(row.get("id"))
        row["nome"] = (row.get("nome") or "").strip()
        row["endereco"] = (row.get("endereco") or "").strip()
        row["latitude"] = _coerce_float(row.get("latitude"))
        row["longitude"] = _coerce_float(row.get("longitude"))
        row["selecionado"] = _coerce_bool(row.get("selecionado")) if row.get("selecionado") is not None else False
        rows.append(row)
    return rows


def to_csv_bytes_from_rows(rows: List[Dict], headers: List[str]) -> bytes:
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return out.getvalue().encode("utf-8")


def to_csv_bytes(df_like) -> bytes:
    if isinstance(df_like, list):
        headers = list(df_like[0].keys()) if df_like else []
        return to_csv_bytes_from_rows(df_like, headers)
    out = StringIO()
    df_like.to_csv(out, index=False) 
    return out.getvalue().encode("utf-8")


def template_points() -> List[Dict]:
    return [
        {"id": 1, "nome": "Cliente A", "endereco": "Rua Exemplo 100", "latitude": -23.55052, "longitude": -46.63331, "selecionado": True},
        {"id": 2, "nome": "Cliente B", "endereco": "Av. Central 200", "latitude": -23.55900, "longitude": -46.63500, "selecionado": True},
        {"id": 3, "nome": "Cliente C", "endereco": "Rua das Flores 300", "latitude": -23.56250, "longitude": -46.64020, "selecionado": False},
    ]
