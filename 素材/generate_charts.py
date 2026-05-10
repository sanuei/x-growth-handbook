"""
X 运营增长完全手册 — 图表生成脚本
使用 gpt-image-1 生成书中插图，统一风格

运行前提：
  pip install openai pillow
  已通过 `codex login` 或设置 OPENAI_API_KEY 环境变量完成登录

使用方式：
  python3 generate_charts.py

生成的图片将保存在本脚本所在目录的 images/ 子文件夹中。
"""

import os
import sys
import base64
import time
from pathlib import Path

# ── 依赖检查 ─────────────────────────────────────────────────────────────────
try:
    from openai import OpenAI
except ImportError:
    print("请先安装 openai：pip install openai")
    sys.exit(1)

try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── 初始化 ───────────────────────────────────────────────────────────────────
client = OpenAI()   # 自动读取 OPENAI_API_KEY 或 Codex 凭证

OUT_DIR = Path(__file__).parent / "images"
OUT_DIR.mkdir(exist_ok=True)

MODEL  = "gpt-image-1"
SIZE   = "1536x1024"   # 横版，适合书籍正文插图
QUALITY = "high"

# ── 全局样式说明（附加在每个 prompt 前）──────────────────────────────────────
STYLE = """
Design style:
- Clean professional Chinese infographic, suitable for a printed book
- Color palette: pure white background (#FFFFFF), near-black (#1A1A1A) for main elements,
  medium gray (#666666) and light gray (#CCCCCC) for secondary elements
- No decorative borders, shadows, or 3D effects — flat, minimal design
- Font: bold sans-serif for titles and key numbers; regular weight for body labels
- All Chinese text must be clearly legible (use standard simplified Chinese characters)
- All numerical data must be exactly as specified — do not invent or approximate
- Resolution: sharp, print-quality rendering at 150dpi equivalent
- No logos, watermarks, or attribution text
"""

