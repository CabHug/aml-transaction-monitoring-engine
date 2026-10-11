# 🛡️ AML Transaction Risk Engine & Compliance Pipeline (Medallion Architecture)

> **Prototipo de motor de riesgo híbrido (Reglas + ML)** para la prevención de Lavado de Activos y Financiación del Terrorismo (**LAFT / SAGRILAFT**). La solución implementa un flujo de ingeniería de datos estructurado en **Arquitectura Medallion (Bronze, Silver y Gold)** para procesar y enriquecer registros transaccionales.

---

## 📌 Resumen del Proyecto

Este proyecto aborda los desafíos del equipo de Compliance al modernizar el monitoreo transaccional transfronterizo y multimoneda (COP/MXN/USD). El objetivo principal es reducir la fricción con usuarios legítimos minimizando falsos positivos mediante un enfoque analítico modular:
* **Ingeniería de Datos Escalable:** Ingesta y estructuración mediante la arquitectura Medallion.
* **Módulo I:** Detección eficiente de patrones de estructuración (*Smurfing / Pitufeo*) en ventanas deslizantes.
* **Módulo II:** Segmentación no supervisada con K-Means y validación por Silueta para identificar arquetipos de riesgo.
* **Módulo III:** Análisis semántico de texto (NLP con TF-IDF y Lexicon Bias) para evaluar la intencionalidad de las transacciones.
* **Módulo IV:** Integración de un *Adjusted Risk Score* para tableros ejecutivos en Business Intelligence.

---

## 🎯 Objetivos de la Practica

- Diseñar un motor de riesgo híbrido escalable para mitigar tipologías de lavado no detectadas por reglas estáticas.
- Implementar la **Arquitectura Medallion** para asegurar la calidad, trazabilidad y optimización del dataset transaccional.
- Detectar operaciones de alta velocidad y bajo valor (smurfing) inferiores a los umbrales de reporte estándar.
- Desarrollar un modelo de clustering no supervisado para transitar de *hard-rules* a arquetipos de comportamiento.
- Enriquecer el scoring con un pipeline de Procesamiento de Lenguaje Natural (NLP) sobre las glosas de pago.

---

## 🏗️ Arquitectura Medallion del Pipeline

```text
               dataset_riesgo_laft.csv (Raw)
                            │
                            ▼
                    ┌─────────────────┐
                    │     BRONZE      │
                    │ Ingesta & Schema│
                    │ CSV → Parquet   │
                    └─────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │     SILVER      │
                    │ Limpieza, Rules │
                    │ & Módulo I      │
                    │ (is_smurfing)   │
                    └─────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │      GOLD       │
                    │ Módulos II & III│
                    │ Clustering KMeans│
                    │ & NLP Risk Score│
                    └─────────────────┘
                            │
                            ▼
               Dataset Enriquecido & Dashboards

aml-transaction-risk-engine/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── README.md
└── dataset_EDA.ipynb
└── modulo_1.py
└── modulo_2.ipynb
└── modulo_3.ipynb
└── visualizacion_enriquecimiento.py



