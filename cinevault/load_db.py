import mysql.connector

def run_sql_file(filename, config):
    try:
        # First connect without DB to create it if missing
        conn = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        with open(filename, 'r', encoding='utf-8') as f:
            sql_queries = f.read()

        # Execute statements securely
        for result in cursor.execute(sql_queries, multi=True):
            pass

        print(f"[OK] Successfully executed {filename}")
        conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to execute {filename} - {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    from config import Config
    
    db_config = {
        'host': Config.MYSQL_HOST,
        'user': Config.MYSQL_USER,
        'password': Config.MYSQL_PASSWORD,
    }
    
    # Run the base schema first just in case
    print("Loading base schema...")
    run_sql_file('schema.sql', db_config)
    
    # Run the real data TMDB seed
    print("Loading real TMDB data...")
    run_sql_file('real_data.sql', db_config)
