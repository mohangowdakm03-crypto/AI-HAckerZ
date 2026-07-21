import os
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

content = """
SAFETY COMPLIANCE MANUAL v1.2

1.0 OVERVIEW
This document outlines the safety compliance standards for the new chemical mixing plant.
All procedures are GOVERNED_BY the OSHA-COMPLIANCE-STANDARD.

2.0 CHEMICAL MIXER OPERATION
The PRIMARY-MIXER is CONNECTED_TO the STORAGE-TANK-B. 
Before operating the PRIMARY-MIXER, the operator must execute the SAFETY-LOCKOUT-PROCEDURE.

3.0 HAZARD AWARENESS
Failure to execute the SAFETY-LOCKOUT-PROCEDURE CAUSES a severe CHEMICAL-SPILL-HAZARD.
If the CHEMICAL-SPILL-HAZARD occurs, it disrupts the entire PLANT-OPERATIONS.
"""

for line in content.split('\n'):
    pdf.cell(0, 8, text=line.strip(), new_x="LMARGIN", new_y="NEXT")

pdf.output("sample_data/safety_manual.pdf")
print("PDF created successfully!")
