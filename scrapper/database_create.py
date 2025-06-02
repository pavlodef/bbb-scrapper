import psycopg2
import os

from database_utils import use_db

def create_tables(cursor, _):

    try:
        cursor.execute("""
        CREATE TABLE addresses (
            id SERIAL PRIMARY KEY,
            address TEXT,
            city TEXT,
            state TEXT,
            postalcode TEXT,
            UNIQUE (address, city, state, postalcode)
        );
        """)
        print("Table 'addresses' created.")
    except psycopg2.errors.DuplicateTable:
        print("Table 'addresses' already exists.")


    try:
        cursor.execute("""
        CREATE TABLE companies (
            id VARCHAR PRIMARY KEY,
            name VARCHAR,
            phone TEXT[],
            website VARCHAR,
            years INT,
            description TEXT,
            address_id INTEGER,
            CONSTRAINT fk_address FOREIGN KEY (address_id)
                REFERENCES addresses(id)
                ON DELETE SET NULL
        );
        """)
        print("Table 'companies' created.")
    except psycopg2.errors.DuplicateTable:
        print("Table 'companies' already exists.")


    try:
        cursor.execute("""
        CREATE TABLE personnel (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            position VARCHAR,
            UNIQUE (name, position)
        );
        """)
        print("Table 'personnel' created.")
    except psycopg2.errors.DuplicateTable:
        print("Table 'personnel' already exists.")


    try:
        cursor.execute("""
        CREATE TABLE company_personnel (
            company_id VARCHAR REFERENCES companies(id) ON DELETE CASCADE,
            personnel_id INT REFERENCES personnel(id) ON DELETE CASCADE,
            PRIMARY KEY (company_id, personnel_id)
        );
        """)
        print("Table 'company_personnel' created.")
    except psycopg2.errors.DuplicateTable:
        print("Table 'company_personnel' already exists.")
    


use_db(
    dsn=os.getenv('DATABASE_URL'),
    callback=create_tables
)



