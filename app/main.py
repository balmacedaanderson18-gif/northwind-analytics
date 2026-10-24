"""
Servidor Backend FastAPI para Northwind Business Intelligence Dashboard
Provee endpoints analíticos optimizados con consultas SQL directas sobre la base de datos real.
"""

import os
import sqlite3
import pandas as pd
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys

# Importar motor RFM
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.rfm_clustering import compute_rfm_and_clustering

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'northwind.db')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

app = FastAPI(
    title="Northwind Business Intelligence API",
    description="Backend analítico sobre base de datos relacional Northwind",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------------------------------------------------------
# 1. Endpoint: KPIs Generales y Reconciliación
# ----------------------------------------------------------------------------
@app.get("/api/kpis")
def get_kpis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category_id: Optional[int] = None,
    country: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if start_date:
        conditions.append("o.orderdate >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("o.orderdate <= ?")
        params.append(end_date)
    if category_id:
        conditions.append("p.categoryid = ?")
        params.append(category_id)
    if country:
        conditions.append("o.shipcountry = ?")
        params.append(country)

    where_clause = " AND ".join(conditions)

    query = f"""
    SELECT 
        COUNT(DISTINCT o.orderid) AS total_orders,
        COUNT(DISTINCT o.customerid) AS active_customers,
        COUNT(DISTINCT od.productid) AS products_sold,
        SUM(od.quantity) AS total_units,
        ROUND(SUM(od.unitprice * od.quantity), 2) AS gross_sales,
        ROUND(SUM(od.unitprice * od.quantity * od.discount), 2) AS total_discount,
        ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS net_sales,
        ROUND(AVG(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS avg_item_net_sales
    FROM orders o
    JOIN order_details od ON o.orderid = od.orderid
    JOIN products p ON od.productid = p.productid
    WHERE {where_clause};
    """

    cursor.execute(query, params)
    row = dict(cursor.fetchone())

    # Flete asociado a las órdenes filtradas
    freight_query = f"""
    SELECT ROUND(SUM(freight), 2) AS total_freight
    FROM orders o
    WHERE o.orderid IN (
        SELECT DISTINCT o2.orderid
        FROM orders o2
        JOIN order_details od ON o2.orderid = od.orderid
        JOIN products p ON od.productid = p.productid
        WHERE {where_clause}
    );
    """
    cursor.execute(freight_query, params)
    f_row = cursor.fetchone()
    row['total_freight'] = f_row[0] if f_row and f_row[0] else 0.0

    # Promedio por orden (AOV)
    if row['total_orders'] and row['total_orders'] > 0 and row['net_sales']:
        row['average_order_value'] = round(row['net_sales'] / row['total_orders'], 2)
    else:
        row['average_order_value'] = 0.0

    conn.close()
    return row

# ----------------------------------------------------------------------------
# 2. Endpoint: Tendencia Temporal Mensual (Ventas Netas)
# ----------------------------------------------------------------------------
@app.get("/api/sales-trend")
def get_sales_trend(
    category_id: Optional[int] = None,
    country: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []
    if category_id:
        conditions.append("p.categoryid = ?")
        params.append(category_id)
    if country:
        conditions.append("o.shipcountry = ?")
        params.append(country)

    where_clause = " AND ".join(conditions)

    query = f"""
    SELECT 
        strftime('%Y-%m', o.orderdate) AS period,
        COUNT(DISTINCT o.orderid) AS orders_count,
        ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS net_sales,
        ROUND(SUM(od.unitprice * od.quantity), 2) AS gross_sales,
        ROUND(SUM(od.unitprice * od.quantity * od.discount), 2) AS discount_amount,
        SUM(od.quantity) AS units
    FROM orders o
    JOIN order_details od ON o.orderid = od.orderid
    JOIN products p ON od.productid = p.productid
    WHERE {where_clause}
    GROUP BY period
    ORDER BY period ASC;
    """
    cursor.execute(query, params)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

# ----------------------------------------------------------------------------
# 3. Endpoint: Desempeño por Categorías
# ----------------------------------------------------------------------------
@app.get("/api/categories-analysis")
def get_categories_analysis():
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        c.categoryid,
        c.categoryname,
        c.description,
        COUNT(DISTINCT p.productid) AS total_products,
        COUNT(DISTINCT od.orderid) AS orders_count,
        SUM(od.quantity) AS units_sold,
        ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS net_sales,
        ROUND(100.0 * SUM(od.unitprice * od.quantity * (1.0 - od.discount)) / 
            (SELECT SUM(unitprice * quantity * (1.0 - discount)) FROM order_details), 2) AS share_pct
    FROM categories c
    JOIN products p ON c.categoryid = p.categoryid
    JOIN order_details od ON p.productid = od.productid
    GROUP BY c.categoryid, c.categoryname, c.description
    ORDER BY net_sales DESC;
    """
    cursor.execute(query)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

# ----------------------------------------------------------------------------
# 4. Endpoint: Top Productos y Análisis de Inventario
# ----------------------------------------------------------------------------
@app.get("/api/top-products")
def get_top_products(limit: int = 15):
    conn = get_db()
    cursor = conn.cursor()
    query = f"""
    SELECT 
        p.productid,
        p.productname,
        c.categoryname,
        s.companyname AS supplier,
        p.unitprice AS catalog_price,
        p.unitsinstock AS stock,
        p.unitsonorder AS on_order,
        p.reorderlevel AS reorder_level,
        p.discontinued,
        SUM(od.quantity) AS units_sold,
        ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS net_sales,
        ROUND(AVG(od.discount) * 100, 1) AS avg_discount_pct
    FROM products p
    JOIN categories c ON p.categoryid = c.categoryid
    JOIN suppliers s ON p.supplierid = s.supplierid
    JOIN order_details od ON p.productid = od.productid
    GROUP BY p.productid, p.productname, c.categoryname, s.companyname, p.unitprice, p.unitsinstock, p.unitsonorder, p.reorderlevel, p.discontinued
    ORDER BY net_sales DESC
    LIMIT ?;
    """
    cursor.execute(query, (limit,))
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

# ----------------------------------------------------------------------------
# 5. Endpoint: Rendimiento de Empleados y Estructura Organizacional
# ----------------------------------------------------------------------------
@app.get("/api/employees-performance")
def get_employees_performance():
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        e.employeeid,
        e.firstname || ' ' || e.lastname AS employee_name,
        e.title,
        e.city,
        e.country,
        e.hiredate,
        COALESCE(m.firstname || ' ' || m.lastname, 'Director / Auto-gestión') AS manager_name,
        COUNT(DISTINCT o.orderid) AS total_orders,
        ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS net_sales,
        SUM(od.quantity) AS total_units,
        ROUND(AVG(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS avg_line_sales
    FROM employees e
    LEFT JOIN employees m ON e.reportsto = m.employeeid
    JOIN orders o ON e.employeeid = o.employeeid
    JOIN order_details od ON o.orderid = od.orderid
    GROUP BY e.employeeid, employee_name, e.title, e.city, e.country, e.hiredate, manager_name
    ORDER BY net_sales DESC;
    """
    cursor.execute(query)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

# ----------------------------------------------------------------------------
# 6. Endpoint: Logística y Eficiencia de Transportistas
# ----------------------------------------------------------------------------
@app.get("/api/logistics")
def get_logistics():
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT 
        s.shipperid,
        s.companyname AS shipper_name,
        s.phone,
        COUNT(o.orderid) AS total_shipments,
        ROUND(SUM(o.freight), 2) AS total_freight,
        ROUND(AVG(o.freight), 2) AS avg_freight_per_order,
        ROUND(AVG(julianday(o.shippeddate) - julianday(o.orderdate)), 1) AS avg_lead_days,
        SUM(CASE WHEN julianday(o.shippeddate) > julianday(o.requireddate) THEN 1 ELSE 0 END) AS delayed_orders,
        ROUND(100.0 * SUM(CASE WHEN julianday(o.shippeddate) <= julianday(o.requireddate) THEN 1 ELSE 0 END) / COUNT(o.orderid), 2) AS on_time_rate_pct
    FROM shippers s
    JOIN orders o ON s.shipperid = o.shipvia
    WHERE o.shippeddate IS NOT NULL
    GROUP BY s.shipperid, s.companyname, s.phone
    ORDER BY total_shipments DESC;
    """
    cursor.execute(query)
    shippers_data = [dict(r) for r in cursor.fetchall()]

    # Destinos principales (países)
    geo_query = """
    SELECT 
        o.shipcountry AS country,
        COUNT(DISTINCT o.orderid) AS total_orders,
        ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS net_sales,
        ROUND(SUM(o.freight), 2) AS total_freight,
        ROUND(AVG(julianday(o.shippeddate) - julianday(o.orderdate)), 1) AS avg_delivery_days
    FROM orders o
    JOIN order_details od ON o.orderid = od.orderid
    WHERE o.shippeddate IS NOT NULL
    GROUP BY country
    ORDER BY net_sales DESC
    LIMIT 12;
    """
    cursor.execute(geo_query)
    geo_data = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "shippers": shippers_data,
        "countries": geo_data
    }

# ----------------------------------------------------------------------------
# 7. Endpoint: Segmentación RFM y Clustering K-Means
# ----------------------------------------------------------------------------
@app.get("/api/customers-rfm")
def get_customers_rfm():
    df = compute_rfm_and_clustering(DB_PATH)
    
    # Resumen agregado por segmentos para dashboards
    rfm_summary = df.groupby('rfm_segment').agg(
        count=('customerid', 'count'),
        total_monetary=('monetary', 'sum'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean')
    ).reset_index().to_dict(orient='records')

    cluster_summary = df.groupby('cluster_name').agg(
        count=('customerid', 'count'),
        total_monetary=('monetary', 'sum'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean')
    ).reset_index().to_dict(orient='records')

    customers_table = df.to_dict(orient='records')

    return {
        "rfm_summary": rfm_summary,
        "cluster_summary": cluster_summary,
        "customers": customers_table
    }

# ----------------------------------------------------------------------------
# 8. Endpoint: Metadatos para Filtros Dinámicos
# ----------------------------------------------------------------------------
@app.get("/api/metadata/filters")
def get_filters():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT categoryid, categoryname FROM categories ORDER BY categoryname;")
    categories = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT shipcountry FROM orders ORDER BY shipcountry;")
    countries = [r[0] for r in cursor.fetchall() if r[0]]

    cursor.execute("SELECT MIN(orderdate), MAX(orderdate) FROM orders;")
    min_date, max_date = cursor.fetchone()

    conn.close()
    return {
        "categories": categories,
        "countries": countries,
        "min_date": min_date,
        "max_date": max_date
    }

# Montar frontend estático
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
