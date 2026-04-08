import mysql.connector

def run_sql_file(filename, connection):
    with open(filename, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Split into statements
    statements = sql.split(';')
    cursor = connection.cursor()
    
    for statement in statements:
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Error executing statement: {statement[:50]}...\nError: {e}")
    
    connection.commit()
    cursor.close()

if __name__ == '__main__':
    try:
        # First connect without database to create it
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        print("Connected to MySQL successfully.")
        
        run_sql_file('schema.sql', conn)
        print("Database schema and seed data loaded successfully.")
        
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"General Error: {e}")
