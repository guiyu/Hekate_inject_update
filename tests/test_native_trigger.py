from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('clang') or shutil.which('cc'),'C compiler required')
class NativeLifetime(unittest.TestCase):
    def test_submit_fail_completion_disconnect_and_timeout_lifetimes(self):
        # Uses NDK Linux headers when host is macOS; native Android tests are
        # compiled by the NDK build separately. Linux CI executes this harness.
        import sys
        if sys.platform!='linux':self.skipTest('Linux usbfs headers required')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);src=ROOT/'apps/android/app/src/main/cpp/trigger.c'
            (p/'h.c').write_text('''#include <assert.h>
#include <errno.h>
#include <time.h>
#include <linux/usbdevice_fs.h>
static int mode=0,ticks=0;
static int fake_clock(clockid_t c,struct timespec *t){t->tv_sec=++ticks;t->tv_nsec=0;return 0;}
static int fake_ioctl(int fd,unsigned long req,void *arg);
#define UNIT_TEST
#define USB_IOCTL fake_ioctl
#define clock_gettime fake_clock
#include "'''+str(src)+'''"
static int fake_ioctl(int fd,unsigned long req,void *arg){
 if(req==USBDEVFS_SUBMITURB){if(mode==0){errno=EACCES;return -1;}return 0;}
 if(req==USBDEVFS_DISCARDURB)return 0;
 if(mode==2){errno=ENODEV;return -1;}
 if(mode==4){errno=EAGAIN;return -1;}
 *(struct usbdevfs_urb**)arg=pending;pending->status=mode==3?-EINVAL:0;return 0;
}
int main(){
 assert(trigger_request(-1,42)==-EINVAL);assert(pending==0);
 assert(trigger_request(-1,0x7000)==-EACCES);assert(pending==0);
 mode=1;assert(trigger_request(1,0x7000)==0);assert(pending==0);
 mode=2;assert(trigger_request(1,0x7000)==1);assert(pending!=0);release_after_close();assert(pending==0);
 mode=3;assert(trigger_request(1,0x7000)==-EINVAL);assert(pending==0);
 mode=4;assert(trigger_request(1,0x7000)==2);assert(pending!=0);release_after_close();assert(pending==0);
 return 0;}
''')
            cc=shutil.which('clang') or shutil.which('cc')
            subprocess.run([cc,'-D_DEFAULT_SOURCE','-fsanitize=address,undefined','-g',str(p/'h.c'),'-o',str(p/'h')],check=True,capture_output=True)
            subprocess.run([str(p/'h')],check=True,capture_output=True)
