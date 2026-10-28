# 2026-10 操作结果与未完成项

本文件是去除设备标识和个人路径后的历史摘要，不是所有机型均可复现的通用教程。

## 已验证

1. 早期 Switch 1 在 RCM 下由 Intel Mac 识别为 APX，使用 Hekate 6.5.4 成功启动原环境 `19.0.0 | AMS 1.8.0 | E`。
2. 备份原资源后更新 Atmosphère 1.12.1 和配套引导文件，主机读数确认 `19.0.0 | AMS 1.12.1 | E`。
3. 准备 23.0.1 离线包，核对发布 SHA-256、ZIP CRC 和 238 个 NCA 内容 ID 哈希；固件文件本体不进入仓库。
4. 完整文件式 emuMMC 备份共 31,276,924,928 字节，包括 BOOT0、BOOT1 和 8 个数据分卷；逐文件校验通过。本机资源备份共 4,706 个文件。外部游戏安装文件没有完整备份。
5. 写入配套资源和固件目录后，420 个文件回读哈希匹配。卡在备份中曾断开，重连后核对中断分卷的已复制前缀并完成续传。

## Daybreak 后的故障与恢复测试

用户报告 Daybreak 安装中报错，随后在 Switch 标志处停留。已保存诊断信息，发现：

- 更新期间旧内核的 nifm 曾报 `2002-4144`，上游错误定义为 `RomNonRealDataVerificationFailed`。
- 后续 sys-patch 记录识别到固件 23.0.1；这条日志本身不证明安装完整。
- SD 上固件包仍全部匹配原哈希；只读文件系统检查通过。

隔离第三方目录后，用户起初仍反馈开屏停留，随后确认进入 `23.0.1 | AMS 1.12.1 | E`；再重启不到 10 秒进入同一虚拟系统。未执行直接 fusee 对比，也未恢复旧镜像。

**目前不能把最初故障确定归因于某个插件。** 插件干扰、首次启动/更新收尾耗时和安装过程问题仍需区分。

## 当前状态

- 固件和大气层已在虚拟系统重复启动验证：`23.0.1 | AMS 1.12.1 | E`。
- 只恢复 sys-patch 1.6.3.0，并限制为作用于 emuMMC；其他第三方模块和补丁仍隔离保存。
- 恢复该组件后，部分游戏可以启动；部分之前被检测为损坏的游戏仍无法启动，复查仍显示损坏。
- 尚未取得具体受影响游戏和内容来源，尚未进行游戏重装、存档删除或完整镜像回退。**不能宣称所有游戏已修复，也不能仅凭提示认定存档丢失。**
- 插件版本清单是下载快照，不是启用列表，也不是全部插件在 23.x 上的兼容性保证。

## 来源

- [Hekate](https://github.com/CTCaer/hekate/releases/tag/v6.5.4)
- [Atmosphère](https://github.com/Atmosphere-NX/Atmosphere/releases/tag/1.12.1)
- [文件系统错误定义](https://github.com/Atmosphere-NX/Atmosphere/blob/master/libraries/libvapours/include/vapours/results/fs_results.hpp)
- [Nintendo 软件损坏检查流程](https://www.nintendo.com/en-gb/Support/Troubleshooting/How-to-Check-for-Corrupted-Data-in-Downloadable-Software-on-Nintendo-Switch-1516160.html)

系统固件曾来自带发布哈希的第三方镜像；文件哈希验证不能替代官方来源信任或主机安装校验。本仓库不包含该固件、控制台密钥或证书。
