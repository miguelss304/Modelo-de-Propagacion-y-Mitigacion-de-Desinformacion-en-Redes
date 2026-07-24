import random
import networkx as nx

def generate_network(n_nodes, model, seed, max_attempts = 100):
    """Genera una red simulada como grafo dirigido.

    Args:
        n_nodes: Número de nodos (personas) en la red.
        model: Modelo de generación, "erdos_renyi" o "barabasi_albert".
        seed: Semilla para reproducibilidad.
        max_attemps: maximo de seguridad de intentos permitidos para generar un grafo conexo

    Returns:
        DiGraph de networkx representando la red simulada. Cada nodo nace con el atributo "activated" = False.

    Raises:
        ValueError: Si `model` no es un valor soportado.
    """
    for attempt in range(max_attempts):
        current_seed = seed + attempt

        if model == "erdos_renyi":
            p = 0.15
            G = nx.erdos_renyi_graph(n_nodes, p, seed=current_seed, directed=True)
        elif model == "barabasi_albert":
            m = 2
            G_undirected = nx.barabasi_albert_graph(n_nodes, m, seed=current_seed)
            G = nx.DiGraph()
            G.add_nodes_from(G_undirected.nodes())

            rng = random.Random(current_seed)
            for u, v in G_undirected.edges():
                if rng.random() < 0.5:
                    G.add_edge(u, v)
                else:
                    G.add_edge(v, u)
        else:
            raise ValueError(f"Modelo no soportado: {model}")

        if nx.is_weakly_connected(G):
            for node in G.nodes():
                G.nodes[node]["activated"] = False
            return G

    raise RuntimeError(
        f"No se pudo generar un grafo conexo tras {max_attempts} intentos "
        f"con n_nodes={n_nodes}, model={model}"
    )

def save_graph(G, path):
    """Guarda un grafo en formato GML.

    Args:
        G: Grafo de networkx (DiGraph) a guardar.
        path: Ruta del archivo destino (ej. "data/example_graph.gml").
    """
    nx.write_gml(G, path)


def load_graph(path):
    """Lee un grafo en formato GML y lo devuelve como Graph

    Args:
        path: Ruta del archivo donde se encuentra el grafo (ej. "data/example_graph.gml").
    """
    return nx.read_gml(path)