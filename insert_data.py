from azure_connector import get_azure_sql_connection
from process_excel import load_and_process_excels
# Nota: La función insert_dataframe_to_sql DEBE recibir la conexión/cursor.

def insert_dataframe_to_sql(df, table_name, cursor, conn):
    # Ya no se abre ni se cierra la conexión aquí
    
    columns = ", ".join([f"[{col}]" for col in df.columns])
    placeholders = ", ".join(["?"] * len(df.columns))

    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    for _, row in df.iterrows():
        cursor.execute(sql, tuple(row.values))

    conn.commit()
    print(f"✔ Insertado correctamente en {table_name}")


if __name__ == "__main__":
    df_pacientes, df_fases = load_and_process_excels()

    # --- Apertura de Conexión Única ---
    conn = get_azure_sql_connection()
    cursor = conn.cursor()
    
    #if not df_pacientes.empty:
        # Pasa cursor y conn
        #insert_dataframe_to_sql(df_pacientes, "tmz_data.Pacientes_tmz", cursor, conn)

    #if not df_fases.empty:
        # Pasa cursor y conn
        #insert_dataframe_to_sql(df_fases, "tmz_data.FasePaciente", cursor, conn)

    # --- Cierre de Conexión Única ---
    cursor.close()
    conn.close()
    
    print("\n✔ CARGA COMPLETA")