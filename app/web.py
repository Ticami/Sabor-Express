from __future__ import annotations

import base64
import os
import sys
from io import BytesIO
from typing import List, Tuple

import requests
from flask import Flask, render_template, request, send_file, redirect, url_for, make_response

try:
    from app.core.data import read_points_csv, template_points, to_csv_bytes_from_rows, to_csv_bytes
    from app.core.geo import distance_matrix, estimate_time_minutes, route_distance_km
    from app.core.optimizer import solve_tsp_cycle
    from app.ui.components import make_graph_figure, make_route_map
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from app.core.data import read_points_csv, template_points, to_csv_bytes_from_rows, to_csv_bytes
    from app.core.geo import distance_matrix, estimate_time_minutes, route_distance_km
    from app.core.optimizer import solve_tsp_cycle
    from app.ui.components import make_graph_figure, make_route_map

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "enderecos.csv")
app = Flask(__name__, template_folder=TEMPLATES_DIR)


def _default_csv_text() -> str:
    try:
        return to_csv_bytes(template_points()).decode("utf-8")
    except Exception:
        rows = template_points()
        if not rows:
            return "id,nome,endereco,latitude,longitude,selecionado\n"
        headers = list(rows[0].keys())
        out = [",".join(headers)]
        for r in rows:
            out.append(
                ",".join(str(r.get(h, "")) for h in headers)
            )
        return "\n".join(out)


@app.route("/", methods=["GET"]) 
def index():
    rows = template_points()
    try:
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, "rb") as f:
                rows = read_points_csv(f.read())
    except Exception:
        rows = template_points()
    try:
        default_speed = int(request.args.get("speed") or request.cookies.get("speed") or 30)
    except Exception:
        default_speed = 30
    return render_template(
        "index.html",
        rows=rows,
        default_name="Sabor Express",
        default_lat=-23.55052,
        default_lon=-46.63331,
        default_speed=default_speed,
    )


@app.route("/optimize", methods=["POST"]) 
def optimize():
    rname = request.form.get("restaurant_name", "Sabor Express")
    rlat = float(request.form.get("restaurant_lat", "-23.55052"))
    rlon = float(request.form.get("restaurant_lon", "-46.63331"))
    raddr = request.form.get("restaurant_addr", "").strip()
    speed_str = str(request.form.get("speed", "30")).strip().replace(",", ".")
    try:
        speed = float(speed_str)
    except Exception:
        speed = 30.0
    csv_text = request.form.get("csv_text", _default_csv_text())
    roads = request.form.get("roads") is not None

    try:
        points = read_points_csv(csv_text)
    except Exception as e:
        return render_template(
            "index.html",
            rows=rows if 'rows' in locals() else template_points(),
            default_name=rname,
            default_lat=rlat,
            default_lon=rlon,
            default_speed=int(speed),
            error=f"Erro ao ler CSV: {e}",
        )

    sel = [p for p in points if p.get("selecionado") and p.get("latitude") is not None and p.get("longitude") is not None]
    rlabel = f"{rname} ({raddr})" if raddr else rname
    names: List[str] = [rlabel] + [str(p.get("nome") or "") for p in sel]
    coords: List[Tuple[float, float]] = [(rlat, rlon)] + [(float(p["latitude"]), float(p["longitude"])) for p in sel]

    if len(coords) <= 1:
        route = [0, 0]
        dm: List[List[float]] = [[0.0 for _ in range(len(coords))] for _ in range(len(coords))]
        total_km = 0.0
        total_min = 0.0
    else:
        dm = distance_matrix(coords)
        selected_nodes = [i for i in range(len(coords)) if i != 0]
        route = solve_tsp_cycle(dm, selected_nodes, start=0)
        total_km = route_distance_km(route, dm)
        total_min = estimate_time_minutes(total_km, speed)

    polyline_coords = None
    osrm_legs = None
    if roads and len(coords) >= 2:
        try:
            seq = [coords[i] for i in route]
            coord_str = ";".join([f"{lon},{lat}" for (lat, lon) in seq])
            url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson&steps=false&annotations=false"
            resp = requests.get(url, timeout=10)
            if resp.ok:
                data = resp.json()
                routes = data.get("routes") or []
                if routes:
                    geo = routes[0]["geometry"]["coordinates"]
                    polyline_coords = [(lat, lon) for lon, lat in geo]
                    osrm_legs = routes[0].get("legs")
        except Exception:
            polyline_coords = None
            osrm_legs = None

    rows_out = []
    cum_km = 0.0
    cum_min = 0.0
    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]
        if osrm_legs and i < len(osrm_legs):
            leg_km = float(osrm_legs[i].get("distance", 0.0)) / 1000.0
        else:
            leg_km = float(dm[a][b]) if dm else 0.0
        leg_min = estimate_time_minutes(leg_km, speed)
        cum_km += leg_km
        cum_min += leg_min
        rows_out.append({
            "ordem": i,
            "de": names[a] if a < len(names) else str(a),
            "para": names[b] if b < len(names) else str(b),
            "lat": coords[b][0] if coords else None,
            "lon": coords[b][1] if coords else None,
            "dist_km": round(leg_km, 3),
            "tempo_min": round(leg_min, 1),
            "acum_km": round(cum_km, 3),
            "acum_min": round(cum_min, 1),
        })

    # recompute totals from legs so speed always applies
    total_km = cum_km
    total_min = cum_min

    map_html = make_route_map(coords, names, route, polyline=polyline_coords)
    try:
        import plotly.io as pio
        graph_html = pio.to_html(make_graph_figure(coords, names, route), include_plotlyjs="cdn", full_html=False)
    except Exception:
        graph_html = "<div>Falha ao renderizar grafo.</div>"

    csv_bytes = to_csv_bytes_from_rows(rows_out, [
        "ordem","de","para","lat","lon","dist_km","tempo_min","acum_km","acum_min"
    ])
    csv_b64 = base64.b64encode(csv_bytes).decode("utf-8")

    html = render_template(
        "result.html",
        rname=rname,
        speed=int(speed),
        roads=roads,
        total_km=round(total_km, 2),
        total_min=round(total_min, 1),
        n_stops=max(0, len(route) - 2),
        table=rows_out,
        csv_b64=csv_b64,
        map_html=map_html,
        graph_html=graph_html,
        original_csv=csv_text,
        rlat=rlat,
        rlon=rlon,
        raddr=raddr,
    )
    resp = make_response(html)
    try:
        resp.set_cookie("speed", str(int(round(speed))), max_age=60 * 60 * 24 * 365)
    except Exception:
        pass
    return resp


@app.route("/optimize", methods=["GET"]) 
def optimize_get():
    return redirect(url_for("index"))


@app.route("/download", methods=["POST"]) 
def download():
    csv_b64 = request.form.get("csv_b64", "")
    try:
        data = base64.b64decode(csv_b64)
    except Exception:
        data = b""
    return send_file(
        BytesIO(data),
        mimetype="text/csv",
        as_attachment=True,
        download_name="rota_sabor_express.csv",
    )


@app.route("/save_points", methods=["POST"]) 
def save_points():
    csv_text = request.form.get("csv_text", "")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(csv_text)
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
