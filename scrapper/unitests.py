import pytest
import os
import psycopg2

@pytest.fixture
def db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()



def test_insert_address_success(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, ("123 Main St", "Townsville", "TS", "12345"))
    address_id = cursor.fetchone()[0]
    assert address_id is not None


def test_unique_address_constraint(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s);
    """, ("456 Elm St", "Villagetown", "VT", "54321"))

    with pytest.raises(psycopg2.errors.UniqueViolation):
        cursor.execute("""
            INSERT INTO addresses (address, city, state, postalcode)
            VALUES (%s, %s, %s, %s);
        """, ("456 Elm St", "Villagetown", "VT", "54321"))



def test_foreign_key_company_address(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, ("789 Oak St", "Cityplace", "CP", "67890"))
    address_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO companies (id, name, address_id)
        VALUES (%s, %s, %s);
    """, ("company_1", "Test Company", address_id))

    cursor.execute("SELECT name FROM companies WHERE id = %s", ("company_1",))
    company = cursor.fetchone()
    assert company[0] == "Test Company"



def test_duplicate_address_fields(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s);
    """, ("100 Maple St", "Townsville", "TS", "11111"))

    # Insert duplicate with same address, city, state, postalcode
    with pytest.raises(psycopg2.errors.UniqueViolation):
        cursor.execute("""
            INSERT INTO addresses (address, city, state, postalcode)
            VALUES (%s, %s, %s, %s);
        """, ("100 Maple St", "Townsville", "TS", "11111"))

def test_duplicate_company_id(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO companies (id, name)
        VALUES (%s, %s);
    """, ("company_123", "First Company"))

    with pytest.raises(psycopg2.errors.UniqueViolation):
        cursor.execute("""
            INSERT INTO companies (id, name)
            VALUES (%s, %s);
        """, ("company_123", "Duplicate Company"))


def test_wrong_data_type_in_address(db_connection):
    cursor = db_connection.cursor()
    with pytest.raises(psycopg2.Error):
        cursor.execute("""
            INSERT INTO addresses (address, city, state, postalcode)
            VALUES (%s, %s, %s, %s);
        """, ("123 Fake St", ["Not", "a", "string"], "TS", None))


def test_wrong_data_type_in_companies(db_connection):
    cursor = db_connection.cursor()
    # years is INT - test inserting string
    with pytest.raises(psycopg2.errors.InvalidTextRepresentation):
        cursor.execute("""
            INSERT INTO companies (id, name, years)
            VALUES (%s, %s, %s);
        """, ("comp_wrong_years", "Bad Years Company", "not_an_int"))


def test_wrong_data_type_in_personnel(db_connection):
    cursor = db_connection.cursor()
    # name and position are VARCHAR - test inserting NULL if not allowed or non-string?
    with pytest.raises(psycopg2.Error):
        cursor.execute("""
            INSERT INTO personnel (name, position)
            VALUES (%s, %s);
        """, (None, 123))  # position as int, name as None



def test_correct_insertion_and_relations(db_connection):
    cursor = db_connection.cursor()

    # Insert address
    cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, ("200 Oak St", "Citytown", "CT", "22222"))
    address_id = cursor.fetchone()[0]

    # Insert company linked to address
    cursor.execute("""
        INSERT INTO companies (id, name, address_id)
        VALUES (%s, %s, %s);
    """, ("company_xyz", "XYZ Corp", address_id))

    # Insert personnel
    cursor.execute("""
        INSERT INTO personnel (name, position)
        VALUES (%s, %s)
        RETURNING id;
    """, ("Alice Smith", "CEO"))
    personnel_id = cursor.fetchone()[0]

    # Link company and personnel
    cursor.execute("""
        INSERT INTO company_personnel (company_id, personnel_id)
        VALUES (%s, %s);
    """, ("company_xyz", personnel_id))

    # Assert address
    cursor.execute("SELECT address, city, state, postalcode FROM addresses WHERE id = %s;", (address_id,))
    addr = cursor.fetchone()
    assert addr == ("200 Oak St", "Citytown", "CT", "22222")

    # Assert company
    cursor.execute("SELECT name, address_id FROM companies WHERE id = %s;", ("company_xyz",))
    comp = cursor.fetchone()
    assert comp == ("XYZ Corp", address_id)

    # Assert personnel
    cursor.execute("SELECT name, position FROM personnel WHERE id = %s;", (personnel_id,))
    person = cursor.fetchone()
    assert person == ("Alice Smith", "CEO")

    # Assert company_personnel link
    cursor.execute("""
        SELECT company_id, personnel_id
        FROM company_personnel
        WHERE company_id = %s AND personnel_id = %s;
    """, ("company_xyz", personnel_id))
    link = cursor.fetchone()
    assert link == ("company_xyz", personnel_id)
