"""
Orquestador del proyecto: genera la red simulada, corre la comparación de
estrategias de intervención, reporta los resultados y muestra el dashboard
de visualización.

Uso:
    python main.py
"""
import random
from src.graph_model import generate_network, save_graph, graph_summary
from src.metrics import compare_strategies
from Graph_Interface import mostrar_dashboard


# ---------------------------------------------------------------------------
# Parámetros por defecto del experimento
# ---------------------------------------------------------------------------

N_NODES = 100
MODEL = "barabasi_albert"          # "erdos_renyi" o "barabasi_albert"
AVG_DEGREE = 4

N_SEEDS = 3                     # cuántos nodos originan la fake news (top-N por out-degree)
PROBABILITY = 0.25
N_REMOVE = 10                     # nodos removidos por cada estrategia
N_SIMULATIONS = 100               # simulaciones Monte Carlo para comparar estrategias

ESTRATEGIA_A_ANIMAR = "greedy"    # cuál estrategia se anima junto al baseline
VELOCIDAD_ANIMACION_MS = 1800


def pedir_parametros():
    """Pide al usuario los parámetros del experimento, con valores por defecto."""
    print("=" * 60)
    print("CONFIGURACIÓN DEL EXPERIMENTO (Enter para usar el valor por defecto)")
    print("=" * 60)

    n_nodes = input(f"Número de nodos [{N_NODES}]: ").strip()
    n_nodes = int(n_nodes) if n_nodes else N_NODES

    model = input(f"Modelo (erdos_renyi/barabasi_albert) [{MODEL}]: ").strip()
    model = model if model else MODEL

    avg_degree = input(f"Grado promedio [{AVG_DEGREE}]: ").strip()
    avg_degree = int(avg_degree) if avg_degree else AVG_DEGREE

    graph_seed = input(f"Semilla del grafo (Enter = aleatoria): ").strip()
    if graph_seed:
        graph_seed = int(graph_seed)
    else:
        graph_seed = random.randint(0, 999_999)
        print(f"  -> semilla del grafo generada: {graph_seed}")

    n_seeds = input(f"Cantidad de nodos semilla [{N_SEEDS}]: ").strip()
    n_seeds = int(n_seeds) if n_seeds else N_SEEDS

    probability = input(f"Probabilidad de activación [{PROBABILITY}]: ").strip()
    probability = float(probability) if probability else PROBABILITY

    n_remove = input(f"Nodos a remover por estrategia [{N_REMOVE}]: ").strip()
    n_remove = int(n_remove) if n_remove else N_REMOVE

    experiment_seed = input(f"Semilla del experimento (Enter = aleatoria): ").strip()
    if experiment_seed:
        experiment_seed = int(experiment_seed)
    else:
        experiment_seed = random.randint(0, 999_999)
        print(f"  -> semilla del experimento generada: {experiment_seed}")

    estrategia = input(
        f"Estrategia a animar (random/betweenness/maxflow_mincut/greedy) [{ESTRATEGIA_A_ANIMAR}]: "
    ).strip()
    estrategia = estrategia if estrategia else ESTRATEGIA_A_ANIMAR

    return {
        "n_nodes": n_nodes,
        "model": model,
        "avg_degree": avg_degree,
        "graph_seed": graph_seed,
        "n_seeds": n_seeds,
        "probability": probability,
        "n_remove": n_remove,
        "experiment_seed": experiment_seed,
        "estrategia_a_animar": estrategia,
    }


def main():
    params = pedir_parametros()

    # 1. Generar la red simulada
    G = generate_network(
        n_nodes=params["n_nodes"],
        model=params["model"],
        seed=params["graph_seed"],
        avg_degree=params["avg_degree"],
    )

    print("\n" + "=" * 60)
    print("RESUMEN DEL GRAFO")
    print("=" * 60)
    summary = graph_summary(G)
    for key, value in summary.items():
        print(f"{key}: {value}")

    # 2. Elegir semillas: los n_seeds nodos con mayor out-degree
    seed_nodes = sorted(
        G.nodes(), key=lambda n: G.out_degree(n), reverse=True
    )[:params["n_seeds"]]
    print(f"\nseed_nodes elegidos (top-{params['n_seeds']} por out-degree): {seed_nodes}")

    # 3. Comparar todas las estrategias de intervención
    print("\n" + "=" * 60)
    print("COMPARACIÓN DE ESTRATEGIAS DE INTERVENCIÓN")
    print("=" * 60)
    resultados = compare_strategies(
        G,
        seed_nodes=seed_nodes,
        probability=params["probability"],
        n_remove=params["n_remove"],
        n_simulations=N_SIMULATIONS,
        seed=params["experiment_seed"],
    )

    for nombre, r in resultados.items():
        print(f"\n[{nombre}]")
        print(f"  nodos removidos: {r['removed']}")
        print(f"  tamaño promedio de cascada: {r['avg_size']:.2f} nodos ({r['avg_pct']:.1f}%)")
        print(f"  pasos promedio: {r['avg_steps']:.2f}")
        print(f"  tiempo de ejecución: {r['runtime_sec']:.3f} s")

    # 4. Guardar el grafo como respaldo para la entrega
    save_graph(G, "data/example_graph.gml")

    if params["n_nodes"] > 300:
        print("Se omite la visualización debido a rendimiento")
        return

    # 5. Mostrar el dashboard visual
    mostrar_dashboard(
        G=G,
        seed_nodes=seed_nodes,
        probability=params["probability"],
        n_remove=params["n_remove"],
        n_simulations=N_SIMULATIONS,
        resultados=resultados,
        estrategia_a_animar=params["estrategia_a_animar"],
        seed=params["experiment_seed"],
        velocidad_animacion_ms=VELOCIDAD_ANIMACION_MS,
    )

    return G, resultados


if __name__ == "__main__":
    main()