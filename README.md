# Hekate_inject_update

在 macOS 上为早期、支持 RCM 漏洞的 Nintendo Switch 1 注入 Hekate。附带大气层升级、emuMMC 备份和故障排查的历史辅助脚本及说明。

**可日常使用的入口是 `inject.command`。维护脚本是固定路径的一次性会话工具，不是通用一键刷机程序。**

## 当前验证状态

截至 2026-10-28，本次设备实测结果：

- Intel Mac → USB RCM 注入成功。
- 虚拟系统显示 `23.0.1 | AMS 1.12.1 | E`，重复启动不到 10 秒。
- 曾发生 Daybreak 安装中报错和开屏停留；隔离第三方插件后最终能够启动，未执行镜像回退。根因尚未完全确定。
- 目前仅恢复 sys-patch 1.6.3.0，配置为 `patch_sysmmc=0`、`patch_emummc=1`。部分游戏恢复启动，但此前被检测为损坏的部分游戏仍失败，复查仍报告损坏。**游戏问题尚未解决。**
- 其他插件和外部补丁仍在 SD 卡隔离目录保留；“已下载最新版”不代表“已启用”或“已通过所有功能测试”。

详细过程见 [本次操作与结果](docs/session-2026-10.md)。

## 适用范围

- macOS、Python **3.11 或更高版本**，支持数据传输的 USB 线。
- 支持 Fusée Gelée 的早期 Switch 1；APX `0955:7321` 检出本身不能证明机型支持漏洞。
- SD 卡上已有可启动的大气层及对应的启动配置。注入脚本不会替你安装大气层。
- 实测平台为 Intel Mac；Apple Silicon 的真实设备注入尚未验收。脚本不支持 Windows/Linux。

仅用于自己有权管理的设备和内容。本仓库不含游戏、密钥、证书、固件整包或设备镜像。

## Quick setup

### 1. 克隆与安装依赖

HTTPS：

```bash
git clone https://github.com/guiyu/Hekate_inject_update.git
cd Hekate_inject_update
```

也可以使用已配置密钥的 SSH：

```bash
git clone git@github.com:guiyu/Hekate_inject_update.git
cd Hekate_inject_update
```

建立独立环境（依赖包含 libusb 和 certifi 可信根证书包，下载保持 HTTPS 证书验证）：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### 2. 准备运行文件

```bash
.venv/bin/python prepare_runtime.py
.venv/bin/python prepare_runtime.py --check
```

准备程序只向本机下载文件，不访问 USB 或 SD 卡：

- Hekate **6.5.4** 注入载荷；
- Atmosphère **1.12.1** 对应的 fusee；
- 固定上游提交的 intermezzo 重定位文件。

下载先写入临时文件，SHA-256 匹配后才替换目标。URL 和固定哈希见 [运行文件清单](manifests/runtime-sources.json)。准备程序不会自动追踪未来的“最新版”，也不下载系统固件、插件或 SD 卡升级包。

### 3. 检测与注入

Switch 进入 RCM 后连接 Mac。RCM 通常是黑屏，但应以 USB 检测结果为准：

```bash
./inject.command --check
```

确认后注入默认的 Hekate：

```bash
./inject.command
```

后续也可在 Finder 中双击 `inject.command`。载荷路径以脚本所在目录解析；日志写入本机 `logs/`。输出原始设备标识的日志不会被 Git 跟踪。

Hekate 启动后选择自己的虚拟系统启动项。**不要照抄其他设备的 emuMMC 配置。**

只有 SD 卡的大气层确实是 1.12.1 时，才可直接发送配套 fusee：

```bash
./inject.command --payload fusee --sd-atmosphere-version 1.12.1
```

该参数只是操作者的版本声明，程序无法通过 RCM 读取并验证卡内版本，也不会强制选择 emuMMC；直接 fusee 启动前，必须自行确认卡内 emuMMC 启用状态及路径。

### 4. 验收

上游输出 `Launch complete!` 或进程退出码为 0，只表示主机端注入流程结束，**不证明主机已成功启动**。请以 Switch 屏幕和设置中的版本为准；本次虚拟系统以末尾 `E` 验收。

