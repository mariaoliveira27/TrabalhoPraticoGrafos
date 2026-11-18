"""Benchmark reproduzível de Dijkstra e Bellman-Ford no snapshot local.

Execute na raiz: python codigo/benchmark_rotas.py
A busca cronometrada inclui reconstrução e exclui leitura/montagem do grafo.
"""
import csv
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codigo"))
from mapa import carregar_mapa, construir_grafo  # noqa: E402
from rotas import calcularRotaDijkstra, calcularRotaBellmanFord  # noqa: E402
from grafo import CRITERIO_DISTANCIA, CRITERIO_TEMPO, CRITERIO_CUSTO  # noqa: E402

MAP_FILE = ROOT / "codigo" / "dados" / "mapa.json"
TABLES = ROOT / "artefatos" / "resultados" / "tabelas"
FIGURES = ROOT / "artefatos" / "resultados" / "figuras"
REPETITIONS = 20
SEED = 20261118
ALGORITHMS = {
    "Dijkstra": calcularRotaDijkstra,
    "Bellman-Ford": calcularRotaBellmanFord,
}
CRITERIA = [CRITERIO_DISTANCIA, CRITERIO_TEMPO, CRITERIO_CUSTO]


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    graph = construir_grafo(carregar_mapa(str(MAP_FILE)))
    vertex_ids = sorted(graph.vertices)
    pairs = [(origin, destination) for origin in vertex_ids for destination in vertex_ids if origin != destination]
    rng = random.Random(SEED)
    rng.shuffle(pairs)
    raw_rows = []
    grouped = {}

    for criterion in CRITERIA:
        for origin, destination in pairs:
            # Aquecimento dos dois algoritmos para a mesma consulta.
            warm_results = {name: function(graph, origin, destination, criterion)
                            for name, function in ALGORITHMS.items()}
            if warm_results["Dijkstra"].getTotal(criterion) != warm_results["Bellman-Ford"].getTotal(criterion):
                raise AssertionError(f"Custos divergentes: {origin} -> {destination}, {criterion}")
            order = list(ALGORITHMS)
            for repetition in range(1, REPETITIONS + 1):
                if repetition % 2 == 0:
                    order.reverse()
                measured = {}
                for name in order:
                    start = time.perf_counter()
                    result = ALGORITHMS[name](graph, origin, destination, criterion)
                    elapsed = time.perf_counter() - start
                    measured[name] = result
                    raw_rows.append({
                        "algoritmo": name, "criterio": criterion,
                        "origem": origin, "destino": destination,
                        "repeticao": repetition, "situacao": result.situacao,
                        "custo_total": result.getTotal(criterion),
                        "tempo_busca_ms": elapsed * 1000,
                        "nos_expandidos": result.nosExpandidos,
                    })
                if measured["Dijkstra"].getTotal(criterion) != measured["Bellman-Ford"].getTotal(criterion):
                    raise AssertionError(f"Custos divergentes após medição: {origin} -> {destination}, {criterion}")

    raw_path = TABLES / "benchmark_buscas_brutas.csv"
    with raw_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(raw_rows[0]))
        writer.writeheader()
        writer.writerows(raw_rows)

    for row in raw_rows:
        key = (row["algoritmo"], row["criterio"])
        grouped.setdefault(key, {"times": [], "nodes": [], "costs": [], "reachable": 0})
        grouped[key]["times"].append(row["tempo_busca_ms"])
        grouped[key]["nodes"].append(row["nos_expandidos"])
        if row["custo_total"] is not None:
            grouped[key]["costs"].append(row["custo_total"])
            grouped[key]["reachable"] += 1

    summary_rows = []
    for (algorithm, criterion), values in grouped.items():
        summary_rows.append({
            "algoritmo": algorithm, "criterio": criterion,
            "vertices": graph.quantidade_vertices(), "arestas_direcionadas": graph.quantidade_arestas(),
            "pares_origem_destino": len(pairs), "consultas_mensuradas": len(values["times"]),
            "consultas_com_rota": values["reachable"],
            "repeticoes_por_par": REPETITIONS,
            "tempo_mediano_ms": statistics.median(values["times"]),
            "desvio_padrao_ms": statistics.stdev(values["times"]),
            "nos_expandidos_mediana": statistics.median(values["nodes"]),
            "custo_medio_otimo_rotas_encontradas": statistics.mean(values["costs"]) if values["costs"] else "",
        })
    summary_path = TABLES / "benchmark_resumo.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    metadata = {
        "commit_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "estado_codigo": "benchmark executado em working tree com alterações não commitadas; use o script e snapshot registrados para reprodução",
        "instante_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": str(MAP_FILE.relative_to(ROOT)),
        "seed_ordem_pares": SEED,
        "pares": len(pairs),
        "criterios": CRITERIA,
        "repeticoes_por_algoritmo_par_criterio": REPETITIONS,
        "aquecimento": "uma execução por algoritmo para cada par e critério, não cronometrada",
        "cronometro": "time.perf_counter; somente chamada da função de busca e reconstrução",
        "grafo": {"vertices": graph.quantidade_vertices(), "arestas_direcionadas": graph.quantidade_arestas()},
        "python": sys.version,
        "plataforma": platform.platform(),
        "processador": platform.processor(),
        "cpu_logicas": __import__("os").cpu_count(),
        "memoria_ram": "não coletada automaticamente",
        "nos_expandidos": "Dijkstra conta vértices amadurecidos; Bellman-Ford conta vértices examinados nas passadas",
        "custos_conferidos_iguais": True,
    }
    (TABLES / "benchmark_metadados.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.8))
    labels = ["distancia", "tempo", "custo"]
    x = list(range(len(labels)))
    width = 0.36
    for offset, algorithm in [(-width / 2, "Dijkstra"), (width / 2, "Bellman-Ford")]:
        medians = [next(row["tempo_mediano_ms"] for row in summary_rows
                        if row["algoritmo"] == algorithm and row["criterio"] == criterion)
                   for criterion in labels]
        ax.bar([position + offset for position in x], medians, width, label=algorithm)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Tempo mediano por busca (ms)")
    ax.set_title(f"Dijkstra e Bellman-Ford — snapshot local ({len(pairs)} pares, {REPETITIONS} repetições)")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "benchmark_tempo_mediano.png", dpi=160)
    plt.close(fig)
    print(f"Grafo: |V|={graph.quantidade_vertices()}, |E|={graph.quantidade_arestas()}")
    print(f"Pares: {len(pairs)}; repetições: {REPETITIONS}; custo coincidente: sim")
    print(f"CSV bruto: {raw_path}")
    print(f"Resumo: {summary_path}")
    print(f"Gráfico: {FIGURES / 'benchmark_tempo_mediano.png'}")
    for row in summary_rows:
        print(f"{row['algoritmo']} / {row['criterio']}: mediana={row['tempo_mediano_ms']:.6f} ms; nós mediana={row['nos_expandidos_mediana']}")

if __name__ == "__main__":
    main()
