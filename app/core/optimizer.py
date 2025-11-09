from typing import List, Sequence


def _nearest_neighbor(dm: Sequence[Sequence[float]], start: int, nodes: Sequence[int]) -> List[int]:
    unvisited = set(nodes)
    if start in unvisited:
        unvisited.remove(start)
    route = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: dm[current][j])
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return route


def _two_opt(route: List[int], dm: Sequence[Sequence[float]]) -> List[int]:
    improved = True
    n = len(route)
    if n <= 4:
        return route
    best_route = route[:]
    best_cost = _route_cost(best_route, dm)
    while improved:
        improved = False
        for i in range(1, n - 2):
            for k in range(i + 1, n - 1):
                new_route = best_route[:i] + best_route[i:k + 1][::-1] + best_route[k + 1:]
                new_cost = _route_cost(new_route, dm)
                if new_cost + 1e-9 < best_cost:
                    best_route = new_route
                    best_cost = new_cost
                    improved = True
        n = len(best_route)
    return best_route


def _route_cost(route: List[int], dm: Sequence[Sequence[float]]) -> float:
    cost = 0.0
    for i in range(len(route) - 1):
        cost += float(dm[route[i]][route[i + 1]])
    return cost


def solve_tsp_cycle(dm: Sequence[Sequence[float]], selected_nodes: Sequence[int], start: int = 0) -> List[int]:
    if not selected_nodes:
        return [start, start]
    nodes = [start] + [n for n in selected_nodes if n != start]
    route = _nearest_neighbor(dm, start, nodes)
    if route[0] != start:
        route = [start] + route
    if route[-1] != start:
        route.append(start)
    route = _two_opt(route, dm)
    if route[-1] != start:
        route.append(start)
    return route
