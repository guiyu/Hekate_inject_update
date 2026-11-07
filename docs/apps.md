# Hekate Injector 应用版

支持 Windows x64、macOS Intel、Android 8.0+。统一中文界面和原创图标，内置 Hekate 6.5.4；应用本身离线运行，不需要下载载荷。

## 使用

1. 确认是支持 Fusée Gelée 的早期 Switch 1，SD 卡已有可启动的 Hekate/大气层配置。
2. Switch 完全关机，进入 RCM，以数据线连接电脑或支持 OTG 的 Android 手机。
3. 打开应用，点击“检测设备”，检测到 `APX 0955:7321` 后点击“注入 Hekate”。Android 按系统提示允许 USB 访问。
4. 查看 Switch 屏幕，在 Hekate 选择自己的虚拟系统入口。不要把“发送完成”当成系统已启动。

应用不安装系统固件，不改动 SD 卡、游戏、存档、emuMMC 或 AutoRCM。载荷固定为已核验的 6.5.4，不自动更新，也不提供容易发生版本错配的 fusee 按钮。旧的 `inject.command` 保持可用。

## 下载和安装

安装包见 [GitHub Releases](https://github.com/guiyu/Hekate_inject_update/releases)。下载后用 SHA256SUMS.txt 核对。

- **Mac Intel**：解压 zip，将 `.app` 拖入“应用程序”或直接打开。无需安装 Python。应用为 ad-hoc 签名、未经 Apple 公证；若系统阻止打开，确认下载来源后在“系统设置 → 隐私与安全性”选择仍要打开。不关闭系统全局安全机制。本版不是 Apple Silicon 原生包，Apple Silicon 兼容性未实测。
- **Windows x64**：完整解压 zip，运行 `Hekate Injector.exe`；不能只拷走 exe，需保留同目录 `_internal`。如找不到 APX，使用 [Zadig 官方工具](https://zadig.akeo.ie/) 为 **APX / VID 0955 PID 7321** 安装 **libusbK** 驱动；不要替换鼠标、键盘、集线器或其他 USB 设备的驱动。Windows UI 包不需要用户安装 Python。
- **Android**：安装 APK，首次允许浏览器/文件管理器安装该 APK。手机需支持 USB Host/OTG，部分机型需手动启用 OTG。仅申请所连接 APX 的 USB 访问授权，不申请网络、文件存储等权限。本版是自签测试构建；后续签名若变化，可能需要卸载旧版注入应用后安装。该应用不存储游戏或存档。
- **iOS**：按用户确认的范围不提供。普通 iPhone + LiveContainer 不具备直接执行此 USB 注入的权限，不发布占位 IPA。

## 构建

Python 3.11，先在项目根目录建立隔离虚拟环境并安装：

```sh
python3 -m venv .build-venv
# Windows 使用 .build-venv\Scripts\python.exe
.build-venv/bin/python -m pip install -r apps/requirements-build.txt
```

在目标桌面操作系统运行：

```sh
python -m apps.build_desktop
```

Windows 还需本机 7-Zip（GitHub Windows runner 已有）。构建脚本下载固定版本运行文件并校验 SHA-256，运行中的应用不会联网。PyInstaller 不能在 Mac 上交叉生成 Windows 应用；仓库 CI 分别在 Windows 和 Intel Mac 构建，真实执行已打包的 `--self-test` 与 `--smoke-ui`。

Android 需要 JDK 17+、Android SDK API 35、build-tools 35.0.0、NDK 27.2.12479018：

```sh
python -m apps.build_android --sdk /path/to/android-sdk --ndk /path/to/ndk/27.2.12479018
```

直接使用 aapt2、javac、d8、clang、zipalign 和 apksigner，不依赖系统 Gradle。构建 arm64-v8a、armeabi-v7a、x86_64，原生库与 APK 使用 16 KB 页面兼容对齐。签名材料在忽略的 `build/signing/`，本地重建会复用该目录；务必自行保管，不提交 Git。CI 首次构建生成的签名不保证跨运行复用，因此 Release 标注为预发布测试版。

产物位于 `dist/`。`python -m apps.make_icons` 可从源代码重新生成 PNG/ICO/ICNS 和 Android 各密度图标。

## 测试与结果解释

```sh
python -m unittest discover -v
python -m unittest discover -s tests -v
```

核心测试验证握手长度、短写停止、资源校验、错误传播及清理；Java 载荷逐字节对照 Python；Linux CI 通过 AddressSanitizer/UBSan 模拟 usbfs 提交拒绝、完成、断开和取消，检查原生缓冲区生命周期。桌面包的自检不会访问 USB。Android APK 检查签名、ABI、内置资源、声明权限和对齐。

Mac 原命令行入口曾在当前设备实测成功。图形应用的构建与启动测试不能替代真机注入验收；Windows、Android 真机注入尚未完成。某些 Android USB 栈可能拒绝超长控制请求，应用会报告底层错误而不会声称启动成功。

## 第三方来源与许可

- 项目及载荷构造遵循 GPL-2.0，保留仓库 LICENSE；未修改原 `vendor/fusee_launcher.py`。
- [Hekate 6.5.4](https://github.com/CTCaer/hekate/tree/v6.5.4)，GPL-2.0，载荷 SHA-256 见 `checksums.json`。
- [Fusée Launcher / intermezzo](https://github.com/nh-server/fusee-interfacee-tk/tree/fc1497e30c95db83d112899de22057590f039940)，GPL-2.0，归属 Kate Temkin / Mikaela Szekely。
- [libusbK 3.1.0.0](https://github.com/mcuee/libusbk/releases/tag/V3.1.0.0)，LGPL-3.0 / BSD 组件；许可证在 `apps/licenses/`，运行 DLL 官方归档与 DLL 的 SHA-256 固定于准备脚本。使用公开 `UsbK_GetProperty`，不依赖私有句柄内存偏移。[对应源代码归档](https://github.com/mcuee/libusbk/releases/download/V3.1.0.0/libusbK-3.1.0.0-src.7z)。运行库动态链接，源码运行方式支持用户自行替换重建的库，重新打包前需更新哈希。
- Python、Tk、PyUSB、libusb-package、PyInstaller、Pillow、certifi 的许可证由打包脚本收集至应用资源目录。图标为本项目原创几何图形，不包含任天堂商标。
