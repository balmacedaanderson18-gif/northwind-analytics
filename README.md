# Northwind Analytics: Business Intelligence & Data Architecture

Proyecto integral académico y profesional de Ingeniería de Datos, Modelado Relacional, Inteligencia de Negocios y Aplicación Full-Stack a partir del dataset original `data/northwind.xlsx`.

Este proyecto cumple rigurosamente con la prohibición de usar datos simulados: **el 100% de las métricas, KPIs, consultas y visualizaciones provienen directamente de los registros reales del archivo Excel**.

---

## 🚀 Arquitectura General del Sistema

El proyecto está diseñado bajo una arquitectura modular de tres capas:

```
northwind-db-dashboard/
├── app/                              # Aplicación Web Full-Stack
│   ├── main.py                       # Backend API con FastAPI y endpoints analíticos
│   └── static/                       # Frontend SPA (Vanilla JS + CSS Glassmorphism + Chart.js)
│       ├── index.html                # Estructura semántica con vistas interactivas
│       ├── css/styles.css            # Sistema de diseño dark-mode premium
│       └── js/dashboard.js           # Orquestación reactiva, filtros dinámicos y gráficos
├── data/
│   └── northwind.xlsx                # Origen de datos maestro (13 hojas)
├── database/
│   ├── schema_sqlite.sql             # DDL Relacional para SQLite (PK, FK, CHECKs, Índices)
│   ├── schema_postgres.sql           # DDL Relacional compatible con PostgreSQL
│   ├── northwind.db                  # Base de datos SQLite normalizada y validada
│   └── queries_bi.sql                # Catálogo de consultas analíticas SQL comentadas
├── docs/
│   ├── data_architecture_mer.md      # MER con Mermaid, cardinalidades y esquema físico
│   └── rfm_clustering_methodology.md # Supuestos y matemática de segmentación RFM / K-Means
├── scripts/
│   ├── load_data.py                  # Pipeline ETL de carga controlada y validación de tipos
│   └── rfm_clustering.py             # Motor analítico RFM (cuantiles) y Clustering (K-Means)
├── tests/
│   └── test_integrity_reconciliation.py # Suite de pruebas automatizadas y conciliación contable
├── requirements.txt                  # Dependencias del entorno Python
└── README.md                         # Guía de reproducción y documentación técnica
```

---

## 📊 Conciliación Matemática y Reconciliación de Totales

Fórmula obligatoria de cálculo de Ventas Netas:
$$\text{Ventas Netas} = \sum (\text{unitprice} \times \text{quantity} \times (1 - \text{discount}))$$

| Métrica Contable | Valor en Excel Original | Valor en SQLite Relacional | Discrepancia | Estado |
| :--- | :---: | :---: | :---: | :---: |
| **Ventas Netas Totales** | **$1,265,793.04** | **$1,265,793.04** | **$0.00** | ✅ **Reconciliado** |
| **Ventas Brutas** | $1,354,458.59 | $1,354,458.59 | $0.00 | ✅ **Reconciliado** |
| **Descuentos Comerciales** | $88,665.55 | $88,665.55 | $0.00 | ✅ **Reconciliado** |
| **Fletes Acumulados** | $64,942.69 | $64,942.69 | $0.00 | ✅ **Reconciliado** |
| **Unidades Vendidas** | 51,317 | 51,317 | 0 | ✅ **Reconciliado** |
| **Total Órdenes** | 830 | 830 | 0 | ✅ **Reconciliado** |
| **Líneas de Detalle** | 2,155 | 2,155 | 0 | ✅ **Reconciliado** |
| **Total de Clientes** | 91 | 91 | 0 | ✅ **Reconciliado** |
| **Violaciones de Claves Foráneas**| 0 | 0 (`PRAGMA foreign_key_check`) | 0 | ✅ **100% Íntegra** |

---

## 📈 Vistas y Características del Dashboard Interactivo

1. **Visión General (KPIs Financieros)**:
   - Tarjetas de KPIs: Ventas Netas, Total Órdenes, Ticket Promedio (AOV: $1,525.05), Descuentos y Fletes.
   - Serie temporal mensual interactiva de Ventas Netas vs Descuentos.
   - Desglose porcentual de la composición de ingresos brutos vs descuentos.
2. **Categorías & Productos**:
   - Distribución de ventas netas por línea de producto (Bebidas y Lácteos lideran la facturación).
   - Volumen de unidades despachadas por categoría.
   - Tabla dinámica de Top 15 productos con estado de catálogo, stock en almacén y pedidos pendientes.
3. **Segmentación de Clientes (RFM & Clustering K-Means)**:
   - Scoring 1 a 5 por cuantiles sobre Recencia, Frecuencia y Valor Monetario Neto.
   - Identificación de 7 segmentos estratégicos (*Campeones, Leales, Prometedores, En Riesgo, Perdidos, Necesitan Atención, Prospectos*).
   - Clustering K-Means ($k=4$) con normalización logarítmica y estandarización Z-score.
   - Tabla completa de los 91 clientes auditados.
4. **Fuerza de Ventas & Estructura Organizacional**:
   - Desempeño individual de vendedores ordenado por facturación neta.
   - Jerarquía de mando con supervisión directa (`reportsto`).
5. **Logística & Transportistas**:
   - Rendimiento de envíos, tasa de puntualidad (`requireddate >= shippeddate`), retrasos y costo medio de flete por *Shipper*.
6. **Auditoría & Reconciliación**:
   - Tabla de verificación matemática estricta para auditores de datos.

---

## 🛠️ Instrucciones de Ejecución Local

### Prerrequisitos
- Python 3.10+ instalado en el sistema.

### Paso 1: Clonar o ingresar al directorio del proyecto
```bash
cd northwind-db-dashboard
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Cargar y poblar la Base de Datos Relacional (ETL)
Ejecuta el script que construye las tablas e inserta los datos en orden topológico estricto:
```bash
python scripts/load_data.py
```

### Paso 4: Ejecutar las pruebas automatizadas de integridad y reconciliación
```bash
python tests/test_integrity_reconciliation.py
```
*El resultado debe indicar que todas las pruebas pasaron con 0 discrepancias y 0 violaciones de integridad.*

### Paso 5: Iniciar la Aplicación Web Full-Stack
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abre tu navegador web e ingresa a:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📑 Documentación Adicional
- [data_architecture_mer.md](docs/data_architecture_mer.md): Diagrama Entidad-Relación en Mermaid, cardinalidades y esquema físico.
- [rfm_clustering_methodology.md](docs/rfm_clustering_methodology.md): Supuestos matemáticos de la segmentación RFM y clustering K-Means.
- [queries_bi.sql](database/queries_bi.sql): Consultas SQL analíticas comentadas paso a paso.
