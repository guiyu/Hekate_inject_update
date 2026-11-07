"""Generate original geometric cable/power icon; no third-party artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent

def make():
    target=ROOT/'icons';target.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGBA',(1024,1024),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,1023,1023),radius=220,fill='#101827')
    d.rounded_rectangle((200,180,824,640),radius=98,fill='#1b3046',outline='#48e1c2',width=22)
    d.arc((365,295,660,590),-55,235,fill='#48e1c2',width=36)
    d.line((512,264,512,408),fill='#eef4fc',width=36)
    d.rounded_rectangle((444,626,580,744),radius=24,fill='#48e1c2')
    d.line((512,730,512,835),fill='#48e1c2',width=32)
    d.line((512,835,685,835),fill='#48e1c2',width=32)
    d.ellipse((663,812,709,858),fill='#eef4fc')
    im.save(target/'icon.png')
    im.save(target/'icon.ico',sizes=[(s,s) for s in (16,24,32,48,64,128,256)])
    im.save(target/'icon.icns')
    im.resize((64,64),Image.Resampling.LANCZOS).save(target/'ui.png')
    android=ROOT/'android/app/src/main/res'
    for folder,size in [('mipmap-mdpi',48),('mipmap-hdpi',72),('mipmap-xhdpi',96),('mipmap-xxhdpi',144),('mipmap-xxxhdpi',192)]:
        p=android/folder;p.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(p/'ic_launcher.png')
    return target
if __name__=='__main__':make()
