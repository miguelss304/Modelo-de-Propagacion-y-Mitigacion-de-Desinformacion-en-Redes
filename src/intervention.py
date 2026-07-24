"""
Módulo de intervención para minimizar la propagación de fake news en un grafo.

Cada estrategia recibe el grafo original G y devuelve:
    - removed: lista de nodos seleccionados para remover (orden de importancia)
    - G_intervened: copia del grafo con esos nodos ya removidos

Todas las estrategias evitan remover nodos que son "seed_nodes" (los que
originan la fake news), ya que removerlos no representa una intervención
realista sobre la red (equivaldría a censurar al emisor original, no a
frenar la difusión).

Este módulo solo decide QUÉ nodos remover. Para medir qué tan efectiva fue
la intervención (tamaño de cascada, % de red afectada, comparación entre
estrategias), ver src/metrics.py.
"""

import random
from collections import Counter

import networkx as nx


# ---------------------------------------------------------------------------
# Utilidades comunes
# ---------------------------------------------------------------------------

def _safe_candidates(G, seed_nodes, exclude=None):
    """Devuelve los nodos elegibles para ser removidos (excluye seeds y ya removidos)."""
    exclude = set(exclude or [])
    return [n for n in G.nodes() if n not in set(seed_nodes) and n not in exclude]


# ---------------------------------------------------------------------------
# Estrategia 0: Caso base (sin intervención) — para comparar el resto
# ---------------------------------------------------------------------------

def baseline(G):
    """Caso base: no se remueve ningún nodo.

    Args:
        G: Grafo original.

    Returns:
        (removed, G_intervenido) donde removed = [] y G_intervenido es una copia de G.
    """
    return [], G.copy()


# ---------------------------------------------------------------------------
# Estrategia 1: Remoción aleatoria
# ---------------------------------------------------------------------------

def remove_random(G, seed_nodes, n_remove, seed):
    """Remueve n_remove nodos al azar (excluyendo los seed_nodes).

    Sirve como estrategia de control: cualquier estrategia "inteligente"
    debería superarla.

    Args:
        G: Grafo original.
        seed_nodes: Nodos que originan la fake news (no se remueven).
        n_remove: Cantidad de nodos a remover.
        seed: Semilla para reproducibilidad.

    Returns:
        (removed, G_intervenido)
    """
    rng = random.Random(seed)
    candidates = _safe_candidates(G, seed_nodes)
    n_remove = min(n_remove, len(candidates))
    removed = rng.sample(candidates, n_remove)

    G_intervened = G.copy()
    G_intervened.remove_nodes_from(removed)
    return removed, G_intervened


# ---------------------------------------------------------------------------
# Estrategia 2: Betweenness Centrality
# ---------------------------------------------------------------------------

def remove_by_betweenness(G, seed_nodes, n_remove):
    """Remueve los n_remove nodos con mayor betweenness centrality.

    La betweenness centrality mide cuántos caminos más cortos entre pares
    de nodos pasan por un nodo dado. En una red de difusión, estos nodos
    actúan como "puentes" entre comunidades, por lo que suelen ser
    responsables de propagar información entre grupos que de otra forma
    estarían desconectados.

    Args:
        G: Grafo original.
        seed_nodes: Nodos que originan la fake news (no se remueven).
        n_remove: Cantidad de nodos a remover.

    Returns:
        (removed, G_intervenido)
    """
    centrality = nx.betweenness_centrality(G, normalized=True)
    ranked = sorted(
        (n for n in centrality if n not in set(seed_nodes)),
        key=lambda n: centrality[n],
        reverse=True,
    )
    removed = ranked[:n_remove]

    G_intervened = G.copy()
    G_intervened.remove_nodes_from(removed)
    return removed, G_intervened


# ---------------------------------------------------------------------------
# Estrategia 3: Max-Flow Min-Cut
# ---------------------------------------------------------------------------