- 返回码 `2`：未检测到 RCM；先核对数据线、接口和设备状态。
- 校验失败或文件缺失：先运行 `prepare_runtime.py`；不忽略哈希错误继续注入。
- Codex 沙箱可能隐藏 USB，需要通过应用的设备访问授权运行；普通终端通常无需 sudo。

## 大气层、系统固件和插件是三件事

| 项目 | 用途 | 更新方式 |
|---|---|---|
| Hekate | 启动引导和维护工具 | 更新载荷及配套 SD 文件 |
| Atmosphère | 大气层运行文件 | 备份后替换 SD 文件，fusee 必须配套 |
| Switch 系统固件 | 系统本身 | 在选定系统内用 Daybreak 安装经过核验的包 |

**Daybreak 不能安装 Atmosphère ZIP。** 本仓库不会自动安装系统固件，不会自动修改 AutoRCM，也不能实现纯软件永久免注入。

维护前应备份镜像、配置和存档。普通大气层文件备份不等于完整 emuMMC 备份；本次文件式 emuMMC 备份包括 BOOT0、BOOT1 和所有数据分卷，但未复制 SD 卡外部的全部游戏安装文件。

本次 SD 卡实际为 exFAT。Daybreak 安装时采用 `Preserve settings` 和 `Install (FAT32 + exFAT)`；这不是格式化 SD 卡。安装范围必须事先在主机确认处于 emuMMC。本仓库没有通用固件安装向导。

## 文件结构

```text
inject.command                     日常注入入口，默认 Hekate
inject.py                          文件校验、macOS USB 连接及注入封装
prepare_runtime.py                 下载固定版本运行文件，支持只读检查
checksums.json                     已记录的公开文件 SHA-256
manifests/                         运行文件来源、插件版本快照
vendor/fusee_launcher.py            固定提交的上游 GPLv2 源码
requirements.txt                   Python 依赖
session_guard.py                   历史脚本显式执行保护
backup_*.py                        本次会话的备份脚本
upgrade_sd.py                      本次大气层 SD 文件升级脚本
download_*.py / stage_resources.py  本次下载与资源整理脚本
write_resources_and_firmware.py     本次资源写卡及固件文件准备脚本
docs/                              操作边界、恢复说明与验收记录
```

`backups/`、`diagnostics/`、`logs/`、`downloads/`、`payloads/`、`staging/` 和 `.venv/` 均只保留在本机，不上传 GitHub。二进制载荷通过准备程序下载。

## 维护与恢复

先读 [维护脚本说明](docs/maintenance.md)。这些脚本固定了本次卷名、版本、时间戳和备份路径，克隆后缺少所需本机清单，不能直接复现整次设备维护。

- 先保存故障日志，再检查来源文件、文件系统和启动配置。
- 插件隔离采用改名保留；先验证基础系统，再逐组恢复。
- 不把下载完成、文件复制完成或一次启动成功当作所有功能验收通过。
- 不批量删除被报告损坏的游戏，不删除存档；单独核对具体游戏和合法可用的原始内容来源。
- 完整镜像回退会回到备份时点，应单独审阅确认范围；仓库没有自动恢复真实系统或 emuMMC 镜像的命令。

## 本机检查

```bash
.venv/bin/python -m unittest -v
.venv/bin/python prepare_runtime.py --check
bash -n inject.command
```

单元测试不访问 USB、SD 卡或真实固件。它们检查损坏文件拒绝、运行文件依赖范围、下载校验和失败时保留原文件；不能替代实际设备验收。

## 上游来源与许可

- [CTCaer/hekate 6.5.4](https://github.com/CTCaer/hekate/releases/tag/v6.5.4)
- [Atmosphère 1.12.1](https://github.com/Atmosphere-NX/Atmosphere/releases/tag/1.12.1)
- [Fusée Launcher 固定源码提交](https://github.com/nh-server/fusee-interfacee-tk/tree/fc1497e30c95db83d112899de22057590f039940)
- [插件版本及来源快照](manifests/plugin-versions-20261027.json)

本项目按 [GNU GPL v2](LICENSE) 发布。上游版权与许可证保留于 `vendor/`；未修改上游注入实现。第三方载荷、插件和固件的权利及许可由各自项目或发行方决定，本仓库不重新分发这些二进制文件。
