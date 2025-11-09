from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import folium
import plotly.graph_objects as go


def make_route_map(
    coords: Sequence[Tuple[float, float]],
    names: Sequence[str],
    route: List[int] | None,
    polyline: Sequence[Tuple[float, float]] | None = None,
) -> str:

    if not coords:
        m = folium.Map(location=[0, 0], zoom_start=2)
        return m._repr_html_()
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(location=center, zoom_start=13, control_scale=True)

    for i, (lat, lon) in enumerate(coords):
        color = "red" if i == 0 else "blue"
        folium.Marker(
            location=(lat, lon),
            tooltip=f"{i}: {names[i]}",
            popup=f"{names[i]}\n({lat:.5f}, {lon:.5f})",
            icon=folium.Icon(color=color, icon="cutlery" if i == 0 else "info-sign"),
        ).add_to(m)

    if polyline:
        folium.PolyLine(polyline, color="green", weight=4, opacity=0.9).add_to(m)
    elif route and len(route) >= 2:
        pts = [(coords[i][0], coords[i][1]) for i in route]
        folium.PolyLine(pts, color="green", weight=4, opacity=0.9).add_to(m)

    return m._repr_html_()


def make_graph_figure(coords: Sequence[Tuple[float, float]], names: Sequence[str], route: List[int] | None):
    if not coords:
        return go.Figure()
    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]

    fig = go.Figure()
    if route and len(route) >= 2:
        xs = []
        ys = []
        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]
            xs += [lons[a], lons[b], None]
            ys += [lats[a], lats[b], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="green", width=2), showlegend=False))

    fig.add_trace(
        go.Scatter(
            x=lons,
            y=lats,
            mode="markers+text",
            text=[f"{i}: {names[i]}" for i in range(len(coords))],
            textposition="top center",
            marker=dict(size=[12 if i == 0 else 8 for i in range(len(coords))], color=["red" if i == 0 else "blue" for i in range(len(coords))]),
            showlegend=False,
        )
    )

    pad = 0.005
    minx, maxx = min(lons), max(lons)
    miny, maxy = min(lats), max(lats)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(title="lon", range=[minx - pad, maxx + pad], scaleanchor="y", scaleratio=math.cos(math.radians((miny + maxy) / 2))),
        yaxis=dict(title="lat", range=[miny - pad, maxy + pad]),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )
    return fig
