import pandas as pd

# --- Función de Utilidad para Normalizar Encabezados ---
def normalize_columns_and_rename(df, table_name):
    """Normaliza nombres de columna y elimina columnas 'UNNAMED'."""
    def clean_name(col):
        clean = col.upper()
        clean = clean.replace(' ', '_').replace('/', '_').replace('.', '').replace('É', 'E')
        clean = clean.replace('__', '_')
        return clean.strip('_')

    original_to_clean = {col: clean_name(col) for col in df.columns}
    df.columns = original_to_clean.values()

    df = df.drop(df.filter(like='UNNAMED').columns, axis=1)
    return df


def load_and_process_excels():
    """Carga, limpia y tipifica los excels para la inserción SQL. Retorna df_pacientes y df_fases."""
    
    # -----------------------------------------------------------
    # 1. Procesamiento de df_pacientes
    # -----------------------------------------------------------
    df_pacientes = pd.read_excel('archivos_excel/pacientes.xlsx', dtype=str)
    df_pacientes = normalize_columns_and_rename(df_pacientes, 'Pacientes')

    # Corrección 1: Asegurar que TODAS las columnas sean strings y manejar NaN
    # Reemplazar NaN con cadena vacía ('') y forzar el tipo string
    df_pacientes = df_pacientes.fillna('')
    for col in df_pacientes.columns:
        df_pacientes[col] = df_pacientes[col].astype(str)
        
    
    


    # -----------------------------------------------------------
    # 2. Procesamiento de df_fases
    # -----------------------------------------------------------
    df_fases = pd.read_excel('archivos_excel/tmz.xlsx', dtype=str)
    df_fases = normalize_columns_and_rename(df_fases, 'FasePaciente')

    if 'DOCUMENTO' in df_fases.columns:
        df_fases = df_fases.rename(columns={'DOCUMENTO': 'PACIENTE_CEDULA'})
    elif 'CEDULA' in df_fases.columns:
        df_fases = df_fases.rename(columns={'CEDULA': 'PACIENTE_CEDULA'})


    # Corrección 2: Asegurar que TODAS las columnas sean strings y manejar NaN
    df_fases = df_fases.fillna('')
    for col in df_fases.columns:
        df_fases[col] = df_fases[col].astype(str)

    # Ajuste clave para la FK (asumiendo que en el excel tmz.xlsx la cédula se llama 'CEDULA')
    df_fases = df_fases.rename(columns={'CEDULA': 'PACIENTE_CEDULA'})

    # **FILTRO CRÍTICO 2 (FK FIX):** Asegurar que solo se inserten fases con pacientes ya cargados
    
    # Obtener la lista de cédulas válidas que se insertarán en Pacientes_tmz
    cedulas_pacientes_validas = df_pacientes['CEDULA'].unique()

    filas_originales_fases = len(df_fases)
    
    # Filtrar df_fases para solo incluir cédulas que estén en la lista de pacientes
    df_fases = df_fases[
        df_fases['PACIENTE_CEDULA'].isin(cedulas_pacientes_validas)
    ]

    print(f"[FasePaciente]: Se omitieron {filas_originales_fases - len(df_fases)} filas porque su PACIENTE_CEDULA no existe en el conjunto de pacientes válidos (Error de FK).")

    

    return df_pacientes, df_fases