def remove_by_maxflow_mincut(G, seed_nodes, n_remove, n_targets=15):
    """Identifica nodos críticos usando el teorema de Max-Flow Min-Cut.

    Idea: entre cada nodo semilla (fuente) y un conjunto de nodos "objetivo"
    (los de mayor in-degree, es decir, los más expuestos a recibir la fake
    news), se calcula el conjunto mínimo de nodos (min vertex cut) cuya
    remoción desconecta ese camino. Los nodos que aparecen con más
    frecuencia en estos cortes mínimos son los "cuellos de botella" del
    grafo: bloquearlos corta la mayor cantidad de rutas de propagación
    posibles con la menor cantidad de remociones (equivalente al max-flow
    que puede pasar por esos caminos).

    Args:
        G: Grafo original (debe ser dirigido).
        seed_nodes: Nodos que originan la fake news (fuentes del flujo).
        n_remove: Cantidad de nodos a remover.
        n_targets: Cuántos nodos de alto in-degree usar como "objetivos"
            para calcular los cortes mínimos (limita el costo computacional).

    Returns:
        (removed, G_intervenido)
    """
    seed_set = set(seed_nodes)
    in_degree = dict(G.in_degree())
    targets = sorted(
        (n for n in G.nodes() if n not in seed_set),
        key=lambda n: in_degree[n],
        reverse=True,
    )[:n_targets]

    cut_counter = Counter()
    for s in seed_nodes:
        if s not in G:
            continue
        for t in targets:
            if t == s or not nx.has_path(G, s, t):
                continue
            try:
                cut = nx.minimum_node_cut(G, s=s, t=t)
            except (nx.NetworkXError, nx.NetworkXNoPath):
                continue
            for node in cut:
                if node not in seed_set:
                    cut_counter[node] += 1

    if cut_counter:
        removed = [n for n, _ in cut_counter.most_common(n_remove)]
    else:
        removed = []

    # Si el corte no alcanzó a llenar n_remove (grafo con pocos caminos
    # redundantes), se completa con los nodos de mayor betweenness restantes.
    if len(removed) < n_remove:
        centrality = nx.betweenness_centrality(G)
        extra = sorted(
            (n for n in centrality if n not in seed_set and n not in removed),
            key=lambda n: centrality[n],
            reverse=True,
        )
        removed += extra[: n_remove - len(removed)]

    G_intervened = G.copy()
    G_intervened.remove_nodes_from(removed)
    return removed, G_intervened


# ---------------------------------------------------------------------------
# Estrategia 4: Greedy
# ---------------------------------------------------------------------------

def remove_greedy(G, seed_nodes, probability, n_remove, n_simulations=30, seed=0,
                   verbose=False):
    """Remueve iterativamente el nodo que más reduce el tamaño esperado de la cascada.

    En cada iteración se evalúa (vía Monte Carlo) el efecto de remover cada
    candidato restante y se elige el que produce la mayor reducción en el
    tamaño promedio de la cascada. Es la estrategia más costosa
    computacionalmente (O(n_remove * n_candidatos * n_simulations)) pero
    en general la más efectiva, ya que optimiza directamente sobre la
    métrica objetivo en lugar de usar un proxy estructural (centralidad).

    Args:
        G: Grafo original.
        seed_nodes: Nodos que originan la fake news (no se remueven).
        probability: Probabilidad de activación por arista.
        n_remove: Cantidad de nodos a remover.
        n_simulations: Simulaciones Monte Carlo por candidato evaluado.
        seed: Semilla base para reproducibilidad.
        verbose: Si True, imprime el progreso de cada iteración.

    Returns:
        (removed, G_intervenido)
    """
    # Import local para evitar import circular (metrics.py importa STRATEGIES
    # de este módulo, y este módulo necesita average_cascade_size de metrics.py
    # solo dentro de esta función).
    from src.metrics import average_cascade_size

    current_G = G.copy()
    removed = []
    seed_set = set(seed_nodes)

    for step in range(n_remove):
        candidates = _safe_candidates(current_G, seed_set)
        if not candidates:
            break

        best_node, best_avg = None, float("inf")
        for node in candidates:
            trial_G = current_G.copy()
            trial_G.remove_node(node)
            active_seeds = [s for s in seed_nodes if s in trial_G]
            stats = average_cascade_size(
                trial_G, active_seeds, probability, n_simulations, seed
            )
            if stats["avg_size"] < best_avg:
                best_avg = stats["avg_size"]
                best_node = node

        removed.append(best_node)
        current_G.remove_node(best_node)

        if verbose:
            print(f"[greedy] paso {step + 1}/{n_remove}: removido '{best_node}' "
                  f"(cascada promedio estimada: {best_avg:.2f})")

    return removed, current_G


# ---------------------------------------------------------------------------
# Registro de estrategias disponibles (usado por metrics.compare_strategies)
# ---------------------------------------------------------------------------

STRATEGIES = {
    "baseline": lambda G, seed_nodes, n_remove, probability, seed: baseline(G),
    "random": lambda G, seed_nodes, n_remove, probability, seed: remove_random(
        G, seed_nodes, n_remove, seed
    ),
    "betweenness": lambda G, seed_nodes, n_remove, probability, seed: remove_by_betweenness(
        G, seed_nodes, n_remove
    ),
    "maxflow_mincut": lambda G, seed_nodes, n_remove, probability, seed: remove_by_maxflow_mincut(
        G, seed_nodes, n_remove
    ),
    "greedy": lambda G, seed_nodes, n_remove, probability, seed: remove_greedy(
        G, seed_nodes, probability, n_remove, seed=seed
    ),
}