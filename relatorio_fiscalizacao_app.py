
# relatorio_fiscalizacao_app.py
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3

# Verifica se está rodando na nuvem (Streamlit Cloud)
is_cloud = os.getenv("HOME") == "/home/appuser"

# Configurar o banco de dados SQLite
def init_db():
    if is_cloud:
        return
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
                    fotos_salvas TEXT,
                    criado_em TEXT
                )''')
    conn.commit()
    conn.close()

# Salvar dados no banco
def salvar_dados(dados):
    if is_cloud:
        return
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute('''INSERT INTO relatorios (
                    fiscal, data, mes_referencia, unidade, municipio, ocorrencias, 
                    conformidades, kit_monitoramento, status_monitoramento, 
                    observacoes_monitoramento, recomendacoes, fotos_salvas, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (
                dados['fiscal'], dados['data'], dados['mes'], dados['unidade'], dados['municipio'],
                dados['ocorrencias'], dados['conformidades'], dados['kit'], dados['status'],
                dados['obs_kit'], dados['recomendacoes'], ", ".join(dados['nomes_fotos']),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              ))
    conn.commit()
    conn.close()

# Gerar o PDF
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
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

    if dados['nomes_fotos']:
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt="Fotos da Fiscalização:", ln=True)

        for i, nome in enumerate(dados['nomes_fotos']):
            if i % 4 == 0 and i != 0:
                pdf.add_page()
            x = 10 + (i % 2) * 100
            y = 30 + ((i % 4) // 2) * 100
            pdf.image(nome, x=x, y=y, w=85, h=80)
            pdf.set_xy(x, y + 82)
            timestamp = datetime.now().strftime("Foto %d/%m/%Y %H:%M:%S")
            pdf.set_font("Arial", size=8)
            pdf.cell(85, 5, txt=timestamp, ln=True, align="C")

    caminho = f"/tmp/relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" if is_cloud else f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
        status = st.radio(f"{item}", ["Conforme", "Não conforme", "Não se aplica"], horizontal=True)
        conforme = "X" if status == "Conforme" else " "
        nao_conforme = "X" if status == "Não conforme" else " "
        nao_aplica = "X" if status == "Não se aplica" else " "
        conformidades.append(f"( {conforme} ) Conforme     ( {nao_conforme} ) Não conforme     ( {nao_aplica} ) Não se aplica     -> {item}")

    st.markdown("**Monitoramento Eletrônico**")
    kit = st.selectbox("Tipo de Kit", ["KIT-1", "KIT-2", "KIT-3", "KIT Específico", "Não identificado"])
    status_kit = st.radio("Status do Sistema", ["Em pleno funcionamento", "Com falhas"])
    obs_kit = st.text_area("Observações do Monitoramento Eletrônico")

    recomendacoes = st.text_area("Recomendações do Fiscal")

    st.markdown("**Fotos da Fiscalização (JPG ou PNG)**")
    imagens = st.file_uploader("Envie até 4 imagens", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    nomes_fotos = []
    for i, imagem in enumerate(imagens[:4]):
        nome_arquivo = f"/tmp/foto_{i+1}_{datetime.now().strftime('%H%M%S')}.jpg" if is_cloud else f"foto_{i+1}_{datetime.now().strftime('%H%M%S')}.jpg"
        with open(nome_arquivo, "wb") as f:
            f.write(imagem.getbuffer())
        nomes_fotos.append(nome_arquivo)

    submitted = st.form_submit_button("Gerar Relatório")

    if submitted:
        dados = {
            'fiscal': fiscal,
            'data': data_fiscalizacao.strftime("%d/%m/%Y"),
            'mes': mes_ref,
            'unidade': unidade,
            'municipio': municipio,
            'ocorrencias': ocorrencias,
            'conformidades': "
".join(conformidades),
            'kit': kit,
            'status': status_kit,
            'obs_kit': obs_kit,
            'recomendacoes': recomendacoes,
            'nomes_fotos': nomes_fotos
        }
        salvar_dados(dados)
        pdf_path = gerar_pdf(dados)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as file:
                pdf_bytes = file.read()
            st.download_button(
                label="📄 Baixar Relatório em PDF",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf"
            )
        else:
            st.error("Erro: o arquivo PDF não foi encontrado.")
