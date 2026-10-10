import pandas as pd
import numpy as np


class SmurfingDetector:
    """
    Motor de Detección de Patrones de Estructuración (Smurfing / Pitufeo).
    
    Aplica operaciones vectorizadas sobre ventanas temporales móviles (rolling windows)
    por cliente para identificar microtransacciones de alta frecuencia que superan
    umbrales de reporte acumulados.
    """

    def __init__(
        self,
        time_window_minutes: int = 60,
        single_tx_max_threshold: float = 500.0,
        accumulated_min_threshold: float = 1000.0,
    ):
        """
        Parámetros de configuración del detector:
        -----------------------------------------
        :param time_window_minutes: Ventana de tiempo a evaluar en minutos (ej. 60 min).
        :param single_tx_max_threshold: Monto máximo de transacción individual a considerar (< $500 USD).
        :param accumulated_min_threshold: Umbral acumulado que genera la alerta (>= $1,000 USD).
        """
        self.time_window = f"{time_window_minutes}min"
        self.single_tx_max_threshold = single_tx_max_threshold
        self.accumulated_min_threshold = accumulated_min_threshold

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Asegura el tipado de fechas y el orden temporal por cliente.
        """
        df_proc = df.copy()
        
        # Validar y convertir timestamp
        if not pd.api.types.is_datetime64_any_dtype(df_proc["timestamp"]):
            df_proc["timestamp"] = pd.to_datetime(df_proc["timestamp"])

        # Ordenar por cliente y tiempo (Indispensable para rolling windows)
        return df_proc.sort_values(by=["customer_id", "timestamp"]).reset_index(drop=True)

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ejecuta el algoritmo de detección de estructuración.

        :param df: DataFrame transaccional de entrada.
        :return: DataFrame enriquecido con 'is_smurfing' y métricas explicativas.
        """
        # Preparar y ordenar datos
        df_sorted = self._prepare_dataframe(df)

        # Filtrar transacciones que cumplen la condición de bajo valor (< $500 USD)
        # Transacciones >= $500 no forman parte del patrón de pitufeo bajo esta regla
        mask_low_value = df_sorted["amount_USD"] < self.single_tx_max_threshold

        # Crear una serie temporal auxiliar solo con los valores válidos para la suma móvil
        df_low_val = df_sorted[mask_low_value].copy()

        if df_low_val.empty:
            # Caso borde: Sin transacciones de bajo valor
            df_sorted["accumulated_amount_window"] = 0.0
            df_sorted["tx_count_window"] = 0
            df_sorted["is_smurfing"] = False
            return df_sorted

        # Cálculo Vectorizado con Rolling Window sobre índice Datetime
        # Se agrupa por customer_id y se aplica ventana móvil de N minutos
        rolling_calc = (
            df_low_val.set_index("timestamp")
            .groupby("customer_id")["amount_USD"]
            .rolling(self.time_window)
        )

        # Cálculo de Suma Acumulada y Conteo en la ventana
        df_low_val["accumulated_amount_window"] = rolling_calc.sum().values
        df_low_val["tx_count_window"] = rolling_calc.count().values

        # Cruzar resultados calculados de vuelta al DataFrame completo
        df_result = pd.merge(
            df_sorted,
            df_low_val[["transaction_id", "accumulated_amount_window", "tx_count_window"]],
            on="transaction_id",
            how="left",
        )

        # Rellenar nulos (transacciones >= $500 no acumulan para esta regla)
        df_result["accumulated_amount_window"] = df_result["accumulated_amount_window"].fillna(0.0)
        df_result["tx_count_window"] = df_result["tx_count_window"].fillna(0).astype(int)

        # Regla Lógica para marcar 'is_smurfing'
        # Condición A: Transacción individual < $500 USD
        # Condición B: Suma acumulada en los últimos 60 min >= $1,000 USD
        # Condición C: Debe ser resultado de al menos 2 transacciones fraccionadas
        df_result["is_smurfing"] = (
            (df_result["amount_USD"] < self.single_tx_max_threshold)
            & (df_result["accumulated_amount_window"] >= self.accumulated_min_threshold)
            & (df_result["tx_count_window"] >= 2)
        )

        return df_result


# Imortar dataframe limpio
df_laft_clean = pd.read_csv('./data/silver/dataset_riesgo_laft_silver.csv', encoding="utf-8")


# Instanciar el detector con los parámetros solicitados
smurfing_engine = SmurfingDetector(
    time_window_minutes=60,       # Ventana <= 60 minutos
    single_tx_max_threshold=500,  # Transacciones < $500 USD
    accumulated_min_threshold=1000 # Umbral acumulado >= $1,000 USD
)

# Procesar tu dataset
df_enriquecido = smurfing_engine.detect(df_laft_clean)

# Revisar resultados del Módulo I
alertas_detectadas = df_enriquecido["is_smurfing"].sum()
pct_alertas = (alertas_detectadas / len(df_enriquecido)) * 100

print(f"Total transacciones analizadas: {len(df_enriquecido)}")
print(f"Transacciones marcadas con is_smurfing: {alertas_detectadas} ({pct_alertas:.2f}%)")

# Mostrar una muestra de las alertas detectadas
df_enriquecido_a = df_enriquecido.copy()
print(df_enriquecido_a[df_enriquecido_a["is_smurfing"]][
    ["transaction_id", "customer_id", "timestamp", "amount_USD", "merchant_or_receiver", "accumulated_amount_window", "tx_count_window", "is_smurfing"]
].head(20))

# Guardado del dataframe modulo 1
df_enriquecido.to_csv("./data/gold/dataset_riesgo_laft_gold_modulo1.csv", sep=",", index=False, encoding="utf-8")