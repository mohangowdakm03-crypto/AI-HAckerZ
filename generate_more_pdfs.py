import os
from fpdf import FPDF

def create_pdf(filename, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in content.strip().split('\n'):
        pdf.cell(0, 8, text=line.strip(), new_x="LMARGIN", new_y="NEXT")
    pdf.output(f"sample_data/{filename}")

pdf1 = """
EMERGENCY PROTOCOL EP-001

1.0 PURPOSE
This protocol outlines the EMERGENCY-SHUTDOWN-PROCEDURE for the main facility.

2.0 EXECUTION
When the FIRE-ALARM is triggered, it indicates a FIRE-HAZARD. 
Operators must immediately execute the EMERGENCY-SHUTDOWN-PROCEDURE.
This procedure isolates the GAS-PIPELINE and shuts off the MAIN-VALVE.
Failure to do so CAUSES a severe EXPLOSION-HAZARD.
"""

pdf2 = """
MAINTENANCE SCHEDULE 2027

The HVAC-SYSTEM requires bi-annual maintenance.
The HVAC-SYSTEM is CONNECTED_TO the EXHAUST-FAN-01.
Maintenance must follow the HVAC-INSPECTION-PROCEDURE.
If the HVAC-INSPECTION-PROCEDURE is skipped, it leads to a POOR-VENTILATION-HAZARD, 
which violates the OSHA-AIR-QUALITY-STANDARD.
"""

create_pdf("emergency_protocol.pdf", pdf1)
create_pdf("maintenance_schedule.pdf", pdf2)
print("PDFs generated!")
