# módulo de geração de relatórios PDF com numeração persistente

from fpdf import FPDF
import os
from datetime import datetime
import qrcode
import sqlite3

class PDFComRodape(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=8)
        self.cell(0, 5, "Relatório técnico gerado pela Supervisão de Segurança Corporativa - SANEAGO", 0, 1, "C")
        self.cell(0, 5, f"Página {self.page_no()}", 0, 0, "C")

# Consulta o último número de relatório gerado
def consultar_ultimo_numero():
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("SELECT ultimo_numero FROM controle_relatorio WHERE id = 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

# Reinicia a contagem de relatórios
def reiniciar_numeracao():
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("UPDATE controle_relatorio SET ultimo_numero = 0 WHERE id = 1")
    conn.commit()
    conn.close()

# Atualiza o número sequencial do relatório
def obter_numero_relatorio():
    conn = sqlite3.connect("relatorios.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS controle_relatorio (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            ultimo_numero INTEGER
        )
    """)
    c.execute("SELECT ultimo_numero FROM controle_relatorio WHERE id = 1")
    row = c.fetchone()
    if row:
        numero = row[0] + 1
        c.execute("UPDATE controle_relatorio SET ultimo_numero = ? WHERE id = 1", (numero,))
    else:
        numero = 1
        c.execute("INSERT INTO controle_relatorio (id, ultimo_numero) VALUES (1, ?)", (numero,))
    conn.commit()
    conn.close()
    return numero

def gerar_pdf(dados):
    relatorio_numero = obter_numero_relatorio()
    pdf = PDFComRodape()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, txt=f"Nº do Relatório: {relatorio_numero:04d}", ln=True, align="R")
    pdf.ln(2)
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

    pdf.set_font("Arial", style='B', size=12)
    pdf.multi_cell(0, 8, "Unidade: " + dados['unidade'])
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, "Município: " + dados['municipio'])

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
                pdf.multi_cell(0, 8, txt=f"Fotos da Fiscalização - {dados['unidade']} ({dados['data']}):")

            x = 10 + (i % 2) * 100
            y = 30 + ((i % 4) // 2) * 100

            pdf.set_draw_color(0, 0, 0)
            pdf.rect(x, y, 85, 80)
            pdf.image(nome, x=x + 1, y=y + 1, w=83, h=78)

            legenda = os.path.splitext(os.path.basename(nome))[0].replace('_', ' ').capitalize()
            pdf.set_xy(x, y + 82)
            pdf.set_font("Arial", size=8)
            pdf.cell(85, 5, txt=legenda, ln=False, align="C")

    qr_info = f"Fiscal: {dados['fiscal']} | Data: {dados['data']} | Unidade: {dados['unidade']}"
    qr = qrcode.make(qr_info)
    qr_path = "/tmp/qrcode.png" if os.getenv("HOME") == "/home/appuser" else "qrcode.png"
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

    caminho = f"/tmp/relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" if os.getenv("HOME") == "/home/appuser" else f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(caminho)
    return caminho
