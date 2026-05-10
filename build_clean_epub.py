#!/usr/bin/env python3
import html
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_EPUB_DIR = ROOT / "epub_analysis"
BUILD_DIR = ROOT / "epub_clean_build"
OUT_EPUB = ROOT / "X运营增长完全手册-排版优化版.epub"

BOOK_TITLE = "X（推特）运营增长完全手册"
AUTHOR = "从零开始的yann"

CHAPTERS = [
    ("ch002.xhtml", ROOT / "第01章-认知篇" / "第01章-认知篇.md"),
    ("ch003.xhtml", ROOT / "第02章-定位篇" / "第02章-定位篇.md"),
    ("ch004.xhtml", ROOT / "第03章-内容篇" / "第03章-内容篇.md"),
    ("ch005.xhtml", ROOT / "第04章-工具篇" / "第04章-工具篇.md"),
    ("ch006.xhtml", ROOT / "第05章-增长篇" / "第05章-增长篇.md"),
    ("ch007.xhtml", ROOT / "第06章-变现篇" / "第06章-变现篇.md"),
    ("ch008.xhtml", ROOT / "第07章-账号安全篇" / "第07章-账号安全篇.md"),
    ("ch009.xhtml", ROOT / "第08章-心态篇" / "第08章-心态篇.md"),
]

FIGURES = {
    "ch002.xhtml": {
        "第一节：基因之别——X 与国内主流平台的底层逻辑": ("file0.png", "四大平台核心特征对比"),
        "2. 互动权重：哪些行为最值钱": ("file1.png", "X 算法互动行为权重示意"),
    },
    "ch004.xhtml": {
        "第三节：Thread 的写作公式": ("file2.png", "Thread 标准结构示意"),
    },
    "ch006.xhtml": {
        "第一节：冷启动——0 到 500 粉的最有效路径": ("file3.png", "X 账号增长阶段路径"),
    },
    "ch007.xhtml": {
        "第一节：X 上的主要变现方式": ("file4.png", "四种变现方式对比"),
    },
}


def slug(text: str) -> str:
    s = re.sub(r"\s+", "-", text.strip().lower())
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "", s)
    return s.strip("-") or "section"


def inline_markup(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def flush_paragraph(out, parts):
    if parts:
        out.append(f"<p>{inline_markup(' '.join(parts))}</p>")
        parts.clear()


def parse_case(lines, i, out):
    # Current line is the opening --- and the next meaningful line is a case title.
    i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    title = re.sub(r"^\*\*|\*\*$", "", lines[i].strip())
    title = title.replace("📌 ", "")
    body = []
    i += 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i].strip()
        if line:
            body.append(line)
        else:
            body.append("")
        i += 1

    out.append('<div class="case-box">')
    out.append(f'<p class="box-title">{inline_markup(title)}</p>')
    para = []
    for line in body:
        if not line:
            flush_paragraph(out, para)
        else:
            para.append(line)
    flush_paragraph(out, para)
    out.append("</div>")
    return i + 1


def parse_markdown(md: str, filename: str):
    lines = md.splitlines()
    out = []
    toc = []
    para = []
    in_ul = False
    i = 0
    h1 = BOOK_TITLE

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            flush_paragraph(out, para)
            if in_ul:
                out.append("</ul>")
                in_ul = False
            i += 1
            continue

        if line == "---":
            next_nonblank = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_nonblank = lines[j].strip()
            flush_paragraph(out, para)
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if next_nonblank.startswith("**📌 案例"):
                i = parse_case(lines, i, out)
                continue
            # Decorative separators in the manuscript become spacing, not visible rules.
            i += 1
            continue

        if line.startswith(">"):
            flush_paragraph(out, para)
            if in_ul:
                out.append("</ul>")
                in_ul = False
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = lines[i].strip()[1:].strip()
                if q:
                    quote.append(q)
                i += 1
            klass = "tip-box" if quote and "运营要点" in quote[0] else "note-box"
            out.append(f'<blockquote class="{klass}">')
            if quote:
                out.append(f'<p class="box-title">{inline_markup(quote[0]).replace("💡 ", "")}</p>')
                for q in quote[1:]:
                    out.append(f"<p>{inline_markup(q)}</p>")
            out.append("</blockquote>")
            continue

        if line.startswith("# "):
            flush_paragraph(out, para)
            if in_ul:
                out.append("</ul>")
                in_ul = False
            h1 = line[2:].strip()
            out.append(f'<h1 id="{slug(h1)}">{inline_markup(h1)}</h1>')
            i += 1
            continue

        if line.startswith("## "):
            flush_paragraph(out, para)
            if in_ul:
                out.append("</ul>")
                in_ul = False
            title = line[3:].strip()
            sid = slug(title)
            toc.append((2, title, sid))
            out.append(f'<h2 id="{sid}">{inline_markup(title)}</h2>')
            maybe_figure = FIGURES.get(filename, {}).get(title)
            if maybe_figure:
                img, cap = maybe_figure
                out.append(figure_html(img, cap))
            i += 1
            continue

        if line.startswith("### "):
            flush_paragraph(out, para)
            if in_ul:
                out.append("</ul>")
                in_ul = False
            title = line[4:].strip()
            sid = slug(title)
            toc.append((3, title, sid))
            out.append(f'<h3 id="{sid}">{inline_markup(title)}</h3>')
            maybe_figure = FIGURES.get(filename, {}).get(title)
            if maybe_figure:
                img, cap = maybe_figure
                out.append(figure_html(img, cap))
            i += 1
            continue

        if line.startswith("- "):
            flush_paragraph(out, para)
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_markup(line[2:].strip())}</li>")
            i += 1
            continue

        if in_ul:
            out.append("</ul>")
            in_ul = False

        para.append(line)
        i += 1

    flush_paragraph(out, para)
    if in_ul:
        out.append("</ul>")
    return h1, toc, "\n".join(out)


