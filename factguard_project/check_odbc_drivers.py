# check_odbc_drivers.py
import pyodbc

print(" Drivers ODBC disponibles :")
for driver in pyodbc.drivers():
    print(f"   - {driver}")
