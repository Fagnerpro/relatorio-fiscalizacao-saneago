# Código principal do aplicativo Streamlit será adicionado manualmente.
# relatorio_fiscalizacao_app.py
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3

# Configurar o banco de dados SQLite
def init_db():
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS relatorios (
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
                    criado_em TEXT
                )''')
    conn.commit()
    conn.close()

# Salvar dados no banco
def salvar_dados(dados):
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute('''INSERT INTO relatorios (
                    fiscal, data, mes_referencia, unidade, municipio, ocorrencias, 
                    conformidades, kit_monitoramento, status_monitoramento, 
                    observacoes_monitoramento, recomendacoes, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (
                dados['fiscal'], dados['data'], dados['mes'], dados['unidade'], dados['municipio'],
                dados['ocorrencias'], dados['conformidades'], dados['kit'], dados['status'],
                dados['obs_kit'], dados['recomendacoes'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              ))
    conn.commit()
    conn.close()

# Gerar o PDF
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="RELATORIO DE FISCALIZACAO - CONTRATO 300000219/2022", ln=True, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Fiscal: {dados['fiscal']}", ln=True)
    pdf.cell(200, 10, txt=f"Data da Fiscalizacao: {dados['data']}", ln=True)
    pdf.cell(200, 10, txt=f"Mes de Referencia: {dados['mes']}", ln=True)
    pdf.cell(200, 10, txt=f"Unidade: {dados['unidade']}", ln=True)
    pdf.cell(200, 10, txt=f"Municipio: {dados['municipio']}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Ocorrencias:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['ocorrencias'])

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Conformidades:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['conformidades'])

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Monitoramento Eletronico:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tipo de Kit: {dados['kit']}", ln=True)
    pdf.cell(200, 10, txt=f"Status: {dados['status']}", ln=True)
    pdf.multi_cell(0, 10, f"Observacoes: {dados['obs_kit']}")

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="Recomendacoes:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['recomendacoes'])

    caminho = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(caminho)
    return caminho

# Interface Streamlit
init_db()
st.title("Relatório de Fiscalização - SANEAGO")

with st.form("formulario"):
    fiscal = st.text_input("Fiscal Responsável")
    data_fiscalizacao = st.date_input("Data da Fiscalização")
    mes_ref = st.text_input("Mês de Referência (MM/AAAA)")
    unidade = st.text_input("Unidade Fiscalizada")
    municipio = st.text_input("Município")
    ocorrencias = st.text_area("Ocorrências Registradas")

    st.markdown("**Conformidades / Não Conformidades**")
    conformidades = []
    opcoes = [
        "Vigilante presente no horário",
        "Apresentação pessoal adequada",
        "Condições do posto",
        "Equipamentos de segurança",
        "Comunicação com a central",
        "Outros"
    ]
    for item in opcoes:
        status = st.radio(f"{item}", ["Conforme", "Não conforme"], horizontal=True)
        conformidades.append(f"( {'X' if status == 'Conforme' else ' '} ) Conforme     ( {'X' if status == 'Não conforme' else ' '} ) Não conforme     -> {item}")

    st.markdown("**Monitoramento Eletrônico**")
    kit = st.selectbox("Tipo de Kit", ["KIT-1", "KIT-2", "KIT-3", "KIT Específico", "Não identificado"])
    status_kit = st.radio("Status do Sistema", ["Em pleno funcionamento", "Com falhas"])
    obs_kit = st.text_area("Observações do Monitoramento Eletrônico")

    recomendacoes = st.text_area("Recomendações do Fiscal")

    submitted = st.form_submit_button("Gerar Relatório")

    if submitted:
        dados = {
            'fiscal': fiscal,
            'data': data_fiscalizacao.strftime("%d/%m/%Y"),
            'mes': mes_ref,
            'unidade': unidade,
            'municipio': municipio,
            'ocorrencias': ocorrencias,
            'conformidades': "\n".join(conformidades),
            'kit': kit,
            'status': status_kit,
            'obs_kit': obs_kit,
            'recomendacoes': recomendacoes
        }
        salvar_dados(dados)
        pdf_path = gerar_pdf(dados)
        with open(pdf_path, "rb") as file:
            st.download_button(
                label="📄 Baixar Relatório em PDF",
                data=file,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf"
            )
