import streamlit as st
import pandas as pd

# ==========================================================
#   FUNCIÓN PRINCIPAL: SIDEBAR DE FILTROS
# ==========================================================
def render_sidebar_filters(df_data):

    # ------------------------------------------------------
    #   CSS – Limpio, sin colores extra
    # ------------------------------------------------------
    st.sidebar.markdown("""
    <style>

    /* Sidebar más compacto */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.5rem !important;
    }

    /* Reduce espacio vertical entre componentes */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.35rem !important;
    }

    /* Agrandar área del multiselect */
    div[data-testid="stMultiSelect"] > div {
        max-height: 420px !important;
        overflow-y: auto !important;
    }

    /* Título del panel */
    .sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    /* Etiquetas de cada filtro */
    .filter-label {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        color: inherit; /* Usa el tema */
    }

    </style>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------
    #   TÍTULO LATERAL
    # ------------------------------------------------------
    st.sidebar.markdown("<div class='sidebar-title'>🔍 Filtros</div>", unsafe_allow_html=True)

    df_filtered = df_data.copy()

    # ======================================================
    # 1️⃣  FILTRO POR ESTADO
    # ======================================================
    st.sidebar.markdown("<div class='filter-label'>Estado</div>", unsafe_allow_html=True)

    if 'ESTADO' in df_filtered.columns:

        estados = ['Todos'] + sorted(
            df_filtered['ESTADO']
            .fillna("PENDIENTE")
            .astype(str)
            .unique()
        )

        sel_estado = st.sidebar.selectbox(
            "",
            estados,
            label_visibility="collapsed"
        )

        if sel_estado != "Todos":
            df_filtered = df_filtered[df_filtered["ESTADO"] == sel_estado]

    # ======================================================
    # 2️⃣  RANGO DE EDAD
    # ======================================================
    st.sidebar.markdown("<div class='filter-label'>Rango de Edad</div>", unsafe_allow_html=True) 

    if 'RANGO_DE_EDAD' in df_filtered.columns:
        
        # 1. Preparación de datos: Asegurar que los nulos se traten como 'Sin Dato'
        df_filtered['RANGO_DE_EDAD'] = df_filtered['RANGO_DE_EDAD'].fillna('Sin Dato')
        
        # 2. Definir Opciones: Incluir 'Todos' al inicio de la lista de rangos únicos
        # Usamos list comprehension para que 'Todos' no se añada si ya está en el DF.
        unique_rangos = [r for r in df_filtered['RANGO_DE_EDAD'].unique().tolist() if r != 'Todos']
        options_con_todos = ['Todos'] + sorted(unique_rangos)
        
        # 3. Widget: Unificar el multiselect para usar la etiqueta 'Todos' por defecto
        selected_rangos = st.sidebar.multiselect(
            "**Rango de Edad**", # Este título es interno, el visible es el de filter-label
            options=options_con_todos,
            default=['Todos'], # <--- Deja solo esta línea para que 'Todos' sea el valor inicial
            label_visibility="collapsed" # Ocultar el título interno del multiselect
        )
        
        # 4. Aplicar Filtro: Si 'Todos' está seleccionado, no filtra (pasa); si no, filtra.
        if 'Todos' in selected_rangos:
            # No se aplica filtro, se usa el df_filtered completo hasta este punto.
            pass 
        else:
            # Aplicamos filtro solo con los rangos seleccionados
            df_filtered = df_filtered[df_filtered['RANGO_DE_EDAD'].isin(selected_rangos)]

    # ======================================================
    # 3️⃣  FECHA DE MUESTRA (SLIDER – SIN CAMBIAR NADA)
    # ======================================================
    st.sidebar.markdown("<div class='filter-label'>Fecha de Muestra</div>", unsafe_allow_html=True)

    fecha_col = "FECHA_DE_RECIBIDO"

    if fecha_col in df_filtered.columns:

        df_filtered[fecha_col] = pd.to_datetime(df_filtered[fecha_col], errors="coerce")
        fechas_validas = df_filtered.dropna(subset=[fecha_col])

        if not fechas_validas.empty:

            min_dt = fechas_validas[fecha_col].min().date()
            max_dt = fechas_validas[fecha_col].max().date()

            if min_dt != max_dt:

                fecha_range = st.sidebar.slider(
                    "",
                    min_value=min_dt,
                    max_value=max_dt,
                    value=(min_dt, max_dt),
                    format="YYYY/MM/DD",
                    label_visibility="collapsed"
                )

                df_filtered = df_filtered[
                    (df_filtered[fecha_col].dt.date >= fecha_range[0]) &
                    (df_filtered[fecha_col].dt.date <= fecha_range[1])
                ]

            else:
                st.sidebar.info(f"Solo existe una fecha: {min_dt}")

        else:
            st.sidebar.warning("No hay fechas válidas disponibles")

    # ======================================================
    # 4️⃣  MÉTRICA FINAL
    # ======================================================
    st.sidebar.markdown("---")
    st.sidebar.metric("Pacientes Filtrados", df_filtered['CEDULA'].nunique())

    return df_filtered
