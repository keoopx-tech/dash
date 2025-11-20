# azure_connector.py

import pyodbc
import streamlit as st
import pandas as pd


@st.cache_resource
def get_azure_sql_connection():
    """
    Establece y cachea la conexión a Azure SQL Database usando st.secrets.
    Retorna el objeto de conexión pyodbc o None en caso de error.
    """
    try:
        # st.secrets['azure_sql'] lee las credenciales del archivo .streamlit/secrets.toml
        conn_str = (
            f"DRIVER={st.secrets['azure_sql']['DRIVER']};"
            f"SERVER={st.secrets['azure_sql']['SERVER']};"
            f"DATABASE={st.secrets['azure_sql']['DATABASE']};"
            f"UID={st.secrets['azure_sql']['USERNAME']};"
            f"PWD={st.secrets['azure_sql']['PASSWORD']};"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except KeyError as e:
        st.error(f"Error de configuración: Falta la clave '{e}' en `.streamlit/secrets.toml` bajo `[azure_sql]`.")
        return None
    except Exception as e:
        st.error(f"Error al intentar conectar a Azure SQL Database. Verifica tu DRIVER, VPN/Firewall y credenciales. Detalle: {e}")
        return None



@st.cache_data(ttl=600)  # Los datos se almacenan en caché por 600 segundos

def fetch_data(query):
    """
    Ejecuta una consulta SQL y retorna los resultados como un DataFrame de Pandas.
    """
    conn = get_azure_sql_connection()
    if conn:
        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error al ejecutar la consulta SQL. Revisa la sintaxis de la query. Detalle: {e}")
            return pd.DataFrame()
    return pd.DataFrame()