# ── 图表定义 ─────────────────────────────────────────────────────────────────
CHARTS = [
    {
        "filename": "fig1-1-platform-radar.png",
        "chapter":  "第一章",
        "caption":  "主流社交平台维度对比",
        "prompt": STYLE + """
Create a RADAR CHART (spider chart / polar chart) titled "主流社交平台维度对比"
comparing 4 social media platforms across 5 dimensions.

Chart title (centered above): 主流社交平台维度对比
Subtitle (smaller, below title): 五个维度得分（满分10分）

5 axes (evenly spaced, labeled at the tips):
  全球曝光 / 话题参与 / 快速传播 / 商业变现 / 文字承载

4 platforms with their scores on each axis in order above:
  X（推特）  : 9, 8, 9, 7, 9  — drawn in solid black (#1A1A1A), filled with 10% black
  微博        : 6, 7, 7, 6, 5  — drawn in dark gray (#444444), filled with 8% gray
  微信公众号  : 3, 4, 3, 8, 7  — drawn in medium gray (#888888), filled with 8% gray
  小红书      : 5, 6, 5, 7, 4  — drawn in light gray (#AAAAAA), filled with 8% gray

Radial scale: 0 (center) to 10 (outer edge), with gridlines at 2, 4, 6, 8, 10
Scale numbers (2, 4, 6, 8, 10) shown on one axis

Legend: 4 colored line swatches + platform name, arranged horizontally below the chart

Overall layout: chart takes up ~75% of image height, legend below, generous white margins
"""
    },
    {
        "filename": "fig1-2-algo-weights.png",
        "chapter":  "第一章",
        "caption":  "X 算法互动权重示意",
        "prompt": STYLE + """
Create a HORIZONTAL BAR CHART titled "X 算法互动权重示意"

Chart title (bold, top-left aligned): X 算法互动权重示意
Footnote (bottom-right, small gray text): * 权重为相对估算值，非官方公开数据

4 horizontal bars, from top to bottom:
  点赞        : weight value = 1   — bar color light gray (#CCCCCC)
  转发 / 引用 : weight value = 20  — bar color dark gray (#555555)
  回复        : weight value = 27  — bar color near-black (#333333)
  关注转化    : weight value = 50  — bar color black (#1A1A1A)

Bar specifications:
- Each bar starts at x=0 and ends at the weight value
- X-axis scale: 0 to 55, with tick marks at 0, 10, 20, 30, 40, 50
- Bar height: medium thickness with visible spacing between bars
- Action label (Chinese) displayed LEFT of each bar, right-aligned
- Weight number displayed RIGHT of each bar end, in bold, larger font size

Additional design:
- X-axis label below: 权重分值（相对值）
- Top and right spines removed (clean chart style)
- Bottom spine in light gray
"""
    },
    {
        "filename": "fig3-1-thread-structure.png",
        "chapter":  "第三章",
        "caption":  "Thread 结构拆解",
        "prompt": STYLE + """
Create a VERTICAL FLOW DIAGRAM titled "Thread 结构拆解" showing the structure of a Twitter/X Thread.

Chart title (bold, centered top): Thread 结构拆解

4 stacked rectangular blocks connected by downward arrows, from top to bottom:

Block 1 — DARKEST (filled black #1A1A1A, white text):
  Label: 钩子（第一条）
  Description: 悬念 · 数字 · 反常识 · 强观点，让人必须点开

  ↓ (downward arrow)

Block 2 — DARK GRAY (#333333, white text):
  Label: 展开（第2至N条）
  Description: 逐步拆解，每条可独立阅读 · 案例、步骤、数据、故事

  ↓ (downward arrow)

Block 3 — MEDIUM GRAY (#555555, light text):
  Label: 小高潮（倒数第2条）
  Description: 核心结论与最强洞察 · 信息密度最高的一条

  ↓ (downward arrow)

Block 4 — LIGHT GRAY (#777777, white text):
  Label: 行动引导（最后一条）
  Description: 转发 · 关注 · 留言 · 链接 · 明确告诉读者下一步

Tip box at the bottom (white background, light gray border, #F5F5F5 fill):
  Title: 关键要点
  Three bullet points:
  · 第一条决定点开率，是 Thread 最重要的一条
  · 每条推文应能独立成立，不依赖上下文
  · 总长度控制在 5 至 15 条，超过 10 条需节奏把控

Blocks are equal width (~70% of image width), centered, with rounded corners.
Arrows are dark gray, centered between blocks.
"""
    },
    {
        "filename": "fig5-1-growth-stages.png",
        "chapter":  "第五章",
        "caption":  "X 账号增长阶段路径",
        "prompt": STYLE + """
Create a HORIZONTAL STAGE DIAGRAM titled "X 账号增长阶段路径" showing 4 growth phases.

Chart title (bold, centered top): X 账号增长阶段路径
Footnote (bottom center, small gray): * 粉丝数仅供参考，实际进度因内容质量和赛道而不同

4 equal-width vertical rectangular cards arranged side by side (left to right),
connected by rightward arrows between them:

Card 1 — LIGHT GRAY (#E8E8E8, dark text #1A1A1A):
  Top number label: 0 → 500（粉丝）
  Stage name (bold): 冷启动期
  Three tactics:
    主动破冰
    评论截流
    每日互动

  → (rightward arrow)

Card 2 — MEDIUM GRAY (#B0B0B0, dark text):
  Top number label: 500 → 2000（粉丝）
  Stage name (bold): 内容验证期
  Three tactics:
    找到爆款类型
    Thread 实验
    数据迭代

  → (rightward arrow)

Card 3 — DARK GRAY (#666666, white text):
  Top number label: 2000 → 5000（粉丝）
  Stage name (bold): 口碑传播期
  Three tactics:
    社群渗透
    跨圈合作
    建立 Newsletter

  → (rightward arrow)

Card 4 — NEAR BLACK (#1A1A1A, white text):
  Top number label: 5000+（粉丝）
  Stage name (bold): 变现加速期
  Three tactics:
    产品 / 课程
    品牌合作
    Build in Public

Cards have slightly rounded corners, equal height, and generous internal padding.
Number labels at top of each card are in a slightly smaller bold font.
Stage names are prominently displayed in the middle of each card.
Tactics are listed below the stage name in smaller regular font.
"""
    },
    {
        "filename": "fig6-1-monetization-compare.png",
        "chapter":  "第六章",
        "caption":  "X 四大变现方式对比",
        "prompt": STYLE + """
Create a BUBBLE SCATTER CHART titled "X 四大变现方式对比" comparing 4 monetization methods.

Chart title (bold, centered top): X 四大变现方式对比
Footnote (bottom-right, small gray): * 数据基于中文推特圈观察，供参考

Axes:
  X-axis label: 入门门槛（粉丝量 / 资源要求）
  Y-axis label: 收入天花板（旋转90度竖排）
  Both axes: scale 1 to 5 (no numbers, use text labels)
  X-axis tick labels (left to right): 极低  低  中  高  极高
  Y-axis tick labels (bottom to top): 极低  低  中  高  极高

4 data points (bubbles):
  品牌合作 / 广告    : x=3 (中), y=4 (高),  bubble size=large,   color=#1A1A1A (black)
  知识产品 / 课程    : x=2 (低), y=5 (极高), bubble size=largest, color=#444444 (dark gray)
  官方订阅分成       : x=4 (高), y=2 (低),   bubble size=small,   color=#AAAAAA (light gray)
  咨询服务           : x=2 (低), y=3 (中),   bubble size=medium,  color=#777777 (gray)

Each bubble:
  - Circular shape with white edge/stroke
  - Method name label displayed near the bubble (avoid overlap)
  - Labels in Chinese, font size proportional to bubble

Chart area: clean grid with light gray dotted gridlines
Top and right spines removed
"""
    },
]

