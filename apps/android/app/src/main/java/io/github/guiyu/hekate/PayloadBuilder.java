package io.github.guiyu.hekate;
import java.io.ByteArrayOutputStream;

/** Same GPLv2 Fusée Launcher layout as apps/core.py. */
public final class PayloadBuilder {
    private static void zeros(ByteArrayOutputStream out,int n) { for(int i=0;i<n;i++)out.write(0); }
    private static void u32(ByteArrayOutputStream out,int n) { for(int i=0;i<4;i++)out.write((n>>>(i*8))&255); }
    public static byte[] build(byte[] payload,byte[] relocator) {
        if(payload.length==0||relocator.length==0||relocator.length>0xe40||payload.length>0x30298)
            throw new IllegalArgumentException("载荷大小无效");
        ByteArrayOutputStream out=new ByteArrayOutputStream();u32(out,0x30298);zeros(out,676);
        out.write(relocator,0,relocator.length);zeros(out,0xe40-relocator.length);
        int first=Math.min(payload.length,0x4000);out.write(payload,0,first);zeros(out,0x4000-first);
        for(int i=0;i<0x21c0/4;i++)u32(out,0x40010000);
        if(payload.length>0x4000)out.write(payload,0x4000,payload.length-0x4000);
        zeros(out,4096-out.size()%4096);
        if(out.size()>0x30298)throw new IllegalArgumentException("载荷过大，拒绝发送");
        return out.toByteArray();
    }
}
