import mysql.connector

passwords = ['', 'root', 'password', '1234', '123456', 'admin']
success = False

for p in passwords:
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=p
        )
        print(f"SUCCESS: Connected with password '{p}'")
        success = True
        conn.close()
        break
    except mysql.connector.Error as err:
        pass

if not success:
    print("FAILED: Could not connect with common default passwords. Please provide the root password.")
