"""
Dashboard animado de propagacion de desinformacion.
Usa graph_model.py, cascade.py, intervention.py y metrics.py del proyecto.

Ventana 1: cascada animada, baseline vs. una estrategia de mitigacion.
Ventana 2: curva de activados + comparacion final entre estrategias.
"""

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

from src.cascade import run_cascade_with_history

COLOR_ACTIVO = "#e63946"
COLOR_INACTIVO = "#b8c4d0"
COLOR_REMOVIDO = "#148D38"

COLORES_ESTRATEGIA = {
    "baseline": "#adb5bd",
    "random": "#f4a261",
    "betweenness": "#2a9d8f",
    "maxflow_mincut": "#264653",
    "greedy": "#e63946",
}


def mostrar_dashboard(G, seed_nodes, probability, n_remove, n_simulations,
                       resultados, estrategia_a_animar, seed,
                       velocidad_animacion_ms=1800):
    """Muestra el dashboard animado de propagacion y comparacion de estrategias.

    Args:
        G: grafo original (sin intervenir), ya con posiciones reproducibles.
        seed_nodes: nodos que originan la fake news.
        probability: probabilidad de activacion por arista.
        n_remove: cantidad de nodos removidos por estrategia (solo para el titulo).
        n_simulations: simulaciones Monte Carlo usadas (solo para el titulo).
        resultados: dict devuelto por metrics.compare_strategies(G, ...).
        estrategia_a_animar: nombre de la estrategia a mostrar junto al baseline
            en la Ventana 1 (debe ser una clave de `resultados`).
        seed: semilla usada en el experimento (solo para mostrar en pantalla).
        velocidad_animacion_ms: milisegundos entre frames de la animacion.
    """
    pos = nx.spring_layout(G, seed=seed, k= 20 / (G.number_of_nodes() ** 0.5),
                            iterations=300)

    G_baseline = G.copy()
    historial_baseline = run_cascade_with_history(G_baseline, seed_nodes, probability, seed)
    curva_baseline = [len(paso) for paso in historial_baseline]

    G_intervenido = resultados[estrategia_a_animar]["graph"]
    seeds_sobrevivientes = [s for s in seed_nodes if s in G_intervenido]
    if seeds_sobrevivientes:
        historial_estrategia = run_cascade_with_history(
            G_intervenido, seeds_sobrevivientes, probability, seed
        )
    else:
        historial_estrategia = [set()]

    max_len = max(len(historial_baseline), len(historial_estrategia))
    historial_baseline_ext = historial_baseline + [historial_baseline[-1]] * (max_len - len(historial_baseline))
    historial_estrategia_ext = historial_estrategia + [historial_estrategia[-1]] * (max_len - len(historial_estrategia))

    # --- ventana 1: grafo animado -------------------------------------------

    fig_grafo, (ax_baseline, ax_estrategia) = plt.subplots(1, 2, figsize=(15, 8))
    fig_grafo.suptitle(f"Cascada de desinformacion: baseline vs. intervencion  (seed={seed})",
                        fontsize=14, fontweight="bold")
    fig_grafo.patch.set_facecolor("#fafafa")

    def _dibujar_grafo_en(ax, G_dibujo, activos, titulo):
        ax.clear()
        colores = [COLOR_ACTIVO if n in activos else COLOR_INACTIVO for n in G_dibujo.nodes()]
        nx.draw_networkx_edges(G_dibujo, pos, ax=ax, alpha=0.25, width=0.8,
                                arrows=True, arrowsize=8)
        nx.draw_networkx_nodes(G_dibujo, pos, ax=ax, node_color=colores, node_size=180,
                                edgecolors="white", linewidths=0.8)
        removidos = [n for n in G.nodes() if n not in G_dibujo.nodes()]
        if removidos:
            nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=removidos,
                                    node_color=COLOR_REMOVIDO, node_size=180,
                                    edgecolors="white", linewidths=0.8)
        ax.set_title(titulo, fontsize=10)
        ax.axis("off")

    def dibujar_frame_grafo(t):
        _dibujar_grafo_en(
            ax_baseline, G_baseline, historial_baseline_ext[t],
            f"Sin intervencion -- paso {t}/{max_len - 1} "
            f"({len(historial_baseline_ext[t])} activados)",
        )
        _dibujar_grafo_en(
            ax_estrategia, G_intervenido, historial_estrategia_ext[t],
            f"Estrategia: {estrategia_a_animar} -- paso {t}/{max_len - 1} "
            f"({len(historial_estrategia_ext[t])} activados)",
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
                                interval=velocidad_animacion_ms, repeat=True)

    # --- ventana 2: resultados ----------------------------------------------

    fig_resultados, (ax_curve, ax_bar) = plt.subplots(2, 1, figsize=(7.5, 8.5))
    fig_resultados.suptitle(f"Resultados de la simulacion  (seed={seed})",
                             fontsize=14, fontweight="bold")
    fig_resultados.patch.set_facecolor("#fafafa")

    def _estilizar_ejes(ax):
        ax.set_facecolor("#fafafa")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color="#dee2e6", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

    def dibujar_frame_resultados(t):
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
        valores_pct = [resultados[n]["avg_pct"] for n in nombres]
        pct_baseline = resultados["baseline"]["avg_pct"]
        colores_barras = [COLORES_ESTRATEGIA.get(n, "#6c757d") for n in nombres]
        barras = ax_bar.bar(nombres, valores_pct, color=colores_barras, zorder=3,
                             edgecolor="white", linewidth=1.2)
        for barra, valor, nombre in zip(barras, valores_pct, nombres):
            etiqueta = f"{valor:.1f}%"
            if nombre != "baseline" and pct_baseline > 0:
                reduccion = (pct_baseline - valor) / pct_baseline * 100
                etiqueta += f"\n(-{reduccion:.0f}%)"
            ax_bar.text(barra.get_x() + barra.get_width() / 2, valor + max(valores_pct) * 0.02,
                        etiqueta, ha="center", va="bottom", fontsize=8.5)
        ax_bar.set_ylim(0, max(valores_pct) * 1.28)
        ax_bar.set_title(f"% de la red afectada por estrategia\n"
                         f"(n_remove={n_remove}, {n_simulations} simulaciones Monte Carlo)",
                         fontsize=11, pad=10)
        ax_bar.set_ylabel("% de nodos activados (promedio)")
        ax_bar.tick_params(axis="x", rotation=15)

        fig_resultados.tight_layout(rect=[0, 0, 1, 0.93])

    anim_resultados = FuncAnimation(fig_resultados, dibujar_frame_resultados, frames=max_len,
                                    interval=velocidad_animacion_ms, repeat=True)

    # --- ventana 3: tiempo de ejecucion por estrategia -----------------------

    fig_tiempo, ax_tiempo = plt.subplots(figsize=(7.5, 5))
    fig_tiempo.suptitle(f"Tiempo de ejecucion por estrategia  (seed={seed})",
                         fontsize=14, fontweight="bold")
    fig_tiempo.patch.set_facecolor("#fafafa")
    ax_tiempo.set_facecolor("#fafafa")
    ax_tiempo.spines["top"].set_visible(False)
    ax_tiempo.spines["right"].set_visible(False)
    ax_tiempo.grid(axis="y", color="#dee2e6", linewidth=0.8, zorder=0)
    ax_tiempo.set_axisbelow(True)

    nombres = list(resultados.keys())
    tiempos = [resultados[n]["runtime_sec"] for n in nombres]
    colores_barras = [COLORES_ESTRATEGIA.get(n, "#6c757d") for n in nombres]
    barras_tiempo = ax_tiempo.bar(nombres, tiempos, color=colores_barras, zorder=3,
                                   edgecolor="white", linewidth=1.2)
    for barra, valor in zip(barras_tiempo, tiempos):
        ax_tiempo.text(barra.get_x() + barra.get_width() / 2, valor + max(tiempos) * 0.02,
                        f"{valor:.2f}s", ha="center", va="bottom", fontsize=9)
    ax_tiempo.set_ylim(0, max(tiempos) * 1.18)
    ax_tiempo.set_title(f"Incluye seleccion de nodos + {n_simulations} simulaciones Monte Carlo",
                         fontsize=10, pad=10)
    ax_tiempo.set_ylabel("segundos")
    ax_tiempo.tick_params(axis="x", rotation=15)
    fig_tiempo.tight_layout(rect=[0, 0, 1, 0.90])

    plt.show()