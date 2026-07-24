import random

def run_cascade(G, seed_nodes, probability, seed):
    """
    Simula la expansion de la fake news a lo largo del grafo

    Args:
        G: grafo generado con anterioridad
        seed_nodes: nodos que empiezan activados
        probability: probabilidad de que un nodo se active
        seed: semilla para reproducibilidad

    Returns:
        activated: lista de nodos activos durante la simulacion
        steps: cantidad de repeticiones hasta que no hubo nuevos nodos activos
        size: cantidad de nodos activos al final de la simulacion

    """

    activated = set(seed_nodes)
    newly_activated = set(seed_nodes)
    rng = random.Random(seed)
    time_step = 0

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
        time_step += 1

    return {"activated": list(activated), "steps": time_step, "size": len(activated)}