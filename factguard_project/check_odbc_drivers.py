import pyodbc

print(" Drivers ODBC disponibles :")
for driver in pyodbc.drivers():
    print(f"   - {driver}")
