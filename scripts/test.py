from azure_connector import get_azure_sql_connection
import pandas as pd

# =============================
# 1. Validar conexión a Azure
# =============================
print("\n== VALIDANDO CONEXIÓN A AZURE SQL ==")

conn = get_azure_sql_connection()

if conn:
    print("✔ Conexión exitosa a Azure SQL")

    try:
        # Probar leer algo en tu BD real
        test_df = pd.read_sql("SELECT TOP 15 name, create_date FROM sys.tables", conn)
        print("\n== TABLAS EN LA BD ==")
        print(test_df)
    except Exception as e:
        print("❌ Error ejecutando query de prueba:", e)

else:
    print("❌ No se pudo conectar a Azure SQL")


# =============================
# 2. Validar lectura de Excel y mostrar head
# =============================
print("\n== VALIDANDO LECTURA DE ARCHIVOS EXCEL ==")

try:
    df_pacientes = pd.read_excel("archivos_excel/pacientes.xlsx", dtype=str)
    print("\n✔ df_pacientes cargado correctamente")
    print(df_pacientes.head())
except Exception as e:
    print("❌ Error cargando pacientes.xlsx:", e)


try:
    df_fases = pd.read_excel("archivos_excel/tmz.xlsx", dtype=str)
    print("\n✔ df_fases cargado correctamente")
    print(df_fases.head())
except Exception as e:
    print("❌ Error cargando tmz.xlsx:", e)
