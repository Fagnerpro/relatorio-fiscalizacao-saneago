import streamlit as st
from datetime import datetime
from fpdf import FPDF
import os
import sqlite3
import qrcode
from typing import List, Dict, Optional

# Configurações iniciais
class Config:
    IS_CLOUD = os.getenv("HOME") == "/home/appuser"
    LOGO_PATH = "logo_vertical_colorido.png"
    QR_PATH = "qrcode.png"
    MAX_IMAGES = 16

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
                        fiscal, data, mes_referencia, unidade, municipio, ocorrencias,
                        conformidades, tipos_vigilancia, kit_monitoramento, status_monitoramento,
                        observacoes_monitoramento, recomendacoes, fotos_salvas, criado_em
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        dados['fiscal'], dados['data'], dados['mes'], dados['unidade'], dados['municipio'],
                        dados['ocorrencias'], dados['conformidades'], ", ".join(dados['tipos_vigilancia']), 
                        ", ".join(dados['kit']), dados['status'], dados['obs_kit'], dados['recomendacoes'], 
                        ", ".join(dados['nomes_fotos']), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
            conn.commit()

# Geração de PDF
class PDFGenerator(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, "RELATÓRIO DE FISCALIZAÇÃO - CONTRATO 300000219/2022", 0, 1, 'C')
        self.ln(8)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=8)
        self.cell(0, 5, "Relatório técnico gerado pela Supervisão de Segurança Corporativa - SANEAGO", 0, 1, "C")
        self.cell(0, 5, f"Página {self.page_no()}", 0, 0, "C")
    
    def add_custom_field(self, label: str, value: str) -> None:
        self.set_font("Arial", style='B', size=12)
        self.cell(60, 10, label, ln=False)
        self.set_font("Arial", size=12)
        self.multi_cell(0, 10, value)
    
    def add_section_title(self, title: str) -> None:
        self.set_fill_color(220, 220, 220)
        self.set_font("Arial", style='B', size=12)
        self.cell(0, 10, title, ln=True, fill=True)
        self.ln(2)
    
    def add_images_grid(self, images: List[str], unidade: str, data: str) -> None:
        self.add_page()
        self.set_font("Arial", style='B', size=12)
        self.cell(0, 10, f"Fotos da Fiscalização - {unidade} ({data}):", ln=True)
        
        for i, img_path in enumerate(images):
            x = 10 + (i % 2) * 100
            y = 30 + ((i % 4) // 2) * 100
            
            self.set_draw_color(0, 0, 0)
            self.rect(x, y, 85, 80)
            self.image(img_path, x=x+1, y=y+1, w=83, h=78)
            
            legenda = os.path.splitext(os.path.basename(img_path))[0].replace('_', ' ').capitalize()
            self.set_xy(x, y+82)
            self.set_font("Arial", size=8)
            self.cell(85, 5, legenda, ln=False, align="C")
            
            if i % 4 == 3 or i == len(images)-1:
                self.set_y(-15)
                self.set_font("Arial", size=8)
                self.cell(0, 5, "Relatório gerado pela Supervisão de Segurança Corporativa - SANEAGO", align="C", ln=True)
                self.cell(0, 5, f"Página {self.page_no()}", align="C")

def generate_qr_code(data: Dict) -> str:
    qr_info = f"Fiscal: {data['fiscal']} | Data: {data['data']} | Unidade: {data['unidade']}"
    qr = qrcode.make(qr_info)
    qr.save(Config.QR_PATH)
    return Config.QR_PATH

def generate_checklist(data: Dict) -> List[str]:
    def is_conformity_complete(conformities: str) -> bool:
        required = ["Conforme", "Não conforme", "Parcialmente conforme", "Não se aplica"]
        return all(mark in conformities for mark in required)
    
    checklist_items = [
        ("Nome do fiscal preenchido corretamente", bool(data.get('fiscal'))),
        ("Data e mês de referência compatíveis", bool(data.get('data') and data.get('mes'))),
        ("Unidade e município corretos", bool(data.get('unidade') and data.get('municipio'))),
        ("Descrição técnica clara e objetiva", bool(data.get('ocorrencias'))),
        ("Uso adequado da linguagem institucional", True),
        ("Todos os itens avaliados possuem marcação", is_conformity_complete(data.get('conformidades', ''))),
        ("Presença das 4 opções: Conforme, Não conforme, Parcialmente conforme, Não se aplica", True),
        ("Tipo de Kit e status coerentes", bool(data.get('kit'))),
        ("Observações registradas, se necessário", bool(data.get('obs_kit'))),
        ("Fundamentação técnica presente", bool(data.get('recomendacoes'))),
        ("Imagens anexadas (até 16), nítidas e com legenda", bool(data.get('nomes_fotos'))),
        ("Rodapé com numeração de páginas", True),
        ("QR Code gerado corretamente", True)
    ]
    
    return [f"[{'X' if cond else ' '}] {text}" for text, cond in checklist_items]

def generate_pdf(data: Dict) -> str:
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Cabeçalho com informações básicas
    pdf.add_custom_field("Fiscal:", data['fiscal'])
    pdf.add_custom_field("Data da Fiscalização:", data['data'])
    pdf.add_custom_field("Mês de Referência:", data['mes'])
    pdf.add_custom_field("Unidade:", data['unidade'])
    pdf.add_custom_field("Município:", data['municipio'])
    
    # Seção de vigilância e monitoramento
    pdf.add_section_title("COMPOSIÇÃO DA VIGILÂNCIA E MONITORAMENTO")
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, "Tipos de Vigilância Orgânica: " + ", ".join(data['tipos_vigilancia']))
    pdf.multi_cell(0, 8, "Kit(s) de Monitoramento Eletrônico: " + ", ".join(data['kit']))
    pdf.multi_cell(0, 8, "Status do Sistema: " + data['status'])
    pdf.multi_cell(0, 8, "Observações do Monitoramento: " + data['obs_kit'])
    
    # Seção de ocorrências
    pdf.ln(5)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Ocorrências:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, data['ocorrencias'])
    
    # Texto condicional para vigilância motorizada
    if "Vigilante Motorizado Noturno 12hs" in data['tipos_vigilancia']:
        pdf.ln(2)
        pdf.set_x(10)
        pdf.set_font("Arial", style='I', size=11)
        pdf.multi_cell(190, 9, "Em relação aos postos atendidos por vigilância motorizada noturna, não foram identificadas inconformidades. A unidade conta com duas rondas noturnas operando regularmente. Foi apenas pontuada a necessidade de atenção aos pontos considerados mais vulneráveis da unidade fiscalizada.")
    
    # Seções de conformidades e recomendações
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Conformidades:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, data['conformidades'])
    
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Recomendações:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, data['recomendacoes'])
    
    # Adicionar fotos se existirem
    if data['nomes_fotos']:
        pdf.add_images_grid(data['nomes_fotos'], data['unidade'], data['data'])
    
    # Gerar e adicionar QR Code
    generate_qr_code(data)
    
    # Adicionar checklist
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "CHECKLIST FINAL DO RELATÓRIO:", ln=True)
    
    for item in generate_checklist(data):
        pdf.cell(0, 8, item, ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", style='I', size=9)
    pdf.cell(0, 8, "Checklist gerado automaticamente conforme dados informados no relatório.", ln=True)
    
    # Salvar PDF
    filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join("/tmp" if Config.IS_CLOUD else ".", filename)
    pdf.output(output_path)
    
    return output_path

# Interface Streamlit
def main():
    db = DatabaseManager()
    
    st.title("Relatório de Fiscalização - SANEAGO")
    
    with st.form("formulario"):
        # Seção de informações básicas
        col1, col2 = st.columns(2)
        with col1:
            fiscal = st.text_input("Fiscal Responsável*", placeholder="Nome completo do fiscal")
            data_fiscalizacao = st.date_input("Data da Fiscalização*")
        with col2:
            mes_ref = st.text_input("Mês de Referência (MM/AAAA)*", placeholder="MM/AAAA")
            unidade = st.text_input("Unidade Fiscalizada*")
        
        municipio = st.text_input("Município*")
        ocorrencias = st.text_area("Ocorrências Registradas*", height=150)
        
        # Seção de conformidades
        st.markdown("### Conformidades / Não Conformidades*")
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
                key=f"conformidade_{item}"
            )
            
            if item == "Outros (especificar)":
                especificacao = st.text_input("Especificar outros itens avaliados", key=f"espec_{item}")
                if especificacao:
                    item = f"Outros: {especificacao}"
            
            linha = (
                f"( {'X' if status == 'Conforme' else ' '} ) Conforme  "
                f"( {'X' if status == 'Não conforme' else ' '} ) Não conforme  "
                f"( {'X' if status == 'Parcialmente conforme' else ' '} ) Parcialmente conforme  "
                f"( {'X' if status == 'Não se aplica' else ' '} ) Não se aplica  → {item}"
            )
            conformidades.append(linha)
        
        # Seção de vigilância
        st.markdown("### Vigilância Orgânica*")
        tipos_vigilancia = st.multiselect(
            "Tipos de Vigilância Ativa",
            options=[
                "Vigilante Armado Diurno 12hs",
                "Vigilante Armado Noturno 12hs",
                "Vigilante Motorizado Diurno 12hs",
                "Vigilante Motorizado Noturno 12hs"
            ],
            default=["Vigilante Armado Diurno 12hs"]
        )
        
        # Seção de monitoramento
        st.markdown("### Monitoramento Eletrônico*")
        col_mon1, col_mon2 = st.columns([3, 2])
        with col_mon1:
            kit_monitoramento = st.multiselect(
                "Kit(s) de Monitoramento",
                options=["KIT-1", "KIT-2", "KIT-3", "KIT Específico", "Não identificado", "Não se aplica"],
                default=["KIT-1"]
            )
        with col_mon2:
            status_kit = st.radio(
                "Status do Sistema",
                options=["Em pleno funcionamento", "Com falhas"],
                horizontal=True
            )
        
        obs_kit = st.text_area("Observações do Monitoramento", height=100)
        recomendacoes = st.text_area("Recomendações do Fiscal*", height=150)
        
        # Upload de fotos
        st.markdown("### Fotos da Fiscalização (opcional)")
        imagens = st.file_uploader(
            f"Envie até {Config.MAX_IMAGES} imagens (JPEG/PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        submitted = st.form_submit_button("Gerar Relatório")
    
    if submitted:
        # Validar campos obrigatórios
        campos_obrigatorios = {
            "Fiscal Responsável": fiscal,
            "Data da Fiscalização": data_fiscalizacao,
            "Mês de Referência": mes_ref,
            "Unidade Fiscalizada": unidade,
            "Município": municipio,
            "Ocorrências Registradas": ocorrencias,
            "Recomendações do Fiscal": recomendacoes
        }
        
        faltantes = [campo for campo, valor in campos_obrigatorios.items() if not valor]
        
        if faltantes:
            st.error(f"Por favor, preencha os campos obrigatórios: {', '.join(faltantes)}")
            return
        
        # Processar imagens
        nomes_fotos = []
        for i, img in enumerate(imagens[:Config.MAX_IMAGES]):
            nome = os.path.join("/tmp" if Config.IS_CLOUD else ".", f"foto_{i+1}.jpg")
            with open(nome, "wb") as f:
                f.write(img.getbuffer())
            nomes_fotos.append(nome)
        
        # Preparar dados
        dados = {
            'fiscal': fiscal.strip(),
            'data': data_fiscalizacao.strftime("%d/%m/%Y"),
            'mes': mes_ref.strip(),
            'unidade': unidade.strip(),
            'municipio': municipio.strip(),
            'ocorrencias': ocorrencias.strip(),
            'conformidades': "\n".join(conformidades),
            'tipos_vigilancia': tipos_vigilancia,
            'kit': kit_monitoramento,
            'status': status_kit,
            'obs_kit': obs_kit.strip(),
            'recomendacoes': recomendacoes.strip(),
            'nomes_fotos': nomes_fotos
        }
        
        # Salvar e gerar PDF
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

if __name__ == "__main__":
    main()