import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3
import qrcode

# Verifica se está rodando na nuvem (Streamlit Cloud)
is_cloud = os.getenv("HOME") == "/home/appuser"

# Caminho do logotipo institucional (usado tanto local quanto na nuvem)
logo_path = "logo_vertical_colorido.png"
qr_path = "qrcode.png"

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

# Gerar o PDF com layout melhorado
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Inserir logotipo institucional com tratamento de erro
    try:
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=80, y=10, w=50)
            pdf.ln(30)
    except Exception as e:
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, txt=f"[LOGO não carregado: {str(e)}]", ln=True)

    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, txt="RELATÓRIO DE FISCALIZAÇÃO - CONTRATO 300000219/2022", ln=True, align="C")
    pdf.ln(8)

    def linha_campo(label, valor):
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(50, 10, txt=label, ln=False)
        pdf.set_font("Arial", size=12)
        pdf.cell(100, 10, txt=valor, ln=True)

    linha_campo("Fiscal:", dados['fiscal'])
    linha_campo("Data da Fiscalização:", dados['data'])
    linha_campo("Mês de Referência:", dados['mes'])
    linha_campo("Unidade:", dados['unidade'])
    linha_campo("Município:", dados['municipio'])

    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Ocorrências:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['ocorrencias'])

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Conformidades:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['conformidades'])

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Monitoramento Eletrônico:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"Tipo de Kit: {dados['kit']}", ln=True)
    pdf.cell(0, 10, txt=f"Status: {dados['status']}", ln=True)
    pdf.multi_cell(0, 10, f"Observações: {dados['obs_kit']}")

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Recomendações:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['recomendacoes'])

    # Gerar QR Code com informações do relatório
    try:
        qr_info = f"Fiscal: {dados['fiscal']} | Data: {dados['data']} | Unidade: {dados['unidade']}"
        qr = qrcode.make(qr_info)
        qr.save(qr_path)
    except Exception as e:
        qr_path = None

    if dados['nomes_fotos']:
        for i, nome in enumerate(dados['nomes_fotos']):
            if i % 4 == 0:
                pdf.add_page()
                pdf.set_font("Arial", style='B', size=12)
                pdf.cell(0, 10, txt=f"Fotos da Fiscalização - {dados['unidade']} ({dados['data']}):", ln=True)

            x = 10 + (i % 2) * 100
            y = 30 + ((i % 4) // 2) * 100
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(x, y, 85, 80)
            pdf.image(nome, x=x + 1, y=y + 1, w=83, h=78)
            pdf.set_xy(x, y + 82)
            legenda = os.path.splitext(os.path.basename(nome))[0].replace("_", " ").capitalize()
            pdf.set_font("Arial", size=8)
            pdf.cell(85, 5, txt=legenda, ln=True, align="C")

            # Rodapé institucional com número de página
            pdf.set_y(-15)
            pdf.set_font("Arial", size=8)
            pdf.cell(0, 5, txt="Relatório gerado pela Supervisão de Segurança Corporativa - SANEAGO", align="C", ln=True)
            pdf.cell(0, 5, txt=f"Página {pdf.page_no()}", align="C")

    # Inserir QR Code na última página (se foi gerado)
    if qr_path and os.path.exists(qr_path):
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, txt="QR Code para validação do relatório:", ln=True)
        pdf.image(qr_path, x=80, y=30, w=50)

    # Adicionar checklist institucional
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Checklist de Validação – Relatório de Fiscalização", ln=True)
    pdf.set_font("Arial", size=10)
    checklist = [
        "1. Identificação Geral:",
        "[ ] Nome do fiscal preenchido corretamente",
        "[ ] Data e mês de referência compatíveis",
        "[ ] Unidade e município corretos",
        "2. Ocorrências:",
        "[ ] Descrição técnica clara e objetiva",
        "[ ] Uso adequado da linguagem institucional",
        "3. Conformidades:",
        "[ ] Todos os itens avaliados possuem marcação",
        "[ ] Presença das 4 opções: Conforme, Não conforme, Parcialmente conforme, Não se aplica",
        "4. Monitoramento Eletrônico:",
        "[ ] Tipo de Kit e status coerentes",
        "[ ] Observações registradas, se necessário",
        "5. Recomendações:",
        "[ ] Fundamentação técnica presente",
        "6. Fotos:",
        "[ ] Imagens anexadas (até 16), nítidas e com legenda",
        "7. Estrutura Visual:",
        "[ ] Logotipo visível na capa",
        "[ ] Rodapé com numeração de páginas",
        "[ ] QR Code gerado corretamente"
    ]
    for item in checklist:
        pdf.cell(0, 8, txt=item, ln=True)

    caminho = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(caminho)
    return caminho
