import pytest
import networkx as nx

from src.graph_model import generate_network
from src.intervention import (
    baseline,
    remove_random,
    remove_by_betweenness,
    remove_by_maxflow_mincut,
    remove_greedy,
)
from src.metrics import average_cascade_size, compare_strategies


def build_chain_graph():
    """Grafo lineal: 0 -> 1 -> 2 -> 3 -> 4. Cada nodo depende solo del anterior."""
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4)])
    return G


def build_bottleneck_graph():
    """Dos clusters densos (0,1,2) y (5,6,7) unidos únicamente por el nodo 4.

    El nodo 4 es el único puente posible entre ambos clusters, por lo que
    debería tener la mayor betweenness centrality y aparecer en cualquier
    corte mínimo entre un nodo del cluster A y uno del cluster B.
    """
    G = nx.DiGraph()
    cluster_a = [0, 1, 2]
    cluster_b = [5, 6, 7]

    for u in cluster_a:
        for v in cluster_a:
            if u != v:
                G.add_edge(u, v)
    for u in cluster_b:
        for v in cluster_b:
            if u != v:
                G.add_edge(u, v)

    G.add_edge(2, 4)
    G.add_edge(4, 2)
    G.add_edge(4, 5)
    G.add_edge(5, 4)

    return G


def build_branching_graph():
    """0 -> 1 -> {2, 3} -> 4. El nodo 1 es el único cuello de botella real."""
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)])
    return G


# ---------------------------------------------------------------------------
# baseline
# ---------------------------------------------------------------------------

def test_baseline_removes_nothing():
    G = build_chain_graph()
    removed, G_intervened = baseline(G)
    assert removed == []
    assert G_intervened.number_of_nodes() == G.number_of_nodes()
    assert set(G_intervened.edges()) == set(G.edges())


def test_baseline_returns_copy_not_same_object():
    G = build_chain_graph()
    _, G_intervened = baseline(G)
    assert G_intervened is not G


# ---------------------------------------------------------------------------
# remove_random
# ---------------------------------------------------------------------------

def test_remove_random_removes_correct_count():
    G = build_chain_graph()
    removed, G_intervened = remove_random(G, seed_nodes=[0], n_remove=2, seed=1)
    assert len(removed) == 2
    assert G_intervened.number_of_nodes() == G.number_of_nodes() - 2


def test_remove_random_excludes_seed_nodes():
    G = build_chain_graph()
    removed, G_intervened = remove_random(G, seed_nodes=[0], n_remove=4, seed=1)
    assert 0 not in removed
    assert 0 in G_intervened.nodes()


def test_remove_random_reproducible_same_seed():
    G = build_chain_graph()
    removed1, _ = remove_random(G, seed_nodes=[0], n_remove=2, seed=7)
    removed2, _ = remove_random(G, seed_nodes=[0], n_remove=2, seed=7)
    assert removed1 == removed2


def test_remove_random_caps_at_available_candidates():
    G = build_chain_graph()
    removed, G_intervened = remove_random(G, seed_nodes=[0], n_remove=100, seed=1)
    assert len(removed) == G.number_of_nodes() - 1
    assert G_intervened.number_of_nodes() == 1


# ---------------------------------------------------------------------------
# remove_by_betweenness
# ---------------------------------------------------------------------------

def test_remove_by_betweenness_selects_bridge_node():
    G = build_bottleneck_graph()
    removed, G_intervened = remove_by_betweenness(G, seed_nodes=[], n_remove=1)
    assert removed == [4]
    assert 4 not in G_intervened.nodes()


def test_remove_by_betweenness_excludes_seed_nodes():
    G = build_bottleneck_graph()
    removed, _ = remove_by_betweenness(G, seed_nodes=[4], n_remove=1)
    assert 4 not in removed


def test_remove_by_betweenness_respects_n_remove():
    G = build_bottleneck_graph()
    removed, _ = remove_by_betweenness(G, seed_nodes=[], n_remove=3)
    assert len(removed) == 3


# ---------------------------------------------------------------------------
# remove_by_maxflow_mincut
# ---------------------------------------------------------------------------

