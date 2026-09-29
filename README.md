# 品牌视频经营分析

给出产品、用途和素材表，生成**结论先行、指导下一步制作与经营优化**的 HTML 报告。

## 安装到 Codex

把下面这句话发给 Codex：

```text
请使用 skill-installer，安装这个 GitHub 技能：
https://github.com/zhengzhentao86/brand-video-analysis/tree/main/skills/brand-video-analysis
安装完成后检查 SKILL.md、scripts、references 和 assets 是否齐全。
```

也可以在已经安装 Codex 技能安装器的 macOS/Linux 终端运行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo zhengzhentao86/brand-video-analysis \
  --path skills/brand-video-analysis
```

安装后在下一轮对话调用；如果当前应用没有显示新技能，重新打开任务或重启应用后再试。安装器发现同名技能时会停止，不会直接覆盖。更新已有版本前请先让 Codex 比较版本并保留备份。

Windows 用户可直接使用上面的自然语言安装指令；终端示例是 macOS/Linux shell 语法。

## 使用

```text
用 $brand-video-analysis 帮我分析：
产品：你的产品
用途：独立站广告投放
素材表：钉钉/飞书链接，或本地 CSV、Excel、视频文件
```

还可以补充品牌网站、目标市场、具体 SKU、广告花费与成交数据；已有背景不用重复填表。不是独立站业务时，技能按实际渠道分析。

## 交付内容

- 结论与优先动作：先改什么、谁交付什么、怎样验证。
- 默认 3 个制作方向，优先方向的分镜、素材清单与 AI 分工。
- 广告与商品页或其他实际购买路径的承接建议。
- 服务决策的图表、明确指标口径，以及不同结果对应的复盘动作。
- 默认 3–5 条代表原视频：前 5 秒逐秒截图、后续关键镜头、音轨核验和并排比较。
- 本地 HTML、可放大截图、视频/音轨，以及完整资源 ZIP。

播放量不等于成交效果；缺少购买数据时只提出待测试方案。无法读取原片会明确标记，不会用表内 AI 分析冒充观看。未读取网站或广告账户时，不会声称完成经营诊断。

## 运行条件

技能是供 Codex 执行的工作流程，不是安装后自动运行的网站或独立软件。只安装本仓库不会自动安装所有依赖，也不会授予第三方数据权限。

| 功能 | 运行条件 |
|---|---|
| 本地报告生成与打包 | Python 3.10+（仅标准库） |
| 原视频抽帧和音轨提取 | ffmpeg、ffprobe |
| 联系表预览 | Pillow，可选 |
| 本地自动转写 | faster-whisper 和已缓存模型，可选；也可用宿主其他可靠转写能力 |
| 自动浏览器验收 | Node.js、Playwright 和可用 Chromium/Chrome；也可用宿主浏览器工具 |
| 钉钉表格 | 已安装并登录的 dws CLI，及对应表格读取权限 |
| 飞书表格 | 已安装并登录的 lark-cli，及对应资料读取权限 |

依赖缺失时由 Codex 按任务检查和处理；无需运行本地 Web 服务。数据源命令遵循 CLI 的当前契约，不内置账号、密钥或客户资料。

## 仓库内容

`skills/brand-video-analysis/` 是完整可安装技能，包含 SKILL.md、界面元数据、数据与交付参考、抽帧/报告/验收脚本及 HTML 版式资源。

不含客户视频、客户表格、私人聊天、生成报告或临时下载链接。

## 验证范围

发布前已用已有真实案例回归抽帧、音轨转写、报告生成、离线桌面/手机显示、媒体播放与放大交互；并检查不足一秒的无音轨视频及异常资源引用。验证说明工具流程可运行，不证明对所有品牌都能提高成交。
