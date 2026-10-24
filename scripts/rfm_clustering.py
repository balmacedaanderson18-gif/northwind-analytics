"""
Módulo de Segmentación de Clientes: Modelo RFM Heurístico & Clustering K-Means
Basado exclusivamente en la fórmula de Ventas Netas: SUM(unitprice * quantity * (1 - discount))
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def compute_rfm_and_clustering(db_path):
    conn = sqlite3.connect(db_path)
    
    # 1. Extracción de Órdenes y Líneas de Venta con Ventas Netas Reales
    query = """
    SELECT 
        o.orderid,
        o.customerid,
        o.orderdate,
        SUM(od.unitprice * od.quantity * (1.0 - od.discount)) AS order_net_sales
    FROM orders o
    JOIN order_details od ON o.orderid = od.orderid
    GROUP BY o.orderid, o.customerid, o.orderdate;
    """
    df_orders = pd.read_sql_query(query, conn)
    df_orders['orderdate'] = pd.to_datetime(df_orders['orderdate'])

    # 2. Catálogo maestro de clientes
    df_customers = pd.read_sql_query("""
        SELECT customerid, companyname, contactname, city, country 
        FROM customers;
    """, conn)
    conn.close()

    # Fecha de corte: 1 día después de la última orden registrada
    ref_date = df_orders['orderdate'].max() + pd.Timedelta(days=1)

    # 3. Agregación RFM por cliente
    rfm = df_orders.groupby('customerid').agg(
        recency=('orderdate', lambda x: (ref_date - x.max()).days),
        frequency=('orderid', 'count'),
        monetary=('order_net_sales', 'sum')
    ).reset_index()

    # Unir con todos los clientes (incluyendo aquellos con 0 órdenes)
    df_rfm = df_customers.merge(rfm, on='customerid', how='left')

    # Para clientes sin órdenes (ej. FISSA, PARIS), recency es infinito o máx, freq=0, monetary=0
    df_rfm['frequency'] = df_rfm['frequency'].fillna(0).astype(int)
    df_rfm['monetary'] = df_rfm['monetary'].fillna(0.0).round(2)
    max_recency = df_rfm['recency'].max()
    df_rfm['recency'] = df_rfm['recency'].fillna(max_recency + 30).astype(int)

    # 4. Segmentación RFM por Cuantiles (Scoring 1-5)
    # Recency: menor es mejor (5 = más reciente)
    # Frequency & Monetary: mayor es mejor (5 = mayor frecuencia/gasto)
    active_mask = df_rfm['frequency'] > 0
    df_active = df_rfm[active_mask].copy()

    # Usamos pd.qcut con rank(method='first') para evitar empates en bins repetidos
    df_active['R_Score'] = pd.qcut(df_active['recency'].rank(method='first', ascending=False), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df_active['F_Score'] = pd.qcut(df_active['frequency'].rank(method='first', ascending=True), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df_active['M_Score'] = pd.qcut(df_active['monetary'].rank(method='first', ascending=True), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def assign_rfm_segment(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        fm = (f + m) / 2.0
        
        if r >= 4 and fm >= 4:
            return "Campeones (Champions)"
        elif r >= 3 and fm >= 3:
            return "Clientes Leales (Loyal)"
        elif r >= 4 and fm <= 2:
            return "Prometedores Recientes (Promising)"
        elif r <= 2 and fm >= 4:
            return "En Riesgo / Alto Valor (At Risk)"
        elif r <= 2 and fm <= 2:
            return "Dormidos / Perdidos (Lost)"
        else:
            return "Necesitan Atención (Need Attention)"

    df_active['rfm_segment'] = df_active.apply(assign_rfm_segment, axis=1)

    # 5. Algoritmo No Supervisado: Clustering K-Means (k=4)
    # Estandarización de características numéricas normalizadas logarítmicamente
    # para mitigar el sesgo por asimetría (skewness) en Monetary y Recency
    features = ['recency', 'frequency', 'monetary']
    df_log = df_active[features].copy()
    df_log['recency'] = np.log1p(df_log['recency'])
    df_log['frequency'] = np.log1p(df_log['frequency'])
    df_log['monetary'] = np.log1p(df_log['monetary'])

    scaler = StandardScaler()
    scaled_matrix = scaler.fit_transform(df_log)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df_active['cluster_id'] = kmeans.fit_predict(scaled_matrix)

    # Mapeo semántico de clusters según sus centroides ordenados por monetary
    cluster_means = df_active.groupby('cluster_id')[['recency', 'frequency', 'monetary']].mean()
    sorted_clusters = cluster_means.sort_values(by='monetary', ascending=False).index.tolist()
    
    cluster_labels = {
        sorted_clusters[0]: "VIP / Tier 1 (Mayor Facturación y Fidelidad)",
        sorted_clusters[1]: "Clientes Frecuentes Activos",
        sorted_clusters[2]: "Compradores Ocasionales Recientes",
        sorted_clusters[3]: "Inactivos o de Bajo Rendimiento"
    }
    df_active['cluster_name'] = df_active['cluster_id'].map(cluster_labels)

    # Reintegrar clientes inactivos sin pedidos
    df_inactive = df_rfm[~active_mask].copy()
    df_inactive['R_Score'] = 0
    df_inactive['F_Score'] = 0
    df_inactive['M_Score'] = 0
    df_inactive['rfm_segment'] = "Prospectos Sin Órdenes (Lead)"
    df_inactive['cluster_id'] = -1
    df_inactive['cluster_name'] = "Sin Historial de Compra"

    final_df = pd.concat([df_active, df_inactive], ignore_index=True)
    return final_df.sort_values(by='monetary', ascending=False)

if __name__ == '__main__':
    import os
    db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'northwind.db')
    results = compute_rfm_and_clustering(db)
    print("--- RESUMEN DE SEGMENTOS RFM ---")
    print(results['rfm_segment'].value_counts())
    print("\n--- RESUMEN DE CLUSTERING K-MEANS ---")
    print(results['cluster_name'].value_counts())
    print("\nTop 5 Clientes por Valor Neto:")
    print(results[['customerid', 'companyname', 'recency', 'frequency', 'monetary', 'rfm_segment', 'cluster_name']].head(5))
