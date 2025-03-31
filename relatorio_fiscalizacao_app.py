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

# Caminhos padrão
logo_path = "logo_vertical_colorido.png"
qr_path = "qrcode.png"

# Configuração do banco SQLite
def init_db():
    if is_cloud:
        return
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS relatorios (
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
                )""")
    conn.commit()
    conn.close()

def salvar_dados(dados):
    if is_cloud:
        return
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("""INSERT INTO relatorios (
                    fiscal, data, mes_referencia, unidade, municipio, ocorrencias,
                    conformidades, tipos_vigilancia, kit_monitoramento, status_monitoramento,
                    observacoes_monitoramento, recomendacoes, fotos_salvas, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (
                dados['fiscal'], dados['data'], dados['mes'], dados['unidade'], dados['municipio'],
                dados['ocorrencias'], dados['conformidades'], ", ".join(dados['tipos_vigilancia']), ", ".join(dados['kit']), dados['status'],
                dados['obs_kit'], dados['recomendacoes'], ", ".join(dados['nomes_fotos']),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              ))
    conn.commit()
    conn.close()

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if os.path.exists(logo_path):
        pdf.image(logo_path, x=80, y=10, w=50)
        pdf.ln(30)

    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, txt="RELATÓRIO DE FISCALIZAÇÃO - CONTRATO 300000219/2022", ln=True, align="C")
    pdf.ln(8)

    def linha_campo(label, valor):
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(60, 10, txt=label, ln=False)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=valor, ln=True)

    linha_campo("Fiscal:", dados['fiscal'])
    linha_campo("Data da Fiscalização:", dados['data'])
    linha_campo("Mês de Referência:", dados['mes'])
    linha_campo("Unidade:", dados['unidade'])
    linha_campo("Município:", dados['municipio'])

    pdf.ln(5)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="COMPOSIÇÃO DA VIGILÂNCIA E MONITORAMENTO", ln=True, fill=True)

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, "Tipos de Vigilância Orgânica: " + ", ".join(dados['tipos_vigilancia']))
    pdf.multi_cell(0, 8, "Kit(s) de Monitoramento Eletrônico: " + ", ".join(dados['kit']))
    pdf.multi_cell(0, 8, "Status do Sistema: " + dados['status'])
    pdf.multi_cell(0, 8, "Observações do Monitoramento: " + dados['obs_kit'])

    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Ocorrências:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['ocorrencias'])

    if "Vigilante Motorizado Noturno 12hs" in dados['tipos_vigilancia']:
        pdf.ln(2)
        pdf.set_x(10)
        pdf.set_font("Arial", style='I', size=11)
        pdf.multi_cell(190, 9, "Em relação aos postos atendidos por vigilância motorizada noturna, não foram identificadas inconformidades. A unidade conta com duas rondas noturnas operando regularmente. Foi apenas pontuada a necessidade de atenção aos pontos considerados mais vulneráveis da unidade fiscalizada.")

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Conformidades:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['conformidades'])

    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="Recomendações:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, dados['recomendacoes'])

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

            legenda = os.path.splitext(os.path.basename(nome))[0].replace('_', ' ').capitalize()
            pdf.set_xy(x, y + 82)
            pdf.set_font("Arial", size=8)
            pdf.cell(85, 5, txt=legenda, ln=False, align="C")

            if i % 4 == 3 or i == len(dados['nomes_fotos']) - 1:
                pdf.set_y(-15)
                pdf.set_font("Arial", size=8)
                pdf.cell(0, 5, txt="Relatório gerado pela Supervisão de Segurança Corporativa - SANEAGO", align="C", ln=True)
                pdf.cell(0, 5, txt=f"Página {pdf.page_no()}", align="C")
        pdf.ln(10)

    qr_info = f"Fiscal: {dados['fiscal']} | Data: {dados['data']} | Unidade: {dados['unidade']}"
    qr = qrcode.make(qr_info)
    qr.save(qr_path)
    pdf.image(qr_path, x=165, y=10, w=30)

    pdf.add_page()
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, txt="CHECKLIST FINAL DO RELATÓRIO:", ln=True)

    checklist = [
        "[ ] Nome do fiscal preenchido corretamente",
        "[ ] Data e mês de referência compatíveis",
        "[ ] Unidade e município corretos",
        "[ ] Descrição técnica clara e objetiva",
        "[ ] Uso adequado da linguagem institucional",
        "[ ] Todos os itens avaliados possuem marcação",
        "[ ] Presença das 4 opções: Conforme, Não conforme, Parcialmente conforme, Não se aplica",
        "[ ] Tipo de Kit e status coerentes",
        "[ ] Observações registradas, se necessário",
        "[ ] Fundamentação técnica presente",
        "[ ] Imagens anexadas (até 16), nítidas e com legenda",
        "[ ] Logotipo visível na capa",
        "[ ] Rodapé com numeração de páginas",
        "[ ] QR Code gerado corretamente"
    ]

    for item in checklist:
        pdf.cell(0, 8, txt=item, ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", style='I', size=9)
    pdf.cell(0, 8, txt="Checklist gerado automaticamente conforme dados informados no relatório.", ln=True)

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
        status = st.radio(item, ["Conforme", "Não conforme", "Parcialmente conforme", "Não se aplica"], horizontal=True, key=item)
        linha = f"( {'X' if status == 'Conforme' else ' '} ) Conforme  " \
                f"( {'X' if status == 'Não conforme' else ' '} ) Não conforme  " \
                f"( {'X' if status == 'Parcialmente conforme' else ' '} ) Parcialmente conforme  " \
                f"( {'X' if status == 'Não se aplica' else ' '} ) Não se aplica  -> {item}"
        conformidades.append(linha)

    st.markdown("### Vigilância Orgânica")
    tipos_vigilancia = st.multiselect("Tipos de Vigilância Ativa", [
        "Vigilante Armado Diurno 12hs",
        "Vigilante Armado Noturno 12hs",
        "Vigilante Motorizado Diurno 12hs",
        "Vigilante Motorizado Noturno 12hs"
    ])

    st.markdown("### Monitoramento Eletrônico")
    kit_monitoramento = st.multiselect("Kit(s) de Monitoramento", ["KIT-1", "KIT-2", "KIT-3", "KIT Específico", "Não identificado", "Não se aplica"])
    status_kit = st.radio("Status do Sistema", ["Em pleno funcionamento", "Com falhas"])
    obs_kit = st.text_area("Observações do Monitoramento")

    recomendacoes = st.text_area("Recomendações do Fiscal")

    st.markdown("### Fotos da Fiscalização")
    imagens = st.file_uploader("Envie até 16 imagens", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    nomes_fotos = []
    for i, img in enumerate(imagens[:16]):
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
        'tipos_vigilancia': tipos_vigilancia,
        'kit': kit_monitoramento,
        'status': status_kit,
        'obs_kit': obs_kit,
        'recomendacoes': recomendacoes,
        'nomes_fotos': nomes_fotos
    }
    salvar_dados(dados)
    pdf_path = gerar_pdf(dados)
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Baixar Relatório em PDF", data=f.read(), file_name=os.path.basename(pdf_path), mime="application/pdf")
