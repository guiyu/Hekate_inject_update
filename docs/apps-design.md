# Hekate Injector 三平台应用设计

日期：2026-11-07

## 已确认的目标

为 Windows、Android、macOS 提供带图标、中文界面、可直接打开的 Switch RCM 注入应用。iPhone 没有越狱或 TrollStore，用户已取消 iOS 版本；不制作 iOS 遥控版或无法注入的占位应用。

## 使用流程

打开应用 → 将支持漏洞的 Switch 1 置于 RCM 并连接数据线 → 检测设备 → 点击“注入 Hekate” → 查看发送结果 → 用户核对 Switch 屏幕。

首页显示内置 Hekate 版本、USB 设备状态、检测与注入按钮和日志。仅检测到 NVIDIA APX 0955:7321 后允许注入。一次只允许一个 USB 操作，操作期间禁用按钮。未连接、权限拒绝、驱动缺失、文件校验失败、USB 断开分别给出明确说明。

发送完成仅显示“载荷已发送，请查看 Switch 屏幕”，不声称系统启动成功。默认使用已有 SHA-256 校验过的 Hekate 6.5.4，不自动升级载荷，不新增直接 fusee 启动入口，避免大气层版本不匹配。

## 方案比较与选择

1. **桌面共享 Python 注入核心与界面，Android 原生 USB Host 应用（推荐）**：复用已在此 Mac 实测的代码；桌面分别打包运行时，Android 使用系统 USB 授权。三版统一图标、中文用语和流程，允许原生布局略有差异。
2. 全部改成网页/WebUSB：无法一致满足独立桌面应用及手机 USB 兼容性要求，因此不采用。
3. 全部用一个跨平台框架：仍需三个 USB 后端，额外引入框架、插件及构建依赖，没有足够收益，因此不采用。

用户已明确要三个可执行平台；上面第一种实现是开发者提出的具体技术方案，待确认。

## 技术方案

### macOS

- 使用 Tk 桌面界面及现有 PyUSB、libusb、Fusée Launcher 后端，PyInstaller 生成 `.app`，内置 Python、依赖和已校验载荷；不依赖仓库目录或用户的 Python 环境。
- 首先构建本机 Intel x86_64 版本；Apple Silicon 如提供单独产物，必须经过独立构建校验，不能把 Intel 包标成通用架构。
- 使用统一图标生成 `.icns`。应用不进行联网下载，不读写 SD 卡。
- 无开发者分发证书时明确标注未公证，说明系统安全提示的处理方式，不承诺零提示安装。

### Windows

- 同一 Python UI 与核心，使用经过适配与测试的 Windows libusbK 后端及匹配驱动。现有 upstream 后端存在资源生命周期、传输计数和错误处理疑点，不能直接把打包成功视作后端可用。
- 在 Windows 构建环境打包 `.exe`；如本机无法直接构建，则通过仓库 CI 构建并下载真实产物。
- 内置 `.ico`、载荷、依赖及许可证；不静默安装驱动，不自动替换任意 USB 设备驱动。说明仅为 APX 0955:7321 安装所需驱动。

### Android

- 原生 Java Activity，使用 Android USB Host API，仅申请当前 APX 设备的 USB 权限，不申请存储、网络等无关权限。
- 内置 Hekate 与 intermezzo，复用同一载荷构造布局与 SHA-256 清单；发送前校验，使用 USB bulk OUT/IN 发送。RCM 大控制请求通过 JNI 使用已授权的 USB 文件描述符提交异步 usbfs URB，不依赖受 PAGE_SIZE 限制的普通 `controlTransfer` 调用。
- 使用 NDK 构建 arm64-v8a、armeabi-v7a 和 x86_64 库；异步 URB 必须具有有界等待、超时取消与回收。错误码必须区分提交失败和触发后的断开；提交失败不能显示已发送成功。
- 最低 Android 8.0（API 26），要求 USB Host/OTG；大控制传输是否被手机 USB 栈支持需真机验收，不能保证所有 Android 设备可注入。
- 提供已签名 APK。签名密钥仅本地保留且排除 Git；无升级密钥恢复承诺。无需 root。

## 产物

- `dist/Hekate-Injector-macOS-Intel.zip`，内含 `.app`。
- `dist/Hekate-Injector-Windows-x64.zip`，内含 `.exe` 及必要运行文件，或经过验证的单文件 `.exe`。
- `dist/Hekate-Injector-Android.apk`。
- 安装/驱动/OTG/RCM/错误说明、源码及可重复构建脚本，产物 SHA-256 清单。
- 自绘统一插线/启动图标，导出 PNG、ICO、ICNS 和 Android 图标资源，不使用任天堂商标。

## 验证与边界

- 测试载荷布局、大小边界、哈希拒绝、短写/USB 失败处理、无设备/权限拒绝路径；桌面 UI 不阻塞主线程。
- 检查 macOS 包依赖、Windows PE 架构与打包文件、Android manifest/签名/内置资源。
- macOS 进行 UI 与无设备操作验证。若有 RCM 真机，再经用户明确当前就绪后注入；Windows/Android 未连接真实设备时明确标注未完成真机验收。
- 不安装固件、不操作游戏/存档/emuMMC、不修改 AutoRCM，不自动执行历史 SD 维护脚本。
- 源码和构建说明可保存至当前仓库；设备日志、备份、签名私钥和构建缓存不得发布。

## 当前构建条件

此 Mac 有 Python 3.11、Swift 命令行工具、JDK 和 Android SDK（API 35、build-tools 35.0.0）；没有完整 Xcode，也没有本地 Windows 环境。桌面打包工具需要安装到项目隔离环境。Windows 产物需从真正的 Windows 构建环境取得。
