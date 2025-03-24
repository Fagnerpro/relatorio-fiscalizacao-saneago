
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3

# Detectar ambiente na nuvem
is_cloud = os.getenv("HOME") == "/home/appuser"

# Inicialização do banco local
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

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="RELATÓRIO DE FISCALIZAÇÃO - CONTRATO 300000219/2022", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Fiscal: {dados['fiscal']}", ln=True)
    pdf.cell(200, 10, txt=f"Data da Fiscalização: {dados['data']}", ln=True)
    pdf.cell(200, 10, txt=f"Mês de Referência: {dados['mes']}", ln=True)
    pdf.cell(200, 10, txt=f"Unidade: {dados['unidade']}", ln=True)
    pdf.cell(200, 10, txt=f"Município: {dados['municipio']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Ocorrências:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['ocorrencias'])
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Conformidades:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['conformidades'])
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Monitoramento Eletrônico:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Tipo de Kit: {dados['kit']}", ln=True)
    pdf.cell(200, 10, txt=f"Status: {dados['status']}", ln=True)
    pdf.multi_cell(0, 10, f"Observações: {dados['obs_kit']}")
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Recomendações:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['recomendacoes'])

    if dados['nomes_fotos']:
        pdf.add_page()
        for i, nome in enumerate(dados['nomes_fotos']):
            if i % 4 == 0 and i != 0:
                pdf.add_page()
            x = 10 + (i % 2) * 100
            y = 30 + ((i % 4) // 2) * 100
            pdf.image(nome, x=x, y=y, w=85, h=80)
            pdf.set_xy(x, y + 82)
            pdf.set_font("Arial", size=8)
            pdf.cell(85, 5, txt=datetime.now().strftime("Foto %d/%m/%Y %H:%M:%S"), ln=True, align="C")

    path = f"/tmp/relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" if is_cloud else f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(path)
    return path

init_db()
st.title("Relatório de Fiscalização - SANEAGO")

with st.form("formulario"):
    fiscal = st.text_input("Fiscal Responsável")
    data_fiscalizacao = st.date_input("Data da Fiscalização")
    mes_ref = st.text_input("Mês de Referência (MM/AAAA)")
    unidade = st.text_input("Unidade Fiscalizada")
    municipio = st.text_input("Município")
    ocorrencias = st.text_area("Ocorrências Registradas")
    st.markdown("### Conformidades / Não Conformidades")
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
        status = st.radio(item, ["Conforme", "Não conforme", "Não se aplica"], horizontal=True, key=item)
        linha = f"( {'X' if status == 'Conforme' else ' '} ) Conforme  "                 f"( {'X' if status == 'Não conforme' else ' '} ) Não conforme  "                 f"( {'X' if status == 'Não se aplica' else ' '} ) Não se aplica  -> {item}"
        conformidades.append(linha)

    st.markdown("### Monitoramento Eletrônico")
    kit = st.selectbox("Tipo de Kit", ["KIT-1", "KIT-2", "KIT-3", "KIT Específico", "Não identificado"])
    status_kit = st.radio("Status do Sistema", ["Em pleno funcionamento", "Com falhas"])
    obs_kit = st.text_area("Observações do Monitoramento Eletrônico")
    recomendacoes = st.text_area("Recomendações do Fiscal")
    st.markdown("### Fotos da Fiscalização")
    imagens = st.file_uploader("Envie até 4 imagens", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    nomes_fotos = []
    for i, img in enumerate(imagens[:4]):
        nome = f"/tmp/foto_{i+1}.jpg" if is_cloud else f"foto_{i+1}.jpg"
        with open(nome, "wb") as f:
            f.write(img.getbuffer())
        nomes_fotos.append(nome)
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
        'recomendacoes': recomendacoes,
        'nomes_fotos': nomes_fotos
    }
    salvar_dados(dados)
    pdf_path = gerar_pdf(dados)
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Baixar Relatório em PDF", data=f.read(), file_name=os.path.basename(pdf_path), mime="application/pdf")
