from src.graph_model import generate_network
import networkx as nx

G = generate_network(n_nodes=60, model="barabasi_albert", seed=934641, avg_degree=4)
seed_nodes = [1, 0]

alcanzables = set(seed_nodes)
for s in seed_nodes:
    alcanzables |= nx.descendants(G, s)

print("nodos alcanzables (teórico):", len(alcanzables))