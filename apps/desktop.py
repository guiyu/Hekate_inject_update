"""Chinese graphical desktop app; USB work never runs on Tk's main thread."""
import argparse
import json
import platform
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
from apps.core import VERSION, HEKATE_VERSION, verified_resources, inject
from apps.transports import open_backend, load_windows_library

def runtime_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'resources'

class App:
    def __init__(self, window, resources=None):
        self.window=window; self.resources=resources or runtime_root()
        self.events=queue.Queue();self.busy=False;self.close_requested=False;self.detected=False
        window.title('Hekate Injector · Switch 注入');window.geometry('680x570');window.minsize(600,520)
        bg='#101827';fg='#eef4fc';muted='#a6b5ca';accent='#48e1c2'
        window.configure(bg=bg)
        outer=tk.Frame(window,bg=bg,padx=30,pady=24);outer.pack(fill='both',expand=True)
        self.icon=tk.PhotoImage(file=str(self.resources/'icon.png'))
        window.iconphoto(True,self.icon)
        header=tk.Frame(outer,bg=bg);header.pack(fill='x')
        tk.Label(header,image=self.icon,bg=bg).pack(side='left',padx=(0,16))
        title=tk.Frame(header,bg=bg);title.pack(side='left')
        tk.Label(title,text='Hekate Injector',font=('',24,'bold'),fg=fg,bg=bg).pack(anchor='w')
        tk.Label(title,text=f'Switch RCM 注入  ·  v{VERSION}',font=('',12),fg=muted,bg=bg).pack(anchor='w',pady=(6,0))
        tk.Label(outer,text=f'内置 Hekate {HEKATE_VERSION}  ·  离线运行  ·  发送前校验文件',fg=muted,bg=bg,font=('',12)).pack(anchor='w',pady=(24,12))
        self.status=tk.StringVar(value='请将 Switch 置于 RCM，并通过数据线连接')
        tk.Label(outer,textvariable=self.status,wraplength=590,justify='left',fg=accent,bg='#19283a',padx=16,pady=16,font=('',13)).pack(fill='x')
        buttons=tk.Frame(outer,bg=bg);buttons.pack(fill='x',pady=18)
        self.check=tk.Button(buttons,text='检测设备',command=lambda:self.start(False),font=('',13),padx=18,pady=8)
        self.check.pack(side='left',padx=(0,12))
        self.send=tk.Button(buttons,text='注入 Hekate',command=lambda:self.start(True),state='disabled',font=('',13,'bold'),padx=18,pady=8)
        self.send.pack(side='left')
        self.output=scrolledtext.ScrolledText(outer,height=9,bg='#0b111c',fg='#d0dceb',insertbackground=fg,font=('Menlo' if platform.system()=='Darwin' else 'Consolas',11),relief='flat',padx=12,pady=10,state='disabled')
        self.output.pack(fill='both',expand=True)
        tk.Label(outer,text='仅支持可利用 RCM 漏洞的 Switch 1。发送结束后，请在主机屏幕确认启动。',fg=muted,bg=bg,font=('',11),wraplength=600,justify='left').pack(anchor='w',pady=(14,0))
        if platform.system()=='Windows':self.log('Windows：APX 0955:7321 需要 libusbK 驱动。请勿替换其他设备驱动。')
        self.log('将 Switch 完全关机并进入 RCM；RCM 通常保持黑屏。')
        window.protocol('WM_DELETE_WINDOW',self.close);window.after(100,self.drain)
    def log(self,line):
        self.output.configure(state='normal');self.output.insert('end',line+'\n');self.output.see('end');self.output.configure(state='disabled')
    def start(self,send):
        if self.busy:return
        self.busy=True;self.check.configure(state='disabled');self.send.configure(state='disabled')
        self.status.set('正在校验文件并检测 USB…')
        def work():
            backend=None
            try:
                payload,relocator=verified_resources(self.resources)
                backend=open_backend(self.resources)
                if send:
                    owned=backend;backend=None
                    result=inject(owned,payload,relocator,lambda s:self.events.put(('log',s)))
                    self.events.put(('sent',result.message))
                else:self.events.put(('detected','已检测到 APX 0955:7321，可点击“注入 Hekate”'))
            except Exception as exc:self.events.put(('error',str(exc)))
            finally:
                if backend is not None:
                    try:backend.close()
                    except Exception:pass
                self.events.put(('done',''))
        threading.Thread(target=work,daemon=False).start()
    def drain(self):
        try:
            while True:
                kind,msg=self.events.get_nowait()
                if kind=='log':self.log(msg)
                elif kind=='done':
                    self.busy=False
                    if self.close_requested:self.window.destroy();return
                    self.check.configure(state='normal');self.send.configure(state='normal' if self.detected else 'disabled')
                else:
                    self.detected=kind=='detected';self.status.set(msg);self.log(msg)
        except queue.Empty:pass
        self.window.after(100,self.drain)
    def close(self):
        if self.busy:
            self.close_requested=True
            if hasattr(self,'status'):self.status.set('正在等待 USB 操作结束，随后关闭…')
        else:self.window.destroy()

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--smoke-ui',action='store_true');p.add_argument('--report')
    args=p.parse_args();resources=runtime_root()
    if args.self_test:
        payload,relocator=verified_resources(resources)
        if platform.system()=='Windows':load_windows_library(resources)
        else:
            import libusb_package
            if libusb_package.get_libusb1_backend() is None:raise RuntimeError('libusb missing')
        result={'version':VERSION,'platform':platform.system(),'resources':'verified','payload_bytes':len(payload),'relocator_bytes':len(relocator),'usb_accessed':False}
        if args.report:Path(args.report).write_text(json.dumps(result),encoding='utf-8')
        if sys.stdout is not None:print(json.dumps(result))
        return
    w=tk.Tk();App(w,resources)
    if args.smoke_ui:
        def finish():
            if args.report:Path(args.report).write_text(json.dumps({'ui':'opened','usb_accessed':False}),encoding='utf-8')
            w.destroy()
        w.after(1800,finish)
    w.mainloop()

if __name__=='__main__':main()
