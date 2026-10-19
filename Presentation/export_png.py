import os, sys, glob
import win32com.client as win32

pptx = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                       r"G:\My Drive\JOM\AI Dashboard\Presentation\EPS_Dashboard_Data_and_Presentation_TH.pptx")
outdir = os.path.join(os.path.dirname(pptx), "render")
os.makedirs(outdir, exist_ok=True)
for f in glob.glob(os.path.join(outdir, "*.png")):
    os.remove(f)

app = win32.DispatchEx("PowerPoint.Application")
pres = app.Presentations.Open(pptx, ReadOnly=True, WithWindow=False)
print("slides:", pres.Slides.Count, "size:", pres.PageSetup.SlideWidth, "x", pres.PageSetup.SlideHeight)
for i in range(1, pres.Slides.Count + 1):
    p = os.path.join(outdir, "slide%02d.png" % i)
    pres.Slides(i).Export(p, "PNG", 1600, 900)
    print("ok", p, os.path.getsize(p))
pres.Close()
app.Quit()
