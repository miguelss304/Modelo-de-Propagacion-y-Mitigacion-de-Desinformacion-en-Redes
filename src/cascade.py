import random

def run_cascade_with_history(G, seed_nodes, probability, seed):
    """Simula la cascada guardando el estado acumulado en cada paso.

    Args:
        G: grafo generado con anterioridad. Se modifica in-place: cada nodo
           activado queda marcado con el atributo "activated"=True.
        seed_nodes: nodos que empiezan activados.
        probability: probabilidad de que un nodo se active.
        seed: semilla para reproducibilidad.

    Returns:
        Lista de sets: historial[t] son los nodos activos acumulados hasta el paso t.

    Raises:
        ValueError: si algún nodo en seed_nodes no existe en el grafo.
    """
    for node in seed_nodes:
        if node not in G.nodes():
            raise ValueError(f"El nodo semilla '{node}' no existe en el grafo")

    activated = set(seed_nodes)
    newly_activated = set(seed_nodes)
    rng = random.Random(seed)
    historial = [activated.copy()]

    for node in seed_nodes:
        G.nodes[node]["activated"] = True

    while newly_activated:
        next_newly_activated = set()
        for node in newly_activated:
            for child_node in G.successors(node):
                if child_node in activated:
                    continue
                if rng.random() < probability:
                    G.nodes[child_node]["activated"] = True
                    activated.add(child_node)
                    next_newly_activated.add(child_node)
        newly_activated = next_newly_activated
        historial.append(activated.copy())

    return historial


def run_cascade(G, seed_nodes, probability, seed):
    """
    Simula la expansion de la fake news a lo largo del grafo

    Args:
        G: grafo generado con anterioridad. Se modifica in-place: cada nodo
           activado queda marcado con el atributo "activated"=True.
        seed_nodes: nodos que empiezan activados
        probability: probabilidad de que un nodo se active
        seed: semilla para reproducibilidad

    Returns:
        activated: lista de nodos activos durante la simulacion
        steps: cantidad de repeticiones hasta que no hubo nuevos nodos activos
        size: cantidad de nodos activos al final de la simulacion

    Raises:
        ValueError: si algún nodo en seed_nodes no existe en el grafo.
    """
    historial = run_cascade_with_history(G, seed_nodes, probability, seed)
    activated = historial[-1]
    return {"activated": list(activated), "steps": len(historial) - 1, "size": len(activated)}