def figure_html(img, caption):
    return (
        '<figure>\n'
        f'  <img src="../media/{img}" alt="{html.escape(caption)}" />\n'
        f'  <figcaption>{html.escape(caption)}</figcaption>\n'
        '</figure>'
    )


def page(title, body, body_type="bodymatter"):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet1.css" />
</head>
<body epub:type="{body_type}">
<section>
{body}
</section>
</body>
</html>
'''


def write_stylesheet():
    css = r'''/* X 增长手册 · clean EPUB stylesheet */
html {
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC", "SimSun", serif;
  font-size: 1em;
  line-height: 1.72;
  color: #202124;
  margin: 0;
  padding: 0;
  word-break: normal;
}

section {
  max-width: 42em;
  margin: 0 auto;
}

h1, h2, h3, .box-title {
  font-family: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Heiti SC", sans-serif;
  page-break-after: avoid;
  break-after: avoid;
}

h1 {
  font-size: 1.8em;
  line-height: 1.32;
  font-weight: 700;
  margin: 2.1em 0 1.15em;
  padding-bottom: 0.45em;
  border-bottom: 1px solid #d9dde3;
  letter-spacing: 0;
}

h2 {
  font-size: 1.28em;
  line-height: 1.42;
  font-weight: 700;
  margin: 2.15em 0 0.75em;
  padding-left: 0.7em;
  border-left: 3px solid #2f6f73;
  color: #152f32;
}

h3 {
  font-size: 1.06em;
  line-height: 1.45;
  font-weight: 700;
  margin: 1.45em 0 0.45em;
  color: #263238;
}

p {
  margin: 0 0 0.78em;
  text-align: justify;
  text-justify: inter-ideograph;
  orphans: 2;
  widows: 2;
}

ul, ol {
  margin: 0.35em 0 1em 1.25em;
  padding: 0;
}

li {
  margin: 0 0 0.45em;
  line-height: 1.68;
}

strong {
  font-weight: 700;
  color: #111827;
}

em {
  color: #5c6670;
  font-style: italic;
}

figure {
  margin: 1.2em 0 1.35em;
  page-break-inside: avoid;
  break-inside: avoid;
}

img {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 0 auto;
}

figcaption {
  margin-top: 0.45em;
  color: #6b7280;
  font-size: 0.86em;
  line-height: 1.45;
  text-align: center;
}

blockquote,
.case-box {
  margin: 1.2em 0 1.35em;
  padding: 0.85em 1em;
  border-radius: 6px;
  page-break-inside: avoid;
  break-inside: avoid;
}

blockquote p,
.case-box p {
  margin: 0.35em 0;
}

.tip-box {
  border-left: 4px solid #2f6f73;
  background: #eef7f6;
  color: #213f42;
}

.note-box {
  border-left: 4px solid #8a6f2a;
  background: #fbf7ea;
  color: #403821;
}

.case-box {
  border: 1px solid #d9dde3;
  background: #f7f8fa;
}

.box-title {
  font-size: 0.96em;
  font-weight: 700;
  margin-bottom: 0.5em !important;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.2em 0;
  font-size: 0.9em;
}

th {
  background: #eef0f2;
  color: #1f2933;
  padding: 0.5em 0.65em;
  text-align: left;
  font-weight: 700;
}

td {
  padding: 0.5em 0.65em;
  border-bottom: 1px solid #e1e5ea;
  vertical-align: top;
}

code {
  font-family: "Menlo", "Consolas", monospace;
  font-size: 0.88em;
  background: #f1f3f5;
  padding: 0.08em 0.28em;
  border-radius: 3px;
}

.titlepage {
  text-align: center;
  margin-top: 22%;
}

.titlepage .title {
  border-bottom: none;
  margin-bottom: 0.45em;
}

.titlepage .subtitle,
.titlepage .author,
.titlepage .rights {
  text-align: center;
  color: #5c6670;
}

