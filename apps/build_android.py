"""Build and sign an APK with the installed official Android SDK/NDK, no Gradle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import subprocess
import sys
import zipfile
from apps.make_icons import make as make_icons
from apps.prepare_app_resources import make as make_resources
ROOT=Path(__file__).resolve().parents[1]

def run(args,**kw):subprocess.run([str(x) for x in args],check=True,**kw)
def main():
    p=argparse.ArgumentParser();p.add_argument('--sdk');p.add_argument('--ndk');args=p.parse_args()
    sdk=Path(args.sdk or os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or Path.home()/'Library/Android/sdk')
    ndk=Path(args.ndk or os.environ.get('ANDROID_NDK_HOME') or ROOT/'build/android-sdk/ndk/27.2.12479018')
    tools=sdk/'build-tools/35.0.0';jar=sdk/'platforms/android-35/android.jar'
    suffix='.exe' if platform.system()=='Windows' else ''
    if not jar.is_file() or not ndk.is_dir():raise SystemExit('Require SDK API 35, build-tools 35.0.0 and NDK 27.2.12479018')
    make_icons();resources=make_resources(False)
    source=ROOT/'apps/android/app/src/main';build=ROOT/'build/android';build.mkdir(parents=True,exist_ok=True)
    (ROOT/'dist').mkdir(exist_ok=True)
    run([tools/('aapt2'+suffix),'compile','--dir',source/'res','-o',build/'resources.zip'])
    base=build/'base.apk'
    run([tools/('aapt2'+suffix),'link','-I',jar,'--manifest',source/'AndroidManifest.xml','-o',base,build/'resources.zip'])
    classes=build/'classes';classes.mkdir(exist_ok=True)
    java=sorted((source/'java').rglob('*.java'))
    run(['javac','-encoding','UTF-8','-source','8','-target','8','-classpath',jar,'-d',classes,*java])
    dex=build/'dex';dex.mkdir(exist_ok=True)
    d8=tools/('d8.bat' if platform.system()=='Windows' else 'd8')
    run([d8,'--min-api','26','--lib',jar,'--output',dex,*sorted(classes.rglob('*.class'))])
    host={'Darwin':'darwin-x86_64','Linux':'linux-x86_64','Windows':'windows-x86_64'}[platform.system()]
    clang=ndk/'toolchains/llvm/prebuilt'/host/'bin'/('clang'+suffix)
    abis={'arm64-v8a':'aarch64-linux-android26','armeabi-v7a':'armv7a-linux-androideabi26','x86_64':'x86_64-linux-android26'}
    libs=[]
    for abi,target in abis.items():
        out=build/abi/'librcmtrigger.so';out.parent.mkdir(exist_ok=True)
        run([clang,f'--target={target}','-std=c11','-D_DEFAULT_SOURCE','-shared','-fPIC','-O2','-Wall','-Werror','-Wno-unused-parameter','-Wl,-z,max-page-size=16384','-Wl,-z,common-page-size=16384','-o',out,source/'cpp/trigger.c'])
        libs.append((abi,out))
    with zipfile.ZipFile(base,'a',compression=zipfile.ZIP_DEFLATED) as z:
        z.write(dex/'classes.dex','classes.dex')
        for abi,out in libs:z.write(out,f'lib/{abi}/librcmtrigger.so',compress_type=zipfile.ZIP_STORED)
        for name in ('payload.bin','intermezzo.bin'):z.write(resources/name,'assets/'+name)
        for f in (resources/'licenses').iterdir():z.write(f,'assets/licenses/'+f.name)
    aligned=build/'aligned.apk';run([tools/('zipalign'+suffix),'-P','16','-f','4',base,aligned])
    signing=ROOT/'build/signing';signing.mkdir(exist_ok=True)
    keystore=signing/'release.jks';password_file=signing/'password.txt'
    if not keystore.exists():
        password_file.write_text(secrets.token_urlsafe(32));password_file.chmod(0o600)
    password=password_file.read_text().strip();env=dict(os.environ,INJECTOR_KEY_PASSWORD=password)
    if not keystore.exists():
        run(['keytool','-genkeypair','-keystore',keystore,'-storetype','JKS','-alias','injector','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=Hekate Injector Community Build','-storepass:env','INJECTOR_KEY_PASSWORD','-keypass:env','INJECTOR_KEY_PASSWORD'],env=env)
        keystore.chmod(0o600)
    apk=ROOT/'dist/Hekate-Injector-Android.apk'
    signer=tools/('apksigner.bat' if platform.system()=='Windows' else 'apksigner')
    run([signer,'sign','--ks',keystore,'--ks-key-alias','injector','--ks-pass','env:INJECTOR_KEY_PASSWORD','--key-pass','env:INJECTOR_KEY_PASSWORD','--out',apk,aligned],env=env)
    run([signer,'verify','--verbose','--print-certs',apk])
    run([tools/('zipalign'+suffix),'-c','-P','16','4',apk])
    manifest=subprocess.check_output([str(tools/('aapt2'+suffix)),'dump','badging',str(apk)],text=True)
    (build/'badging.txt').write_text(manifest)
    if 'uses-permission:' in manifest:raise RuntimeError('Unexpected Android permission')
    with zipfile.ZipFile(apk) as z:
        for n in ('payload.bin','intermezzo.bin'):
            if z.read('assets/'+n)!=(resources/n).read_bytes():raise RuntimeError('APK payload mismatch')
    print('Signed APK verified:',hashlib.sha256(apk.read_bytes()).hexdigest())
if __name__=='__main__':main()