def test_remove_by_maxflow_mincut_finds_bottleneck():
    G = build_bottleneck_graph()
    removed, G_intervened = remove_by_maxflow_mincut(G, seed_nodes=[0], n_remove=1)
    # El corte mínimo entre el cluster A y el cluster B puede caer en cualquiera
    # de los dos extremos del puente (4 o 5): ambos desconectan igual de bien.
    assert removed[0] in {4, 5}
    assert removed[0] not in G_intervened.nodes()


def test_remove_by_maxflow_mincut_disconnects_clusters():
    G = build_bottleneck_graph()
    removed, G_intervened = remove_by_maxflow_mincut(G, seed_nodes=[0], n_remove=1)
    assert not nx.has_path(G_intervened, 0, 7) if 7 in G_intervened else True


def test_remove_by_maxflow_mincut_excludes_seed_nodes():
    G = build_bottleneck_graph()
    removed, _ = remove_by_maxflow_mincut(G, seed_nodes=[0, 4], n_remove=2)
    assert 0 not in removed
    assert 4 not in removed


# ---------------------------------------------------------------------------
# remove_greedy
# ---------------------------------------------------------------------------

def test_remove_greedy_finds_the_critical_bottleneck():
    G = build_branching_graph()
    removed, G_intervened = remove_greedy(
        G, seed_nodes=[0], probability=1.0, n_remove=1, n_simulations=5, seed=1
    )
    assert removed == [1]
    assert 1 not in G_intervened.nodes()


def test_remove_greedy_never_removes_seed_nodes():
    G = build_branching_graph()
    removed, _ = remove_greedy(
        G, seed_nodes=[0], probability=1.0, n_remove=3, n_simulations=5, seed=1
    )
    assert 0 not in removed


def test_remove_greedy_outperforms_or_matches_random():
    G = build_branching_graph()
    seed_nodes = [0]
    _, G_greedy = remove_greedy(
        G, seed_nodes, probability=1.0, n_remove=1, n_simulations=5, seed=1
    )
    _, G_random = remove_random(G, seed_nodes, n_remove=1, seed=1)

    stats_greedy = average_cascade_size(G_greedy, seed_nodes, 1.0, n_simulations=5, seed=1)
    stats_random = average_cascade_size(G_random, seed_nodes, 1.0, n_simulations=5, seed=1)

    assert stats_greedy["avg_size"] <= stats_random["avg_size"]


# ---------------------------------------------------------------------------
# Tests de integración: las 4 estrategias sobre grafos reales
# (erdos_renyi y barabasi_albert), generados con generate_network.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_all_strategies_run_without_error_on_generated_graphs(model):
    G = generate_network(30, model, seed=3)
    seed_nodes = [max(G.out_degree(), key=lambda x: x[1])[0]]

    results = compare_strategies(
        G, seed_nodes, probability=0.2, n_remove=3, n_simulations=10, seed=1,
    )

    assert set(results.keys()) == {
        "baseline", "random", "betweenness", "maxflow_mincut", "greedy"
    }
    for name, r in results.items():
        if name != "baseline":
            assert len(r["removed"]) <= 3
        assert all(s not in r["removed"] for s in seed_nodes)
        assert 0 <= r["avg_pct"] <= 100


@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_intervention_never_removes_more_nodes_than_available(model):
    G = generate_network(10, model, seed=5)
    seed_nodes = [0]

    for strategy_name in ["random", "betweenness", "maxflow_mincut"]:
        fn = {
            "random": lambda: remove_random(G, seed_nodes, n_remove=50, seed=1),
            "betweenness": lambda: remove_by_betweenness(G, seed_nodes, n_remove=50),
            "maxflow_mincut": lambda: remove_by_maxflow_mincut(G, seed_nodes, n_remove=50),
        }[strategy_name]
        removed, G_intervened = fn()
        assert len(removed) <= G.number_of_nodes() - len(seed_nodes)
        assert G_intervened.number_of_nodes() >= 1


@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_generated_graphs_reproducible_intervention_results(model):
    """Misma semilla + mismo grafo generado -> mismo resultado de intervención."""
    G1 = generate_network(20, model, seed=2)
    G2 = generate_network(20, model, seed=2)
    seed_nodes = [0]

    removed1, _ = remove_random(G1, seed_nodes, n_remove=3, seed=9)
    removed2, _ = remove_random(G2, seed_nodes, n_remove=3, seed=9)
    assert removed1 == removed2