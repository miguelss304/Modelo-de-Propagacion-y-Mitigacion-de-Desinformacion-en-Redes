"""
Módulo de métricas: evalúa el efecto de una intervención sobre la propagación.

Este módulo no decide qué nodos remover (eso vive en intervention.py); solo
mide qué tan bien funcionó una intervención ya aplicada, usando simulación
Monte Carlo sobre el modelo de cascada (Independent Cascade Model).
"""

from src.cascade import run_cascade
from src.intervention import STRATEGIES


def reset_activation(G):
    """Reinicia el atributo 'activated' de todos los nodos a False.

    Necesario porque run_cascade muta el grafo in-place; para correr
    múltiples simulaciones (Monte Carlo) sobre el mismo grafo hay que
    limpiar el estado entre corridas.

    Args:
        G: Grafo de networkx.
    """
    for node in G.nodes():
        G.nodes[node]["activated"] = False


def average_cascade_size(G, seed_nodes, probability, n_simulations, seed):
    """Estima el tamaño esperado de la cascada mediante simulación Monte Carlo.

    Args:
        G: Grafo sobre el que se simula.
        seed_nodes: Nodos que inician la propagación.
        probability: Probabilidad de activación por arista (Independent Cascade).
        n_simulations: Número de simulaciones a promediar.
        seed: Semilla base para reproducibilidad (cada simulación usa seed+i).

    Returns:
        dict con:
            "avg_size": tamaño promedio de la cascada (nodos alcanzados)
            "avg_pct": porcentaje promedio de la red afectada
            "avg_steps": número promedio de pasos hasta estabilizar
            "sizes": lista con el tamaño de cada simulación individual
    """
    if not seed_nodes or G.number_of_nodes() == 0:
        return {"avg_size": 0.0, "avg_pct": 0.0, "avg_steps": 0.0, "sizes": []}

    sizes, steps_list = [], []
    for i in range(n_simulations):
        reset_activation(G)
        result = run_cascade(G, seed_nodes, probability, seed=seed + i)
        sizes.append(result["size"])
        steps_list.append(result["steps"])

    reset_activation(G)
    avg_size = sum(sizes) / len(sizes)
    avg_steps = sum(steps_list) / len(steps_list)
    avg_pct = avg_size / G.number_of_nodes() * 100

    return {"avg_size": avg_size, "avg_pct": avg_pct, "avg_steps": avg_steps, "sizes": sizes}


def compare_strategies(G, seed_nodes, probability, n_remove, n_simulations=50, seed=0,
                        strategies=None):
    """Corre y compara todas (o algunas) las estrategias de intervención.

    Args:
        G: Grafo original.
        seed_nodes: Nodos que originan la fake news.
        probability: Probabilidad de activación por arista.
        n_remove: Cantidad de nodos a remover en cada estrategia.
        n_simulations: Simulaciones Monte Carlo para evaluar el resultado final.
        seed: Semilla para reproducibilidad.
        strategies: Lista de nombres de estrategias a correr (subset de
            STRATEGIES.keys() en intervention.py). Si es None, corre todas.

    Returns:
        dict {nombre_estrategia: {"removed": [...], "avg_size": ..., "avg_pct": ...,
              "avg_steps": ..., "graph": G_intervenido}}
    """
    names = strategies or list(STRATEGIES.keys())
    results = {}

    for name in names:
        fn = STRATEGIES[name]
        removed, G_intervened = fn(G, seed_nodes, n_remove, probability, seed)
        active_seeds = [s for s in seed_nodes if s in G_intervened]
        stats = average_cascade_size(
            G_intervened, active_seeds, probability, n_simulations, seed
        )
        results[name] = {
            "removed": removed,
            "avg_size": stats["avg_size"],
            "avg_pct": stats["avg_pct"],
            "avg_steps": stats["avg_steps"],
            "graph": G_intervened,
        }

    return results