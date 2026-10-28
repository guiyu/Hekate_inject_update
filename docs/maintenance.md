# 历史维护脚本与恢复边界

这些脚本保存了本次设备操作的实现，便于审阅；它们不是跨设备的通用升级工具。默认拒绝执行，必须显式传入 `--run-session-script`，且只能在仓库根目录运行。依赖断言的检查禁止使用 `python -O`。

## 脚本与前置条件

| 脚本 | 作用 | 前置条件与限制 |
|---|---|---|
| `backup_emummc.py` | 流式复制、校验文件式 emuMMC，支持中断后核对前缀续传 | 固定 `/Volumes/Untitled`、`emuMMC/SD00/eMMC` 与本次备份目录；需要额外磁盘空间；不适用于分区式 emuMMC |
| `backup_resources.py` | 保存当前大气层、引导、自制程序、配置及资源 | 固定卷名及备份目录；再次执行会更新此备份，需先自行保留其他代次 |
| `download_firmware_parts.py` | 对提供了大小、URL 和 SHA-256 的包分段下载并组装校验 | 需要本机 `downloads/firmware-23.0.1-release.json`；并发 32，不是通用下载器；只校验内容哈希，不验证发行方身份 |
| `download_plugin_assets.py` | 根据本机下载计划下载资源 | 需要本机 download-plan.json；有发布哈希时比对，无哈希时只记录本次 SHA-256 |
| `stage_resources.py` | 将本次已核验资源整理成 SD 相对路径 | 固定本次包布局与工具版本；不自动处理未来版本；本身不写 SD 卡 |
| `upgrade_sd.py` | 本次 AMS 1.8.0 → 1.12.1 文件升级 | 需要完整本机资源备份及其 manifest；固定路径；不安装系统固件 |
| `write_resources_and_firmware.py` | 更新本次资源、将固件放入 SD 卡 | 需要完整 emuMMC 和资源备份、原引导分区身份匹配及本机清单；固件只放文件，实际安装由 Daybreak 完成 |

**不要照抄卷名，也不要为了绕过检查而伪造 manifest。** 执行前逐行审阅路径、备份代次、版本、配置和影响范围。本机源数据未上传，故全新克隆不能直接执行这套会话流程。

显式执行形式仅供审阅后使用，例如：

```bash
python3 backup_emummc.py --run-session-script
```

这条命令将复制固定位置的文件式 emuMMC，而不是预览。大备份需持续保持设备连接。`progress.json` 仅表示部分进度；只有完整清单状态为 `complete-and-verified` 才算本次备份完成。

## 插件隔离与逐组恢复

故障诊断时，将以下目录原地移入 SD 根目录的 `recovery-disabled-20261028/`，保留原位置的空目录：

- `atmosphere/contents`
- `atmosphere/exefs_patches`
- `atmosphere/kip_patches`
- `atmosphere/nro_patches`

此举保留原文件，但暂停自定义模块、游戏模组和外部补丁。不要将全部目录一次性搬回并声称问题已解决。本次仅将 `contents/420000000000000B`（sys-patch）移回，随后核对：

```ini
[options]
patch_sysmmc=0
patch_emummc=1
```

sys-clk 的原版 23.x 支持未确认，保持开机停用；没有自动改用涉及电压和高频修改的分支。其他资源下载版本见版本清单，当前启用状态以实际 SD 卡与设备测试为准。

## 文件系统与 macOS 元数据

本次 SD 卡是 exFAT，分区类型标记在 diskutil 中可显示为 Windows_NTFS；应以实际挂载文件系统为准。只读 `fsck_exfat -n` 检查通过不代表卡上每一份游戏内容都完整，也不能证明存储介质永远可靠。

macOS 曾为更新文件产生 `._` AppleDouble 元数据，导致固件目录内按扩展名计数翻倍。实际 238 个 NCA 的 SHA-256 均匹配；仅对本次写入文件配对的元数据做过备存清理。不要无差别删除隐藏文件或个人文件。

文件写入需先同步并回读校验，再安全弹卡。本次仅对 SD 卡关闭 Spotlight 索引；没有结束全局索引服务。不要将强制卸载作为有文件仍在写入时的常规步骤。

## 回退

仓库不包含镜像回退命令，也没有执行过本次镜像回退。若以后确需回退：

1. 完全关机，确认正确 SD 卡和 emuMMC 类型。
2. 保存当前故障日志与必要状态，核实完整备份每个分卷的大小和哈希。
3. 审阅将覆盖的目标及将回退到的存档时点，获得明确授权后再恢复。
4. 回读校验，使用配套引导环境，在主机上验证系统、游戏和存档。

恢复大气层文件不能修复任意 NAND 内部损坏；恢复完整 emuMMC 镜像也不能自动补回未备份的外部游戏安装数据。
