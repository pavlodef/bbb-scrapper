import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
def use_db(
    dbname,
    user,
    password,
    host="localhost",
    port="5432",
    autocommit=False,
    callback=None
):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        if autocommit:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()
        if callback:
            callback(cursor, conn)
        if not autocommit:
            conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def save_company_to_db(cursor, company):
    cursor.execute("SELECT 1 FROM companies WHERE id = %s;", (company.company_id,))
    exists = cursor.fetchone()

    if exists:
        print(f"Duplicate ID, tried to update: {company.company_id}")

    else:
        cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (company.address, company.city, company.state, company.postalCode))
    
        address_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO companies (id, name, phone, website, years, description, address_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            company.company_id,
            company.name,
            company.phone,
            company.websiteUrl,
            company.years,
            company.description,
            address_id
        ))

        print(company.owners)
        if company.owners:
            for name, position in company.owners.items():
                cursor.execute("""
                    INSERT INTO personnel (name, position)
                    VALUES (%s, %s)
                    ON CONFLICT (name, position) DO UPDATE
                        SET name = EXCLUDED.name
                    RETURNING id;
                """, (name, position))
                
                personnel_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO company_personnel (company_id, personnel_id)
                    VALUES (%s, %s)
                    ON CONFLICT (company_id, personnel_id) DO NOTHING;
                """, (company.company_id, personnel_id))