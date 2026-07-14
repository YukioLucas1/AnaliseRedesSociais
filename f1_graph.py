import fastf1
from fastf1.ergast import Ergast
from pathlib import Path
import pandas as pd
from collections import defaultdict
from itertools import combinations
import time

# =========================
# CACHE
# =========================
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

ergast = Ergast()

# =========================
# DOWNLOAD
# =========================
all_dfs = []

for year in range(1994, 2027):
    try:
        res = ergast.get_race_results(season=year, limit=1000)

        if res.content:
            for df_year in res.content:
                df_year = df_year.copy()
                df_year["season"] = year
                all_dfs.append(df_year)

        time.sleep(0.2)

    except Exception as e:
        print(f"Erro {year}: {e}")

df = pd.concat(all_dfs, ignore_index=True)

# =========================
# PADRONIZAÇÃO
# =========================
df = df.rename(columns={
    "constructorName": "team"
})

df = df.dropna(subset=["driverId", "team", "season"])
df["season"] = df["season"].astype(int)

# =========================
# NODES (MODELO DA SUA IMAGEM)
# =========================
def build_nodes(df_subset):
    nodes = df_subset[[
        "driverId",
        "givenName",
        "familyName",
        "driverNationality"
    ]].drop_duplicates()

    nodes["Label"] = nodes["givenName"] + " " + nodes["familyName"]

    nodes = nodes.rename(columns={
        "driverId": "Id",
        "driverNationality": "Nationality"
    })

    return nodes[["Id", "Label", "Nationality"]]

# =========================
# EDGES
# =========================
def build_edges(df_subset):
    edges = defaultdict(int)

    grouped = df_subset.groupby(["season", "team"])

    for (_, _), group in grouped:
        drivers = group["driverId"].unique()

        for d1, d2 in combinations(sorted(drivers), 2):
            edges[(d1, d2)] += 1

    return edges

# =========================
# EXPORT NO MODELO DA IMAGEM
# =========================
def export_graph(prefix, df_subset):
    nodes = build_nodes(df_subset)
    edges = build_edges(df_subset)

    # 🔵 NODES (como na imagem)
    nodes.to_csv(f"{prefix}_nodes.csv", index=False)

    # 🔴 EDGES (como na imagem)
    edges_df = pd.DataFrame(
        [(a, b, w) for (a, b), w in edges.items()],
        columns=["Source", "Target", "Weight"]
    )
    edges_df.to_csv(f"{prefix}_edges.csv", index=False)

    print(f"Exportado: {prefix}")

# =========================
# 3 GRAFOS
# =========================
periodos = {
    "graph_2016_2026": df[(df["season"] >= 2016)],
    "graph_2005_2015": df[(df["season"] >= 2005) & (df["season"] <= 2015)],
    "graph_1994_2004": df[(df["season"] >= 1994) & (df["season"] <= 2004)],
}

for name, subset in periodos.items():
    print(f"\nProcessando {name}")
    export_graph(name, subset)

print("\nFinalizado.")