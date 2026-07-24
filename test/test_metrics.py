import pytest
import networkx as nx

from src.graph_model import generate_network
from src.metrics import average_cascade_size, compare_strategies


def build_chain_graph():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4)])
    return G


def build_branching_graph():
    """0 -> 1 -> {2, 3} -> 4. El nodo 1 es el único cuello de botella real."""
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)])
    return G


# ---------------------------------------------------------------------------
# average_cascade_size
# ---------------------------------------------------------------------------

def test_average_cascade_size_zero_probability_only_seeds():
    G = build_chain_graph()
    stats = average_cascade_size(G, seed_nodes=[0], probability=0.0, n_simulations=5, seed=1)
    assert stats["avg_size"] == 1
    assert all(s == 1 for s in stats["sizes"])


def test_average_cascade_size_full_probability_reaches_all():
    G = build_chain_graph()
    stats = average_cascade_size(G, seed_nodes=[0], probability=1.0, n_simulations=5, seed=1)
    assert stats["avg_size"] == G.number_of_nodes()
    assert stats["avg_pct"] == 100.0


def test_average_cascade_size_empty_seed_nodes():
    G = build_chain_graph()
    stats = average_cascade_size(G, seed_nodes=[], probability=1.0, n_simulations=5, seed=1)
    assert stats["avg_size"] == 0.0
    assert stats["sizes"] == []


def test_average_cascade_size_resets_graph_state():
    G = build_chain_graph()
    average_cascade_size(G, seed_nodes=[0], probability=1.0, n_simulations=3, seed=1)
    assert all(G.nodes[n]["activated"] is False for n in G.nodes())


# ---------------------------------------------------------------------------
# compare_strategies
# ---------------------------------------------------------------------------

def test_compare_strategies_returns_all_requested_strategies():
    G = build_branching_graph()
    results = compare_strategies(
        G, seed_nodes=[0], probability=1.0, n_remove=1, n_simulations=5, seed=1,
        strategies=["baseline", "random"],
    )
    assert set(results.keys()) == {"baseline", "random"}


def test_compare_strategies_result_has_expected_fields():
    G = build_branching_graph()
    results = compare_strategies(
        G, seed_nodes=[0], probability=1.0, n_remove=1, n_simulations=5, seed=1,
        strategies=["baseline"],
    )
    expected_keys = {"removed", "avg_size", "avg_pct", "avg_steps", "graph"}
    assert expected_keys.issubset(results["baseline"].keys())


def test_compare_strategies_baseline_has_no_removed_nodes():
    G = build_branching_graph()
    results = compare_strategies(
        G, seed_nodes=[0], probability=1.0, n_remove=2, n_simulations=5, seed=1,
        strategies=["baseline"],
    )
    assert results["baseline"]["removed"] == []


# ---------------------------------------------------------------------------
# Integración con grafos reales
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_intervention_reduces_or_maintains_cascade_vs_baseline(model):
    """Sobre un grafo real, cualquier estrategia dirigida (no random) debería
    reducir la cascada esperada respecto al caso base, o al menos no empeorarla."""
    G = generate_network(30, model, seed=3)
    seed_nodes = [max(G.out_degree(), key=lambda x: x[1])[0]]

    results = compare_strategies(
        G, seed_nodes, probability=0.25, n_remove=4, n_simulations=40, seed=7,
        strategies=["baseline", "betweenness", "greedy"],
    )

    assert results["betweenness"]["avg_size"] <= results["baseline"]["avg_size"]
    assert results["greedy"]["avg_size"] <= results["baseline"]["avg_size"]