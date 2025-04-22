
from fpdf import FPDF
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'PRIME CVD Risk Assessment Report', 0, 1, 'C')

def create_pdf_report(patient_data, risk_data, ldl_history):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PRIME CVD Risk Assessment', 0, 1, 'C')
    return pdf.output(dest='S').encode('latin1')
