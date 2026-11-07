带图标和中文界面的 Switch 1 RCM 注入工具，默认内置并校验 Hekate 6.5.4，离线运行。

下载：
- Windows x64：`Hekate-Injector-Windows-x64.zip`，解压后运行 `Hekate Injector.exe`。首次使用需要为 **APX 0955:7321** 安装 libusbK 驱动。
- macOS Intel：`Hekate-Injector-macOS-Intel.zip`，解压后打开 `.app`，不需要安装 Python。应用未公证，系统可能要求到“隐私与安全性”确认打开。不是 Apple Silicon 原生版本。
- Android 8.0+：`Hekate-Injector-Android.apk`，安装后连接支持 OTG 的数据线并允许 USB 授权，支持 arm64-v8a、armeabi-v7a、x86_64。

验收边界：
- 安装包通过资源校验、桌面窗口启动检查、APK 签名/架构检查和跨语言载荷测试。
- 原命令行 Mac 注入已在此 Switch 上实测；新版 GUI 的 Windows 和 Android **尚未完成真机注入验收**，不保证所有 Android USB 栈均可注入。
- “载荷已发送”不证明 Switch 已启动；请查看主机屏幕。仅适用于支持 RCM 漏洞的早期 Switch 1。
- iOS 没有发布：LiveContainer 不能补足直接 USB 注入权限。
- 本次为预发布测试版。Android 使用本次构建生成的自签证书，后续构建签名可能变化；更新可能需要卸载旧版应用。它不保存游戏或存档。
- 不安装系统固件，不改动 SD 卡、游戏、存档或 AutoRCM。

完整源码、构建步骤、第三方来源与驱动说明见仓库 `docs/apps.md`。请使用 `SHA256SUMS.txt` 核验下载文件。
