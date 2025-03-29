import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3
import qrcode
import unicodedata

# Verifica se está rodando na nuvem (Streamlit Cloud)
is_cloud = os.getenv("HOME") == "/home/appuser"

# Caminho do logotipo institucional
logo_path = "logo_vertical_colorido.png"
qr_path = "qrcode.png"

# Função para remover acentos (solução provisória para compatibilidade com latin-1)
def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('latin-1', 'ignore').decode('latin-1')

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
                    tipos_vigilancia TEXT,
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
                    conformidades, tipos_vigilancia, kit_monitoramento, status_monitoramento, 
                    observacoes_monitoramento, recomendacoes, fotos_salvas, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (
                dados['fiscal'], dados['data'], dados['mes'], dados['unidade'], dados['municipio'],
                dados['ocorrencias'], dados['conformidades'], ", ".join(dados['tipos_vigilancia']), ", ".join(dados['kit']), dados['status'],
                dados['obs_kit'], dados['recomendacoes'], ", ".join(dados['nomes_fotos']),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              ))
    conn.commit()
    conn.close()

# Gerar o PDF com layout completo

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if os.path.exists(logo_path):
        pdf.image(logo_path, x=80, y=10, w=50)
        pdf.ln(30)

    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, txt=remover_acentos("RELATORIO DE FISCALIZACAO - CONTRATO 300000219/2022"), ln=True, align="C")
    pdf.ln(8)

    def linha_campo(label, valor):
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(60, 10, txt=remover_acentos(label), ln=False)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=remover_acentos(valor), ln=True)

    linha_campo("Fiscal:", dados['fiscal'])
    linha_campo("Data da Fiscalizacao:", dados['data'])
    linha_campo("Mes de Referencia:", dados['mes'])
    linha_campo("Unidade:", dados['unidade'])
    linha_campo("Municipio:", dados['municipio'])

    pdf.ln(5)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt=remover_acentos("COMPOSICAO DA VIGILANCIA E MONITORAMENTO"), ln=True, fill=True)

    pdf.set_font("Arial", style='', size=11)
    pdf.multi_cell(0, 8, remover_acentos("Tipos de Vigilancia Organica: " + ", ".join(dados['tipos_vigilancia'])))
    pdf.multi_cell(0, 8, remover_acentos("Kit(s) de Monitoramento Eletronico: " + ", ".join(dados['kit'])))
    pdf.multi_cell(0, 8, remover_acentos("Status do Sistema: " + dados['status']))
    pdf.multi_cell(0, 8, remover_acentos("Observacoes do Monitoramento: " + dados['obs_kit']))

    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt=remover_acentos("Ocorrencias:"), ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, remover_acentos(dados['ocorrencias']))

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt=remover_acentos("Conformidades:"), ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, remover_acentos(dados['conformidades']))

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt=remover_acentos("Recomendacoes:"), ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, remover_acentos(dados['recomendacoes']))

    # Página de fotos
    if dados['nomes_fotos']:
        for i, nome in enumerate(dados['nomes_fotos']):
            if i % 4 == 0:
                pdf.add_page()
                pdf.set_font("Arial", style='B', size=12)
                pdf.cell(0, 10, txt=remover_acentos(f"Fotos da Fiscalizacao - {dados['unidade']} ({dados['data']}):"), ln=True)
            x = 10 + (i % 2) * 100
            y = 30 + ((i % 4) // 2) * 100
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(x, y, 85, 80)
            pdf.image(nome, x=x + 1, y=y + 1, w=83, h=78)
            pdf.set_xy(x, y + 82)
            legenda = os.path.splitext(os.path.basename(nome))[0].replace("_", " ").capitalize()
            pdf.set_font("Arial", size=8)
            pdf.cell(85, 5, txt=remover_acentos(legenda), ln=True, align="C")
            pdf.set_y(-15)
            pdf.set_font("Arial", size=8)
            pdf.cell(0, 5, txt=remover_acentos("Relatorio gerado pela Supervisao de Seguranca Corporativa - SANEAGO"), align="C", ln=True)
            pdf.cell(0, 5, txt=remover_acentos(f"Pagina {pdf.page_no()}"), align="C")

    # QR Code
    qr_info = f"Fiscal: {dados['fiscal']} | Data: {dados['data']} | Unidade: {dados['unidade']}"
    qr = qrcode.make(qr_info)
    qr.save(qr_path)

    pdf.add_page()
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt=remover_acentos("QR Code para validacao do relatorio:"), ln=True)
    pdf.image(qr_path, x=80, y=30, w=50)

    # Checklist final
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt=remover_acentos("Checklist de Validacao – Relatorio de Fiscalizacao"), ln=True)
    pdf.set_font("Arial", size=10)
    checklist = [
        "1. Identificacao Geral:",
        "[ ] Nome do fiscal preenchido corretamente",
        "[ ] Data e mes de referencia compativeis",
        "[ ] Unidade e municipio corretos",
        "2. Ocorrencias:",
        "[ ] Descricao tecnica clara e objetiva",
        "[ ] Uso adequado da linguagem institucional",
        "3. Conformidades:",
        "[ ] Todos os itens avaliados possuem marcacao",
        "[ ] Presenca das 4 opcoes: Conforme, Nao conforme, Parcialmente conforme, Nao se aplica",
        "4. Monitoramento Eletronico:",
        "[ ] Tipo de Kit e status coerentes",
        "[ ] Observacoes registradas, se necessario",
        "5. Recomendacoes:",
        "[ ] Fundamentacao tecnica presente",
        "6. Fotos:",
        "[ ] Imagens anexadas (ate 16), nitidas e com legenda",
        "7. Estrutura Visual:",
        "[ ] Logotipo visivel na capa",
        "[ ] Rodape com numeracao de paginas",
        "[ ] QR Code gerado corretamente"
    ]
    for item in checklist:
        pdf.cell(0, 8, txt=remover_acentos(item), ln=True)

    caminho = f"/tmp/relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" if is_cloud else f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(caminho)
    return caminho
