import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3
import qrcode
from typing import List, Dict, Optional
from io import BytesIO
import uuid

# Configurações iniciais
class Config:
    IS_CLOUD = os.getenv("HOME") == "/home/appuser"
    LOGO_PATH = "logo_vertical_colorido.png"
    QR_PATH = "qrcode.png"
    MAX_IMAGES = 16
    UNICODE_FONT_PATH = "DejaVuSansCondensed.ttf"  # Corrigido para arquivo fornecido

# Banco de dados SQLite
class DatabaseManager:
    def __init__(self):
        self.init_db()

    def init_db(self):
        if Config.IS_CLOUD:
            return

        with sqlite3.connect("relatorios.db") as conn:
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

    def salvar_dados(self, dados: Dict) -> None:
        if Config.IS_CLOUD:
            return
        with sqlite3.connect("relatorios.db") as conn:
            c = conn.cursor()
            c.execute("""INSERT INTO relatorios (
                        fiscal, data, mes_referencia, unidade, municipio,
                        ocorrencias, conformidades, tipos_vigilancia,
                        kit_monitoramento, status_monitoramento,
                        observacoes_monitoramento, recomendacoes,
                        fotos_salvas, criado_em
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (
                          dados["fiscal"], dados["data"], dados["mes_referencia"], dados["unidade"], dados["municipio"],
                          dados["ocorrencias"], dados["conformidades"], ", ".join(dados["tipos_vigilancia"]),
                          ", ".join(dados["kit_monitoramento"]), dados["status_monitoramento"],
                          dados["observacoes_monitoramento"], dados["recomendacoes"],
                          ", ".join(dados["fotos_salvas"]),
                          dados.get("criado_em", datetime.now().isoformat())
                      ))
            conn.commit()

# Geração de PDF
class PDFUnicode(FPDF):
    def __init__(self):
        super().__init__()
        font_path = os.path.dirname(os.path.abspath(__file__))

        self.add_font("DejaVuSansCondensed", "", os.path.join(font_path, "DejaVuSansCondensed.ttf"), uni=True)
        self.add_font("DejaVuSansCondensed", "B", os.path.join(font_path, "DejaVuSansCondensed-Bold.ttf"), uni=True)
        self.add_font("DejaVuSansCondensed", "I", os.path.join(font_path, "DejaVuSansCondensed-BoldOblique.ttf"), uni=True)
        self.set_auto_page_break(auto=True, margin=15)
        self.set_font("DejaVuSansCondensed", size=12)
        self.add_page()

    def header(self):
        self.set_font("DejaVuSansCondensed", 'B', 14)
        self.cell(0, 10, "RELATÓRIO DE FISCALIZAÇÃO - CONTRATO 300000219/2022", 0, 1, 'C')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVuSansCondensed", size=8)
        self.cell(0, 5, "Relatório técnico gerado pela Supervisão de Segurança Corporativa - SANEAGO", 0, 1, "C")
        self.cell(0, 5, f"Página {self.page_no()}", 0, 0, "C")

    def adicionar_texto(self, texto: str):
        self.multi_cell(0, 10, texto)

    def add_custom_field(self, label: str, value: str) -> None:
        self.set_font("DejaVuSansCondensed", style='B', size=12)
        self.cell(60, 10, label, ln=False)
        self.set_font("DejaVuSansCondensed", size=12)
        self.multi_cell(0, 10, value)

    def add_section_title(self, title: str) -> None:
        self.set_fill_color(220, 220, 220)
        self.set_font("DejaVuSansCondensed", style='B', size=12)
        self.cell(0, 10, title, ln=True, fill=True)
        self.ln(2)

    def add_images_grid(self, images: List[str]) -> None:
        for i, img_path in enumerate(images):
        # Adiciona nova página a cada 4 imagens
         if i % 4 == 0:
            self.add_page()
            self.ln(20)

        x = 10 + (i % 2) * 100
        y = 30 + ((i % 4) // 2) * 100

        self.set_draw_color(0, 0, 0)
        self.rect(x, y, 85, 80)
        self.image(img_path, x=x+1, y=y+1, w=83, h=78)

        legenda = os.path.splitext(os.path.basename(img_path))[0].replace('_', ' ').capitalize()
        self.set_xy(x, y+82)
        self.set_font("DejaVuSansCondensed", size=8)
        self.cell(85, 5, legenda, ln=False, align="C")

        if i % 2 == 1:
            self.ln(90)


# Continuação no próximo bloco: funções generate_pdf, gerar_pdf_apos_salvar e main

def generate_pdf(data: Dict) -> str:
    pdf = PDFUnicode()
    pdf.add_custom_field("Fiscal:", data['fiscal'])
    pdf.add_custom_field("Data da Fiscalização:", data['data'])
    pdf.add_custom_field("Mês de Referência:", data['mes_referencia'])
    pdf.add_custom_field("Unidade:", data['unidade'])
    pdf.add_custom_field("Município:", data['municipio'])
    pdf.add_section_title("Composição da Vigilância e Monitoramento")
    pdf.adicionar_texto("Tipos de Vigilância Orgânica: " + ", ".join(data['tipos_vigilancia']))
    pdf.adicionar_texto("Kit(s) de Monitoramento Eletrônico: " + ", ".join(data['kit_monitoramento']))
    pdf.adicionar_texto("Status do Sistema: " + data['status_monitoramento'])
    pdf.adicionar_texto("Observações do Monitoramento: " + data['observacoes_monitoramento'])
    pdf.add_section_title("Ocorrências")
    pdf.adicionar_texto(data['ocorrencias'])
    pdf.add_section_title("Conformidades")
    pdf.adicionar_texto(data['conformidades'])
    pdf.add_section_title("Recomendações")
    pdf.adicionar_texto(data['recomendacoes'])
    if data['fotos_salvas']:
        pdf.add_images_grid(data['fotos_salvas'])
    filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join("/tmp" if Config.IS_CLOUD else ".", filename)
    pdf.output(output_path)
    return output_path

def gerar_pdf_apos_salvar(db, dados, unidade, data_fiscalizacao):
    try:
        db.salvar_dados(dados)
        pdf_path = generate_pdf(dados)
        with open(pdf_path, "rb") as f:
            st.success("Relatório gerado com sucesso!")
            st.download_button(
                "📄 Baixar Relatório em PDF",
                data=f.read(),
                file_name=f"relatorio_{unidade}_{data_fiscalizacao.strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {str(e)}")

def main():
    db = DatabaseManager()
    st.title("Relatório de Fiscalização - SANEAGO")

    with st.form("formulario"):
        fiscal = st.text_input("Fiscal Responsável*")
        data_fiscalizacao = st.date_input("Data da Fiscalização*")
        mes_ref = st.text_input("Mês de Referência (MM/AAAA)*")
        unidade = st.text_input("Unidade Fiscalizada*")
        municipio = st.text_input("Município*")
        ocorrencias = st.text_area("Ocorrências Registradas*")
        recomendacoes = st.text_area("Recomendações do Fiscal*")
        tipos_vigilancia = st.multiselect("Tipos de Vigilância Orgânica", [
            "Vigilante Armado Diurno 12hs",
            "Vigilante Armado Noturno 12hs",
            "Vigilante Motorizado Diurno 12hs",
            "Vigilante Motorizado Noturno 12hs"
        ])
        kit_monitoramento = st.multiselect("Kit(s) de Monitoramento", [
            "KIT-1", "KIT-2", "KIT-3", "KIT Específico", "Não identificado", "Não se aplica"
        ])
        status_kit = st.radio("Status do Sistema", ["Em pleno funcionamento", "Com falhas"], horizontal=True)
        obs_kit = st.text_area("Observações do Monitoramento")

        st.markdown("### Conformidades / Não Conformidades")
        conformidades = []
        opcoes = [
            "Vigilante presente no horário",
            "Apresentação pessoal adequada",
            "Condições do posto",
            "Equipamentos de segurança",
            "Comunicação com a central",
            "Outros (especificar)"
        ]
        for item in opcoes:
            status = st.radio(
                item,
                options=["Conforme", "Não conforme", "Parcialmente conforme", "Não se aplica"],
                horizontal=True,
                key=f"conf_{item}"
            )
            if item == "Outros (especificar)":
                especificar = st.text_input("Especifique")
                if especificar:
                    item = f"Outros: {especificar}"
            linha = (
                f"( {'X' if status == 'Conforme' else ' '} ) Conforme  "
                f"( {'X' if status == 'Não conforme' else ' '} ) Não conforme  "
                f"( {'X' if status == 'Parcialmente conforme' else ' '} ) Parcialmente conforme  "
                f"( {'X' if status == 'Não se aplica' else ' '} ) Não se aplica  → {item}"
            )
            conformidades.append(linha)

        imagens = st.file_uploader(
            f"Envie até {Config.MAX_IMAGES} imagens (JPEG/PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        submitted = st.form_submit_button("Gerar Relatório")

    if submitted:
        nomes_fotos = []
        for i, img in enumerate(imagens[:Config.MAX_IMAGES] if imagens else []):
            nome = os.path.join("/tmp" if Config.IS_CLOUD else ".", f"foto_{uuid.uuid4().hex}.jpg")
            with open(nome, "wb") as f:
                f.write(img.getbuffer())
            nomes_fotos.append(nome)

        dados = {
            "fiscal": fiscal.strip(),
            "data": data_fiscalizacao.strftime("%d/%m/%Y"),
            "mes_referencia": mes_ref.strip(),
            "unidade": unidade.strip(),
            "municipio": municipio.strip(),
            "ocorrencias": ocorrencias.strip(),
            "conformidades": "\n".join(conformidades),
            "tipos_vigilancia": tipos_vigilancia,
            "kit_monitoramento": kit_monitoramento,
            "status_monitoramento": status_kit,
            "observacoes_monitoramento": obs_kit.strip(),
            "recomendacoes": recomendacoes.strip(),
            "fotos_salvas": nomes_fotos,
            "criado_em": datetime.now().isoformat()
        }

        gerar_pdf_apos_salvar(db, dados, unidade, data_fiscalizacao)

if __name__ == "__main__":
    main()




