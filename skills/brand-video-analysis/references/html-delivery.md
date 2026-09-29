# HTML 交付与验收

## 内容与布局

沿用第二版的原则：杂志式留白、清晰标题、克制配色、真实截图；默认浅暖底、深绿与砖红强调，可按品牌调整 CSS。图表用静态 SVG/HTML 预嵌，先渲染正文，CDN 不可用时也能阅读。Tailwind 已关闭 preflight，避免覆盖标题大小；本地 CSS 足以离线显示。不要用动态 fetch 加载本地 JSON 作为首屏数据依赖。

`assets/report.template` 是内部模板，不直接交给用户。`render_report.py` 读取 agent 编写的 JSON 内容，插入通用版式；不会自动分析源数据。先完成真实研究，再写 payload。不要把原始表格内容直接当 HTML，标题、帖文、转写使用 `html.escape`；body_html 只放自己构建的受控标签。

## Payload 契约

```json
{
  "title": "品牌｜视频优化决策报告",
  "brand": "当前品牌",
  "hero_html": "已写好真实结论的 header HTML",
  "sections": [
    {"id":"actions","nav":"先看结论","title":"本轮优先动作","body_html":"真实动作 HTML"},
    {"id":"production","nav":"具体怎么拍","title":"制作方案","body_html":"真实分镜 HTML"}
  ],
  "footer": "日期、版本与证据边界",
  "extra_css": "可选品牌适配 CSS",
  "share_files": ["source/data-clean.json", "source/manifest.json", "browser-checks.json", "qa-desktop.png", "qa-mobile.png"]
}
```

示意字符串须替换为真实内容，不能交占位报告。section 的 show_nav=false 可隐藏次级导航但保留锚点；不要塞过多导航项。

常用类可直接看 report.css：`hero hero-copy hero-images eyebrow lead jump primary-link`；`three two direction priority label callout notice`；`chart bar-row track rank-row`；`case case-top chips frames analysis-grid audio table-wrap compare compare-card`；`journey timeline`。三列自动在窄屏折叠，截图网格按屏宽调整。

截图按钮格式：

```html
<figure>
  <button class="zoom" data-img="assets/v01/frame-000001p000.jpg" data-caption="V01 · 1.00 秒 · 真实动作说明" aria-label="放大截图">
    <img src="assets/v01/frame-000001p000.jpg" alt="真实画面说明" loading="lazy">
    <span class="time">01.00s</span>
  </button>
  <figcaption>事实描述与用途；不要写未经验证的功能结论。</figcaption>
</figure>
```

原片与音轨使用本地相对路径 `<video controls preload="metadata" ...>` / `<audio controls ...>`。关键信息放文本，不只放 hover 或颜色。表格允许局部横滑，整个手机页面不得横向溢出。

## 构建流程

```bash
python3 <技能目录>/scripts/render_report.py --payload <内部目录>/report.json --out <交付目录>
node <技能目录>/scripts/check_browser.cjs <交付目录绝对路径> <已安装playwright模块路径> <Chrome路径>
python3 <技能目录>/scripts/render_report.py --check-only --payload <内部目录>/report.json --out <交付目录> --zip <分享包路径>.zip
```

先用宿主依赖发现工具找到现有运行时与 Playwright；也可用实际可用浏览器完成同等检查。不要把某台电脑的用户名、依赖路径写进技能。`check_browser.cjs` 默认阻断外网做离线验证，截图、媒体起播、放大与 Escape 都检查；无浏览器/模块直接报告未验，不自动安装或启服务。

`--check-only` 检查缺失资源、重复 id、坏锚点和绝对 file URL。打包包含页面引用的本地资源及显式 share_files；share_files 必须是脱敏并检查过的文件。脚本的路径检查不是凭证检测，agent 仍须审查内容。原始 JSON、签名媒体 URL、用户私人原话、.venv、node_modules、脚本内部日志不入包。

## 验收重点

- 把证据区用到的图片全部加载，避免将 lazy-load 未加载误判为坏图。
- 实际查看桌面与手机截图；另看一页主图表和一页逐帧内容。
- 导航、原片时间、放大/关闭、视频与音轨实际播放均正常。
- 标记哪些检查为自动、哪些为目视；不把 HTML 正常说成内容或转化有效。
- 手动核算一张图，核对 3–5 条案例的证据映射，保证统计与正文同源。
- ZIP 内 HTML 与本地正式入口一致，资源完整，中文文件名用 Python zipfile 等可靠 UTF-8 归档；包内优先 ASCII 路径。
- 修订时更新用户已打开的 index.html 和原分享包；历史快照用 .snapshot 或放内部目录。
