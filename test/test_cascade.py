import pytest
import networkx as nx
from src.cascade import run_cascade

def test_probability_zero_only_activates_seeds():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2)])
    resultado = run_cascade(G, seed_nodes=[0], probability=0.0, seed=42)
    assert resultado["activated"] == [0]
    assert resultado["steps"] == 1
    assert resultado["size"] == 1

def test_probability_one_activates_all():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2)])
    resultado = run_cascade(G, seed_nodes=[0], probability=1.0, seed=42)
    assert set(resultado["activated"]) == {0, 1, 2}
    assert resultado["steps"] == 3
    assert resultado["size"] == 3

def test_reproducibility_same_seed_same_result():
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])
    resultado1 = run_cascade(G, seed_nodes=[0], probability=0.5, seed=42)
    resultado2 = run_cascade(G, seed_nodes=[0], probability=0.5, seed=42)
    assert resultado1 == resultado2