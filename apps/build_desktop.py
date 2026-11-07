"""Run on the target OS: python -m apps.build_desktop."""
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from apps.make_icons import make as icons
from apps.prepare_app_resources import make as resources
ROOT=Path(__file__).resolve().parents[1]

def main():
    system=platform.system()
    if system not in ('Darwin','Windows'):raise SystemExit('Build on macOS or Windows')
    icons();resources()
    ext='icns' if system=='Darwin' else 'ico'
    args=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir',
        '--name','Hekate Injector','--paths',str(ROOT),'--icon',str(ROOT/f'apps/icons/icon.{ext}'),
        '--add-data',str(ROOT/'apps/resources')+':resources','--collect-all','libusb_package',
        '--hidden-import','usb.backend.libusb1','--hidden-import','usb.core','--hidden-import','tkinter',
        '--hidden-import','apps.transports','--osx-bundle-identifier','io.github.guiyu.hekateinjector',str(ROOT/'apps/desktop.py')]
    if system=='Windows':
        index=args.index('--osx-bundle-identifier');del args[index:index+2]
        args += ['--add-binary',str(ROOT/'apps/resources/libusbK.dll')+':resources']
    subprocess.run(args,cwd=ROOT,check=True)
    if system=='Darwin':
        app=ROOT/'dist/Hekate Injector.app'
        subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
        exe=app/'Contents/MacOS/Hekate Injector'
        subprocess.run([str(exe),'--self-test','--report',str(ROOT/'build/desktop-self-test.json')],check=True)
        subprocess.run([str(exe),'--smoke-ui','--report',str(ROOT/'build/desktop-ui-test.json')],check=True)
        subprocess.run(['ditto','-c','-k','--keepParent',str(app),str(ROOT/'dist/Hekate-Injector-macOS-Intel.zip')],check=True)
    else:
        exe=ROOT/'dist/Hekate Injector/Hekate Injector.exe'
        subprocess.run([str(exe),'--self-test','--report',str(ROOT/'build/desktop-self-test.json')],check=True)
        subprocess.run([str(exe),'--smoke-ui','--report',str(ROOT/'build/desktop-ui-test.json')],check=True)
        shutil.make_archive(str(ROOT/'dist/Hekate-Injector-Windows-x64'),'zip',ROOT/'dist','Hekate Injector')
    print('Standalone desktop build verified.')
if __name__=='__main__':main()
