-- ============================================================================
-- Northwind Relational Database Schema DDL for SQLite
-- Generado con restricciones de Integridad Referencial y Validaciones CHECK
-- ============================================================================

PRAGMA foreign_keys = ON;

-- 1. Tabla: region
DROP TABLE IF EXISTS region;
CREATE TABLE region (
    regionid INTEGER PRIMARY KEY,
    regiondescription TEXT NOT NULL
);

-- 2. Tabla: territories
DROP TABLE IF EXISTS territories;
CREATE TABLE territories (
    territoryid INTEGER PRIMARY KEY,
    territorydescription TEXT NOT NULL,
    regionid INTEGER NOT NULL,
    CONSTRAINT fk_territories_region FOREIGN KEY (regionid) 
        REFERENCES region (regionid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 3. Tabla: categories
DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
    categoryid INTEGER PRIMARY KEY,
    categoryname TEXT NOT NULL UNIQUE,
    description TEXT,
    picture TEXT
);

-- 4. Tabla: suppliers
DROP TABLE IF EXISTS suppliers;
CREATE TABLE suppliers (
    supplierid INTEGER PRIMARY KEY,
    companyname TEXT NOT NULL,
    contactname TEXT,
    contacttitle TEXT,
    address TEXT,
    city TEXT,
    region TEXT,
    postalcode TEXT,
    country TEXT,
    phone TEXT,
    fax TEXT,
    homepage TEXT
);

-- 5. Tabla: customers
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customerid TEXT PRIMARY KEY,
    companyname TEXT NOT NULL,
    contactname TEXT,
    contacttitle TEXT,
    address TEXT,
    city TEXT,
    region TEXT,
    postalcode TEXT,
    country TEXT,
    phone TEXT,
    fax TEXT,
    CONSTRAINT chk_customerid_len CHECK (length(customerid) <= 10)
);

-- 6. Tabla: employees (con autorreferencia jerárquica)
DROP TABLE IF EXISTS employees;
CREATE TABLE employees (
    employeeid INTEGER PRIMARY KEY,
    lastname TEXT NOT NULL,
    firstname TEXT NOT NULL,
    title TEXT,
    titleofcourtesy TEXT,
    birthdate TEXT,
    hiredate TEXT,
    address TEXT,
    city TEXT,
    region TEXT,
    postalcode TEXT,
    country TEXT,
    homephone TEXT,
    extension INTEGER,
    photo TEXT,
    notes TEXT,
    reportsto INTEGER,
    photopath TEXT,
    CONSTRAINT fk_employees_reportsto FOREIGN KEY (reportsto) 
        REFERENCES employees (employeeid) ON UPDATE CASCADE ON DELETE SET NULL
);

-- 7. Tabla: employeeterritories (Relación N:M entre employees y territories)
DROP TABLE IF EXISTS employeeterritories;
CREATE TABLE employeeterritories (
    employeeid INTEGER NOT NULL,
    territoryid INTEGER NOT NULL,
    PRIMARY KEY (employeeid, territoryid),
    CONSTRAINT fk_et_employee FOREIGN KEY (employeeid) 
        REFERENCES employees (employeeid) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_et_territory FOREIGN KEY (territoryid) 
        REFERENCES territories (territoryid) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 8. Tabla: shippers
DROP TABLE IF EXISTS shippers;
CREATE TABLE shippers (
    shipperid INTEGER PRIMARY KEY,
    companyname TEXT NOT NULL,
    phone TEXT
);

-- 9. Tabla: usstates (Catálogo de Estados de EE.UU.)
DROP TABLE IF EXISTS usstates;
CREATE TABLE usstates (
    stateid INTEGER PRIMARY KEY,
    statename TEXT NOT NULL,
    stateabbr TEXT NOT NULL UNIQUE,
    stateregion TEXT
);

-- 10. Tabla: products
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    productid INTEGER PRIMARY KEY,
    productname TEXT NOT NULL,
    supplierid INTEGER NOT NULL,
    categoryid INTEGER NOT NULL,
    quantityperunit TEXT,
    unitprice REAL NOT NULL DEFAULT 0.0 CHECK (unitprice >= 0),
    unitsinstock INTEGER NOT NULL DEFAULT 0 CHECK (unitsinstock >= 0),
    unitsonorder INTEGER NOT NULL DEFAULT 0 CHECK (unitsonorder >= 0),
    reorderlevel INTEGER NOT NULL DEFAULT 0 CHECK (reorderlevel >= 0),
    discontinued INTEGER NOT NULL DEFAULT 0 CHECK (discontinued IN (0, 1)),
    CONSTRAINT fk_products_supplier FOREIGN KEY (supplierid) 
        REFERENCES suppliers (supplierid) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_products_category FOREIGN KEY (categoryid) 
        REFERENCES categories (categoryid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 11. Tabla: orders
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    orderid INTEGER PRIMARY KEY,
    customerid TEXT NOT NULL,
    employeeid INTEGER NOT NULL,
    orderdate TEXT NOT NULL,
    requireddate TEXT,
    shippeddate TEXT,
    shipvia INTEGER NOT NULL,
    freight REAL NOT NULL DEFAULT 0.0 CHECK (freight >= 0),
    shipname TEXT,
    shipaddress TEXT,
    shipcity TEXT,
    shipregion TEXT,
    shippostalcode TEXT,
    shipcountry TEXT,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customerid) 
        REFERENCES customers (customerid) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_employee FOREIGN KEY (employeeid) 
        REFERENCES employees (employeeid) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_shipper FOREIGN KEY (shipvia) 
        REFERENCES shippers (shipperid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 12. Tabla: order_details (Líneas de Detalle de Órdenes con PK compuesta)
DROP TABLE IF EXISTS order_details;
CREATE TABLE order_details (
    orderid INTEGER NOT NULL,
    productid INTEGER NOT NULL,
    unitprice REAL NOT NULL CHECK (unitprice >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    discount REAL NOT NULL DEFAULT 0.0 CHECK (discount >= 0.0 AND discount <= 1.0),
    PRIMARY KEY (orderid, productid),
    CONSTRAINT fk_od_order FOREIGN KEY (orderid) 
        REFERENCES orders (orderid) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_od_product FOREIGN KEY (productid) 
        REFERENCES products (productid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================================
-- Índices para Optimización de Consultas Analíticas (BI & Dashboard)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_orders_customerid ON orders(customerid);
CREATE INDEX IF NOT EXISTS idx_orders_employeeid ON orders(employeeid);
CREATE INDEX IF NOT EXISTS idx_orders_orderdate ON orders(orderdate);
CREATE INDEX IF NOT EXISTS idx_orders_shipvia ON orders(shipvia);
CREATE INDEX IF NOT EXISTS idx_order_details_orderid ON order_details(orderid);
CREATE INDEX IF NOT EXISTS idx_order_details_productid ON order_details(productid);
CREATE INDEX IF NOT EXISTS idx_products_categoryid ON products(categoryid);
CREATE INDEX IF NOT EXISTS idx_products_supplierid ON products(supplierid);
CREATE INDEX IF NOT EXISTS idx_territories_regionid ON territories(regionid);
