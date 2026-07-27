# Propagación de desinformación en redes sociales

Modelado de la propagación de información falsa en una red social representada como
un grafo, con estrategias de intervención para minimizar su alcance.

## Descripción

Este proyecto simula la propagación de desinformación sobre redes sociales sintéticas
mediante el *Independent Cascade Model* (ICM), y evalúa distintas estrategias para
mitigar su alcance removiendo un subconjunto de usuarios de la red: remoción aleatoria
(control), centralidad de intermediación (*betweenness*), corte mínimo de vértices
(Max-Flow/Min-Cut) y una estrategia *greedy* basada en simulación de Monte Carlo.

Las redes se generan sintéticamente mediante los modelos Erdős–Rényi y
Barabási-Albert, como grafos dirigidos que representan relaciones asimétricas de
seguimiento (análogas a Twitter/X o Instagram). El sistema incluye un dashboard
interactivo para visualizar la comparación entre estrategias.

## Integrantes

- Miguel Angel Sánchez Sandoval
- Sebastián González Torres
- Sebastián Polo Álvarez

Curso: Matemáticas Discretas I — Universidad Nacional de Colombia
Docente: Jhoan Sebastián Tenjo García

## Estado actual

- [x] Generación de red simulada (Erdős–Rényi y Barabási-Albert)
- [x] Independent Cascade Model
- [x] Estrategia de intervención por centralidad (betweenness)
- [x] Estrategias adicionales (greedy, Max-Flow/Min-Cut, aleatoria)
- [x] Visualización comparativa (dashboard)

## Requisitos

- Python 3.11 (otras versiones, especialmente 3.14, pueden dar problemas con numpy/matplotlib)

## Instalación

```bash
git clone https://github.com/miguelss304/Modelo-de-Propagacion-y-Mitigacion-de-Desinformacion-en-Redes.git
cd Modelo-de-Propagacion-y-Mitigacion-de-Desinformacion-en-Redes
python -m venv venv
source venv/Scripts/activate   # Git Bash en Windows; Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

El programa pide por consola los parámetros del experimento (número de nodos, modelo
de red, grado promedio, probabilidad de activación, número de semillas, nodos a
remover, etc.), mostrando el valor por defecto entre corchetes. Presionar Enter en
cada campo usa ese valor por defecto.

Al finalizar, el programa:
1. Imprime un resumen del grafo generado (nodos, aristas, densidad, conexidad).
2. Compara las cinco estrategias de intervención y muestra sus métricas en consola.
3. Guarda el grafo generado en `data/example_graph.gml` como respaldo.
4. Abre un dashboard interactivo con la comparación visual de estrategias.

## Ejemplo de uso

```bash
$ python main.py
============================================================
CONFIGURACIÓN DEL EXPERIMENTO (Enter para usar el valor por defecto)
============================================================
Número de nodos [100]: 
Modelo (erdos_renyi/barabasi_albert) [barabasi_albert]: 
Grado promedio [4]: 
Semilla del grafo (Enter = aleatoria): 
  -> semilla del grafo generada: 668764
Cantidad de nodos semilla [3]: 
Probabilidad de activación [0.25]: 
Nodos a remover por estrategia [10]: 
Semilla del experimento (Enter = aleatoria): 
  -> semilla del experimento generada: 294181
Estrategia a animar (random/betweenness/maxflow_mincut/greedy) [greedy]: 

============================================================
RESUMEN DEL GRAFO
============================================================
n_nodes: 100
n_edges: 196
density: 0.019797979797979797
avg_degree: 3.92
is_weakly_connected: True

seed_nodes elegidos (top-3 por out-degree): [1, 5, 24]

============================================================
COMPARACIÓN DE ESTRATEGIAS DE INTERVENCIÓN
============================================================

[baseline]
  nodos removidos: []
  tamaño promedio de cascada: 13.32 nodos (13.3%)
  pasos promedio: 3.66
  tiempo promedio de ejecucion : 0.01

[random]
  nodos removidos: [93, 2, 91, 90, 78, 3, 39, 68, 65, 19]
  tamaño promedio de cascada: 12.33 nodos (13.7%)
  pasos promedio: 3.48
  tiempo promedio de ejecucion : 0.00

[betweenness]
  nodos removidos: [0, 3, 6, 8, 39, 11, 9, 12, 38, 10]
  tamaño promedio de cascada: 9.80 nodos (10.9%)
  pasos promedio: 2.90
  tiempo promedio de ejecucion : 0.02

[maxflow_mincut]
  nodos removidos: [7, 22, 6, 9, 12, 89, 75, 14, 72, 92]
  tamaño promedio de cascada: 11.21 nodos (12.5%)
  pasos promedio: 3.19
  tiempo promedio de ejecucion : 0.14

[greedy]
  nodos removidos: [7, 0, 3, 11, 23, 43, 8, 20, 33, 37]
  tamaño promedio de cascada: 7.34 nodos (8.2%)
  pasos promedio: 2.58
  tiempo promedio de ejecucion : 1.27
  ```

## Estructura del repositorio

```bash
.
├── main.py                # Orquestador: genera la red, corre el experimento, muestra el dashboard
├── Graph_Interface.py     # Dashboard de visualización
├── src/
│   ├── graph_model.py     # Generación de redes (Erdős–Rényi, Barabási-Albert)
│   ├── cascade.py         # Independent Cascade Model
│   ├── intervention.py    # Estrategias de intervención sobre la red
│   └── metrics.py         # Estimación Monte Carlo y comparación de estrategias
├── data/
│   └── example_graph.gml  # Grafo de ejemplo guardado tras una ejecución
└── requirements.txt
```

## Nota sobre el uso de IA

Durante el desarrollo de este trabajo se utilizó inteligencia artificial (Claude, de Anthropic) como herramienta de apoyo en distintas etapas del proyecto, dado que Python no es un lenguaje con el que el equipo tenga experiencia previa consolidada.

El uso se concentró en las siguientes áreas:

- **Implementación en Python:** apoyo con sintaxis del lenguaje, manejo de estructuras de datos, uso de las librerías `networkx`,`matplotlib` , y depuración de errores en el código.
- **Generación de visualizaciones:** creación de las gráficas a partir de los datos numéricos producidos por las simulaciones del equipo.
- **Redacción y formato:** apoyo en la redacción de tablas, discusión de resultados y conclusiones del informe, a partir del análisis y las decisiones tomadas por los integrantes del equipo.

La formulación matemática del problema, la selección de los modelos de generación de redes, la definición del Independent Cascade Model y de las estrategias de intervención, las decisiones de diseño del sistema, y la ejecución y verificación de todas las simulaciones reportadas en este proyecto, fueron realizadas por los integrantes del equipo a partir de los conceptos vistos en el curso de Matemáticas Discretas o investigados por cuenta propia. Todos los resultados numéricos presentados corresponden a ejecuciones reales del sistema implementado, verificadas directamente por los integrantes antes de su inclusión en el informe.