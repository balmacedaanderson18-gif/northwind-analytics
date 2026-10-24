"""
ETL Pipeline: Carga del archivo Excel northwind.xlsx a la Base de Datos Relacional SQLite
Cumpliendo orden topológico estricto de claves foráneas y validación de tipos.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'northwind.xlsx')
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'northwind.db')
SQL_SCHEMA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema_sqlite.sql')

def load_data():
    print(f"[*] Iniciando proceso ETL...")
    print(f"[*] Origen: {EXCEL_FILE}")
    print(f"[*] Destino DB: {DB_FILE}")

    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"No se encontró el archivo {EXCEL_FILE}")

    # 1. Conectar a SQLite y ejecutar DDL con PRAGMA foreign_keys = ON
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("[*] Creando tablas desde DDL...")
    with open(SQL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()

    # 2. Leer hojas de Excel
    xl = pd.ExcelFile(EXCEL_FILE)
    sheet_names = xl.sheet_names
    print(f"[*] Hojas detectadas en Excel: {sheet_names}")

    # Nota sobre shippers_tmp: Es idéntica en estructura y datos a shippers (redundancia/staging).
    # Se documenta su preservación analítica y se descarta del modelo transaccional normalizado.

    # Orden topológico de inserción respetando Foreign Keys:
    # 1. region
    # 2. territories (FK -> region)
    # 3. categories
    # 4. suppliers
    # 5. customers
    # 6. employees (FK autorreferencial reportsto)
    # 7. employeeterritories (FK -> employees, territories)
    # 8. shippers
    # 9. usstates
    # 10. products (FK -> suppliers, categories)
    # 11. orders (FK -> customers, employees, shippers)
    # 12. order_details (FK -> orders, products)

    tables_order = [
        'region',
        'territories',
        'categories',
        'suppliers',
        'customers',
        'employees',
        'employeeterritories',
        'shippers',
        'usstates',
        'products',
        'orders',
        'order_details'
    ]

    for table in tables_order:
        print(f"[*] Procesando y cargando tabla: {table}...")
        df = pd.read_excel(EXCEL_FILE, sheet_name=table)
        
        # Estandarización de nombres de columnas a minúsculas
        df.columns = [c.lower() for c in df.columns]

        # Tratamiento específico de tipos de datos y nulos
        if table == 'employees':
            # Formatear fechas a string ISO (YYYY-MM-DD)
            df['birthdate'] = pd.to_datetime(df['birthdate']).dt.strftime('%Y-%m-%d')
            df['hiredate'] = pd.to_datetime(df['hiredate']).dt.strftime('%Y-%m-%d')
            # reportsto puede tener NaN
            df['reportsto'] = df['reportsto'].apply(lambda x: int(x) if pd.notnull(x) else None)

        elif table == 'orders':
            df['orderdate'] = pd.to_datetime(df['orderdate']).dt.strftime('%Y-%m-%d')
            df['requireddate'] = pd.to_datetime(df['requireddate']).dt.strftime('%Y-%m-%d')
            df['shippeddate'] = pd.to_datetime(df['shippeddate']).apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else None
            )
            df['freight'] = df['freight'].astype(float)
            df['shipvia'] = df['shipvia'].astype(int)
            df['employeeid'] = df['employeeid'].astype(int)

        elif table == 'order_details':
            df['orderid'] = df['orderid'].astype(int)
            df['productid'] = df['productid'].astype(int)
            df['unitprice'] = df['unitprice'].astype(float)
            df['quantity'] = df['quantity'].astype(int)
            df['discount'] = df['discount'].astype(float)

        elif table == 'products':
            df['productid'] = df['productid'].astype(int)
            df['supplierid'] = df['supplierid'].astype(int)
            df['categoryid'] = df['categoryid'].astype(int)
            df['unitprice'] = df['unitprice'].astype(float)
            df['unitsinstock'] = df['unitsinstock'].astype(int)
            df['unitsonorder'] = df['unitsonorder'].astype(int)
            df['reorderlevel'] = df['reorderlevel'].astype(int)
            df['discontinued'] = df['discontinued'].astype(int)

        elif table == 'employeeterritories':
            df['employeeid'] = df['employeeid'].astype(int)
            df['territoryid'] = df['territoryid'].astype(int)

        elif table == 'territories':
            df['territoryid'] = df['territoryid'].astype(int)
            df['regionid'] = df['regionid'].astype(int)

        # Inserción con to_sql
        df.to_sql(table, conn, if_exists='append', index=False)
        print(f"    -> {len(df)} registros insertados exitosamente.")

    conn.commit()
    conn.close()
    print("[✓] Proceso ETL finalizado con éxito total e integridad garantizada.")

if __name__ == '__main__':
    load_data()
