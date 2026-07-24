import pytest
import networkx as nx
from src.graph_model import generate_network, save_graph, load_graph

@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_generate_network_is_weakly_connected(model):
    G = generate_network(20, model, seed=1)
    assert nx.is_weakly_connected(G)
    assert G.number_of_nodes() == 20


@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_generate_network_is_directed(model):
    G = generate_network(20, model, seed=1)
    assert G.is_directed()


@pytest.mark.parametrize("model", ["erdos_renyi", "barabasi_albert"])
def test_generate_network_reproducible(model):
    G1 = generate_network(20, model, seed=5)
    G2 = generate_network(20, model, seed=5)
    assert set(G1.edges()) == set(G2.edges())


def test_generate_network_invalid_model_raises():
    with pytest.raises(ValueError):
        generate_network(20, "modelo_inventado", seed=1)