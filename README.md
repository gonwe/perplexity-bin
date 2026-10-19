# Perplexity 官方 Linux 版 AUR 包

[AUR](https://aur.archlinux.org/packages/perplexity-bin) · [GitHub](https://github.com/gonwe/perplexity-bin)

将 Perplexity 官方 Linux DEB 转换为 Arch Linux / CachyOS 软件包。包名是
`perplexity-bin`，启动命令为 `perplexity`，支持 x86_64。

应用来自 Perplexity 官方软件源，保留官方 Electron、界面和 Linux 原生后端。
本仓库仅维护打包脚本，不代表 Perplexity 官方，也不是旧的社区网页封装版。
软件本体采用上游专有条款，打包脚本采用 0BSD。

## 安装

```bash
yay -S perplexity-bin
# 或 paru -S perplexity-bin
```

也可以检查本仓库的 PKGBUILD 后运行：

```bash
git clone https://github.com/gonwe/perplexity-bin.git
cd perplexity-bin
makepkg -si
```

与旧社区包 `perplexity` 冲突，安装时包管理器会提示移除旧包。安装本包不会
自动安装 Docker、NVIDIA 工具包或启用服务；可选本地模型运行环境须按 Arch
方式自行配置。上游随附的 Ubuntu 安装脚本不适用于 Arch。

## 中文输入及启动参数

Wayland 桌面存在 XWayland 时，启动器默认使用 `--ozone-platform=x11`，用于兼容
部分 Electron/KDE 环境下的 Fcitx 中文输入。Chromium 沙箱保持启用。

自定义参数写入 `~/.config/perplexity-flags.conf`，每行一个完整参数；空行和
以 `#` 开头的注释忽略，不执行 shell 表达式。例如选择原生 Wayland：

```text
--ozone-platform=wayland
--enable-wayland-ime
```

也可以直接执行 `perplexity --ozone-platform=wayland --enable-wayland-ime`。

## 上游来源

- [Portable Computer 官方介绍和 Linux 安装说明](https://www.perplexity.ai/en-GB/hub/products/portable-computer)
- [官方 APT 包索引](https://packages.perplexity.ai/deb/dists/stable/main/binary-amd64/Packages)
- [官方发布公告](https://www.perplexity.ai/hub/blog/introducing-portable-computer-for-local-first-ai)

当前初始版本为 **26.10.2，构建 117519**。下载 URL 中的 `+` 必须编码成 `%2B`。
DEB 的 SHA256 固定记录在 PKGBUILD 中，构建时会校验全部来源。

## 更新维护

通过维护者本机 Codex 的定期任务，每天北京时间 10:00 检查官方 APT 索引。
有新版或新构建时，更新配方、构建校验、提交 GitHub，等待 CI 成功后同步 AUR。
无变化时不重复提交，也不发送日常通知。本机需要开机并运行 Codex；无需将个人
SSH 私钥上传到 GitHub。GitHub Actions 对 push、PR 和手动触发执行 Arch 构建验证。

```bash
python3 scripts/update.py --check   # 只检查上游
python3 scripts/update.py --apply   # 更新版本、构建号、SHA256 和 .SRCINFO
scripts/validate.sh                # 构建并检查包，需要已安装 depends 和打包工具
```

同版本的新构建递增 `pkgrel`；应用新版本重置 `pkgrel=1`。自动更新拒绝降级，
也拒绝同版本、同构建号却改变 SHA256 的上游文件，留待人工检查。
SHA256 来自官方 HTTPS 索引，并非独立的代码审计或数字签名验证。

维护者提交验证后的文件并推送 GitHub，确认 CI 成功后执行：

```bash
scripts/publish-aur.sh
```

该脚本只向 AUR 发布配方及其必需的本地来源文件，并读取远端 `.SRCINFO` 确认。
自动化不升级维护者本机已安装的软件；用户通过正常 AUR 升级流程获取新版。

Namcap 检查保留共享库、权限和包元数据等规则；排除不适用于此上游布局的
`elfpaths`（官方二进制位于 `/opt`），以及把应用模板的独立 Python venv 误判为
宿主依赖的 `pydepends` 和 `shebangdepends`。其他 Namcap 错误会阻止验证通过。

## 验证范围

首次发布检查完整软件包构建、桌面入口、官方 Linux 登录界面启动和实际中文
输入。登录后的聊天、Computer 工作流及本地模型执行需要相应账号或硬件，
不属于已完成的验证。
