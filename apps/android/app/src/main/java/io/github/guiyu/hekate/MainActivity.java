package io.github.guiyu.hekate;
import android.app.*;
import android.content.*;
import android.hardware.usb.*;
import android.os.*;
import android.graphics.Color;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.Arrays;

public final class MainActivity extends Activity {
    static { System.loadLibrary("rcmtrigger"); }
    private static final Object USB_LOCK=new Object();
    private static final String PERMISSION="io.github.guiyu.hekate.USB_PERMISSION";
    private static native int triggerRequest(int fd,int length);
    private static native void releaseAfterClose();
    private UsbManager manager;
    private UsbDevice selected;
    private volatile UsbDeviceConnection active;
    private volatile boolean destroyed=false;
    private boolean busy=false,workerRunning=false;
    private TextView status,log;
    private Button detect,send;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final BroadcastReceiver receiver=new BroadcastReceiver() {
        @Override public void onReceive(Context c,Intent i) {
            if(PERMISSION.equals(i.getAction())) {
                UsbDevice granted=i.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                if(!busy||workerRunning||destroyed)return;
                if(i.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED,false)&&granted!=null&&selected!=null&&granted.getDeviceId()==selected.getDeviceId())runInjection(granted);
                else {message("USB 权限未授予，未发送载荷");setBusy(false);}
            } else if(UsbManager.ACTION_USB_DEVICE_DETACHED.equals(i.getAction())) {
                UsbDevice removed=i.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                if(removed!=null&&selected!=null&&removed.getDeviceId()==selected.getDeviceId()) {
                    selected=null;
                    if(!workerRunning) {message("USB 已断开，请重新检测设备");setBusy(false);}
                }
            }
        }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);manager=(UsbManager)getSystemService(USB_SERVICE);
        getWindow().setStatusBarColor(Color.rgb(16,24,39));getWindow().setNavigationBarColor(Color.rgb(16,24,39));
        LinearLayout column=new LinearLayout(this);column.setOrientation(LinearLayout.VERTICAL);column.setPadding(dp(24),dp(32),dp(24),dp(20));column.setBackgroundColor(Color.rgb(16,24,39));
        TextView heading=label("Hekate Injector",28,Color.WHITE);heading.setTypeface(null,1);column.addView(heading);
        column.addView(label("Switch RCM 注入 · v1.0.0",14,Color.rgb(166,181,202)));
        TextView intro=label("内置 Hekate 6.5.4\n连接 USB OTG 数据线后，先检测设备。",16,Color.rgb(166,181,202));intro.setPadding(0,dp(24),0,dp(20));column.addView(intro);
        status=label("等待检测 APX / RCM",17,Color.rgb(72,225,194));column.addView(status);
        LinearLayout row=new LinearLayout(this);row.setPadding(0,dp(16),0,dp(12));
        detect=new Button(this);detect.setText("检测设备");detect.setOnClickListener(v->detect());row.addView(detect,new LinearLayout.LayoutParams(0,dp(56),1));
        send=new Button(this);send.setText("注入 Hekate");send.setEnabled(false);send.setOnClickListener(v->authorize());row.addView(send,new LinearLayout.LayoutParams(0,dp(56),1));column.addView(row);
        ScrollView scroll=new ScrollView(this);log=label("仅支持可利用 RCM 漏洞的 Switch 1。\nRCM 通常保持黑屏。\n",13,Color.rgb(208,220,235));log.setTextIsSelectable(true);scroll.addView(log);column.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        column.addView(label("载荷发送不等于系统已启动，请在 Switch 屏幕验收。",12,Color.rgb(166,181,202)));setContentView(column);
        IntentFilter filter=new IntentFilter(PERMISSION);filter.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        if(Build.VERSION.SDK_INT>=33)registerReceiver(receiver,filter,Context.RECEIVER_NOT_EXPORTED);else registerReceiver(receiver,filter);
    }
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+0.5f);}
    private TextView label(String s,int size,int color){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);return t;}
    private void message(String s){if(destroyed)return;status.setText(s);log.append(s+"\n");}
    private void setBusy(boolean b){busy=b;detect.setEnabled(!b);send.setEnabled(!b&&selected!=null);}
    private void detect(){
        if(busy)return;selected=null;
        for(UsbDevice d:manager.getDeviceList().values())if(d.getVendorId()==0x0955&&d.getProductId()==0x7321){selected=d;break;}
        message(selected==null?"未检测到 APX；检查 RCM、OTG 和数据线":"已检测到 APX 0955:7321，可点击注入");setBusy(false);
    }
    private void authorize(){
        if(busy||selected==null)return;setBusy(true);
        if(manager.hasPermission(selected))runInjection(selected);
        else {
            message("请在系统对话框中允许 USB 访问");
            int flags=PendingIntent.FLAG_UPDATE_CURRENT|(Build.VERSION.SDK_INT>=31?PendingIntent.FLAG_MUTABLE:0);
            PendingIntent p=PendingIntent.getBroadcast(this,0,new Intent(PERMISSION).setPackage(getPackageName()),flags);
            try{manager.requestPermission(selected,p);}catch(Exception e){message("无法申请 USB 权限："+e.getMessage());setBusy(false);}
        }
    }
    private byte[] asset(String name,String sha)throws Exception {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        try(InputStream in=getAssets().open(name)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
        byte[] bytes=out.toByteArray();StringBuilder hex=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))hex.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        if(!hex.toString().equals(sha))throw new IOException("文件校验失败："+name);return bytes;
    }
    private void runInjection(UsbDevice device){
        workerRunning=true;message("校验文件并准备 USB…");
        new Thread(()->{
            String result;
            synchronized(USB_LOCK){
                UsbDeviceConnection connection=null;UsbInterface intf=null;
                try{
                    if(destroyed)throw new IOException("应用已关闭，已取消");
                    byte[] payload=asset("payload.bin","95f6e933e32e028f3ae90f0b0857ff47800e834bdace38a0ab019d8ed35a8c24");
                    byte[] relocator=asset("intermezzo.bin","8517c0cb36ecb0b53129ae15269cf7f28a4f48ea599e8b6fc4cb8ead96ea3dfa");
                    byte[] image=PayloadBuilder.build(payload,relocator);
                    connection=manager.openDevice(device);if(connection==null)throw new IOException("无法打开设备，检查 USB 授权");active=connection;
                    UsbEndpoint input=null,output=null;
                    for(int j=0;j<device.getInterfaceCount();j++){
                        UsbInterface candidate=device.getInterface(j);UsbEndpoint ci=null,co=null;
                        for(int k=0;k<candidate.getEndpointCount();k++){
                            UsbEndpoint e=candidate.getEndpoint(k);
                            if(e.getType()==UsbConstants.USB_ENDPOINT_XFER_BULK){if(e.getAddress()==0x81)ci=e;if(e.getAddress()==0x01)co=e;}
                        }
                        if(ci!=null&&co!=null){intf=candidate;input=ci;output=co;break;}
                    }
                    if(intf==null||!connection.claimInterface(intf,true))throw new IOException("无法占用 RCM USB 接口");
                    byte[] id=new byte[16];if(connection.bulkTransfer(input,id,16,1500)!=16)throw new IOException("RCM 握手不完整，已停止");
                    main.post(()->message("正在发送 Hekate 6.5.4…"));int packets=0;
                    for(int off=0;off<image.length;off+=4096){
                        if(destroyed)throw new IOException("应用已关闭，已停止");
                        byte[] chunk=Arrays.copyOfRange(image,off,off+4096);
                        if(connection.bulkTransfer(output,chunk,4096,1500)!=4096)throw new IOException("USB 写入不完整；请重新进入 RCM");packets++;
                    }
                    if(packets%2==0&&connection.bulkTransfer(output,new byte[4096],4096,1500)!=4096)throw new IOException("USB 缓冲切换失败");
                    if(destroyed)throw new IOException("应用已关闭，未触发");
                    int code=triggerRequest(connection.getFileDescriptor(),0x7000);
                    if(code<0)throw new IOException("底层 USB 触发失败，错误 "+code+"；手机 USB 栈可能不支持此请求");
                    result=code==0?"触发请求已返回；请查看 Switch 屏幕确认启动":"触发后 USB 断开或超时（"+code+"）；启动结果未确认，请查看 Switch 屏幕";
                }catch(Exception e){result="已停止："+e.getMessage();}
                finally{
                    // Closing usbfs cancels outstanding URBs before their buffers are freed.
                    if(connection!=null){try{if(intf!=null)connection.releaseInterface(intf);}catch(Exception ignored){}connection.close();}
                    active=null;releaseAfterClose();
                }
            }
            final String text=result;main.post(()->{if(!destroyed){workerRunning=false;selected=null;message(text);setBusy(false);}});
        },"RCM USB").start();
    }
    @Override public void onDestroy(){
        destroyed=true;try{unregisterReceiver(receiver);}catch(Exception ignored){}
        // Worker performs bounded transfer/cancel/drain and owns connection close.
        // It observes destroyed between packets; never free native buffers here.
        super.onDestroy();
    }
}
