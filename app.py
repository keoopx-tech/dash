import streamlit as st
from azure_connector import fetch_data
from sidebar_filters import render_sidebar_filters
from azure_connector import fetch_data
import plotly.express as px
import pandas as pd

# --- 1. CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Dashboard Clínico TMZ")

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
        F.MES,
        F.DEPARTAMENTO, F.CIUDAD,
        F.EPS,
        F.RESULTADOS_A_CORTE_14_OCTUBRE_JOHN,
        F.MUESTRA_ENVIADA_A_ESPAÑA
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


if "resultados_tmz" in df_data.columns:
    df_data["resultados_tmz"] = df_data["resultados_tmz"].map({True: "SI", False: "NO"})

# -----------------------------------------------------------------
# 3. INTERFAZ Y VISUALIZACIONES
# -----------------------------------------------------------------


st.title("SEGUIMIENTO A PACIENTES: TMZ")
st.caption("Pacientes - tamizaje")
#st.dataframe(df_data)

col_g1, col_g2, col_g3, col_g4 = st.columns(4)


df_filtered = render_sidebar_filters(df_data)

#  >>>>>> KPIs <<<<<<
def render_kpis(df):
    # ======== Cálculos base ========
    total_reg = len(df)
    pacientes_unicos = df["CEDULA"].nunique() if "CEDULA" in df else 0

    pendientes = len(df[df["ESTADO"] == "PENDIENTE"]) if "ESTADO" in df else 0
    realizados = len(df[df["ESTADO"] == "REALIZADO"]) if "ESTADO" in df else 0
    programados = len(df[df["ESTADO"] == "PROGRAMADO"]) if "ESTADO" in df else 0

    # Si tienes una columna que indique si fue enviado a laboratorio
    col_lab = None
    for c in df.columns:
        if c.lower() in ["enviado_lab", "estado_lab", "muestra_enviada", "enviado"]:
            col_lab = c
            break

    enviados_lab = len(df[df[col_lab] == "SI"]) if col_lab else 0

    # ======== Mostrar KPIs con Streamlit ========
    st.markdown("### 📊 Indicadores Generales")

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("👥 Pacientes únicos", pacientes_unicos)
    with kpi2:
        st.metric("📄 Total registros", total_reg)
    with kpi3:
        st.metric("⏳ Pendientes", pendientes)

    kpi4, kpi5, kpi6 = st.columns(3)
    with kpi4:
        st.metric("✔️ Realizados", realizados)
    with kpi5:
        st.metric("📅 Programados", programados)
    with kpi6:
        st.metric("🧪 Enviados a laboratorio", enviados_lab)
##>>>>>> KPIs <<<<<<

st.header("📑 Datos de Detalle Filtrados")
col_left, col_right = st.columns([3, 1])

with col_left:
    # 🛑 CAMBIO CRÍTICO: Usar df_filtered aquí
    st.dataframe(df_filtered, use_container_width=True) # Eliminamos .head(100) para mostrar el set filtrado completo
    
    
with col_right:
    # Función para convertir DataFrame a CSV para descarga
    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    
    csv = convert_df(df_filtered)
