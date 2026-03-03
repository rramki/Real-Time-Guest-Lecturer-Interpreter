from fpdf import FPDF

def generate_pdf(text, filename="translated_output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for line in text.split('\n'):
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)
    return filename
