/* GPL-2.0: async usbfs RCM trigger. Own the URB until reap or fd close. */
#include <errno.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>
#include <linux/usbdevice_fs.h>
#ifndef UNIT_TEST
#include <jni.h>
#endif
#ifndef USB_IOCTL
#define USB_IOCTL ioctl
#endif
static struct usbdevfs_urb *pending;
static int64_t millis(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000+t.tv_nsec/1000000;}
static void release_after_close(void){if(pending){free(pending->buffer);free(pending);pending=NULL;}}
static int trigger_request(int fd,int length){
    if(pending||length!=0x7000)return -EINVAL;
    struct usbdevfs_urb *urb=calloc(1,sizeof(*urb));
    if(!urb)return -ENOMEM;
    unsigned char *b=calloc(1,8+length);if(!b){free(urb);return -ENOMEM;}
    b[0]=0x82;b[1]=0;b[6]=length&255;b[7]=(length>>8)&255;
    urb->type=USBDEVFS_URB_TYPE_CONTROL;urb->endpoint=0;urb->buffer=b;urb->buffer_length=8+length;
    if(USB_IOCTL(fd,USBDEVFS_SUBMITURB,urb)<0){int e=errno;free(b);free(urb);return -e;}
    pending=urb;int64_t deadline=millis()+1800;int cancelled=0;
    for(;;){
        struct usbdevfs_urb *done=NULL;
        if(USB_IOCTL(fd,USBDEVFS_REAPURBNDELAY,&done)==0){
            if(done!=urb)return -EPROTO; // caller closes fd before cleanup
            int status=urb->status;release_after_close();
            if(status==0)return 0;
            if(status==-ENODEV||status==-ESHUTDOWN||status==-EPROTO||status==-EILSEQ)return 1;
            if(cancelled&&(status==-ENOENT||status==-ECONNRESET))return 2;
            return status<0?status:-EIO;
        }
        int e=errno;
        if(e!=EAGAIN&&e!=EINTR){return e==ENODEV?1:-e;}
        if(millis()>=deadline){
            if(cancelled)return 2; // close cancels; pending buffer stays allocated
            if(USB_IOCTL(fd,USBDEVFS_DISCARDURB,urb)<0&&errno!=EINVAL&&errno!=ENODEV)return -errno;
            cancelled=1;deadline=millis()+500;
        }
        usleep(1000);
    }
}
#ifndef UNIT_TEST
JNIEXPORT jint JNICALL Java_io_github_guiyu_hekate_MainActivity_triggerRequest(JNIEnv *env,jclass c,jint fd,jint length){return trigger_request(fd,length);}
JNIEXPORT void JNICALL Java_io_github_guiyu_hekate_MainActivity_releaseAfterClose(JNIEnv *env,jclass c){release_after_close();}
#endif
