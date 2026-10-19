import os, sys
import win32com.client as win32

pptx = os.path.abspath(r"G:\My Drive\JOM\AI Dashboard\Presentation\EPS_Dashboard_Data_and_Presentation_TH.pptx")
pdf = os.path.join(os.path.dirname(pptx), "EPS_Dashboard_Data_and_Presentation_TH.pdf")
app = win32.DispatchEx("PowerPoint.Application")
pres = app.Presentations.Open(pptx, ReadOnly=True, WithWindow=False)
pres.SaveAs(pdf, 32)  # ppSaveAsPDF
pres.Close()
app.Quit()
print("pdf:", pdf, os.path.getsize(pdf), "bytes")
