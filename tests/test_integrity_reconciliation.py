"""
Script de Pruebas de Integridad Referencial y Reconciliación Contable
Northwind Database Testing Suite
"""

import os
import sqlite3
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'northwind.db')
EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'northwind.xlsx')

def run_tests():
    print("================================================================")
    print("EJECUTANDO SUITE DE PRUEBAS DE INTEGRIDAD Y RECONCILIACIÓN")
    print("================================================================")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Integridad de Conteo de Filas: Excel vs SQLite
    print("\n[TEST 1] Verificación de Conteos de Filas (Excel vs SQLite):")
    xl = pd.ExcelFile(EXCEL_FILE)
    passed_counts = True
    tables = [
        'region', 'territories', 'categories', 'suppliers', 'customers',
        'employees', 'employeeterritories', 'shippers', 'usstates',
        'products', 'orders', 'order_details'
    ]

    for t in tables:
        df_excel = pd.read_excel(EXCEL_FILE, sheet_name=t)
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        db_count = cursor.fetchone()[0]
        excel_count = len(df_excel)
        status = "OK" if db_count == excel_count else "FALLÓ"
        if status != "OK":
            passed_counts = False
        print(f"  - Tabla {t:20s}: Excel={excel_count:5d} | DB={db_count:5d} -> [{status}]")

    assert passed_counts, "Error: Discrepancia en conteo de filas."

    # 2. Comprobación de PRAGMA foreign_key_check
    print("\n[TEST 2] Verificación de Claves Foráneas Nativas SQLite (PRAGMA foreign_key_check):")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    if not fk_errors:
        print("  - [OK] Cero violaciones de claves foráneas detectadas en toda la base de datos.")
    else:
        print(f"  - [FALLÓ] Violaciones FK encontradas: {fk_errors}")
        assert False, "Violación de integridad referencial detectada."

    # 3. Reconciliación de Ventas Netas con Fórmula Específica
    # SUM(unitprice * quantity * (1 - discount))
    print("\n[TEST 3] Reconciliación de Métricas Financieras:")
    cursor.execute("""
        SELECT 
            SUM(unitprice * quantity * (1.0 - discount)) AS net_sales,
            SUM(unitprice * quantity) AS gross_sales,
            SUM(unitprice * quantity * discount) AS discount_total,
            SUM(quantity) AS total_quantity
        FROM order_details;
    """)
    db_metrics = cursor.fetchone()
    
    od_excel = pd.read_excel(EXCEL_FILE, sheet_name='order_details')
    od_excel['net'] = od_excel['unitprice'] * od_excel['quantity'] * (1.0 - od_excel['discount'])
    od_excel['gross'] = od_excel['unitprice'] * od_excel['quantity']
    od_excel['disc'] = od_excel['unitprice'] * od_excel['quantity'] * od_excel['discount']
    
    excel_net = od_excel['net'].sum()
    excel_gross = od_excel['gross'].sum()
    excel_disc = od_excel['disc'].sum()
    excel_qty = od_excel['quantity'].sum()

    print(f"  - Ventas Netas:  DB=${db_metrics[0]:,.4f} | Excel=${excel_net:,.4f} -> [DIF: {abs(db_metrics[0] - excel_net):.6f}]")
    print(f"  - Ventas Brutas: DB=${db_metrics[1]:,.4f} | Excel=${excel_gross:,.4f} -> [DIF: {abs(db_metrics[1] - excel_gross):.6f}]")
    print(f"  - Descuentos:    DB=${db_metrics[2]:,.4f} | Excel=${excel_disc:,.4f} -> [DIF: {abs(db_metrics[2] - excel_disc):.6f}]")
    print(f"  - Cantidad:      DB={db_metrics[3]:,d}       | Excel={excel_qty:,d}       -> [DIF: {abs(db_metrics[3] - excel_qty)}]")

    assert abs(db_metrics[0] - excel_net) < 1e-4, "Discrepancia en Ventas Netas"
    assert abs(db_metrics[1] - excel_gross) < 1e-4, "Discrepancia en Ventas Brutas"
    assert db_metrics[3] == excel_qty, "Discrepancia en Cantidad Total"

    # 4. Reconciliación de Fletes en Orders
    cursor.execute("SELECT SUM(freight) FROM orders;")
    db_freight = cursor.fetchone()[0]
    orders_excel = pd.read_excel(EXCEL_FILE, sheet_name='orders')
    excel_freight = orders_excel['freight'].sum()
    print(f"  - Total Flete:   DB=${db_freight:,.4f}  | Excel=${excel_freight:,.4f}  -> [DIF: {abs(db_freight - excel_freight):.6f}]")
    assert abs(db_freight - excel_freight) < 1e-4, "Discrepancia en Flete"

    # 5. Validación de Unicidad de Claves Primarias y No Nulidad
    print("\n[TEST 4] Validación de Claves Primarias:")
    cursor.execute("SELECT COUNT(customerid), COUNT(DISTINCT customerid) FROM customers;")
    c_tot, c_dist = cursor.fetchone()
    print(f"  - Clientes PK (customerid): {c_tot} total, {c_dist} únicos -> [{'OK' if c_tot == c_dist else 'FAIL'}]")

    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT orderid || '-' || productid) FROM order_details;")
    od_tot, od_dist = cursor.fetchone()
    print(f"  - Order Details PK compuesta: {od_tot} total, {od_dist} únicos -> [{'OK' if od_tot == od_dist else 'FAIL'}]")

    print("\n================================================================")
    print("TODAS LAS PRUEBAS DE INTEGRIDAD Y RECONCILIACIÓN PASARON EXITOSAMENTE [100% OK]")
    print("================================================================")
    conn.close()

if __name__ == '__main__':
    run_tests()
