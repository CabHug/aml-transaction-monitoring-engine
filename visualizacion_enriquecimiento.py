"""
Enriquecimiento simple para Power BI.
Uso: python enriquecer_simple.py entrada.csv salida.csv
"""
import sys
import numpy as np
import pandas as pd

UMBRAL_USD = 1_000  # umbral de reporte


def enriquecer(df):
    df = df.copy()

    # Tiempo
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["fecha"] = df["timestamp"].dt.normalize()
    df["anio_mes"] = df["timestamp"].dt.strftime("%Y-%m")
    df["dia_semana"] = df["timestamp"].dt.day_name()
    df["dia_semana_num"] = df["timestamp"].dt.dayofweek + 1  # 1 = lunes (para ordenar en BI)
    df["hora"] = df["timestamp"].dt.hour
    df["franja_horaria"] = pd.cut(
        df["hora"], bins=[-1, 5, 11, 17, 23],
        labels=["Madrugada", "Mañana", "Tarde", "Noche"]).astype(str)

    # Monto
    u = UMBRAL_USD
    cortes = [-np.inf, u * 0.05, u * 0.10, u * 0.50, u * 0.90, u, np.inf]
    etiquetas = ["Muy bajo", "Bajo", "Medio", "Alto", "Cerca del umbral", "Sobre el umbral"]
    df["rango_monto"] = pd.cut(df["amount_USD"], bins=cortes, labels=etiquetas).astype(str)
    df["cerca_umbral"] = (df["amount_USD"] >= u * 0.9) & (df["amount_USD"] < u)

    # Receptor concentrado (muchos clientes distintos hacia el mismo receptor)
    n_cli = df.groupby("merchant_or_receiver")["customer_id"].transform("nunique")
    df["n_clientes_receptor"] = n_cli
    df["receptor_concentrado"] = n_cli >= max(n_cli.quantile(0.90), 3)

    # Score de riesgo compuesto (0-100)
    nlp = df["nlp_risk_score"]
    nlp = nlp / nlp.max() if nlp.max() > 1 else nlp
    df["score_riesgo"] = (100 * (
        0.35 * nlp
        + 0.30 * df["is_smurfing"].astype(float)
        + 0.20 * df["fuera_de_clustering"].astype(float)
        + 0.15 * df["receptor_concentrado"].astype(float)
    )).round(2)
    df["categoria_riesgo"] = pd.cut(
        df["score_riesgo"], bins=[-0.01, 25, 50, 75, 100.01],
        labels=["Bajo", "Medio", "Alto", "Crítico"]).astype(str)

    # Descripción vacía
    df["sin_descripcion"] = df["payment_description"].isna()

    return df


df = pd.read_csv("./data/gold/dataset_riesgo_laft_gold_NLP_riskscore_modulo3.csv")
out = enriquecer(df)
out.to_csv("./data/gold/dataset_riesgo_laft_gold_visual_enriquecido.csv", index=False, encoding="utf-8-sig")
print(f"OK: {out.shape[0]} filas x {out.shape[1]} columnas")