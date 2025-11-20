from azure_connector import get_azure_sql_connection
import pandas as pd
import os
import io

# --- Función de Utilidad para Normalizar Encabezados ---
def normalize_columns_and_rename(df, table_name):
    """Limpia los nombres de columna y retorna el DataFrame con los nuevos nombres."""
    
    # 1. Definir la lógica de limpieza
    def clean_name(col):
        # Convertir a mayúsculas
        clean = col.upper()
        # Reemplazar espacios, '/', '.' y tildes por '_'
        clean = clean.replace(' ', '_').replace('/', '_').replace('.', '').replace('É', 'E')
        # Limpiar cualquier doble guion bajo resultante de espacios contiguos
        clean = clean.replace('__', '_')
        # Quitar guiones bajos al inicio/final si los hay
        return clean.strip('_')

    # 2. Aplicar la limpieza
    original_to_clean = {col: clean_name(col) for col in df.columns}
    df.columns = original_to_clean.values()
    
    # 3. Imprimir el mapeo
    print(f"\n--- Mapeo de Columnas para {table_name.upper()} ---")
    for original, clean in original_to_clean.items():
        print(f"   '{original}' -> '{clean}'")
    print("--------------------------------------")
    
    # 4. Eliminar Columnas UNNAMED
    df = df.drop(df.filter(like='UNNAMED').columns, axis=1)
    return df

# --- NUEVAS FUNCIONES PARA GENERACIÓN DE SQL ---

def map_pandas_to_sql(dtype):
    """Mapea los tipos de Pandas (después de conversiones) a tipos de SQL Server."""
    dtype_str = str(dtype).lower()
    
    if 'int' in dtype_str:
        return 'INT'
    if 'float' in dtype_str:
        return 'FLOAT'
    if 'datetime' in dtype_str:
        return 'DATETIME2'
    # Usamos NVARCHAR(255) para strings por defecto, excepto para fechas específicas.
    return 'NVARCHAR(255)' 

def generate_create_table_sql(df, table_name):
    """Genera la sentencia CREATE TABLE SQL a partir del DataFrame limpio."""
    sql = f"-- Tabla generada a partir del archivo {table_name}.xlsx\n"
    sql += f"DROP TABLE IF EXISTS {table_name};\n"
    sql += "GO\n\n"
    sql += f"CREATE TABLE {table_name} (\n"
    
    col_definitions = []
    
    # 1. Definición de la Columna ID Autoincremental y PK (SOLO para Pacientes)
    if table_name == 'Pacientes':
        col_definitions.append("    [ID_PACIENTE] INT IDENTITY(1,1) PRIMARY KEY")
        
    # 2. Definición del resto de columnas
    for col_name, dtype in df.dtypes.items():
        sql_type = map_pandas_to_sql(dtype)
        sql_def = None
        
        # --- Lógica de Restricciones y Tipos Específicos ---
        
        # CÉDULA: Clave Única y NOT NULL
        if col_name == 'CEDULA':
            sql_def = f"    [{col_name}] NVARCHAR(50) NOT NULL UNIQUE"
        
        # NOMBRES DE COLUMNAS DE FECHA (Mantenidas como String)
        elif 'FECHA' in col_name or 'MES' in col_name:
             sql_def = f"    [{col_name}] NVARCHAR(50) NULL"
        
        # OBSERVACIONES (NVARCHAR(MAX) para texto largo)
        elif 'OBSERVACIONES' in col_name:
            sql_def = f"    [{col_name}] NVARCHAR(MAX) NULL"
        
        # Columna ESTADO (Importante para el dashboard, NO NULL)
        elif col_name == 'ESTADO':
            sql_def = f"    [{col_name}] NVARCHAR(100) NOT NULL"
            
        # FASE_ORDEN (Asumiendo que se convertirá a INT)
        elif col_name == 'FASE_ORDEN' and table_name == 'FasePaciente':
             sql_def = f"    [{col_name}] INT NOT NULL"
             
        # Tipo por defecto (NVARCHAR(255) para el resto de strings)
        if sql_def is None:
            sql_def = f"    [{col_name}] {sql_type} NULL"
            
        col_definitions.append(sql_def)

    sql += ",\n".join(col_definitions)
    sql += "\n);\n"
    
    # 3. Adición de Clave Foránea (para FasePaciente)
    if table_name == 'FasePaciente':
        sql += "\nALTER TABLE FasePaciente ADD CONSTRAINT FK_PacienteFase \n"
        sql += "FOREIGN KEY (PACIENTE_CEDULA) REFERENCES Pacientes(CEDULA);\n"
        
    sql += "GO\n"
    
    return sql