#cover-image svg {
  width: 100%;
  height: auto;
}
'''
    (BUILD_DIR / "EPUB" / "styles" / "stylesheet1.css").write_text(css, encoding="utf-8")


def write_ch001():
    body = f'''
<h1 id="x推特运营增长完全手册">{BOOK_TITLE}</h1>
<p><strong>中文创作者的系统化运营指南</strong></p>
<p>逻辑主线：认知 → 定位 → 内容 → 工具 → 增长 → 变现 → 安全 → 心态</p>
<p>适合人群：有一定网感、想在 X 平台系统化运营的中文用户</p>
<blockquote class="note-box">
  <p>本书涉及平台功能、算法机制及第三方工具的描述，均基于撰写时的情况。X 平台持续迭代，建议读者结合最新官方信息核实相关内容。</p>
</blockquote>
'''
    (BUILD_DIR / "EPUB" / "text" / "ch001.xhtml").write_text(page(BOOK_TITLE, body), encoding="utf-8")


def write_cover_fix():
    cover = BUILD_DIR / "EPUB" / "text" / "cover.xhtml"
    text = cover.read_text(encoding="utf-8")
    text = text.replace('preserveAspectRatio="none"', 'preserveAspectRatio="xMidYMid meet"')
    cover.write_text(text, encoding="utf-8")


def write_nav(chapter_tocs):
    items = ['<li><a href="text/ch001.xhtml#x推特运营增长完全手册">X（推特）运营增长完全手册</a></li>']
    for filename, title, toc in chapter_tocs:
        sub = ""
        h2s = [(t, sid) for level, t, sid in toc if level == 2]
        if h2s:
            sub_items = "\n".join(
                f'<li><a href="text/{filename}#{sid}">{html.escape(t)}</a></li>' for t, sid in h2s
            )
            sub = f"\n<ol>\n{sub_items}\n</ol>"
        items.append(f'<li><a href="text/{filename}#{slug(title)}">{html.escape(title)}</a>{sub}</li>')

    nav = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{BOOK_TITLE}</title>
  <link rel="stylesheet" type="text/css" href="styles/stylesheet1.css" />
</head>
<body>
<nav epub:type="toc" id="toc">
  <h1 id="toc-title">{BOOK_TITLE}</h1>
  <ol class="toc">
    {"".join(items)}
  </ol>
</nav>
<nav epub:type="landmarks" id="landmarks" hidden="hidden">
  <ol>
    <li><a href="text/cover.xhtml" epub:type="cover">Cover</a></li>
    <li><a href="#toc" epub:type="toc">Table of contents</a></li>
  </ol>
</nav>
</body>
</html>
'''
    (BUILD_DIR / "EPUB" / "nav.xhtml").write_text(nav, encoding="utf-8")


def update_modified_time():
    opf = BUILD_DIR / "EPUB" / "content.opf"
    text = opf.read_text(encoding="utf-8")
    text = re.sub(
        r"<meta property=\"dcterms:modified\">[^<]+</meta>",
        "<meta property=\"dcterms:modified\">2026-05-10T00:00:00Z</meta>",
        text,
    )
    opf.write_text(text, encoding="utf-8")


def validate():
    text_files = list((BUILD_DIR / "EPUB" / "text").glob("*.xhtml"))
    problems = []
    for path in text_files:
        text = path.read_text(encoding="utf-8")
        if " ## " in text or "\n##" in text:
            problems.append(f"raw heading marker in {path.name}")
        if path.name.startswith("ch") and path.name != "ch001.xhtml":
            if "<h2" not in text:
                problems.append(f"missing h2 in {path.name}")
    if problems:
        raise RuntimeError("; ".join(problems))
    subprocess.run(["tidy", "-qe", "-xml", "-utf8", *map(str, text_files)], check=False)


def pack_epub():
    if OUT_EPUB.exists():
        OUT_EPUB.unlink()
    subprocess.run(["zip", "-X0", str(OUT_EPUB), "mimetype"], cwd=BUILD_DIR, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        ["zip", "-Xr9D", str(OUT_EPUB), "META-INF", "EPUB"],
        cwd=BUILD_DIR,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def main():
    if not SOURCE_EPUB_DIR.exists():
        raise SystemExit("Missing epub_analysis directory. Unzip the source EPUB first.")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    shutil.copytree(SOURCE_EPUB_DIR, BUILD_DIR)

    write_stylesheet()
    write_cover_fix()
    write_ch001()

    chapter_tocs = []
    for filename, md_path in CHAPTERS:
        md = md_path.read_text(encoding="utf-8")
        title, toc, body = parse_markdown(md, filename)
        (BUILD_DIR / "EPUB" / "text" / filename).write_text(page(title, body), encoding="utf-8")
        chapter_tocs.append((filename, title, toc))

    write_nav(chapter_tocs)
    update_modified_time()
    validate()
    pack_epub()
    print(OUT_EPUB)


if __name__ == "__main__":
    main()
