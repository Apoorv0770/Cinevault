import mysql.connector

try:
    conn = mysql.connector.connect(host='localhost', user='root', password='0Cinevault07@')
    print("SUCCESS_UNQUOTED")
    conn.close()
except Exception as e:
    print("FAILED_UNQUOTED:", e)

try:
    conn = mysql.connector.connect(host='localhost', user='root', password='"0Cinevault07@"')
    print("SUCCESS_QUOTED")
    conn.close()
except Exception as e:
    print("FAILED_QUOTED:", e)
