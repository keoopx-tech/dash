import pandas as pd
import streamlit as st
import azure_connector
from azure_connector import get_azure_sql_connection






st.set_page_config(page_title="DB Loader", layout="wide")


st.write("Importando desde:", azure_connector.__file__)
# Asumiendo que azure_connector.py tiene tus funciones de conexión

# Asumiendo que tienes esta función para generar el SQL (vista en discusiones previas)

# Definición de los archivos Excel y los nombres de las tablas finales
EXCEL_FILES = {
    'Pacientes_tmz': 'archivos_excel/pacientes.xlsx',
    'FasePaciente': 'archivos_excel/tmz.xlsx'
}

# --- Función de Utilidad para Limpieza y Normalización ---
def clean_and_normalize_dataframe(df, table_name):
    """Limpia nombres, elimina UNNAMED y aplica renombramientos específicos."""
    
    # 1. Normalización de Nombres
    def clean_name(col):
        clean = col.upper()
        # Reemplazar espacios, '/', '.', y tildes por '_'
        clean = clean.replace(' ', '_').replace('/', '_').replace('.', '').replace('É', 'E')
        clean = clean.replace('__', '_')
        return clean.strip('_')

    df.columns = [clean_name(col) for col in df.columns]
    
    # 2. Eliminación de Columnas UNNAMED
    initial_cols = len(df.columns)
    df = df.drop(df.filter(like='UNNAMED').columns, axis=1)
    st.info(f"Eliminadas {initial_cols - len(df.columns)} columnas 'UNNAMED' en {table_name}.")

    # 3. Renombramientos específicos para el esquema
    if table_name == 'Pacientes_tmz':
        df = df.rename(columns={
            'FECHA_DE_PROGRAMACION_DE_CITA': 'FECHA_PROG_CITA',
            'IPS_INSTITUTO_QUE_REMITE': 'IPS_QUE_REMITE',
            'OBSERVACIONES1': 'OBSERVACIONES_2'
        })
        # *Opcional: Si decides convertir las fechas a datetime en Python, hazlo aquí*

    elif table_name == 'FasePaciente':
        # !!! EL CAMBIO CRÍTICO: Renombrar la columna Cédula/Documento para la FK !!!
        # Se asume que el campo clave en tmz.xlsx se llama 'DOCUMENTO' o 'CEDULA'. 
        # Si se llama 'DOCUMENTO' después de la normalización, se renombra a 'PACIENTE_CEDULA'.
        if 'DOCUMENTO' in df.columns:
            df = df.rename(columns={'DOCUMENTO': 'PACIENTE_CEDULA'})
        # Si ya se llama CEDULA pero queremos estandarizar:
        elif 'CEDULA' in df.columns:
             df = df.rename(columns={'CEDULA': 'PACIENTE_CEDULA'})

        # *Opcional: Conversión a INT si la columna ORDEN_X_MES debe ser numérica*
        # if 'ORDEN_X_MES' in df.columns:
        #    df['ORDEN_X_MES'] = pd.to_numeric(df['ORDEN_X_MES'], errors='coerce').astype('Int64')

    return df

# --- Función de Carga Principal ---
def setup_and_load_data():
    st.title(" ETL: Carga de Datos a Azure SQL (Esquema tmz_data)")
    
    # Intenta obtener la conexión al motor SQL
    try:
        engine = get_azure_sql_connection()
        st.success("Conexión a Azure SQL establecida.")
    except Exception as e:
        st.error(f"Error al conectar a Azure SQL: {e}")
        return

    for table_name, file_name in EXCEL_FILES.items():
        st.subheader(f"Procesando: {table_name}")
        
        try:
            # 1. Lectura del Excel (todo como string)
            df = pd.read_excel(file_name, dtype=str)
            st.write(f"Filas leídas originalmente: {len(df)}")

            # 2. Limpieza y Normalización
            df_clean = clean_and_normalize_dataframe(df, table_name)
            
            # 3. Generación del SQL (Solo si queremos recrear la tabla)
            # Aunque las tablas ya existen, esta línea se usa para verificación.
            # create_sql = generate_create_table_sql(df_clean, table_name)
            # engine.execute(create_sql) 
            
            # 4. Carga de Datos con Pandas to_sql
            st.info(f"Insertando {len(df_clean)} filas en tmz_data.{table_name}...")
            
            # !!! EL CAMBIO CRÍTICO: ESPECIFICAR EL ESQUEMA !!!
            df_clean.to_sql(
                table_name, 
                con=engine, 
                schema='tmz_data',         # <-- Nuevo Esquema
                if_exists='append',       # o 'replace' si quieres borrar la tabla antes
                index=False
            )
            
            st.success(f"Carga exitosa en tmz_data.{table_name}. Columnas finales: {list(df_clean.columns)}")

        except FileNotFoundError:
            st.error(f"ERROR: No se encontró el archivo '{file_name}'. Omitiendo tabla {table_name}.")
        except Exception as e:
            st.error(f"Error durante la carga de {table_name}: {e}")
            # Muestra las columnas del DF para ayudar a depurar errores de mapeo
            st.code(f"Columnas del DF que causaron el error: {list(df_clean.columns)}")

# if __name__ == '__main__':
#     setup_and_load_data()