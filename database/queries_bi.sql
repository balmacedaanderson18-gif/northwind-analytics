-- ============================================================================
-- Northwind Relational Database: Consultas Analíticas y Métricas de Negocio (BI)
-- Todas las consultas utilizan exclusivamente datos reales y verificables.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. RECONCILIACIÓN FINANCIERA GENERAL
-- Calcula: Total Ventas Brutas, Descuentos Totales, Ventas Netas y Fletes
-- Fórmula de Ventas Netas exigida: SUM(unitprice * quantity * (1 - discount))
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT o.orderid) AS total_ordenes,
    COUNT(*) AS total_lineas_pedido,
    SUM(od.quantity) AS total_unidades_vendidas,
    ROUND(SUM(od.unitprice * od.quantity), 2) AS ventas_brutas,
    ROUND(SUM(od.unitprice * od.quantity * od.discount), 2) AS total_descuentos_otorgados,
    ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS ventas_netas,
    ROUND(SUM(DISTINCT o.freight), 2) AS total_fletes -- O suma agrupada de fletes
FROM order_details od
JOIN orders o ON od.orderid = o.orderid;

-- ----------------------------------------------------------------------------
-- 2. VENTAS NETAS Y PARTICIPACIÓN POR CATEGORÍA DE PRODUCTOS
-- Revela qué líneas de negocio generan la mayor parte del flujo de caja.
-- ----------------------------------------------------------------------------
SELECT 
    c.categoryid,
    c.categoryname,
    COUNT(DISTINCT od.orderid) AS ordenes_asociadas,
    SUM(od.quantity) AS volumen_unidades,
    ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS ventas_netas,
    ROUND(100.0 * SUM(od.unitprice * od.quantity * (1.0 - od.discount)) / 
        (SELECT SUM(unitprice * quantity * (1.0 - discount)) FROM order_details), 2) AS pct_participacion
FROM categories c
JOIN products p ON c.categoryid = p.categoryid
JOIN order_details od ON p.productid = od.productid
GROUP BY c.categoryid, c.categoryname
ORDER BY ventas_netas DESC;

-- ----------------------------------------------------------------------------
-- 3. TOP 10 PRODUCTOS POR VENTAS NETAS Y RENDIMIENTO DE STOCK
-- Cruza facturación neta con stock en almacén y pedidos pendientes.
-- ----------------------------------------------------------------------------
SELECT 
    p.productid,
    p.productname,
    c.categoryname,
    s.companyname AS proveedor,
    p.unitprice AS precio_catalogo,
    SUM(od.quantity) AS unidades_vendidas,
    ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS ventas_netas,
    p.unitsinstock AS stock_actual,
    p.unitsonorder AS unidades_en_camino,
    p.reorderlevel AS nivel_reorden
FROM products p
JOIN categories c ON p.categoryid = c.categoryid
JOIN suppliers s ON p.supplierid = s.supplierid
JOIN order_details od ON p.productid = od.productid
GROUP BY p.productid, p.productname, c.categoryname, s.companyname, p.unitprice, p.unitsinstock, p.unitsonorder, p.reorderlevel
ORDER BY ventas_netas DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 4. RENDIMIENTO DE EMPLEADOS Y JERARQUÍA DE VENTAS
-- Muestra la facturación neta generada por cada vendedor y su supervisor directo.
-- ----------------------------------------------------------------------------
SELECT 
    e.employeeid,
    e.firstname || ' ' || e.lastname AS empleado,
    e.title AS cargo,
    COALESCE(m.firstname || ' ' || m.lastname, 'Es Director / Sin Supervisor') AS supervisor,
    COUNT(DISTINCT o.orderid) AS pedidos_gestionados,
    ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS ventas_netas_generadas,
    ROUND(AVG(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS ticket_promedio_linea
FROM employees e
LEFT JOIN employees m ON e.reportsto = m.employeeid
JOIN orders o ON e.employeeid = o.employeeid
JOIN order_details od ON o.orderid = od.orderid
GROUP BY e.employeeid, empleado, e.title, supervisor
ORDER BY ventas_netas_generadas DESC;

-- ----------------------------------------------------------------------------
-- 5. RENDIMIENTO LOGÍSTICO Y COSTOS DE TRANSPORTE POR EMPRESA DE ENVÍO
-- Analiza puntualidad de envíos, retrasos y flete promedio.
-- ----------------------------------------------------------------------------
SELECT 
    s.shipperid,
    s.companyname AS transportista,
    COUNT(o.orderid) AS total_envios,
    ROUND(SUM(o.freight), 2) AS total_fletes_cobrados,
    ROUND(AVG(o.freight), 2) AS flete_promedio_por_pedido,
    ROUND(AVG(julianday(o.shippeddate) - julianday(o.orderdate)), 1) AS dias_promedio_despacho,
    SUM(CASE WHEN julianday(o.shippeddate) > julianday(o.requireddate) THEN 1 ELSE 0 END) AS envios_con_retraso,
    ROUND(100.0 * SUM(CASE WHEN julianday(o.shippeddate) <= julianday(o.requireddate) THEN 1 ELSE 0 END) / COUNT(o.orderid), 2) AS tasa_puntualidad_pct
FROM shippers s
JOIN orders o ON s.shipperid = o.shipvia
WHERE o.shippeddate IS NOT NULL
GROUP BY s.shipperid, s.companyname
ORDER BY total_envios DESC;

-- ----------------------------------------------------------------------------
-- 6. TENDENCIA TEMPORAL MENSUAL DE VENTAS NETAS
-- Permite visualizar la evolución histórica de ventas netas mes a mes.
-- ----------------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', o.orderdate) AS periodo_mes,
    COUNT(DISTINCT o.orderid) AS total_pedidos,
    ROUND(SUM(od.unitprice * od.quantity * (1.0 - od.discount)), 2) AS ventas_netas,
    ROUND(SUM(od.unitprice * od.quantity * od.discount), 2) AS descuentos
FROM orders o
JOIN order_details od ON o.orderid = od.orderid
GROUP BY periodo_mes
ORDER BY periodo_mes ASC;

-- ----------------------------------------------------------------------------
-- 7. CÁLCULO BASE PARA SEGMENTACIÓN RFM (Recencia, Frecuencia, Valor Monetario)
-- Fecha de Referencia: Día siguiente a la última orden (1998-05-07)
-- ----------------------------------------------------------------------------
WITH OrderSales AS (
    SELECT 
        o.orderid,
        o.customerid,
        o.orderdate,
        SUM(od.unitprice * od.quantity * (1.0 - od.discount)) AS order_net_total
    FROM orders o
    JOIN order_details od ON o.orderid = od.orderid
    GROUP BY o.orderid, o.customerid, o.orderdate
),
CustomerRFM AS (
    SELECT 
        c.customerid,
        c.companyname,
        c.country,
        c.city,
        CAST(ROUND(julianday('1998-05-07') - julianday(MAX(os.orderdate))) AS INT) AS recency_days,
        COUNT(os.orderid) AS frequency,
        ROUND(COALESCE(SUM(os.order_net_total), 0), 2) AS monetary_net_sales
    FROM customers c
    LEFT JOIN OrderSales os ON c.customerid = os.customerid
    GROUP BY c.customerid, c.companyname, c.country, c.city
)
SELECT * FROM CustomerRFM
ORDER BY monetary_net_sales DESC;
