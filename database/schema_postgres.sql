-- ============================================================================
-- Northwind Relational Database Schema DDL for PostgreSQL
-- Tipos de datos estrictos, restricciones PK/FK, validaciones CHECK e índices
-- ============================================================================

-- Limpieza previa opcional
DROP TABLE IF EXISTS order_details CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS usstates CASCADE;
DROP TABLE IF EXISTS shippers CASCADE;
DROP TABLE IF EXISTS employeeterritories CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS territories CASCADE;
DROP TABLE IF EXISTS region CASCADE;

-- 1. Tabla: region
CREATE TABLE region (
    regionid INT PRIMARY KEY,
    regiondescription VARCHAR(50) NOT NULL
);

-- 2. Tabla: territories
CREATE TABLE territories (
    territoryid INT PRIMARY KEY,
    territorydescription VARCHAR(50) NOT NULL,
    regionid INT NOT NULL,
    CONSTRAINT fk_territories_region FOREIGN KEY (regionid) 
        REFERENCES region (regionid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 3. Tabla: categories
CREATE TABLE categories (
    categoryid INT PRIMARY KEY,
    categoryname VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    picture TEXT
);

-- 4. Tabla: suppliers
CREATE TABLE suppliers (
    supplierid INT PRIMARY KEY,
    companyname VARCHAR(60) NOT NULL,
    contactname VARCHAR(50),
    contacttitle VARCHAR(50),
    address VARCHAR(80),
    city VARCHAR(30),
    region VARCHAR(30),
    postalcode VARCHAR(20),
    country VARCHAR(30),
    phone VARCHAR(30),
    fax VARCHAR(30),
    homepage TEXT
);

-- 5. Tabla: customers
CREATE TABLE customers (
    customerid VARCHAR(10) PRIMARY KEY,
    companyname VARCHAR(60) NOT NULL,
    contactname VARCHAR(50),
    contacttitle VARCHAR(50),
    address VARCHAR(80),
    city VARCHAR(30),
    region VARCHAR(30),
    postalcode VARCHAR(20),
    country VARCHAR(30),
    phone VARCHAR(30),
    fax VARCHAR(30)
);

-- 6. Tabla: employees
CREATE TABLE employees (
    employeeid INT PRIMARY KEY,
    lastname VARCHAR(30) NOT NULL,
    firstname VARCHAR(30) NOT NULL,
    title VARCHAR(50),
    titleofcourtesy VARCHAR(10),
    birthdate DATE,
    hiredate DATE,
    address VARCHAR(80),
    city VARCHAR(30),
    region VARCHAR(30),
    postalcode VARCHAR(20),
    country VARCHAR(30),
    homephone VARCHAR(30),
    extension INT,
    photo TEXT,
    notes TEXT,
    reportsto INT,
    photopath VARCHAR(255),
    CONSTRAINT fk_employees_reportsto FOREIGN KEY (reportsto) 
        REFERENCES employees (employeeid) ON UPDATE CASCADE ON DELETE SET NULL
);

-- 7. Tabla: employeeterritories
CREATE TABLE employeeterritories (
    employeeid INT NOT NULL,
    territoryid INT NOT NULL,
    PRIMARY KEY (employeeid, territoryid),
    CONSTRAINT fk_et_employee FOREIGN KEY (employeeid) 
        REFERENCES employees (employeeid) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_et_territory FOREIGN KEY (territoryid) 
        REFERENCES territories (territoryid) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 8. Tabla: shippers
CREATE TABLE shippers (
    shipperid INT PRIMARY KEY,
    companyname VARCHAR(50) NOT NULL,
    phone VARCHAR(30)
);

-- 9. Tabla: usstates
CREATE TABLE usstates (
    stateid INT PRIMARY KEY,
    statename VARCHAR(50) NOT NULL,
    stateabbr VARCHAR(2) NOT NULL UNIQUE,
    stateregion VARCHAR(30)
);

-- 10. Tabla: products
CREATE TABLE products (
    productid INT PRIMARY KEY,
    productname VARCHAR(60) NOT NULL,
    supplierid INT NOT NULL,
    categoryid INT NOT NULL,
    quantityperunit VARCHAR(50),
    unitprice NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (unitprice >= 0),
    unitsinstock INT NOT NULL DEFAULT 0 CHECK (unitsinstock >= 0),
    unitsonorder INT NOT NULL DEFAULT 0 CHECK (unitsonorder >= 0),
    reorderlevel INT NOT NULL DEFAULT 0 CHECK (reorderlevel >= 0),
    discontinued SMALLINT NOT NULL DEFAULT 0 CHECK (discontinued IN (0, 1)),
    CONSTRAINT fk_products_supplier FOREIGN KEY (supplierid) 
        REFERENCES suppliers (supplierid) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_products_category FOREIGN KEY (categoryid) 
        REFERENCES categories (categoryid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 11. Tabla: orders
CREATE TABLE orders (
    orderid INT PRIMARY KEY,
    customerid VARCHAR(10) NOT NULL,
    employeeid INT NOT NULL,
    orderdate DATE NOT NULL,
    requireddate DATE,
    shippeddate DATE,
    shipvia INT NOT NULL,
    freight NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (freight >= 0),
    shipname VARCHAR(60),
    shipaddress VARCHAR(80),
    shipcity VARCHAR(30),
    shipregion VARCHAR(30),
    shippostalcode VARCHAR(20),
    shipcountry VARCHAR(30),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customerid) 
        REFERENCES customers (customerid) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_employee FOREIGN KEY (employeeid) 
        REFERENCES employees (employeeid) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_shipper FOREIGN KEY (shipvia) 
        REFERENCES shippers (shipperid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 12. Tabla: order_details
CREATE TABLE order_details (
    orderid INT NOT NULL,
    productid INT NOT NULL,
    unitprice NUMERIC(10, 2) NOT NULL CHECK (unitprice >= 0),
    quantity INT NOT NULL CHECK (quantity > 0),
    discount NUMERIC(4, 2) NOT NULL DEFAULT 0.0 CHECK (discount >= 0.0 AND discount <= 1.0),
    PRIMARY KEY (orderid, productid),
    CONSTRAINT fk_od_order FOREIGN KEY (orderid) 
        REFERENCES orders (orderid) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_od_product FOREIGN KEY (productid) 
        REFERENCES products (productid) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================================
-- Índices para Rendimiento en PostgreSQL
-- ============================================================================
CREATE INDEX idx_orders_customerid ON orders(customerid);
CREATE INDEX idx_orders_employeeid ON orders(employeeid);
CREATE INDEX idx_orders_orderdate ON orders(orderdate);
CREATE INDEX idx_orders_shipvia ON orders(shipvia);
CREATE INDEX idx_order_details_orderid ON order_details(orderid);
CREATE INDEX idx_order_details_productid ON order_details(productid);
CREATE INDEX idx_products_categoryid ON products(categoryid);
CREATE INDEX idx_products_supplierid ON products(supplierid);
CREATE INDEX idx_territories_regionid ON territories(regionid);