# ── 生成函数 ─────────────────────────────────────────────────────────────────
def generate_image(chart: dict) -> bool:
    filename = chart["filename"]
    out_path = OUT_DIR / filename
    print(f"\n{'─'*60}")
    print(f"生成中：{filename}  ({chart['chapter']} · {chart['caption']})")
    print(f"{'─'*60}")

    try:
        response = client.images.generate(
            model=MODEL,
            prompt=chart["prompt"],
            n=1,
            size=SIZE,
            quality=QUALITY,
        )

        # gpt-image-1 返回 base64
        img_b64 = response.data[0].b64_json
        if img_b64:
            img_bytes = base64.b64decode(img_b64)
        else:
            # 也可能返回 url
            import urllib.request
            img_bytes = urllib.request.urlopen(response.data[0].url).read()

        # 可选：用 Pillow 转换为 PNG 并压缩
        if HAS_PIL:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img.save(out_path, "PNG", optimize=True)
        else:
            out_path.write_bytes(img_bytes)

        size_kb = out_path.stat().st_size // 1024
        print(f"✓ 已保存：{out_path}  ({size_kb} KB)")
        return True

    except Exception as e:
        print(f"✗ 生成失败：{e}")
        return False


# ── 主流程 ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("X 运营增长完全手册 — 图表生成脚本")
    print(f"模型：{MODEL}  |  尺寸：{SIZE}  |  质量：{QUALITY}")
    print(f"输出目录：{OUT_DIR.resolve()}")
    print("=" * 60)

    # 支持只生成特定图表：python3 generate_charts.py fig1-1 fig3-1
    targets = sys.argv[1:] if len(sys.argv) > 1 else []

    ok, fail = 0, 0
    for chart in CHARTS:
        if targets and not any(t in chart["filename"] for t in targets):
            print(f"跳过：{chart['filename']}")
            continue

        success = generate_image(chart)
        if success:
            ok += 1
        else:
            fail += 1

        # 避免速率限制
        if ok + fail < len(CHARTS):
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"完成！成功 {ok} 张，失败 {fail} 张")
    print(f"图片保存在：{OUT_DIR.resolve()}")
    if ok > 0:
        print("\n下一步：把生成的 images/ 文件夹告诉 Cowork，")
        print("它会自动将图片打包进 EPUB。")
    print("=" * 60)


if __name__ == "__main__":
    main()
