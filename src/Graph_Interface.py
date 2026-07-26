"""
Dashboard animado de propagacion de desinformacion.
Usa graph_model.py, cascade.py, intervention.py y metrics.py del proyecto.

Ventana 1: cascada animada, baseline vs. una estrategia de mitigacion.
Ventana 2: curva de activados + comparacion final entre estrategias.

Correr desde la raiz del proyecto (donde esta la carpeta src/).
"""

import sys
import os
sys.path.append(os.path.abspath("."))

import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from src.cascade import run_cascade_with_history
from src.graph_model import generate_network, load_graph
from src.intervention import STRATEGIES
from src.metrics import compare_strategies



# --- parametros, ajusta a tu gusto -----------------------------------------

USAR_GRAFO_GUARDADO = True      # True = carga RUTA_GRAFO / False = genera uno nuevo
RUTA_GRAFO = "data/example_graph.gml"

N_NODES = 60                    # solo aplica si USAR_GRAFO_GUARDADO = False
MODEL = "erdos_renyi"           # solo aplica si USAR_GRAFO_GUARDADO = False ("erdos_renyi" / "barabasi_albert")

# SEED = None -> se elige una seed aleatoria en cada corrida (y se muestra en
# pantalla para poder copiarla y reusarla despues).
# SEED = <numero> -> siempre usa esa seed, mismo resultado en cada corrida.
SEED = None
if SEED is None:
    SEED = random.randint(0, 999_999)
print(f"[info] seed usada en esta corrida: {SEED}")

PROBABILITY = 0.25             # probabilidad de activacion por arista (Independent Cascade)
N_SEEDS = 2                     # cuantos nodos originan la fake news
N_REMOVE = 9                    # cuantos nodos remueve cada estrategia de mitigacion
N_SIMULATIONS = 200             # simulaciones Monte Carlo para el panel de barras (sube esto si el resultado varia mucho entre corridas)

ESTRATEGIA_GRAFO = "greedy"     # cual estrategia se anima junto al baseline en la Ventana 1
                                 # opciones: random / betweenness / maxflow_mincut / greedy
VELOCIDAD_ANIMACION_MS = 1800   # milisegundos entre frames de la animacion

# --- grafo y cascada base ----------------------------------------------------

if USAR_GRAFO_GUARDADO:
    G = nx.DiGraph(load_graph(RUTA_GRAFO))
    G = nx.relabel_nodes(G, {n: int(n) for n in G.nodes()})
else:
    G = generate_network(N_NODES, MODEL, SEED)

# k alto separa mas los nodos y ayuda a que se crucen menos las aristas
pos = nx.spring_layout(G, seed=SEED, k=7 / (G.number_of_nodes() ** 0.5), iterations=300)

seed_nodes = sorted(G.nodes(), key=lambda n: G.out_degree(n), reverse=True)[:N_SEEDS]

G_baseline = G.copy()
historial_baseline = run_cascade_with_history(G_baseline, seed_nodes, PROBABILITY, SEED)
curva_baseline = [len(paso) for paso in historial_baseline]

nodos_removidos, G_intervenido = STRATEGIES[ESTRATEGIA_GRAFO](
    G, seed_nodes, N_REMOVE, PROBABILITY, SEED
)
seeds_sobrevivientes = [s for s in seed_nodes if s in G_intervenido]
if seeds_sobrevivientes:
    historial_estrategia = run_cascade_with_history(
        G_intervenido, seeds_sobrevivientes, PROBABILITY, SEED
    )
else:
    historial_estrategia = [set()]

# repetimos el ultimo estado del historial mas corto para que ambas
# animaciones terminen al mismo tiempo
max_len = max(len(historial_baseline), len(historial_estrategia))
historial_baseline += [historial_baseline[-1]] * (max_len - len(historial_baseline))
historial_estrategia += [historial_estrategia[-1]] * (max_len - len(historial_estrategia))

resultados = compare_strategies(
    G, seed_nodes, PROBABILITY, N_REMOVE,
    n_simulations=N_SIMULATIONS, seed=SEED,
)

COLOR_ACTIVO = "#e63946"
COLOR_INACTIVO = "#b8c4d0"
COLOR_REMOVIDO = "#148D38"


# --- ventana 1: grafo animado -----------------------------------------------

fig_grafo, (ax_baseline, ax_estrategia) = plt.subplots(1, 2, figsize=(15, 8))
fig_grafo.suptitle(f"Cascada de desinformacion: baseline vs. intervencion  (seed={SEED})",
                    fontsize=14, fontweight="bold")
fig_grafo.patch.set_facecolor("#fafafa")


def _dibujar_grafo_en(ax, G_dibujo, activos, titulo):
    """Dibuja un grafo coloreado por estado en el eje dado.

    Args:
        ax: eje de matplotlib donde dibujar.
        G_dibujo: grafo a dibujar (puede tener menos nodos que G si la
            estrategia removio algunos).
        activos: set de nodos activados en el paso actual.
        titulo: texto del titulo del panel.
    """
    ax.clear()
    colores = [COLOR_ACTIVO if n in activos else COLOR_INACTIVO for n in G_dibujo.nodes()]
    nx.draw_networkx_edges(G_dibujo, pos, ax=ax, alpha=0.25, width=0.8,
                            arrows=True, arrowsize=8)
    nx.draw_networkx_nodes(G_dibujo, pos, ax=ax, node_color=colores, node_size=180,
                            edgecolors="white", linewidths=0.8)
    # nodos que la estrategia removio: no estan en G_dibujo, los pintamos aparte
    removidos = [n for n in G.nodes() if n not in G_dibujo.nodes()]
    if removidos:
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=removidos,
                                node_color=COLOR_REMOVIDO, node_size=180,
                                edgecolors="white", linewidths=0.8)
    ax.set_title(titulo, fontsize=10)
    ax.axis("off")


