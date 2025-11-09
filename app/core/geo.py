import math
from typing import List, Sequence


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def distance_matrix(coords: Sequence[Sequence[float]]) -> List[List[float]]:
    n = len(coords)
    dm: List[List[float]] = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        lat1, lon1 = coords[i]
        for j in range(i + 1, n):
            lat2, lon2 = coords[j]
            d = haversine_km(lat1, lon1, lat2, lon2)
            dm[i][j] = d
            dm[j][i] = d
    return dm


def route_distance_km(route: List[int], dm: Sequence[Sequence[float]]) -> float:
    total = 0.0
    for i in range(len(route) - 1):
        total += float(dm[route[i]][route[i + 1]])
    return total


def estimate_time_minutes(distance_km: float, speed_kmh: float) -> float:
    if speed_kmh <= 0:
        return float("nan")
    return (distance_km / speed_kmh) * 60.0
