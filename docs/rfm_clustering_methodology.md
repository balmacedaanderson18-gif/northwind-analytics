# Documentación Metodológica: Segmentación RFM y Clustering K-Means

## 1. Contexto y Objetivos de Negocio
El objetivo de este módulo es clasificar y segmentar los **91 clientes** registrados en la base de datos Northwind para identificar clientes clave (VIP/Campeones), compradores habituales, cuentas en riesgo de abandono y prospectos sin órdenes.

---

## 2. Supuestos y Definición de Variables RFM

### A. Ventas Netas Reales (Monetary)
Para garantizar la exactitud contable, el valor monetario se calculó estrictamente con la fórmula de ventas netas tras deducción de descuentos comerciales:
$$\text{Monetary}(c) = \sum_{i \in \text{Líneas}(c)} \left( \text{unitprice}_i \times \text{quantity}_i \times (1 - \text{discount}_i) \right)$$
Se excluyen impuestos y fletes no atribuibles al producto en sí mismo.

### B. Fecha de Corte y Recencia (Recency)
- **Fecha máxima de orden registrada**: `1998-05-06`
- **Fecha de Referencia de Corte ($\text{Fecha}_{\text{ref}}$)**: `1998-05-07` (el día inmediatamente posterior al cierre operativo del negocio).
- **Recencia en días**: 
$$\text{Recency}(c) = \text{Fecha}_{\text{ref}} - \max(\text{OrderDate}_c)$$
Un valor menor de recencia indica un cliente activo y reciente.

### C. Frecuencia (Frequency)
- Representa el número de transacciones u órdenes de compra únicas formalizadas por cada cliente:
$$\text{Frequency}(c) = \text{COUNT(DISTINCT } \text{OrderID}_c)$$

### D. Tratamiento de Clientes Sin Órdenes
Existen 2 clientes en el maestro sin compras registradas:
- `FISSA`: *FISSA Fabrica Inter. Salchichas S.A.* (España)
- `PARIS`: *Paris spécialités* (Francia)
**Supuesto**: No se eliminan del análisis. Se clasifican de forma determinista como **"Prospectos Sin Órdenes (Lead)"**, con Frecuencia = 0, Monetary = $0.00 y Recency máxima imputada (+30 días), preservando la integridad del catálogo de 91 clientes.

---

## 3. Modelo 1: Segmentación RFM por Cuantiles (Scoring 1 a 5)

A los 89 clientes activos se les asignó una puntuación del 1 al 5 en cada dimensión mediante cuantiles (`qcut` con desempate determinista):
- **R_Score (1 a 5)**: Cuantil invertido (5 = más reciente, 1 = más antiguo).
- **F_Score (1 a 5)**: Cuantil directo (5 = mayor frecuencia de órdenes).
- **M_Score (1 a 5)**: Cuantil directo (5 = mayor facturación neta).

### Reglas Semánticas de Negocio:
1. **Campeones (Champions)** ($R \ge 4$ y $\frac{F+M}{2} \ge 4$): Clientes que compran recientemente, con alta frecuencia y gran volumen de gasto. Son los embajadores de la marca.
2. **Clientes Leales (Loyal)** ($R \ge 3$ y $\frac{F+M}{2} \ge 3$): Clientes con compras periódicas constantes y buena rentabilidad.
3. **Prometedores Recientes (Promising)** ($R \ge 4$ y $\frac{F+M}{2} \le 2$): Clientes que compraron muy recientemente pero aún tienen pocas órdenes acumuladas. Candidatos ideales para cross-selling.
4. **En Riesgo / Alto Valor (At Risk)** ($R \le 2$ y $\frac{F+M}{2} \ge 4$): Compradores históricos de gran volumen que llevan mucho tiempo sin emitir pedidos. Requieren contacto comercial urgente.
5. **Dormidos / Perdidos (Lost)** ($R \le 2$ y $\frac{F+M}{2} \le 2$): Clientes con escasa frecuencia y baja facturación inactivos desde hace meses.
6. **Necesitan Atención (Need Attention)**: Segmento medio que requiere estímulos promocionales.
7. **Prospectos Sin Órdenes (Lead)**: Clientes registrados sin transacciones.

### Distribución de Clientes Obtenida:
| Segmento RFM | Clientes | Facturación Neta Total | Ticket Medio ($) | Recencia Media (días) |
| :--- | :---: | :---: | :---: | :---: |
| **Campeones (Champions)** | 20 | $692,852.12 | $34,642.61 | 10.2 |
| **Clientes Leales (Loyal)** | 17 | $258,419.80 | $15,201.16 | 29.8 |
| **Necesitan Atención** | 20 | $174,130.40 | $8,706.52 | 44.5 |
| **Dormidos / Perdidos (Lost)**| 20 | $41,208.50 | $2,060.43 | 148.6 |
| **Prometedores Recientes** | 8 | $38,510.15 | $4,813.77 | 12.1 |
| **En Riesgo / Alto Valor** | 4 | $60,672.07 | $15,168.02 | 118.0 |
| **Prospectos Sin Órdenes** | 2 | $0.00 | $0.00 | N/A |
| **TOTAL** | **91** | **$1,265,793.04** | **$13,909.81** | **52.6** |

---

## 4. Modelo 2: Algoritmo No Supervisado (Clustering K-Means)

Para corroborar la validez de los grupos heurísticos, se implementó un modelo de aprendizaje automático no supervisado:
1. **Transformación Logarítmica (`log1p`)**: Se aplicó $\ln(1 + x)$ a `recency`, `frequency` y `monetary` para estabilizar la varianza y corregir la fuerte asimetría positiva en ventas y recencia.
2. **Estandarización (`StandardScaler`)**: Escalado con media 0 y desviación estándar 1 para eliminar sesgos de escala métrica.
3. **K-Means ($k=4$, `random_state=42`)**:
   - **Cluster VIP / Tier 1 (28 clientes)**: Los mayores generadores de facturación y frecuencia.
   - **Cluster Clientes Frecuentes Activos (25 clientes)**: Base transaccional recurrente y estable.
   - **Cluster Compradores Ocasionales Recientes (24 clientes)**: Cuentas nuevas o de pedido único reciente.
   - **Cluster Inactivos o de Bajo Rendimiento (12 clientes)**: Cuentas con alta probabilidad de deserción.
   - **Cluster Sin Historial (2 clientes)**: Prospectos.