def dibujar_frame_grafo(t):
    """Dibuja el frame t en los dos paneles (baseline y estrategia).

    Args:
        t: paso de tiempo actual (0 a max_len - 1).
    """
    _dibujar_grafo_en(
        ax_baseline, G_baseline, historial_baseline[t],
        f"Sin intervencion -- paso {t}/{max_len - 1} "
        f"({len(historial_baseline[t])} activados)",
    )
    _dibujar_grafo_en(
        ax_estrategia, G_intervenido, historial_estrategia[t],
        f"Estrategia: {ESTRATEGIA_GRAFO} -- paso {t}/{max_len - 1} "
        f"({len(historial_estrategia[t])} activados)",
    )
    leyenda = [
        Line2D([0], [0], marker='o', color='w', label='Susceptible',
               markerfacecolor=COLOR_INACTIVO, markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Activado',
               markerfacecolor=COLOR_ACTIVO, markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Removido (mitigacion)',
               markerfacecolor=COLOR_REMOVIDO, markersize=10),
    ]
    fig_grafo.legend(handles=leyenda, loc="lower center", ncol=3, fontsize=9, frameon=False)
    fig_grafo.tight_layout(rect=[0, 0.05, 1, 0.93])


anim_grafo = FuncAnimation(fig_grafo, dibujar_frame_grafo, frames=max_len,
                            interval=VELOCIDAD_ANIMACION_MS, repeat=True)


# --- ventana 2: resultados --------------------------------------------------

fig_resultados, (ax_curve, ax_bar) = plt.subplots(2, 1, figsize=(7.5, 8.5))
fig_resultados.suptitle(f"Resultados de la simulacion  (seed={SEED})",
                         fontsize=14, fontweight="bold")
fig_resultados.patch.set_facecolor("#fafafa")

COLORES_ESTRATEGIA = {
    "baseline": "#adb5bd",
    "random": "#f4a261",
    "betweenness": "#2a9d8f",
    "maxflow_mincut": "#264653",
    "greedy": "#e63946",
}


def _estilizar_ejes(ax):
    ax.set_facecolor("#fafafa")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#dee2e6", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def dibujar_frame_resultados(t):
    """Dibuja el frame t de la curva de activados; el panel de barras es
    el mismo en todos los frames (comparacion final entre estrategias).

    Args:
        t: paso de tiempo actual (0 a max_len - 1).
    """
    ax_curve.clear()
    ax_bar.clear()
    _estilizar_ejes(ax_curve)
    _estilizar_ejes(ax_bar)

    xs = range(t + 1)
    ax_curve.plot(xs, curva_baseline[: t + 1], color=COLOR_ACTIVO, marker="o",
                   markersize=5, linewidth=2, zorder=3)
    ax_curve.fill_between(xs, curva_baseline[: t + 1], color=COLOR_ACTIVO,
                            alpha=0.15, zorder=2)
    ax_curve.set_xlim(0, max(max_len - 1, 1))
    ax_curve.set_ylim(0, max(curva_baseline) + 1)
    ax_curve.set_title("Nodos activados por paso (sin intervencion)", fontsize=11, pad=10)
    ax_curve.set_xlabel("paso de tiempo (t)")
    ax_curve.set_ylabel("# activados")

    nombres = list(resultados.keys())
    valores = [resultados[n]["avg_size"] for n in nombres]
    colores_barras = [COLORES_ESTRATEGIA.get(n, "#6c757d") for n in nombres]
    barras = ax_bar.bar(nombres, valores, color=colores_barras, zorder=3,
                          edgecolor="white", linewidth=1.2)
    for barra, valor in zip(barras, valores):
        ax_bar.text(barra.get_x() + barra.get_width() / 2, valor + max(valores) * 0.02,
                     f"{valor:.1f}", ha="center", va="bottom", fontsize=9)
    ax_bar.set_ylim(0, max(valores) * 1.18)
    ax_bar.set_title(f"Tamaño promedio de cascada por estrategia\n"
                      f"(n_remove={N_REMOVE}, {N_SIMULATIONS} simulaciones Monte Carlo)",
                      fontsize=11, pad=10)
    ax_bar.set_ylabel("# nodos activados (promedio)")
    ax_bar.tick_params(axis="x", rotation=15)

    fig_resultados.tight_layout(rect=[0, 0, 1, 0.93])


anim_resultados = FuncAnimation(fig_resultados, dibujar_frame_resultados, frames=max_len,
                                 interval=VELOCIDAD_ANIMACION_MS, repeat=True)

plt.show()

# anim_grafo.save("propagacion_grafo.gif", writer="pillow", fps=2)
# anim_resultados.save("propagacion_resultados.gif", writer="pillow", fps=2)
