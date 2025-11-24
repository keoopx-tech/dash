import streamlit as st
from azure_connector import fetch_data
from sidebar_filters import render_sidebar_filters
from azure_connector import fetch_data
import plotly.express as px
import pandas as pd

# --- 1. CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Dashboard Clínico TMZ")

st.markdown(
    """
    <style>
    /* 1. Imagen de fondo para el área principal */
    [data-testid="stAppViewContainer"] {
        background-image: url("https://www.freepik.es/vector-gratis/fondo-abstracto-diseno-cuadricula-hexagonal-puntos_418612096.htm#fromView=search&page=1&position=2&uuid=25a3462c-288f-46c5-9104-2dab60ad2b10&query=WHITE+BACKGROUND+MEDICAL+"); 
        background-size: cover;
        background-attachment: fixed; /* Opcional: mantiene la imagen fija al hacer scroll */
        background-position: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. CARGA DE DATOS CON LEFT JOIN ---

@st.cache_data(ttl=600)
def load_data():
    """Carga los datos usando LEFT JOIN para incluir todos los pacientes."""
    # LEFT JOIN: Mantiene TODAS las filas de Pacientes_tmz (tabla izquierda).
    query = """
    SELECT 
        P.CEDULA, 
        P.NOMBRE,
        P.NOMBRE_MEDICO,
        F.GENERO,
        F.EDAD,
        F.RANGO_DE_EDAD,
        P.FECHA_DE_RECIBIDO,
        F.FECHA_TOMA_MUESTRA,
        P.ESTADO,
        P.MES_DE_TOMA,
        --F.MES,
        F.DEPARTAMENTO, F.CIUDAD,
        F.EPS,
        F.RESULTADOS_A_CORTE_14_OCTUBRE_JOHN,
        F.MUESTRA_ENVIADA_A_ESPAÑA,
        p.OBSERVACIONES
    FROM 
        tmz_data.Pacientes_tmz P  -- Tabla izquierda (Todos los pacientes)
    LEFT JOIN 
        tmz_data.FasePaciente F ON P.CEDULA = F.PACIENTE_CEDULA;
    """
    df_merged = fetch_data(query)
    fecha_columna = 'FECHA_TOMA_MUESTRA'

    if fecha_columna in df_merged.columns:
        # 1. Convertir a numérico (manejar 'None' o 'NaN' como errores)
        df_merged[fecha_columna] = pd.to_numeric(
            df_merged[fecha_columna], 
            errors='coerce'  # Convierte los valores no numéricos (como 'None') a NaN
        )
        
        # 2. Aplicar la conversión de fecha serial de Excel
        # La unidad es 'Días' ('D') y el origen es el 1 de enero de 1900.
        df_merged[fecha_columna] = pd.to_datetime(
            df_merged[fecha_columna], 
            unit='D', 
            origin='1899-12-30', # Excel usa el 30 de diciembre de 1899 como día 0
            errors='coerce'
        )

    COLUMNA_MES_PROGRAMACION = 'MES_DE_TOMA'
    NUEVO_NOMBRE_MES = 'MES_PROGRAMACION'
    
    # Diccionario para mapear número a nombre del mes en español y mayúsculas
    mes_map = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL', 
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO', 
        9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
    }

    if COLUMNA_MES_PROGRAMACION in df_merged.columns:
        # Asegurarse de que sea tipo int para el mapeo, convirtiendo errores a NaN (luego a 'Sin Dato')
        df_merged[COLUMNA_MES_PROGRAMACION] = pd.to_numeric(
            df_merged[COLUMNA_MES_PROGRAMACION], errors='coerce'
        ).astype('Int64') # Int64 maneja NaN con enteros
        
        # Aplicar el mapeo
        df_merged[COLUMNA_MES_PROGRAMACION] = df_merged[COLUMNA_MES_PROGRAMACION].map(mes_map)
        
        # Renombrar la columna
        df_merged.rename(columns={COLUMNA_MES_PROGRAMACION: NUEVO_NOMBRE_MES}, inplace=True)
        
        # Rellenar valores nulos (que pueden ser del LEFT JOIN o errores de conversión)
        df_merged[NUEVO_NOMBRE_MES] = df_merged[NUEVO_NOMBRE_MES].fillna('SIN DATO')


    # Manejo de Nulos después del LEFT JOIN (los pacientes sin fase tendrán NULL aquí)
    if 'FASE_ACTUAL' in df_merged.columns:
         df_merged['FASE_ACTUAL'] = df_merged['FASE_ACTUAL'].fillna('Sin Fase Registrada')
    
    if 'FECHA_FASE' in df_merged.columns:
         # Conversión a fecha (usando errors='coerce' para manejar nulos/errores)
         df_merged['FECHA_FASE'] = pd.to_datetime(df_merged['FECHA_FASE'], errors='coerce')

    return df_merged




# --- LLAMAR A LA FUNCIÓN DE CARGA ---
df_data = load_data()
df_data.rename(columns={"RESULTADOS_A_CORTE_14_OCTUBRE_JOHN": "RESULTADOS_TMZ"}, inplace=True)
df_data.rename(columns={"MUESTRA_ENVIADA_A_ESPAÑA": "ENVIADA_A_LABORATORIO"}, inplace=True)

columna_booleana = 'ENVIADA_A_LABORATORIO'

if columna_booleana in df_data.columns:
        
    # 1. Convertir la columna al tipo booleano de Pandas (maneja nulos como False)
    # Esto convierte TRUE/1 a True, y FALSE/0/None/NaN a False
    df_data[columna_booleana] = df_data[columna_booleana].astype(bool)

    # 2. Aplicar el mapeo limpio con el método .map()
    df_data[columna_booleana] = df_data[columna_booleana].map({
        True: "SÍ",  # Solo si es True estricto
        False: "NO"  # Todo lo demás (False, None, 0, NaN)
        })
# -----------------------------------------------------------------
# 3. INTERFAZ Y VISUALIZACIONES
# -----------------------------------------------------------------


st.title("SEGUIMIENTO A PACIENTES: TMZ")
st.caption("Pacientes - tamizaje")
#st.dataframe(df_data)

col_g1, col_g2, col_g3, col_g4 = st.columns(4)


df_filtered = render_sidebar_filters(df_data)

#  >>>>>> KPIs <<<<<<
# --- EN app.py (Reemplaza la función def render_kpis(df):) ---

def render_kpis(df):
    
    # 1. Crear un DataFrame de pacientes ÚNICOS dentro del set filtrado
    df_unicos = df.drop_duplicates(subset=['CEDULA'])
    
    # ======== Cálculos de Indicadores por Paciente Único ========
    total_pacientes_unicos = df_unicos["CEDULA"].nunique()

    # 2. Tamizaje Realizado
    realizado_tamizaje = df_unicos[df_unicos["ESTADO"] == "REALIZADO"].shape[0]

    # 3. Pacientes con Resultados
    # Asume que un resultado existe si la columna no es nula y no está vacía
    if "RESULTADOS_TMZ" in df_unicos.columns:
        
        # 1. Definir la condición de EXCLUSIÓN total:
        
        # a) Es nulo o None
        is_null = df_unicos["RESULTADOS_TMZ"].isna()
        
        # b) Es una cadena vacía (después de convertir a string para manejar posibles tipos)
        is_empty = (df_unicos["RESULTADOS_TMZ"].astype(str) == '')
        
        # c) Contiene "Pendiente de reporte" (solo en los que tienen algún valor string)
        is_pending = df_unicos["RESULTADOS_TMZ"].astype(str).str.contains("Pendiente de reporte", case=False, na=False)
        
        # 2. Combinar las condiciones de exclusión: (Nulo O Vacío O Pendiente)
        is_excluded = is_null | is_empty | is_pending
        
        # 3. Contar los que NO cumplen la condición de exclusión (usando el operador de inversión ~)
        con_resultados = df_unicos[~is_excluded].shape[0]
        
    else:
        con_resultados = 0
        
    # 4. Enviados a Laboratorio (usa el valor 'SÍ' que mapeamos)
    if "ENVIADA_A_LABORATORIO" in df_unicos.columns:
        enviados_lab = df_unicos[df_unicos["ENVIADA_A_LABORATORIO"] == "SÍ"].shape[0]
    else:
        enviados_lab = 0
        
    # 5. Desglose por Género
    genero_counts = df_unicos["GENERO"].value_counts()
    genero_f = genero_counts.get('F', 0)
    genero_m = genero_counts.get('M', 0)
    
    # ======== Mostrar KPIs con Streamlit (4 columnas) ========
    st.markdown("### 📊 Indicadores Generales (Pacientes Únicos)")

    # --- Fila 1: Totales y Progreso ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Pacientes", total_pacientes_unicos)
    with col2:
        st.metric("✔️ Tamizaje Realizado", realizado_tamizaje)
    with col3:
        st.metric("🧪 Enviados a Laboratorio", enviados_lab)
    with col4:        
        st.metric("🔬 Con Resultados TMZ", con_resultados)
        
    st.markdown("---") # Separador visual para la segunda fila
    
    # --- Fila 2: Desglose y Estado ---
    #col5, col6, col7, col8 = st.columns(4)

    #pendientes = df_unicos[df_unicos["ESTADO"] == "PENDIENTE"].shape[0]
    #programados = df_unicos[df_unicos["ESTADO"] == "PROGRAMADO"].shape[0]

    #with col5:
    #    st.metric("♀️ F", genero_f)
    #with col6:
    #    st.metric("♂️ M", genero_m)
    #with col7:
    #    st.metric("⏳ Pendientes", pendientes)
    #with col8:
    #    st.metric("📅 Programados", programados)

# Llamada a la función (¡CRÍTICO!)
# Nota: La función debe ser llamada después de definirla y después de df_filtered.

render_kpis(df_data)

st.header("📑 Datos de Detalle Filtrados")

# La tabla ocupa el 100% del ancho principal del contenedor.
st.dataframe(
    df_filtered, 
    use_container_width=True 
)
    