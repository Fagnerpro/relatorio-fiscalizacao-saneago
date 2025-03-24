
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3

is_cloud = os.getenv("HOME") == "/home/appuser"

def init_db():
    if is_cloud:
        return
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fiscal TEXT,
            data TEXT,
            mes_referencia TEXT,
            unidade TEXT,
            municipio TEXT,
            ocorrencias TEXT,
            conformidades TEXT,
            kit_monitoramento TEXT,
            status_monitoramento TEXT,
            observacoes_monitoramento TEXT,
            recomendacoes TEXT,
            fotos_salvas TEXT,
            criado_em TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_dados(dados):
    if is_cloud:
        return
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO relatorios (
            fiscal, data, mes_referencia, unidade, municipio, ocorrencias,
            conformidades, kit_monitoramento, status_monitoramento,
            observacoes_monitoramento, recomendacoes, fotos_salvas, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dados['fiscal'], dados['data'], dados['mes'], dados['unidade'], dados['municipio'],
        dados['ocorrencias'], dados['conformidades'], dados['kit'], dados['status'],
        dados['obs_kit'], dados['recomendacoes'], ", ".join(dados['nomes_fotos']),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Fiscalização", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Fiscal: {dados['fiscal']}")
    pdf.multi_cell(0, 10, f"Data: {dados['data']}")
    pdf.multi_cell(0, 10, f"Mês: {dados['mes']}")
    caminho = f"/tmp/relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" if is_cloud else f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(caminho)
    return caminho

init_db()
st.title("Relatório de Fiscalização - SANEAGO")

with st.form("formulario"):
    fiscal = st.text_input("Fiscal Responsável")
    data_fiscalizacao = st.date_input("Data da Fiscalização")
    mes_ref = st.text_input("Mês de Referência (MM/AAAA)")
    unidade = st.text_input("Unidade Fiscalizada")
    municipio = st.text_input("Município")
    ocorrencias = st.text_area("Ocorrências Registradas")
    submitted = st.form_submit_button("Gerar Relatório")

if submitted:
    dados = {
        'fiscal': fiscal,
        'data': data_fiscalizacao.strftime("%d/%m/%Y"),
        'mes': mes_ref,
        'unidade': unidade,
        'municipio': municipio,
        'ocorrencias': ocorrencias,
        'conformidades': "Padrão",
        'kit': "KIT-1",
        'status': "Em pleno funcionamento",
        'obs_kit': "Sem observações",
        'recomendacoes': "Nenhuma",
        'nomes_fotos': []
    }
    salvar_dados(dados)
    pdf_path = gerar_pdf(dados)
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as file:
            st.download_button(
                label="📄 Baixar Relatório em PDF",
                data=file.read(),
                file_name=os.path.basename(pdf_path),
                mime="application/pdf"
            )
