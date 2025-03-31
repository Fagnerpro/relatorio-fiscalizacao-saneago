import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3
import qrcode
import unicodedata

# Mostrar erros detalhados na interface Streamlit
try:
    st.set_option('client.showErrorDetails', True)
except Exception as e:
    st.error(f"Erro ao configurar Streamlit: {e}")
    raise

# Verifica se está rodando na nuvem (Streamlit Cloud)
is_cloud = os.getenv("HOME") == "/home/appuser"

# Caminho do logotipo institucional
logo_path = "logo_vertical_colorido.png"
qr_path = "qrcode.png"

# Função para remover acentos (solução provisória para compatibilidade com latin-1)
def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('latin-1', 'ignore').decode('latin-1')

# Configurar o banco de dados SQLite
# (continuação esperada...)