def main():
    """Ejecuta la lectura, limpieza y genera el script SQL final."""
    
    # --- Archivo 1: Pacientes ---
    try:
        df_pacientes = pd.read_excel('archivos_excel/pacientes.xlsx', dtype=str)
        df_pacientes = normalize_columns_and_rename(df_pacientes, 'Pacientes')
        
       
        sql_pacientes = generate_create_table_sql(df_pacientes, 'Pacientes')
        
        print("--- Estructura de df_pacientes (Limpio) ---")
        print(df_pacientes.info())
        print("\nPrimeras filas (Limpio):")
        print(df_pacientes.head(1))
        
    except FileNotFoundError:
        print("ERROR: No se encontró 'pacientes.xlsx'. Asegúrate de que el archivo existe.")
        df_pacientes = pd.DataFrame() 
        sql_pacientes = None
        
    print("\n" + "="*50 + "\n")

    # --- Archivo 2: Fases de Paciente ---
    try:
        df_fases = pd.read_excel('archivos_excel/tmz.xlsx', dtype=str)
        df_fases = normalize_columns_and_rename(df_fases, 'FasePaciente')
        
        # Ajuste clave para Clave Foránea
        df_fases = df_fases.rename(columns={'CEDULA': 'PACIENTE_CEDULA'})
        
        sql_fases = generate_create_table_sql(df_fases, 'FasePaciente')

        print("--- Estructura de df_fases (Limpio) ---")
        print(df_fases.info())
        print("\nPrimeras filas (Limpio):")
        print(df_fases.head(1))
        
    except FileNotFoundError:
        print("ERROR: No se encontró 'tmz.xlsx'. Asegúrate de que el archivo existe.")
        df_fases = pd.DataFrame() 
        sql_fases = None
    
    # --- Imprimir el SQL Final ---
    #print("\n\n" + "="*80)
    #print("||       SENTENCIAS SQL FINALES (Copia y pega en Azure Portal)       ||")
    #print("="*80)
    
    #if sql_pacientes:
    #    print(sql_pacientes)
    #if sql_fases:
    #    print(sql_fases)
    
    #print("="*80)




def insert_dataframe_to_sql(df, table_name):
    """
    Inserta un DataFrame en Azure SQL usando pyodbc.
    """
    conn = get_azure_sql_connection()
    if conn is None:
        print("❌ No hay conexión a Azure SQL.")
        return

    cursor = conn.cursor()

    # Columnas
    columns = ", ".join([f"[{col}]" for col in df.columns])
    placeholders = ", ".join(["?"] * len(df.columns))

    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    try:
        for _, row in df.iterrows():
            cursor.execute(sql, tuple(row.values))

        conn.commit()
        print(f"✔ Datos insertados correctamente en {table_name}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error insertando datos en {table_name}: {e}")

    finally:
        cursor.close()
        conn.close()


# ====== INSERTAR DATOS A LAS TABLAS ======
from azure_connector import get_azure_sql_connection

print("\n--- INSERTANDO DATOS EN SQL SERVER ---\n")

if not df_pacientes.empty:
    insert_dataframe_to_sql(df_pacientes, "tmz_data.Pacientes_tmz")

if not df_fases.empty:
    insert_dataframe_to_sql(df_fases, "tmz_data.FasePaciente")

print("\n✔ CARGA COMPLETA.")
# Ejecutar la función principal si el script se corre directamente
if __name__ == '__main__':
    main()
    print("="*80)

   