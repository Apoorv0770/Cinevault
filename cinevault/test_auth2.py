import mysql.connector

try:
    conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='0Cinevault07@')
    print("SUCCESS_127_UNQUOTED")
    conn.close()
except Exception as e:
    print("FAILED_127_UNQUOTED:", e)
