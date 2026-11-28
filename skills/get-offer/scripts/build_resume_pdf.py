#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把简历 Markdown 源稿生成 PDF，并自动核验成品。只用 Python 3.8+ 标准库。

用法
  build_resume_pdf.py 源稿.md [--style 样式] [--out 输出.pdf] [--final [--sample]] [--max-pages N] [--font 字体名] [--lang 语言]
  build_resume_pdf.py --html 已填好的页面.html [--source 源稿.md] [--out 输出.pdf] [--final [--sample]]
  build_resume_pdf.py --check-pdf 某.pdf [--source 源稿.md] [--final [--sample]] [--max-pages N]

  默认在源稿旁生成同名 .pdf；模板默认取本脚本旁的 ../assets/resume-navy.html（墨蓝商务）。
  --style 换自带样式：classic 经典单栏、cobalt 钴蓝边栏、cinnabar 朱砂时间轴、pine 松绿成果版、
  paper 暖纸书刊（也可写中文名或编号 1 到 5）。换样式只改排法，文字和每条经历的对应关系不变；
  非默认样式的默认文件名是“源稿名-样式名.pdf”，不覆盖墨蓝商务那份。--check-pdf 复检这类 PDF
  要加同一个 --style（成果版旁边的数字、边栏的先后要按样式核对）；--html 页面自带样式信息。
  成果版只把原句已有、含义明确的结果（有前后值的变化、幅度、促成或覆盖的数量）放到经历旁，
  访谈、回看、整理等过程数字不算；一段经历没有就不放。
  --out、--save-html 不能和源稿、模板、--html 页面或彼此是同一个文件（大小写不同、硬链接、
  符号链接也算），否则不运行（退出码 2）。
  页面语言：源稿几乎没有中文时按英文处理（lang="en"，文档标题以“Resume”结尾），--lang 可以指定。
  三种稿子怎么跑：初稿和待补稿什么都不加；真实投递稿加 --final；
  演练稿（虚构材料）的最终版加 --final --sample。
  间距：先按模板的标准间距排；页数超过 --max-pages 时自动换成模板的紧凑间距再排一次，
  字号不变，结果里写明用了哪一档。--density standard 或 compact 可以固定一档。
  浏览器查找顺序：--browser，环境变量 GETOFFER_BROWSER、CHROME_PATH，
  然后是 Chrome、Edge、Chromium 的常见安装位置和 PATH。

退出码
  0  生成并通过检查（可以有警告）
  1  发现问题，逐条列出“是什么、在哪、怎么修”。这时不写 --out 指向的正式文件：
     打印出的 PDF 另存到系统临时目录（按正式文件路径分开存，不同目录的同名稿互不覆盖），
     文件名带“未通过”，只供查看，路径写在结果里；PDF 文字读不出来（加密、结构损坏）也算这一类
  2  无法运行：参数错、文件不存在、找不到浏览器、源稿结构不认识

源稿写法（逐行识别）
  1. 第一个非空行必须是“# 姓名”，全稿只有一个一级标题。
  2. 姓名到第一个“## 栏目”之间是页头，每个非空行单独成一行（不合并）：
     - 第一条不以“>”开头的页头行，如果不含“｜”或“|”、不含“@”、不像电话号码
       （7 位以上数字，中间可夹空格或短横线）且不超过 40 个字符，就是目标岗位，
       显示在姓名右侧；否则没有目标岗位这一项；
     - 其余每行是一行信息行（联系方式、到岗时间等），原样显示；
     - 以“>”开头的行是稿件提示（例如“待补草稿，勿投递”），显示在信息行里并用橙色标出
       （.draft-note），算作草稿提示，不算空位；只在初稿和待补稿里保留。
     页头里不接受列表、表格或其他标题。
  3. “## 栏目名”开始一个栏目。栏目名决定条目头怎么排（英文栏目名不分大小写）：
     - 含“教育”或“Education”：条目头除时间外全部放进标题行，条目下的段落是教育补充信息（.education-detail）；
     - 含“项目”“竞赛”“作品”“科研”“论文”“课题”，或 Project、Competition、Research、
       Publication、Portfolio、Thesis：条目头除时间外全部放进标题行，
       段落是职责范围（.scope）；
     - 其他栏目（实习、工作、校园等任职类）：第一段是公司或组织名（.entry-title），
       其余各段用“｜”连起来放在下一行作实际岗位（.entry-role），段落是职责范围（.scope）。
  4. 条目头两种写法：“### 名称｜岗位或专业｜时间”，或整行以加粗开头的
     “**名称** ｜ 岗位 ｜ 时间”。分隔符用全角“｜”或半角“|”，两侧空格可有可无。
     最后一段含四位年份（19xx 或 20xx）或“至今”“现在”“Present”时当作时间，右对齐；
     否则这个条目没有时间。
  5. “#### 项目名”只能出现在条目里，开始一个项目分组（.project），之后的要点和段落都属于它，
     直到下一个“####”“###”或“##”。
  6. 要点以“- ”开头（也接受“* ”“+ ”）。紧跟在要点后面、不空行也不带符号的行算这条要点的续行。
     要点开头的“**主题**”是主题标签（.theme），后面可以跟“：”“:”、全角空格或直接接正文，
     分隔符原样保留。条目里的普通段落可跨多行，连续的行合并成一段。
  7. 不在条目里的段落和要点（例如技能栏目）按技能段落排（.skills），一条一段，不显示圆点；
     开头的“**主题**”同样加粗。
  8. 单独一行“---”（或“***”“___”）之后是演练稿的虚构标记，只能写普通段落或“>”行，
     放在页面末尾的小字提示里（.sample-notice），外层的“*……*”去掉。标记要写明是演练或虚构材料，
     例如“演练用虚构材料，请勿用于真实投递”；只写“感谢阅读”之类不算。
  9. “[待确认：……]”（冒号全角半角都可）是待补空位，在任何位置都用橙色标出（.pending）并计数。
  10. 反斜杠转义（如“\\*”）按字面输出；要点开头以外的加粗、斜体和行内代码只去掉符号，
      按普通文字输出并给出警告。源稿里的 HTML 一律当普通文字显示，不会成为页面标签。

  以下写法报错并给出行号（退出码 2）：表格、图片、链接“[文字](网址)”、代码块、HTML 注释、
  有序列表、多级或缩进列表、要点下空行后的缩进段落、“#####”及更深的标题、“#”后不空格、
  第二个“# ”、“# 姓名”之前的内容、栏目外的“###”或条目头、条目外的“####”、页头里的列表、
  正文里的“>”引用、“===”或“---”标题下划线、“---”之后的标题或列表、第二条“---”。

成品检查（打印后自动做，--check-pdf 也走同一套）
  文件确为 PDF；没有残留的 {{；页数不超过 --max-pages（默认 1）；
  字体 ToUnicode 映射和提取出的文字里没有康熙部首（U+2F00-2FDF）或部首补充（U+2E80-2EFF）字符；
  按 ToUnicode 从内容流提取文字，NFKC 归一后核对源稿每一行（标题的每一段、每条要点）都原样连续出现，
  英文词与词之间的空格也要对上（换行处可以是空格也可以是长词断开）；数字对调、改写、丢字、
  一行挪到别的经历下（先后不同）、条目头公司和岗位对调（时间排在哪都行），或多出源稿没有的文字
  （例如把一条成果多复制给另一段经历，“18”写成“180”或“-18”，“HTML”写成“HTML5”，
  “C”写成“C++”）都算问题；页头各行先后不限；
  只有要点符号、分隔符、“个人简历”这类页眉，以及页脚里整行的页码不算多出：
  PDF 里是离上下纸边 2 cm 以内、整行只有页码的那一行，HTML 里是 <footer>、position:fixed 或页码类名里的字；
  自定义模板自带的固定文字可以不出现，出现时只能出现一次、不能只剩半截，
  --html、--check-pdf 复检时要用 --template 指定同一份模板；
  单页稿文字只到页面不足 3/4 时提示可能没写满；多页稿末页只有几行时提示。
  --final 另查：正文至少有一个栏目且没有空栏目；没有待补空位（橙色标记和普通文字里的都算）、
  没有草稿提示和虚构标记、页面文字里没有样式名、事实编号（E001-F02）等内部标签，单独的 E101 这类只提醒；
  从源稿、--html 页面和 PDF 文字层三处查，入口不同规则相同；
  “演练”“示例”这类也可能出现在真实经历里的词只提醒，不算问题。
  --final --sample 用于演练稿的最终版：空位、草稿提示和内部标签照查，“---”之后的虚构标记
  必须保留并写明是演练或虚构材料，PDF 文字层里也要找得到这句提示（没有反而算问题）；
  只核验 PDF 时 --final --sample 必须带 --source（看不到源稿就判断不了是不是演练稿）；
  --final 时页面里有“请勿投递”“均为虚构”“Fictional resume”这类声明，或单独成句的“Do not submit.”算问题，
  经历里的“组织应急演练用时 30 分钟”“设计虚构人物”“who do not submit their forms”不算；
  虚构提示要写明是虚构或只供练习，“Thank you for reviewing my writing samples”不算；
  通过后仍是演练稿，结果里写明不能用于真实投递。
  文字层出现部首且没有指定 --font 时，自动换候选中文字体重试，最多 3 次。
  PDF 文字读不出来（加密、结构损坏）时算问题（退出码 1），正式稿检查标为未做，不给通过。
"""

import argparse
import hashlib
import html as htmllib
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import unicodedata
import zlib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

EXIT_OK = 0
EXIT_PROBLEM = 1
EXIT_CANNOT_RUN = 2

ASSETS = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_TEMPLATE = ASSETS / "resume-navy.html"
# 可选样式：(英文名, 模板文件, 中文名, 编号)。编号 0 是默认的墨蓝商务。
STYLES = (
    ("navy", "resume-navy.html", "墨蓝商务", 0),
    ("classic", "resume-classic.html", "经典单栏", 1),
    ("cobalt", "resume-cobalt.html", "钴蓝边栏", 2),
    ("cinnabar", "resume-cinnabar.html", "朱砂时间轴", 3),
    ("pine", "resume-pine.html", "松绿成果版", 4),
    ("paper", "resume-paper.html", "暖纸书刊", 5),
)


def find_style(value):
    """按英文名、中文名或编号找样式，返回 (英文名, 模板路径, 中文名)；找不到抛 CannotRun。"""
    key = (value or "").strip().lower()
    for sid, fname, cname, num in STYLES:
        if key in (sid, cname.lower(), str(num), "第%d套" % num, "第 %d 套" % num):
            return sid, ASSETS / fname, cname
    raise CannotRun("没有这个样式：%s" % value, hint="可选：" + "；".join(
        "%s（%s，编号 %d）" % (cname, sid, num) for sid, _, cname, num in STYLES))
BROWSER_ENV_VARS = ("GETOFFER_BROWSER", "CHROME_PATH")

PENDING_RE = re.compile(r"\[待确认[：:][^\[\]]*\]")
RADICAL_RANGES = ((0x2F00, 0x2FDF), (0x2E80, 0x2EFF))
SEP_RE = re.compile(r"\s*[｜|]\s*")
DATE_RE = re.compile(r"(?:19|20)\d{2}|至今|现在|\b(?:Present|present|Now|now)\b")
PHONE_RE = re.compile(r"(?:\d[\s\-]?){7,}")
EDU_WORDS = ("教育", "education")
PROJECT_WORDS = ("项目", "竞赛", "作品", "科研", "论文", "课题",
                 "project", "competition", "research", "publication", "portfolio", "thesis")
ASCII_PUNCT = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

# 自动重试用的候选字体。macOS 一项实测过（Chrome 打印）：苹方、冬青黑体、黑体-简、宋体-简、楷体-简
# 的文字层都会出现部首字符，所以不放进来；Windows、Linux 两项按常见字体给出，未在本机实测。
FONT_CANDIDATES = {
    "darwin": ["Arial Unicode MS", "STHeiti"],
    "win32": ["Microsoft YaHei", "DengXian", "SimHei"],
    "linux": ["Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei"],
}

STYLE_NAMES = tuple(cname for _, _, cname, _ in STYLES)
# 正式稿里任何位置都不该出现的技术痕迹与模板标记；样式名按“独立标签或模板额外印出”单独判断，不误拦真实经历词组。
INTERNAL_LABELS = (
    "resume-section", "entry-title", "entry-date", "entry-role",
    "education-detail", "project-title", "sample-notice", "draft-note",
    "getoffer-layout", "getoffer-style", 'class="', "{{", "}}",
)
# 待补稿才会写的说法，任何正式稿里都算问题。源稿的标记已经单独报过时不再重复报。
DRAFT_PHRASES = ("待补草稿", "待补稿")
# 声明整份材料是演练稿的说法（不分大小写、忽略空白）：真实投递稿里算问题，--sample 的演练稿里本来就该有，不查。
# 只收指向“这份材料”的整句式声明。经历里的“组织应急演练用时 30 分钟”“设计虚构人物”
# “提醒没有 do not submit 表单的用户”都不算；拿不准的词只提醒（见 DRAFT_HINT_WORDS）。
SAMPLE_PHRASES = ("勿投递", "勿用于真实投递", "不能用于真实投递", "请勿用于投递", "仅供演练", "仅供练习",
                  "均为虚构", "纯属虚构", "虚构简历", "演练用虚构", "演练用材料", "fictional resume",
                  "fictitious resume", "resume is fictional", "not for real applications", "for practice only",
                  "do not submit this resume", "do not use for real applications")
# 真实经历里也可能出现的词（应急演练、示例代码、TODO 应用），只提醒，由人判断。
DRAFT_HINT_WORDS = ("待确认", "待补", "演练", "虚构", "示范", "示例", "占位符", "墨蓝", "TODO", "TBD",
                    "fictional", "do not submit")
SAMPLE_HINT_WORDS = ("演练", "虚构")
# 已经确定是末尾的虚构提示（源稿“---”之后或 .sample-notice）时，写“演练”“虚构”也够说明。
# 只写“感谢阅读”这类不算。
# 要说明材料是虚构的或只供练习；“Thank you for reviewing my writing samples”这类不算。
NOTICE_MARK_WORDS = SAMPLE_PHRASES + ("演练", "虚构", "练习用", "模拟材料", "示例材料", "fictional", "fictitious",
                                      "for practice", "practice only", "practice material", "mock resume",
                                      "sample resume")
SAMPLE_MARK_EXAMPLE = "演练用虚构材料，请勿用于真实投递"
DENSITY_NAMES = {"standard": "标准", "compact": "紧凑"}
# 经历库的事实编号（E001-F02）一定是内部标签；单独的 E001 也可能是真实的型号或故障码（E101），只提醒。
FACT_ID_RE = re.compile(r"(?<![A-Za-z0-9])E\d{3}-F\d{2}(?![0-9])")
EXP_ID_RE = re.compile(r"(?<![A-Za-z0-9-])E\d{3}(?![0-9]|-F\d)")


class CannotRun(Exception):
    """无法运行（退出码 2）。details 是逐条说明。"""

    def __init__(self, message, details=None, hint=None):
        Exception.__init__(self, message)
        self.message = message
        self.details = details or []
        self.hint = hint


class Report(object):
    def __init__(self):
        self.checks = []
        self.problems = []
        self.warnings = []
        self.facts = []

    def check(self, status, name, detail):
        self.checks.append((status, name, detail))

    def problem(self, what, where, fix):
        self.problems.append((what, where, fix))

    def warn(self, text):
        if text not in self.warnings:
            self.warnings.append(text)

    def fact(self, label, value):
        self.facts.append((label, value))


# ---------------------------------------------------------------------------
# Markdown 源稿解析
# ---------------------------------------------------------------------------

class Resume(object):
    def __init__(self):
        self.name = ""
        self.name_line = 0
        self.target_role = None
        self.meta = []          # (kind, text, lineno)，kind 为 "line" 或 "note"
        self.sections = []
        self.notices = []       # (text, lineno)，--- 之后的演练标记
        self.warnings = []


class Section(object):
    def __init__(self, title, lineno):
        self.title = title
        self.lineno = lineno
        low = title.lower()
        if any(w in low for w in EDU_WORDS):
            self.kind = "education"
        elif any(w in low for w in PROJECT_WORDS):
            self.kind = "project"
        else:
            self.kind = "job"
        self.items = []         # 栏目级的 ["para"|"bullet", text, lineno] 与 Entry 对象


class Entry(object):
    def __init__(self, parts, lineno):
        self.parts = parts
        self.lineno = lineno
        self.items = []         # ["para"|"bullet", text, lineno] 与 Project 对象


class Project(object):
    def __init__(self, title, lineno):
        self.title = title
        self.lineno = lineno
        self.items = []


def is_wide(ch):
    return unicodedata.east_asian_width(ch) in ("W", "F")


def join_text(a, b):
    if not a:
        return b
    if not b:
        return a
    if is_wide(a[-1]) or is_wide(b[0]):
        return a + b
    return a + " " + b


HEADING_RE = re.compile(r"^(#+)(\s+|$)(.*)$")
BULLET_RE = re.compile(r"^([-*+])\s+(.*)$")
ORDERED_RE = re.compile(r"^\d{1,3}[.)](\s|$)")
HR_RE = re.compile(r"^([-*_])(?:\s*\1){2,}$")
BOLD_ENTRY_RE = re.compile(r"^\*\*([^*]+?)\*\*\s*[｜|]\s*(.+)$")
LINK_RE = re.compile(r"(?<!\\)\[[^\]]*\]\([^)]*\)")
SETEXT_RE = re.compile(r"^=+$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")


def split_heading(text):
    return [p for p in (s.strip() for s in SEP_RE.split(text.strip())) if p]


def parse_markdown(text):
    """解析源稿，返回 Resume。结构不认识时抛 CannotRun（带行号）。"""
    res = Resume()
    errors = []
    lines = text.splitlines()
    state = {"stage": "before", "section": None, "entry": None, "project": None,
             "para": [], "bullet": None, "blank": True}

    def err(ln, msg):
        errors.append("第 %d 行：%s" % (ln, msg))

    def container():
        return state["project"] or state["entry"] or state["section"]

    def flush():
        para = state["para"]
        if para:
            joined = ""
            for t, _ in para:
                joined = join_text(joined, t)
            ln = para[0][1]
            if state["stage"] == "trailer":
                res.notices.append((joined, ln))
            else:
                container().items.append(["para", joined, ln])
            state["para"] = []

    for ln, raw in enumerate(lines, 1):
        line = raw.replace("\t", "    ").rstrip()
        s = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if ln == 1:
            s = s.lstrip("\ufeff")
        if not s:
            flush()
            state["bullet"] = None
            state["blank"] = True
            continue
        was_blank = state["blank"]
        state["blank"] = False
        stage = state["stage"]

        # 任何位置都不认识的结构
        if s.startswith("```") or s.startswith("~~~"):
            err(ln, "代码块不认识，请改成普通段落或要点")
            continue
        if s.startswith("<!--"):
            err(ln, "HTML 注释不认识，注释里的内容不会进简历，请删除或改成正文")
            continue
        if s.startswith("|") or TABLE_SEP_RE.match(s):
            err(ln, "表格不认识，请改成条目和要点")
            continue
        if "![" in s and re.search(r"!\[[^\]]*\]\(", s):
            err(ln, "图片不认识，简历正文不放图片")
            continue
        if LINK_RE.search(s):
            err(ln, "链接写法“[文字](网址)”不认识，请直接写出网址文字")
            continue
        if SETEXT_RE.match(s) and not was_blank:
            err(ln, "“===”标题下划线不认识，请用“# ”“## ”写标题")
            continue
        m = HEADING_RE.match(s)
        if s.startswith("#") and not m:
            err(ln, "“#”后面要空一格才是标题")
            continue

        if stage == "trailer":
            if m or BULLET_RE.match(s) or ORDERED_RE.match(s) or HR_RE.match(s):
                err(ln, "“---”之后只能写演练或虚构标记的普通段落；如果把“---”当分隔线用，请删掉它")
                continue
            if s.startswith(">"):
                flush()
                res.notices.append((s.lstrip(">").strip(), ln))
                continue
            state["para"].append((s, ln))
            continue

        if HR_RE.match(s):
            if stage == "before":
                err(ln, "“# 姓名”之前不能有内容")
                continue
            if not was_blank and (state["para"] or stage == "header"):
                prev = lines[ln - 2].strip() if ln >= 2 else ""
                if prev and not prev.startswith("#"):
                    err(ln, "“---”紧贴在文字下面会被当成标题下划线；作演练标记分隔时前面空一行")
                    continue
            flush()
            state["bullet"] = None
            state["stage"] = "trailer"
            continue

        if m:
            level = len(m.group(1))
            title = m.group(3).strip()
            title = re.sub(r"\s+#+$", "", title).strip()
            if not title:
                err(ln, "标题是空的")
                continue
            if level >= 5:
                err(ln, "“%s”级标题太深，只认 # 到 ####" % ("#" * level))
                continue
            if level == 1:
                if stage != "before":
                    err(ln, "只能有一个一级标题（姓名）")
                    continue
                res.name = title
                res.name_line = ln
                state["stage"] = "header"
                continue
            if stage == "before":
                err(ln, "第一个标题必须是“# 姓名”")
                continue
            flush()
            state["bullet"] = None
            if level == 2:
                sec = Section(title, ln)
                res.sections.append(sec)
                state.update(stage="body", section=sec, entry=None, project=None)
            elif level == 3:
                if state["section"] is None:
                    err(ln, "“###”条目要放在某个“## 栏目”下面")
                    continue
                entry = Entry(split_heading(title), ln)
                state["section"].items.append(entry)
                state.update(entry=entry, project=None)
            else:
                if state["entry"] is None:
                    err(ln, "“####”项目分组要放在某个“###”条目下面")
                    continue
                proj = Project(title, ln)
                state["entry"].items.append(proj)
                state["project"] = proj
            continue

        if stage == "before":
            err(ln, "“# 姓名”之前不能有内容")
            continue

        if ORDERED_RE.match(s):
            err(ln, "有序列表（1. 2. 3.）不认识，请改用“- ”要点")
            continue

        bm = BULLET_RE.match(s)
        if stage == "header":
            if bm:
                err(ln, "姓名下面只放目标岗位和信息行（普通文字行），不要用列表")
                continue
            if s.startswith(">"):
                res.meta.append(("note", s.lstrip(">").strip(), ln))
            else:
                res.meta.append(("line", s, ln))
            continue

        # 正文（栏目内）
        if s.startswith(">"):
            err(ln, "正文里的“>”引用不认识；草稿提示请放在姓名下面，演练标记放在末尾“---”之后")
            continue
        if bm:
            if indent >= 2:
                err(ln, "多级或缩进列表不认识，请改成同一级要点")
                continue
            flush()
            item = ["bullet", bm.group(2).strip(), ln]
            container().items.append(item)
            state["bullet"] = item
            continue
        if indent >= 2 and was_blank and state["bullet"] is None:
            prev_items = container().items
            if prev_items and isinstance(prev_items[-1], list) and prev_items[-1][0] == "bullet":
                err(ln, "要点下面空行后的缩进段落不认识，请并进上一条要点或单独成段")
                continue
        if state["bullet"] is not None:
            state["bullet"][1] = join_text(state["bullet"][1], s)
            continue
        if indent >= 4 and was_blank:
            err(ln, "缩进 4 格的内容会被当成代码块，请顶格写")
            continue
        be = BOLD_ENTRY_RE.match(s)
        if be and not state["para"]:
            if state["section"] is None:
                err(ln, "条目头要放在某个“## 栏目”下面")
                continue
            entry = Entry([be.group(1).strip()] + split_heading(be.group(2)), ln)
            state["section"].items.append(entry)
            state.update(entry=entry, project=None)
            continue
        state["para"].append((s, ln))

    flush()
    if not res.name and not errors:
        errors.append("第 1 行：找不到“# 姓名”，源稿第一行应写“# 姓名”")
    if errors:
        raise CannotRun("源稿里有不认识的结构，没有生成 PDF（内容不会被静默丢掉）", errors,
                        "按 --help 里的源稿写法修改这些行；结构确实特殊时，手工填好模板后用 --html 打印")

    first = next((m for m in res.meta if m[0] == "line"), None)
    if first is not None:
        t = first[1]
        if ("｜" not in t and "|" not in t and "@" not in t and not PHONE_RE.search(t)
                and len(t) <= 40):
            res.target_role = (t, first[2])
            res.meta.remove(first)
    return res


# ---------------------------------------------------------------------------
# 行内处理与 HTML 生成
# ---------------------------------------------------------------------------

def _protect_escapes(s):
    return re.sub(r"\\([%s])" % re.escape(ASCII_PUNCT), lambda m: chr(0xE000 + ord(m.group(1))), s)


def _restore_escapes(s):
    return re.sub("[\ue000-\ue07f]", lambda m: chr(ord(m.group(0)) - 0xE000), s)


def _strip_markup(s):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    t = re.sub(r"\*(\S(?:.*?\S)?)\*", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    return t, t != s


def render_inline(text, lineno, warnings, quiet=False):
    """转义后输出；只生成 .pending 一种标签。"""
    protected = _protect_escapes(text)
    out = []
    changed = False
    for i, piece in enumerate(re.split(r"(\[待确认[：:][^\[\]]*\])", protected)):
        if not piece:
            continue
        clean, did = _strip_markup(piece)
        changed = changed or did
        clean = htmllib.escape(_restore_escapes(clean), quote=True)
        out.append('<span class="pending">%s</span>' % clean if i % 2 else clean)
    if changed and not quiet and lineno:
        warnings.append("第 %d 行：去掉了加粗、斜体或代码符号，按普通文字输出（只有要点开头的加粗会保留为主题标签）" % lineno)
    return "".join(out)


THEME_RE = re.compile(r"^\*\*(.+?)\*\*(.*)$")


def render_themed(text, lineno, warnings):
    m = THEME_RE.match(text)
    if not m or not m.group(1).strip():
        return render_inline(text, lineno, warnings)
    return '<span class="theme">%s</span>%s' % (
        render_inline(m.group(1), lineno, warnings), render_inline(m.group(2), lineno, warnings))


LAYOUT_META_RE = re.compile(r"<meta\s+name=\"getoffer-layout\"\s+content=\"([^\"]*)\"", re.I)
STYLE_META_RE = re.compile(r"<meta\s+name=\"getoffer-style\"\s+content=\"([^\"]*)\"", re.I)


def template_layout(html_text):
    """模板或页面自己声明的版式开关（<meta name="getoffer-layout">），没有就是墨蓝商务的默认排法。

    inline：公司和岗位同一行；timeline：日期在左栏、有日期才画时间节点；metrics：经历旁放一个成果数字；
    aside：教育和技能放进侧栏（模板里的 {{aside}}）；footer：结尾连着的教育、技能并成两栏；
    key-bold：要点里的成果原句加粗；num-accent：要点里的数字换强调色；split-meta：信息行按“｜”拆开。
    """
    m = LAYOUT_META_RE.search(html_text or "")
    return frozenset(m.group(1).split()) if m else frozenset()


def template_style_name(html_text):
    m = STYLE_META_RE.search(html_text or "")
    return m.group(1) if m else ""


# ---- 成果识别：只认原句里已有、含义明确且实际达成的结果；过程数据、未达目标和无法完整识别的数值都不算
_MAG = r"(?:千万|百万|十万|万|千|亿)"
_BASE_UNIT = (r"(?:个百分点|百分点|小时|分钟|人次|个月|%|％|秒|天|周|月|年|人|名|位|条|个|次|题|笔|单|家|元|"
              r"件|篇|份|项|倍|所|场|ms|MB|GB|s|h)")
_UNIT = r"(?:" + _MAG + r"\s*" + _BASE_UNIT + r"|" + _MAG + r"|" + _BASE_UNIT + r")"
_DIGITS = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_NUM = _DIGITS + r"(?:\s*" + _UNIT + r")?"
_QUAL = r"(?:约|近|超过|超|逾)?\s*"
_UP_DOWN = r"(?:提升|提高|增长|增加|上升|增|涨|升|降低|下降|减少|缩短|压缩|降)"
_OUTCOME = (r"(?:促成|达成|实现|带来|获得|获|节省|节约|覆盖|新增|带动|拿下|签约|吸引|获客|服务|产生|贡献|售出|卖出|"
            r"成交|回收|筹得|募集|转化)")
PROCESS_WORDS = ("访谈", "调研", "回看", "整理", "收集", "梳理", "阅读", "抽查", "抽取", "抽样", "标注", "复测", "对比",
                 "走访", "问卷", "分析", "测试", "盘点", "统计", "撰写", "编写", "绘制", "画了", "画出")
CLAUSE_SPLIT_RE = re.compile(r"[，；;。！!？?]|(?<!\d),|,(?!\d)")
CHANGE_RE = re.compile(r"(?P<subj>[^，,；;。、！!？?（）()]{1,20}?)\s*(?P<q>" + _QUAL + r")(?:由|从)\s*(?P<a>" + _NUM +
                       r")\s*" + _UP_DOWN + r"(?:到|至)\s*(?P<b>" + _NUM + r")")
RATE_RE = re.compile(r"(?P<subj>[^，,；;。、！!？?（）()]{1,20}?)\s*(?P<verb>" + _UP_DOWN + r"|节省|节约)了?\s*(?P<v>" + _QUAL +
                     _DIGITS + r"\s*(?:%|％|个百分点|百分点|倍))")
OUTCOME_RE = re.compile(r"(?P<pre>[^，,；;。、！!？?（）()]{0,10}?)(?P<verb>" + _OUTCOME + r")了?\s*(?P<v>" + _QUAL +
                        _DIGITS + r"\s*" + _UNIT + r")(?P<noun>[\u4e00-\u9fff]{0,4})")
LEAD_WORDS_RE = re.compile(r"^(?:并且|并|使得|使|让|将|把|最终|最后|随后|后|同时|推动|帮助|令|从而|进而|其中|且)+")
ACTUAL_WORD_RE = re.compile(r"实际|实测|最终|现已")
ACTUAL_LEAD_RE = re.compile(
    r"^(?:但|而|不过)?\s*(?:目前|现已|最终|最后)?\s*(?:实际|实际上|实测)?(?:上|已|已经|仅|只)?\s*(?:将|把|使|让)?\s*"
)
TARGET_NOUN_RE = re.compile(r"目标(?:用户|人群|客群|客户|市场|院校|企业|商家|读者|受众|岗位|群体|场景|渠道)")
ACHIEVED_PLAN_RE = re.compile(r"(?:达成|完成|实现|超额|超越|突破)[^，,；;。]{0,6}(?:目标|计划|预期)")
PLAN_LEFT_RE = re.compile(r"(?:目标|计划|预计|预期|期望|希望|力争|拟将|拟把|拟于|旨在|假设|设想|待验证|尚未|未达)")
UNMET_RIGHT_RE = re.compile(
    r"(?:是|为|系|属|作为)[^，,；;。]{0,8}(?:目标|计划|预期|设想)"
    r"|[（(][^）)]{0,8}(?:目标|计划|预计|预期|设想|待验证)"
    r"|(?:尚未|未达成|未完成|未实现|未上线|未落地|未达标|未达预期|暂未|待验证|待上线|进行中)"
)
UNMET_NEXT_RE = re.compile(r"(?:尚未|未达成|未完成|未实现|未上线|未落地|未达标|未达预期|暂未)")
PLAN_SUBJ_RE = re.compile(r"^.*?(?:目标|计划|预计|预期|期望|希望|力争|拟|旨在|设想)(?:是|为)?(?:将|把|使|让)?\s*")
PLAN_CLAUSE_SUBJ_RE = re.compile(
    r"(?:目标|计划|预计|预期|期望)(?:是|为)?(?:将|把|使|让)\s*([\u4e00-\u9fffA-Za-z]{2,12}?)"
    r"(?=\s*(?:从|由|" + _UP_DOWN + r"|控制在|达|到))"
)
TRUNCATED_TAIL_RE = re.compile(
    r"^[\d.,+%％/~\-—–+$¥￥€£A-Za-z]"
    r"|^\s*(?:余|多|美[元金]|港元|港币|欧元|日元|英镑)"
)


class Result(object):
    """一句要点里的一个成果：phrase 是原句里的那一段（经典单栏加粗它），value、label 是成果版旁边显示的数字和说明。"""

    def __init__(self, kind, phrase, value, label, rank):
        self.kind, self.phrase, self.value, self.label, self.rank = kind, phrase, value, label, rank


def _clean_label(text):
    text = LEAD_WORDS_RE.sub("", (text or "").strip())
    return re.sub(r"\s+", " ", text).strip(" ：:，,")


def _has_unit(num_text):
    return bool(re.sub(r"[\d,.\s]+", "", num_text or ""))


def _complete_match(clause, m, kind):
    """检查匹配到的数值和单位是否完整：数值前后被截断或前后单位缺失时不生成残缺成果块。"""
    num_group = "a" if kind == "change" else "v"
    before = clause[:m.start(num_group)].rstrip()
    if before and before[-1] in "-−+~$¥￥€£.,0123456789":
        return False
    if kind == "change":
        before_b = clause[:m.start("b")].rstrip()
        if before_b and before_b[-1] in "-−+~$¥￥€£.,0123456789":
            return False
        a_unit, b_unit = _has_unit(m.group("a")), _has_unit(m.group("b"))
        if a_unit and not b_unit:
            return False
        if not b_unit and clause[m.end():].strip():
            return False
        tail = clause[m.end():]
    else:
        tail = clause[m.end("v"):]
    return not TRUNCATED_TAIL_RE.search(tail)


def _mask_safe_targets(s):
    s = TARGET_NOUN_RE.sub(lambda m: "〇" * len(m.group(0)), s)
    return ACHIEVED_PLAN_RE.sub(lambda m: "〇" * len(m.group(0)), s)


def _is_unachieved(clause, num_start, match_end, next_clause=""):
    """该数字是否只是目标、预计或尚未达成，而非实际结果。"""
    masked = _mask_safe_targets(clause)
    left = masked[:num_start]
    right = masked[match_end:]
    if PLAN_LEFT_RE.search(left):
        last_plan = max(m.end() for m in PLAN_LEFT_RE.finditer(left))
        if not re.search(r"实际|实测", left[last_plan:]):
            return True
    if UNMET_RIGHT_RE.search(right):
        return True
    if next_clause:
        nxt = _mask_safe_targets(next_clause)
        if UNMET_NEXT_RE.search(nxt) and not re.search(r"实际|实测", nxt):
            return True
    return False


def _resolve_subject(raw_subj, context_subj):
    cleaned = _clean_label(raw_subj)
    if ACTUAL_WORD_RE.search(cleaned):
        stripped = _clean_label(ACTUAL_LEAD_RE.sub("", cleaned))
        return stripped or context_subj
    return cleaned


def _extract_plan_subject(raw_subj):
    cand = _clean_label(PLAN_SUBJ_RE.sub("", (raw_subj or "").strip()))
    if len(squash(cand)) >= 2 and not any(w in cand for w in PROCESS_WORDS):
        return cand
    return ""


def find_results(text):
    """从一句要点（已去掉 Markdown 符号的纯文字）里找成果，按在句中的位置返回。"""
    out = []
    if "待确认" in text:
        return out
    clauses = [c for c in CLAUSE_SPLIT_RE.split(text) if c.strip()]
    context_subj = ""
    for idx, clause in enumerate(clauses):
        next_clause = clauses[idx + 1] if idx + 1 < len(clauses) else ""
        pm = PLAN_CLAUSE_SUBJ_RE.search(_mask_safe_targets(clause))
        if pm:
            cand = _clean_label(clause[pm.start(1):pm.end(1)])
            if len(squash(cand)) >= 2 and not any(w in cand for w in PROCESS_WORDS):
                context_subj = cand
        found = []
        for m in CHANGE_RE.finditer(clause):
            if not _complete_match(clause, m, "change"):
                continue
            if _is_unachieved(clause, m.start("q"), m.end(), next_clause):
                context_subj = _extract_plan_subject(m.group("subj")) or context_subj
                continue
            label = _resolve_subject(m.group("subj"), context_subj)
            if len(squash(label)) >= 2 and not any(w in label for w in PROCESS_WORDS):
                context_subj = label
                a = (m.group("q").strip() + " " + m.group("a").strip()).strip()
                found.append((m.start("subj") + (len(m.group("subj")) - len(m.group("subj").lstrip())),
                              Result("change", clause[m.start("subj"):m.end()].strip(), "%s → %s" % (a, m.group("b").strip()),
                                     label, 0)))
        if not found:
            for m in RATE_RE.finditer(clause):
                if not _complete_match(clause, m, "rate"):
                    continue
                if _is_unachieved(clause, m.start("verb"), m.end(), next_clause):
                    context_subj = _extract_plan_subject(m.group("subj")) or context_subj
                    continue
                subj = _resolve_subject(m.group("subj"), context_subj)
                label = subj + m.group("verb") if subj else ""
                if len(squash(label)) >= 3 and not any(w in label for w in PROCESS_WORDS):
                    found.append((m.start(), Result("rate", clause[m.start("subj"):m.end()].strip(), m.group("v").strip(),
                                                    label, 1)))
        if not found:
            for m in OUTCOME_RE.finditer(clause):
                if not _complete_match(clause, m, "outcome"):
                    continue
                if _is_unachieved(clause, m.start("verb"), m.end(), next_clause):
                    continue
                pre = clause[:m.start("verb")]
                if any(w in pre for w in PROCESS_WORDS):
                    continue
                pre_clean = _clean_label(ACTUAL_LEAD_RE.sub("", _clean_label(m.group("pre")))) if ACTUAL_WORD_RE.search(
                    m.group("pre")) else _clean_label(m.group("pre"))
                label = pre_clean + m.group("verb") + m.group("noun")
                if len(squash(label)) >= 2:
                    found.append((m.start("verb"), Result("outcome", clause[m.start("verb"):m.end()].strip(),
                                                          m.group("v").strip(), label, 2)))
        out.extend(r for _, r in sorted(found, key=lambda x: x[0]))
    return [r for r in out if r.phrase and r.phrase in text]


def plain_text(t):
    """源稿一行要点去掉 Markdown 符号后的样子，和页面上显示的文字一致。"""
    return _restore_escapes(_strip_markup(_protect_escapes(t))[0])


def entry_bullets(items):
    """条目里的全部要点（含项目分组里的），按源稿顺序给出 (文字, 行号)。"""
    out = []
    for item in items:
        if isinstance(item, Project):
            out.extend(entry_bullets(item.items))
        elif item[0] == "bullet":
            out.append((item[1], item[2]))
    return out


def entry_result(entry):
    """一段经历最有代表性的一个成果：先看有前后值的变化，再看幅度，最后看结果数量；同类取最先出现的。
    返回 (Result, 行号) 或 None。只在本段自己的要点里找，不同经历的数字不会串。"""
    best = None
    for text, ln in entry_bullets(entry.items):
        for r in find_results(plain_text(text)):
            if best is None or r.rank < best[0].rank:
                best = (r, ln)
    return best


def _text_segments(html_text):
    """把一段 HTML 切成 [(是不是文字, 片段)]，待补空位里的文字当作标签，不动。"""
    out, depth = [], 0
    for part in re.split(r"(<[^>]+>)", html_text):
        if not part:
            continue
        if part.startswith("<"):
            if part.startswith('<span class="pending"'):
                depth += 1
            elif part == "</span>" and depth:
                depth -= 1
            out.append((False, part))
        else:
            out.append((depth == 0, part))
    return out


_ENTITY_OR_NUM_RE = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);|(\d+(?:[.,]\d+)?(?:\s?[%％])?)")


def emphasize(html_text, raw, layout):
    """按样式给要点加强调，只改标签不改文字：key-bold 把成果原句加粗，num-accent 把数字换强调色（跳过字符实体）。"""
    if "key-bold" in layout:
        segs = _text_segments(html_text)
        for r in find_results(plain_text(raw)):
            target = htmllib.escape(r.phrase, quote=True)
            for i, (is_text, part) in enumerate(segs):
                if is_text and part.count(target) == 1:
                    segs[i] = (False, part.replace(target, '<strong class="key">%s</strong>' % target))
                    break
        html_text = "".join(p for _, p in segs)
    if "num-accent" in layout:
        html_text = "".join(
            _ENTITY_OR_NUM_RE.sub(lambda m: '<span class="num">%s</span>' % m.group(1) if m.group(1) else m.group(0), p)
            if is_text else p for is_text, p in _text_segments(html_text))
    return html_text


def split_entry_parts(parts):
    parts = list(parts)
    date = None
    if len(parts) >= 2 and DATE_RE.search(parts[-1]) and len(parts[-1]) <= 30:
        date = parts.pop()
    return parts, date


def _render_items(items, para_class, warnings, indent, layout=frozenset()):
    out = []
    pad = " " * indent
    bullets = []

    def close():
        if bullets:
            out.append(pad + '<ul class="points">%s</ul>' % "".join(
                "<li>%s</li>" % emphasize(render_themed(t, ln, warnings), t, layout) for t, ln in bullets))
            del bullets[:]

    for item in items:
        if isinstance(item, Project):
            close()
            out.append(pad + '<div class="project"><p class="project-title">%s</p>' %
                       render_inline(item.title, item.lineno, warnings, quiet=True))
            out.extend(_render_items(item.items, "scope", warnings, indent + 2, layout))
            out.append(pad + "</div>")
        elif item[0] == "bullet":
            bullets.append((item[1], item[2]))
        else:
            close()
            out.append(pad + '<p class="%s">%s</p>' % (para_class, render_inline(item[1], item[2], warnings)))
    close()
    return out


def side_section(sec):
    """侧栏和结尾两栏放的栏目：教育，或只有零散段落、没有条目的栏目（技能、证书）。"""
    return sec.kind == "education" or (sec.items and not any(isinstance(i, Entry) for i in sec.items))


def tail_sections(res):
    """结尾连着的侧栏类栏目（至少两个时才并成两栏）。"""
    tail = []
    for sec in reversed(res.sections):
        if not side_section(sec):
            break
        tail.insert(0, sec)
    return tail if len(tail) >= 2 else []


def aside_sections(res, layout):
    return [sec for sec in res.sections if side_section(sec)] if "aside" in layout else []


def render_sections(res, warnings, layout=frozenset()):
    """返回 (正文栏目, 侧栏栏目) 两段 HTML。墨蓝商务和自定义模板没有版式开关，排法和以前一样。"""
    aside = aside_sections(res, layout)
    tail = tail_sections(res) if "footer" in layout else []
    main_out, side_out = [], []
    for sec in res.sections:
        out = side_out if sec in aside else main_out
        if tail and sec is tail[0]:
            out.append('<div class="tail">')
        _render_section(sec, out, warnings, layout)
        if tail and sec is tail[-1]:
            out.append("</div>")
    return "\n    ".join(main_out), "\n    ".join(side_out)


_TIMELINE_RANGE_RE = re.compile(r"\s+(至今|现在)\s*$|\s*((?:至|到)(?!今)|–|—|~)\s*|\s+(to|-)\s+", re.I)
_TIMELINE_HYPHEN_RE = re.compile(r"-(?=(?:19|20)\d{2}|至今|现在|(?:Present|Now)\b)", re.I)


def _break_timeline_date(shown):
    """时间轴左栏窄，在起止连接符处换行，不拆开 2025-03 这类年月里的连字符，也不把“至今”拆开。"""
    m = _TIMELINE_RANGE_RE.search(shown)
    if m:
        if m.group(1):
            return shown[:m.start()] + "<br>" + m.group(1)
        sep = m.group(2) or m.group(3)
        return shown[:m.start()] + "<br>" + sep + " " + shown[m.end():]
    return _TIMELINE_HYPHEN_RE.sub("<br>- ", shown, count=1)
def _inline_title(parts, warnings, lineno):
    first = '<b>%s</b>' % render_inline(parts[0], lineno, warnings, quiet=True)
    return first + "".join('<span class="entry-sub">%s</span>' % render_inline(p, lineno, warnings, quiet=True)
                           for p in parts[1:])


def _render_section(sec, out, warnings, layout):
    out.append('<section class="resume-section">')
    out.append("  <h2>%s</h2>" % render_inline(sec.title, sec.lineno, warnings, quiet=True))
    loose = []

    def close_loose():
        if loose:
            out.append('  <div class="skills">%s</div>' % "".join(
                "<p>%s</p>" % render_themed(t, ln, warnings) for t, ln in loose))
            del loose[:]

    for item in sec.items:
        if not isinstance(item, Entry):
            loose.append((item[1], item[2]))
            continue
        close_loose()
        parts, date = split_entry_parts(item.parts)
        para_class = "education-detail" if sec.kind == "education" else "scope"
        if "inline" in layout:
            head = '<p class="entry-title">%s</p>' % _inline_title(parts, warnings, item.lineno)
            role = None
        else:
            if sec.kind == "job" and len(parts) > 1:
                title, role = parts[0], "｜".join(parts[1:])
            else:
                title, role = "｜".join(parts), None
            head = '<p class="entry-title">%s</p>' % render_inline(title, item.lineno, warnings, quiet=True)
        date_html = ""
        if date:
            shown = render_inline(date, item.lineno, warnings, quiet=True)
            if "timeline" in layout and sec.kind != "education":
                shown = _break_timeline_date(shown)
            date_html = '<p class="entry-date">%s</p>' % shown
        body = _render_items(item.items, para_class, warnings, 6, layout)
        result = entry_result(item) if ("metrics" in layout and sec.kind != "education") else None
        timeline = "timeline" in layout and sec.kind != "education"
        if timeline and date_html:
            out.append('  <div class="entry timeline-entry">')
            out.append("    " + date_html)
            out.append('    <div class="record">')
            out.append('      <div class="entry-head">%s</div>' % head)
        elif timeline:
            out.append('  <div class="entry timeline-entry no-date">')
            out.append('    <div class="record">')
            out.append('      <div class="entry-head">%s</div>' % head)
        else:
            out.append('  <div class="entry">')
            out.append('    <div class="entry-head">%s%s</div>' % (head, date_html))
        if role:
            out.append('    <p class="entry-role">%s</p>' % render_inline(role, item.lineno, warnings, quiet=True))
        if result:
            r = result[0]
            out.append('    <div class="entry-body has-result"><div class="entry-main">')
            out.extend(body)
            out.append('    </div><div class="result"><p class="result-value">%s</p><p class="result-label">%s</p></div></div>'
                       % (htmllib.escape(r.value), htmllib.escape(r.label)))
        elif "metrics" in layout:
            out.append('    <div class="entry-body">')
            out.extend(body)
            out.append("    </div>")
        else:
            out.extend(body)
        if timeline:
            out.append("    </div>")
        out.append("  </div>")
    close_loose()
    out.append("</section>")


def resume_lang(res):
    """源稿几乎没有中文（汉字不到字母和汉字总数的 5%）时按英文处理，否则按中文。"""
    texts = [res.name] + [t for _, t, _ in res.meta] + ([res.target_role[0]] if res.target_role else [])
    for sec in res.sections:
        texts.append(sec.title)
        stack = list(sec.items)
        while stack:
            it = stack.pop()
            if isinstance(it, (Entry, Project)):
                texts.append("".join(it.parts) if isinstance(it, Entry) else it.title)
                stack.extend(it.items)
            else:
                texts.append(it[1])
    joined = "".join(texts)
    han = sum(1 for ch in joined if "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf")
    letters = sum(1 for ch in joined if ch.isascii() and ch.isalpha())
    return "en" if letters and han < 0.05 * (han + letters) else "zh-CN"


def set_lang(html_text, lang):
    m = HTML_TAG_RE.search(html_text)
    if not m:
        return html_text
    attrs = m.group(1)
    if re.search(r"\blang\s*=", attrs, re.I):
        attrs = re.sub(r"""\blang\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", 'lang="%s"' % lang, attrs, count=1, flags=re.I)
    else:
        attrs = ' lang="%s"' % lang + attrs
    return html_text[:m.start()] + "<html" + attrs + ">" + html_text[m.end():]


def _meta_item(text, lineno, warnings):
    """信息行的一项。短的整项不断开；邮箱、网址这类长串只在 @ . - _ / 之后断行，不切开单词。"""
    html = render_inline(text, lineno, warnings)
    if len(text) <= 24 or not re.search(r"@|://|www\.", text):
        return '<span class="meta-item">%s</span>' % html
    html = re.sub(r"(@|\.|-|_|/)(?=[^<>]*(?:<|$))", r"\1<wbr>", html)
    return '<span class="meta-item meta-long">%s</span>' % html


def render_html(res, template_text, lang=None):
    """lang 为 None 时按 resume_lang 判断。"""
    warnings = res.warnings
    lang = lang or resume_lang(res)
    for ph in ("{{name}}", "{{sections}}"):
        if ph not in template_text:
            raise CannotRun("模板里缺少占位符 %s" % ph, hint="换用技能自带的 assets/resume-navy.html，或用 --template 指定完整模板")
    tpl = re.sub(r"<!--.*?-->\s*", "", template_text, flags=re.S)
    name = render_inline(res.name, res.name_line, warnings, quiet=True)
    role_html = ""
    if res.target_role:
        role_html = render_inline(res.target_role[0], res.target_role[1], warnings)
    else:
        tpl = re.sub(r"\s*<p class=\"target-role\">\{\{target_role\}\}</p>", "", tpl)
    layout = template_layout(template_text)
    meta = []
    for kind, t, ln in res.meta:
        if kind != "note" and "split-meta" in layout:
            parts = [x for x in SEP_RE.split(t) if x.strip()]
            body = '<span class="sep">｜</span>'.join(_meta_item(x, ln, warnings) for x in parts)
            meta.append("<p>%s</p>" % body)
            continue
        body = render_inline(t, ln, warnings)
        meta.append('<p><span class="draft-note">%s</span></p>' % body if kind == "note" else "<p>%s</p>" % body)
    if not meta:
        tpl = re.sub(r"\s*<div class=\"meta\">\{\{meta_lines\}\}</div>", "", tpl)
    notice = "".join('<p class="sample-notice">%s</p>' % render_inline(_strip_wrapper(t), ln, warnings, quiet=True)
                     for t, ln in res.notices)
    title_text = res.name + ("-" + res.target_role[0] if res.target_role else "") + (
        "-Resume" if lang == "en" else "-简历")
    values = {
        "document_title": htmllib.escape(_restore_escapes(_strip_markup(_protect_escapes(title_text))[0])),
        "name": name,
        "target_role": role_html,
        "meta_lines": "".join(meta),
        "sample_notice": notice,
    }
    values["sections"], values["aside"] = render_sections(res, warnings, layout)
    # 一次性替换，源稿文字里出现的 {{xxx}} 不会被二次替换
    return set_lang(re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), tpl), lang)


def _strip_wrapper(t):
    m = re.match(r"^(\*{1,2}|_{1,2})(.+)\1$", t.strip())
    return m.group(2) if m else t


# ---------------------------------------------------------------------------
# 页面文字与内容守恒
# ---------------------------------------------------------------------------

class PageText(HTMLParser):
    """取 <body> 里的可见文字，并统计 .pending / .draft-note / .sample-notice。

    text 是全部可见文字，块级元素（段落、列表项、标题等）之间用换行隔开，行内元素直接相连；
    margin 与 text 逐字对应，标出页脚（<footer>、position:fixed 或页码类名）里的字，页码只在这里放过；
    clean 同样按块换行，去掉了 .pending / .draft-note / .sample-notice 里的文字，用来查正文有没有混进草稿用语。
    """

    SKIP = ("script", "style", "title", "head", "template", "noscript")
    VOID = ("br", "img", "hr", "meta", "link", "input", "base", "col", "area", "source", "wbr")
    BLOCK = ("p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "section", "header", "footer",
             "main", "article", "aside", "nav", "table", "thead", "tbody", "tr", "td", "th", "dl", "dt", "dd",
             "blockquote", "pre", "figure", "figcaption", "address", "br", "hr")
    MARGIN_CLASSES = ("footer", "page-footer", "page-number", "pagenum", "page-num")

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.parts = []
        self.clean_parts = []
        self.buf = []
        self.mask = []
        self.skip = 0
        self.stack = []
        self.marked_depth = 0
        self.margin_depth = 0
        self.pending = 0
        self.notices = 0
        self.draft_notes = 0
        self.notice_depth = 0
        self.notice_parts = []

    def _emit(self, text, margin, clean=True):
        self.buf.append(text)
        self.mask.extend([margin] * len(text))
        if clean:
            self.clean_parts.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK and not self.skip:
            self._emit("\n", False)
        if tag in self.VOID:
            return
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        marked = "pending" in classes or "sample-notice" in classes or "draft-note" in classes
        self.pending += "pending" in classes
        self.notices += "sample-notice" in classes
        self.draft_notes += "draft-note" in classes
        notice = "sample-notice" in classes
        margin = (tag == "footer" or any(c in self.MARGIN_CLASSES for c in classes)
                  or bool(re.search(r"position\s*:\s*fixed", a.get("style") or "", re.I)))
        self.stack.append((tag, tag in self.SKIP, marked, notice, margin))
        if tag in self.SKIP:
            self.skip += 1
        if marked:
            self.marked_depth += 1
        if notice:
            self.notice_depth += 1
        if margin:
            self.margin_depth += 1

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for _, skip, marked, notice, margin in self.stack[i:]:
                    self.skip -= skip
                    self.marked_depth -= marked
                    self.notice_depth -= notice
                    self.margin_depth -= margin
                del self.stack[i:]
                break
        if tag in self.BLOCK and not self.skip:
            self._emit("\n", False)

    def handle_data(self, data):
        if self.skip:
            return
        self.parts.append(data)
        self._emit(data, self.margin_depth > 0, clean=not self.marked_depth)
        if self.notice_depth:
            self.notice_parts.append(data)

    @classmethod
    def of(cls, html_text):
        p = cls()
        p.feed(html_text)
        p.close()
        p.text = "".join(p.buf)
        p.margin = p.mask
        p.clean = "".join(p.clean_parts)
        p.notice_text = " ".join(p.notice_parts)
        return p

    def pieces(self):
        """页面的每个文字节点当作一段 (0, 文字)，没有源稿时用来逐段核对 PDF。"""
        return [(0, t) for t in self.parts if squash(t)]


def squash(text, nfkc=False):
    if nfkc:
        text = unicodedata.normalize("NFKC", text)
    return "".join(ch for ch in text if not ch.isspace() and unicodedata.category(ch) not in ("Cf", "Cc"))


LINE_BREAKS = "\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"


def _word(c):
    return c.isascii() and c.isalnum()


def normalize(text, nfkc=False, margin=None):
    """比较用的文字，返回 (文字, 页边标记)。

    空白只在两个英文字母或数字之间保留一个：同一行里的空格写成 " "；只有换行时写成 "\n"，
    表示这里可能本来是空格（PDF 自动换行处不画空格），也可能是长词断开。其余空白都去掉，
    所以中文断行、全角空格、“18 %”和“18%”这类版面差异不影响结果，“now here”和“nowhere”仍能分开。
    """
    if margin is not None and len(margin) != len(text):
        margin = None
    chars = []
    for i, ch in enumerate(text):
        mk = bool(margin[i]) if margin is not None else False
        for c in (unicodedata.normalize("NFKC", ch) if nfkc else ch):
            if c.isspace():
                chars.append(("\n" if c in LINE_BREAKS else " ", mk))
            elif unicodedata.category(c) not in ("Cf", "Cc"):
                chars.append((c, mk))
    out, mask = [], []
    i = 0
    while i < len(chars):
        c, mk = chars[i]
        if c in " \n":
            j = i
            only_break = True
            while j < len(chars) and chars[j][0] in " \n":
                only_break = only_break and chars[j][0] == "\n"
                j += 1
            if out and j < len(chars) and _word(out[-1]) and _word(chars[j][0]):
                out.append("\n" if only_break else " ")
                mask.append(mk)
            i = j
            continue
        out.append(c)
        mask.append(mk)
        i += 1
    return "".join(out), mask


def piece_pattern(norm):
    """一段源稿文字在页面里的匹配式：源稿的空格可以对上空格或换行；两个英文字符之间可以夹一个换行（长词断开）。"""
    out = []
    for k, c in enumerate(norm):
        if c == " ":
            out.append("[ \n]")
            continue
        out.append(re.escape(c))
        if k + 1 < len(norm) and _word(c) and _word(norm[k + 1]):
            out.append("\n?")
    return re.compile("".join(out))


class Pieces(list):
    """[(行号, 文字)]。groups 把几行并成一组：组内先后不限（例如页头里目标岗位排在姓名旁边，
    “>”稿件提示写在岗位前面也行），组与组之间仍按源稿先后。"""

    def __init__(self, items=(), groups=None):
        list.__init__(self, items)
        self.groups = groups or {}


def source_pieces(text):
    """源稿里页面必须显示的文字，按行给出 (行号, 文字)。不复用解析器，用来独立核对；
    加粗、斜体、行内代码和反斜杠转义按渲染时的同一套规则去掉符号（“A\\*”“`a*b`”“3*4”里的星号都保留）。"""
    out = Pieces()
    in_header = False
    for ln, raw in enumerate(text.splitlines(), 1):
        s = raw.strip().lstrip("\ufeff")
        if re.match(r"^#\s", s):
            in_header = True
        elif re.match(r"^#{2,}\s", s):
            in_header = False
        if in_header:
            out.groups[ln] = "header"
        if not s or HR_RE.match(s):
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        bm = BOLD_ENTRY_RE.match(s)
        if m:
            body = re.sub(r"\s+#+$", "", m.group(2))
            pieces = split_heading(body) if len(m.group(1)) == 3 else [body]
        elif re.match(r"^[-*+]\s+", s):
            pieces = [re.sub(r"^[-*+]\s+", "", s)]
        elif s.startswith(">"):
            pieces = [s.lstrip(">")]
        elif in_header and ln in out.groups and not re.match(r"^#\s", s):
            # 信息行按“｜”拆开：有的样式把联系方式排成几行，页头各行本来就先后不限
            pieces = [x for x in SEP_RE.split(s) if x.strip()]
        elif bm:
            pieces = [bm.group(1)] + split_heading(bm.group(2))
        else:
            pieces = [s]
        for p in pieces:
            p = _restore_escapes(_strip_markup(_protect_escapes(p))[0])
            if squash(p):
                out.append((ln, p))
    return out


def layout_pieces(src_text, res, layout):
    """按样式要在页面上出现的源稿文字。

    aside：侧栏（页头和侧栏栏目）和正文各自按源稿先后排，两栏之间不比先后；
    metrics：每段经历旁的成果数字和说明紧跟在这段经历的最后一行之后，挪到别的经历旁会报先后不对。
    """
    base = source_pieces(src_text)
    if not layout or res is None:
        return base
    lines = src_text.splitlines()
    starts = sorted([sec.lineno for sec in res.sections] +
                    [ln for ln, raw in enumerate(lines, 1) if HR_RE.match(raw.strip()) and res.sections
                     and ln > res.sections[0].lineno] + [len(lines) + 1])

    def end_of(start):
        return min(x for x in starts if x > start) - 1

    tagged = [(ln, p, None) for ln, p in base]
    if "metrics" in layout:
        entries = [(e, sec) for sec in res.sections for e in sec.items if isinstance(e, Entry)]
        bounds = sorted([e.lineno for e, _ in entries] + starts)
        for e, sec in reversed(entries):
            if sec.kind == "education":
                continue
            found = entry_result(e)
            if not found:
                continue
            last = min(x for x in bounds if x > e.lineno) - 1
            at = max([i + 1 for i, (ln, _, _) in enumerate(tagged) if ln <= last] or [len(tagged)])
            rkey = ("result", e.lineno)
            tagged[at:at] = [(found[1], found[0].value, rkey), (found[1], found[0].label, rkey)]
    items = [(ln, p) for ln, p, _ in tagged]
    keys = dict((i, k) for i, (_, _, k) in enumerate(tagged) if k is not None)
    streams = {}
    pieces = Pieces(items, base.groups)
    if "aside" in layout:
        side_lines = set(ln for ln, g in base.groups.items() if g == "header")
        for sec in aside_sections(res, layout):
            side_lines.update(range(sec.lineno, end_of(sec.lineno) + 1))
        for i, (ln, _) in enumerate(items):
            streams[i] = "aside" if ln in side_lines else "main"
        pieces.stream_order = ["aside", "main"]
    pieces.keys, pieces.streams = keys, streams
    return pieces


class TextDiff(object):
    """源稿和页面或 PDF 文字的比对结果。

    missing：页面里缺的字符（Counter）；
    broken：字符都在、但没有原样连续出现的段（数字对调、改写、挪到别处），[(行号, 文字)]；
    lines：缺字所在的段；
    order：位置和源稿不同的行（例如一条成果挪到了别的经历下），算问题；
    fields：条目头里公司、岗位等字段的先后和源稿不同（例如公司和岗位对调），时间可以排在任何位置；
    extra：页面里多出来、源稿和模板都没有的文字（例如把一条成果多复制给另一段经历），[(前一行行号, 文字)]。
    """

    def __init__(self):
        self.missing = Counter()
        self.broken = []
        self.lines = []
        self.order = []
        self.fields = []
        self.extra = []

    def problem_lines(self):
        return self.lines + self.broken + self.order + self.fields + self.extra


# 版面自己加的字符：空白、条目头的分隔符、要点符号。只有全是这些字符的剩余文字才不算多出来；
# 数字、字母、汉字和 %、+、# 这类会改变意思的符号都算内容（“18”写成“18%”、“C”写成“C++”）。
LAYOUT_CHARS = set(" \n｜|▪•·●◦∙‧■□◆◇▸►–—-/:：,，、;；")
# 紧挨数字时会改变意思的符号：“18%”写成“-18%”、“18”写成“18/20”。
SIGN_CHARS = set("-–—/+±−")
# 常见页眉，在哪都不算多出来。
HEADER_WORDS_RE = re.compile(r"^(?:个人简历|简历|履历|resume|cv|curriculumvitae)$", re.I)
# 页码：只有落在页边（PDF 上下边距、HTML 页脚）里才不算多出来。
PAGE_NO_RE = re.compile(r"^(?:[-–—]?\d{1,3}[-–—]?|\d{1,3}/\d{1,3}|第\d{1,3}页(?:[,，/]?共\d{1,3}页)?|"
                        r"page\d{1,3}(?:of\d{1,3})?)$", re.I)


def _meaningful(run):
    """去掉版面字符后剩下的文字。"""
    return "".join(ch for ch in run if ch not in LAYOUT_CHARS)


def compare_text(pieces, page_text, nfkc, template=(), margin=None, strict_streams=False):
    """逐段核对页面文字和源稿：内容一样、先后一样、没有多出来的。

    - 每段（标题的一段、一条要点、一行信息）在页面里原样连续出现，英文词与词之间的空格也要对上；
    - 行与行按源稿先后出现，下一行从上一行结束之后找起。页头各行（pieces.groups）先后不限；
      同一条目头拆成的几段（公司、岗位、时间）里，时间可以排在任何位置，其余按源稿先后；
    - 每段占用页面里的一处文字，不和别的段共用。template 是模板自带的固定文字（每个文字节点一段），
      可以不出现，出现时各占用一处：只剩半截（“作品履历”写成“作品”）或多出一份都会剩下文字；
    - 全部对上之后页面里还剩下的文字就是多出来的。只有分隔符、要点符号、常见页眉，
      以及 margin 标出的页边里的页码不算。
    pieces 分了几栏（边栏样式）时每栏各自按先后核对；strict_streams 时后一栏从前一栏最后一处之后找起
    （HTML 里侧栏整个排在正文前面，侧栏内容挪进正文会报；PDF 里侧栏可能续到下一页，不这样要求）。
    """
    page, mask = normalize(page_text, nfkc, margin)
    flat = page.replace(" ", "").replace("\n", "")
    groups = getattr(pieces, "groups", {})
    keys = getattr(pieces, "keys", {})
    streams = getattr(pieces, "streams", {})
    diff = TextDiff()
    want = Counter()
    rows = []
    for i, (ln, p) in enumerate(pieces):
        norm = normalize(p, nfkc)[0]
        want.update(norm.replace(" ", ""))
        if norm:
            key = keys.get(i) or (groups.get(ln, ln) if ln else None)
            st = streams.get(i, "main")
            item = (piece_pattern(norm), p)
            if rows and key is not None and rows[-1][0] == key and rows[-1][3] == st:
                rows[-1][2].append(item)
            else:
                rows.append((key, ln, [item], st))
    order = list(getattr(pieces, "stream_order", None) or ["main"])
    order += [r[3] for r in rows if r[3] not in order]
    rows = [r for st in order for r in rows if r[3] == st]
    diff.missing = want - Counter(flat)

    owner = [0] * len(page)     # 每个字被哪一行占用；0 表示还没被占用，-1 表示模板文字
    used = [False] * len(page)

    def find_free(pat, start):
        pos = start
        while pos <= len(page):
            mt = pat.search(page, pos)
            if mt is None:
                return None
            if mt.end() > mt.start() and not any(used[mt.start():mt.end()]):
                return mt
            pos = mt.start() + 1
        return None

    def take(mt, ln):
        for k in range(mt.start(), mt.end()):
            used[k] = True
            owner[k] = ln or -1

    cursor = 0
    stream = None
    stream_end = 0
    line_end = {}
    for key, ln, group, st in rows:
        if st != stream:
            # 每一栏各自从页面开头找起（侧栏和正文分开比先后）；严格时从上一栏结束处找起
            stream, cursor = st, (stream_end if strict_streams else 0)
        is_result = isinstance(key, tuple) and len(key) == 2 and key[0] == "result"
        # 成果块在 HTML 里排在该段经历末尾；PDF 跨页时可能画在第 1 页右栏、早于第 2 页要点，但仍须在本条目头之后、下一条目之前
        start = cursor if (strict_streams or not is_result) else line_end.get(key[1], cursor)
        absent = [raw for pat, raw in group if pat.search(page) is None]
        if absent:
            for raw in absent:
                target = diff.lines if any(ch in diff.missing for ch in squash(raw, nfkc)) else diff.broken
                target.append((ln, raw.strip()))
            group = [g for g in group if g[1] not in absent]
            if not group:
                continue
        # 组内长的先占位置，短的再找剩下的：“北京大学计算机学院｜计算机”里专业不会落进院名
        found = {}
        for idx, (pat, raw) in sorted(enumerate(group), key=lambda g: -len(g[1][1])):
            mt = find_free(pat, start)
            if mt is None:
                break
            take(mt, ln)
            found[idx] = mt
        if len(found) == len(group):
            ends = [mt.end() for mt in found.values()]
            cursor = max([cursor] + ends) if is_result else min(ends)
            if isinstance(key, int):
                line_end[key] = max(ends)
            stream_end = max([stream_end] + ends)
            if key == ln and len(group) > 1:
                last_is_date = bool(DATE_RE.search(group[-1][1]))
                fixed = [found[i].start() for i in range(len(group) - (1 if last_is_date else 0))]
                if fixed != sorted(fixed):
                    diff.fields.append((ln, "｜".join(raw.strip() for _, raw in group)))
        else:
            diff.order.append((ln, group[0][1].strip()))
            for idx, (pat, raw) in enumerate(group):
                if idx not in found:
                    mt = find_free(pat, 0)
                    if mt is not None:
                        take(mt, ln)

    for t in template:
        norm = normalize(t, nfkc)[0]
        if not norm:
            continue
        mt = find_free(piece_pattern(norm), 0)
        if mt is not None:
            take(mt, 0)

    if not diff.lines and not diff.broken:
        k = 0
        while k < len(page):
            if used[k]:
                k += 1
                continue
            j = k
            while j < len(page) and not used[j]:
                j += 1
            run = page[k:j]
            words = _meaningful(run)
            core = "".join(ch for ch in run if ch not in " \n")
            in_margin = all(mask[x] for x in range(k, j) if page[x] not in " \n")
            signs = [x for x in range(k, j) if page[x] in SIGN_CHARS and
                     ((x > 0 and page[x - 1].isdigit()) or (x + 1 < len(page) and page[x + 1].isdigit()))]
            if in_margin and core and PAGE_NO_RE.match(core):
                ok = True
            elif signs:
                ok = False
            else:
                ok = not words or bool(HEADER_WORDS_RE.match(words))
            if not ok:
                before = next((owner[x] for x in range(k - 1, -1, -1) if owner[x]), 0)
                diff.extra.append((max(before, 0), run.strip(" \n").replace("\n", " ")))
            k = j
    return diff


def describe_extra(extra, limit=5):
    out = []
    for ln, run in extra[:limit]:
        out.append("“%s”%s" % (run[:40], "（第 %d 行之后）" % ln if ln else ""))
    return "；".join(out)


def describe_lines(lines, limit=8):
    out = []
    for ln, t in lines[:limit]:
        out.append(("第 %d 行“%s”" if ln else "页面文字“%s”") % ((ln, t[:30]) if ln else (t[:30],)))
    return "；".join(out) or "无法定位到具体行"


def describe_missing(missing, limit=20):
    items = sorted(missing.items(), key=lambda kv: -kv[1])
    shown = "、".join("“%s”%s" % (ch, "×%d" % n if n > 1 else "") for ch, n in items[:limit])
    if len(items) > limit:
        shown += " 等 %d 种" % len(items)
    return shown


def find_radicals(text):
    found = []
    for ch in text:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in RADICAL_RANGES):
            found.append(ch)
    return found


def radical_label(ch):
    norm = unicodedata.normalize("NFKC", ch)
    if norm != ch:
        return "“%s”(U+%04X，本应是“%s”)" % (ch, ord(ch), norm)
    return "“%s”(U+%04X)" % (ch, ord(ch))


# ---------------------------------------------------------------------------
# 最小 PDF 解析（只为核验：页数、字体、ToUnicode、文字层、文字位置）
# ---------------------------------------------------------------------------

class PDFError(Exception):
    pass


class Name(str):
    pass


class Kw(str):
    pass


class Ref(object):
    __slots__ = ("num", "gen")

    def __init__(self, num, gen):
        self.num = num
        self.gen = gen


class Stream(object):
    def __init__(self, dic, raw):
        self.dic = dic
        self.raw = raw


WS = frozenset(b" \t\r\n\x00\x0c")
DELIMS = frozenset(b"()<>[]{}/%")
_NOTSET = object()


class Lexer(object):
    def __init__(self, data, pos=0):
        self.d = data
        self.p = pos
        self.n = len(data)

    def skip(self):
        d, n, p = self.d, self.n, self.p
        while p < n:
            c = d[p]
            if c in WS:
                p += 1
            elif c == 37:
                while p < n and d[p] not in (10, 13):
                    p += 1
            else:
                break
        self.p = p

    def token(self):
        self.skip()
        d, p, n = self.d, self.p, self.n
        if p >= n:
            return None
        c = d[p]
        if c == 47:
            q = p + 1
            while q < n and d[q] not in WS and d[q] not in DELIMS:
                q += 1
            self.p = q
            raw = re.sub(rb"#([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), d[p + 1:q])
            return Name(raw.decode("latin-1"))
        if c == 40:
            return self._string()
        if c == 60:
            if d[p + 1:p + 2] == b"<":
                self.p = p + 2
                return Kw("<<")
            q = d.find(b">", p)
            if q < 0:
                q = n
            hexs = re.sub(rb"[^0-9A-Fa-f]", b"", d[p + 1:q])
            if len(hexs) % 2:
                hexs += b"0"
            self.p = q + 1
            return bytes.fromhex(hexs.decode("ascii"))
        if c == 62:
            if d[p + 1:p + 2] == b">":
                self.p = p + 2
                return Kw(">>")
            self.p = p + 1
            return Kw(">")
        if c in (91, 93, 123, 125, 41):
            self.p = p + 1
            return Kw(chr(c))
        q = p
        while q < n and d[q] not in WS and d[q] not in DELIMS:
            q += 1
        tok = d[p:q]
        self.p = q
        try:
            return int(tok)
        except ValueError:
            pass
        try:
            return float(tok)
        except ValueError:
            pass
        return Kw(tok.decode("latin-1"))

    def _string(self):
        d, n = self.d, self.n
        p = self.p + 1
        depth = 1
        out = bytearray()
        esc = {110: 10, 114: 13, 116: 9, 98: 8, 102: 12}
        while p < n:
            c = d[p]
            if c == 92:
                p += 1
                if p >= n:
                    break
                e = d[p]
                if e in esc:
                    out.append(esc[e])
                    p += 1
                elif 48 <= e <= 55:
                    q = p
                    while q < n and q < p + 3 and 48 <= d[q] <= 55:
                        q += 1
                    out.append(int(d[p:q], 8) & 255)
                    p = q
                elif e == 13:
                    p += 1
                    if p < n and d[p] == 10:
                        p += 1
                elif e == 10:
                    p += 1
                else:
                    out.append(e)
                    p += 1
                continue
            if c == 40:
                depth += 1
            elif c == 41:
                depth -= 1
                if depth == 0:
                    p += 1
                    break
            out.append(c)
            p += 1
        self.p = p
        return bytes(out)

    def obj(self, tok=_NOTSET, refs=True):
        if tok is _NOTSET:
            tok = self.token()
        if tok is None:
            raise PDFError("意外结束")
        if isinstance(tok, Kw):
            if tok == "[":
                arr = []
                while True:
                    t = self.token()
                    if t is None:
                        raise PDFError("数组没有结束")
                    if isinstance(t, Kw) and t == "]":
                        return arr
                    arr.append(self.obj(t, refs))
            if tok == "<<":
                dic = {}
                while True:
                    k = self.token()
                    if k is None:
                        raise PDFError("字典没有结束")
                    if isinstance(k, Kw) and k == ">>":
                        return dic
                    if not isinstance(k, Name):
                        continue
                    dic[str(k)] = self.obj(refs=refs)
            if tok == "true":
                return True
            if tok == "false":
                return False
            if tok == "null":
                return None
            return tok
        if refs and isinstance(tok, int) and not isinstance(tok, bool):
            save = self.p
            t2 = self.token()
            if isinstance(t2, int) and not isinstance(t2, bool):
                t3 = self.token()
                if isinstance(t3, Kw) and t3 == "R":
                    return Ref(tok, t2)
            self.p = save
        return tok


def _png_unpredict(data, columns, colors, bpc):
    bpp = max(1, colors * bpc // 8)
    rowlen = (columns * colors * bpc + 7) // 8
    out = bytearray()
    prev = bytearray(rowlen)
    i = 0
    while i + rowlen < len(data) + 1 and i < len(data):
        ft = data[i]
        row = bytearray(data[i + 1:i + 1 + rowlen])
        i += 1 + rowlen
        if len(row) < rowlen:
            row.extend(b"\0" * (rowlen - len(row)))
        for x in range(rowlen):
            a = row[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ft == 1:
                row[x] = (row[x] + a) & 255
            elif ft == 2:
                row[x] = (row[x] + b) & 255
            elif ft == 3:
                row[x] = (row[x] + ((a + b) >> 1)) & 255
            elif ft == 4:
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                row[x] = (row[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        out += row
        prev = row
    return bytes(out)


def _ascii85(data):
    data = re.sub(rb"\s", b"", data)
    if data.startswith(b"<~"):
        data = data[2:]
    end = data.find(b"~>")
    if end >= 0:
        data = data[:end]
    out = bytearray()
    group = []
    for c in data:
        if c == 122 and not group:
            out += b"\0\0\0\0"
            continue
        group.append(c - 33)
        if len(group) == 5:
            v = 0
            for g in group:
                v = v * 85 + g
            out += (v & 0xFFFFFFFF).to_bytes(4, "big")
            group = []
    if group:
        k = len(group)
        group += [84] * (5 - k)
        v = 0
        for g in group:
            v = v * 85 + g
        out += (v & 0xFFFFFFFF).to_bytes(4, "big")[:k - 1]
    return bytes(out)


class PDFDoc(object):
    def __init__(self, data):
        head = data[:1024]
        start = head.find(b"%PDF-")
        if start < 0:
            raise PDFError("不是 PDF")
        self.data = data
        self.version = head[start + 5:start + 8].decode("latin-1", "replace")
        self.objects = {}
        self.trailer = {}
        self._scan()
        self._load_object_streams()
        self._load_trailer()

    def _scan(self):
        d = self.data
        pat = re.compile(rb"(?<![0-9])(\d+)\s+(\d+)\s+obj\b")
        pos = 0
        while True:
            m = pat.search(d, pos)
            if not m:
                break
            num = int(m.group(1))
            lex = Lexer(d, m.end())
            try:
                obj = lex.obj()
            except (PDFError, ValueError, RecursionError):
                pos = m.end()
                continue
            lex.skip()
            end = lex.p
            if isinstance(obj, dict) and d.startswith(b"stream", lex.p):
                s = lex.p + 6
                if d[s:s + 2] == b"\r\n":
                    s += 2
                elif d[s:s + 1] in (b"\n", b"\r"):
                    s += 1
                length = obj.get("Length")
                raw = None
                if isinstance(length, int) and length >= 0:
                    tail = d[s + length:s + length + 32].lstrip(b"\r\n \t")
                    if tail.startswith(b"endstream"):
                        raw = d[s:s + length]
                        end = s + length
                if raw is None:
                    e = d.find(b"endstream", s)
                    if e < 0:
                        e = len(d)
                    raw = d[s:e]
                    if raw.endswith(b"\r\n"):
                        raw = raw[:-2]
                    elif raw.endswith(b"\n") or raw.endswith(b"\r"):
                        raw = raw[:-1]
                    end = e
                obj = Stream(obj, raw)
                end = d.find(b"endstream", end)
                end = len(d) if end < 0 else end + 9
            self.objects[num] = obj
            pos = end

    def _load_object_streams(self):
        for num, obj in list(self.objects.items()):
            if not (isinstance(obj, Stream) and obj.dic.get("Type") == "ObjStm"):
                continue
            try:
                data = self.stream_data(obj)
                n = int(self.resolve(obj.dic.get("N", 0)))
                first = int(self.resolve(obj.dic.get("First", 0)))
                lex = Lexer(data)
                pairs = [(lex.token(), lex.token()) for _ in range(n)]
                for onum, off in pairs:
                    if not isinstance(onum, int) or onum in self.objects:
                        continue
                    self.objects[onum] = Lexer(data, first + int(off)).obj()
            except (PDFError, ValueError, TypeError, zlib.error):
                continue

    def _load_trailer(self):
        d = self.data
        for m in re.finditer(rb"trailer\s*<<", d):
            try:
                t = Lexer(d, m.end() - 2).obj()
                if isinstance(t, dict):
                    self.trailer.update(t)
            except PDFError:
                pass
        for obj in self.objects.values():
            if isinstance(obj, Stream) and obj.dic.get("Type") == "XRef":
                for k in ("Root", "Encrypt", "Info"):
                    if k in obj.dic and k not in self.trailer:
                        self.trailer[k] = obj.dic[k]

    def resolve(self, obj, depth=0):
        while isinstance(obj, Ref) and depth < 32:
            obj = self.objects.get(obj.num)
            depth += 1
        return obj

    def stream_data(self, stream):
        data = stream.raw
        filters = self.resolve(stream.dic.get("Filter"))
        parms = self.resolve(stream.dic.get("DecodeParms"))
        if filters is None:
            return data
        if not isinstance(filters, list):
            filters = [filters]
            parms = [parms]
        if not isinstance(parms, list):
            parms = [parms] * len(filters)
        for i, f in enumerate(filters):
            f = self.resolve(f)
            p = self.resolve(parms[i]) if i < len(parms) else None
            if f in ("FlateDecode", "Fl"):
                dec = zlib.decompressobj()
                try:
                    data = dec.decompress(data)
                except zlib.error:
                    raise PDFError("流解压失败")
                if isinstance(p, dict) and int(self.resolve(p.get("Predictor", 1)) or 1) >= 10:
                    data = _png_unpredict(data, int(self.resolve(p.get("Columns", 1))),
                                          int(self.resolve(p.get("Colors", 1))),
                                          int(self.resolve(p.get("BitsPerComponent", 8))))
            elif f in ("ASCIIHexDecode", "AHx"):
                h = re.sub(rb"[^0-9A-Fa-f]", b"", data.split(b">")[0])
                data = bytes.fromhex((h + (b"0" if len(h) % 2 else b"")).decode("ascii"))
            elif f in ("ASCII85Decode", "A85"):
                data = _ascii85(data)
            else:
                raise PDFError("不支持的压缩方式 %s" % f)
        return data

    def pages(self):
        root = self.resolve(self.trailer.get("Root"))
        if not isinstance(root, dict):
            root = next((o for o in self.objects.values() if isinstance(o, dict) and o.get("Type") == "Catalog"), None)
        result = []
        if isinstance(root, dict):
            seen = set()

            def walk(node, inherited, depth):
                node_obj = self.resolve(node)
                if not isinstance(node_obj, dict) or depth > 64 or id(node_obj) in seen:
                    return
                seen.add(id(node_obj))
                inh = dict(inherited)
                for k in ("Resources", "MediaBox"):
                    if k in node_obj:
                        inh[k] = node_obj[k]
                kids = self.resolve(node_obj.get("Kids"))
                if node_obj.get("Type") == "Pages" or isinstance(kids, list):
                    for kid in kids or []:
                        walk(kid, inh, depth + 1)
                else:
                    page = dict(node_obj)
                    for k, v in inh.items():
                        page.setdefault(k, v)
                    result.append(page)

            walk(root.get("Pages"), {}, 0)
        if not result:
            result = [o for o in self.objects.values() if isinstance(o, dict) and o.get("Type") == "Page"]
        return result

    def fonts(self):
        return [(num, o) for num, o in sorted(self.objects.items())
                if isinstance(o, dict) and o.get("Type") == "Font" and o.get("Subtype") != "CIDFontType0"
                and o.get("Subtype") != "CIDFontType2"]


def _utf16(b):
    if len(b) == 1:
        return chr(b[0])
    if len(b) % 2:
        b = b[:-1]
    return b.decode("utf-16-be", "replace")


def parse_cmap(data):
    """返回 (码到字符串的映射, codespace 列表 [(字节数, 下限, 上限)])。"""
    lex = Lexer(data)
    mapping = {}
    codespace = []
    while True:
        tok = lex.token()
        if tok is None:
            break
        if not isinstance(tok, Kw):
            continue
        if tok == "begincodespacerange":
            while True:
                lo = lex.token()
                if lo is None or (isinstance(lo, Kw) and lo == "endcodespacerange"):
                    break
                hi = lex.token()
                if isinstance(lo, bytes) and isinstance(hi, bytes) and lo:
                    codespace.append((len(lo), int.from_bytes(lo, "big"), int.from_bytes(hi, "big")))
        elif tok == "beginbfchar":
            while True:
                src = lex.token()
                if src is None or (isinstance(src, Kw) and src == "endbfchar"):
                    break
                dst = lex.token()
                if isinstance(src, bytes) and isinstance(dst, bytes):
                    mapping[int.from_bytes(src, "big")] = _utf16(dst)
        elif tok == "beginbfrange":
            while True:
                lo = lex.token()
                if lo is None or (isinstance(lo, Kw) and lo == "endbfrange"):
                    break
                hi = lex.token()
                dst = lex.obj(lex.token(), refs=False)
                if not (isinstance(lo, bytes) and isinstance(hi, bytes)):
                    continue
                a, b = int.from_bytes(lo, "big"), int.from_bytes(hi, "big")
                if b < a or b - a > 65535:
                    continue
                if isinstance(dst, list):
                    for i, item in enumerate(dst[:b - a + 1]):
                        if isinstance(item, bytes):
                            mapping[a + i] = _utf16(item)
                elif isinstance(dst, bytes) and dst:
                    if len(dst) == 1:
                        for i in range(b - a + 1):
                            mapping[a + i] = chr(dst[0] + i)
                        continue
                    units = [int.from_bytes(dst[k:k + 2], "big") for k in range(0, len(dst) - 1, 2)]
                    for i in range(b - a + 1):
                        u = units[:-1] + [units[-1] + i]
                        raw = b"".join((x & 0xFFFF).to_bytes(2, "big") for x in u)
                        mapping[a + i] = raw.decode("utf-16-be", "replace")
    return mapping, codespace


class FontInfo(object):
    def __init__(self, doc, fdict):
        self.subtype = str(doc.resolve(fdict.get("Subtype")) or "")
        base = doc.resolve(fdict.get("BaseFont"))
        if base is None:
            # Type3 字体（Chrome 对部分字体这样输出）没有 BaseFont，名字在 FontDescriptor 里
            fdesc = doc.resolve(fdict.get("FontDescriptor"))
            if isinstance(fdesc, dict):
                base = doc.resolve(fdesc.get("FontName"))
                fam = doc.resolve(fdesc.get("FontFamily"))
                if base is None and isinstance(fam, bytes):
                    base = fam.decode("latin-1")
        self.base = re.sub(r"^[A-Z]{6}\+", "", str(base or fdict.get("Name") or "未命名字体"))
        self.cid = self.subtype == "Type0"
        tu = doc.resolve(fdict.get("ToUnicode"))
        self.has_tounicode = isinstance(tu, Stream)
        self.map, self.codespace = {}, []
        self.cmap_error = None
        if self.has_tounicode:
            try:
                self.map, self.codespace = parse_cmap(doc.stream_data(tu))
            except PDFError as e:
                self.cmap_error = str(e)
        self.simple = {}
        if not self.cid:
            enc = doc.resolve(fdict.get("Encoding"))
            codec = "mac_roman" if enc == "MacRomanEncoding" else "cp1252"
            for i in range(256):
                try:
                    self.simple[i] = bytes([i]).decode(codec)
                except UnicodeDecodeError:
                    pass
            if isinstance(enc, dict):
                diffs = doc.resolve(enc.get("Differences")) or []
                code = 0
                for item in diffs:
                    item = doc.resolve(item)
                    if isinstance(item, int):
                        code = item
                    elif isinstance(item, Name):
                        ch = _glyph_char(item)
                        if ch:
                            self.simple[code] = ch
                        else:
                            self.simple.pop(code, None)
                        code += 1
        desc = None
        if self.cid:
            desc_fonts = doc.resolve(fdict.get("DescendantFonts"))
            if isinstance(desc_fonts, list) and desc_fonts:
                df = doc.resolve(desc_fonts[0])
                if isinstance(df, dict):
                    desc = doc.resolve(df.get("FontDescriptor"))
        else:
            desc = doc.resolve(fdict.get("FontDescriptor"))
        self.embedded = self.subtype == "Type3" or (
            isinstance(desc, dict) and any(k in desc for k in ("FontFile", "FontFile2", "FontFile3")))

    def decode(self, bs):
        out = []
        unmapped = 0
        i = 0
        n = len(bs)
        while i < n:
            size = 2 if self.cid else 1
            if self.codespace and not self.cid:
                for clen, lo, hi in sorted(self.codespace):
                    if i + clen <= n and lo <= int.from_bytes(bs[i:i + clen], "big") <= hi:
                        size = clen
                        break
            code = int.from_bytes(bs[i:i + size], "big")
            i += size
            ch = self.map.get(code)
            if ch is None and not self.cid:
                ch = self.simple.get(code)
            if ch is None:
                unmapped += 1
                continue
            out.append(ch)
        return "".join(out), unmapped


_GLYPHS = {"space": " ", "period": ".", "comma": ",", "hyphen": "-", "colon": ":", "semicolon": ";",
           "parenleft": "(", "parenright": ")", "slash": "/", "at": "@", "bullet": "•",
           "endash": "–", "emdash": "—", "quoteright": "’", "quoteleft": "‘", "percent": "%"}


def _glyph_char(name):
    if name in _GLYPHS:
        return _GLYPHS[name]
    m = re.match(r"^uni([0-9A-Fa-f]{4})$", name)
    if m:
        return chr(int(m.group(1), 16))
    if len(name) == 1:
        return name
    return None


IDENT = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]


def _mul(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return [a1 * a2 + b1 * c2, a1 * b2 + b1 * d2, c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
            e1 * a2 + f1 * c2 + e2, e1 * b2 + f1 * d2 + f2]


def _nums(ops, k):
    vals = ops[-k:] if len(ops) >= k else None
    if vals is None or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        return None
    return [float(v) for v in vals]


class TextRun(object):
    def __init__(self, doc):
        self.doc = doc
        self.font_cache = {}
        self.chunks = []        # (文字, 基线高度)
        self.ys = []
        self.unmapped = 0
        self.used_fonts = []
        self.missing_tounicode = set()

    def font(self, resources, name):
        fonts = self.doc.resolve(resources.get("Font")) if isinstance(resources, dict) else None
        ref = fonts.get(str(name)) if isinstance(fonts, dict) else None
        key = ref.num if isinstance(ref, Ref) else id(ref)
        if key not in self.font_cache:
            fd = self.doc.resolve(ref)
            self.font_cache[key] = FontInfo(self.doc, fd) if isinstance(fd, dict) else None
        info = self.font_cache[key]
        if info is not None:
            if info.base not in self.used_fonts:
                self.used_fonts.append(info.base)
            if info.cid and not info.has_tounicode:
                self.missing_tounicode.add(info.base)
        return info

    def run(self, data, resources, ctm, depth=0):
        lex = Lexer(data)
        ops = []
        gstack = []
        tm = tlm = IDENT
        tl = 0.0
        font = None
        while True:
            tok = lex.token()
            if tok is None:
                break
            if not (isinstance(tok, Kw) and tok not in ("[", "<<", "true", "false", "null")):
                try:
                    ops.append(lex.obj(tok, refs=False))
                except PDFError:
                    break
                continue
            op = str(tok)
            if op == "q":
                gstack.append(ctm)
            elif op == "Q":
                ctm = gstack.pop() if gstack else ctm
            elif op == "cm":
                m = _nums(ops, 6)
                if m:
                    ctm = _mul(m, ctm)
            elif op == "BT":
                tm = tlm = IDENT
            elif op == "Tf" and len(ops) >= 2:
                font = self.font(resources, ops[-2])
            elif op == "TL":
                m = _nums(ops, 1)
                tl = m[0] if m else tl
            elif op in ("Td", "TD"):
                m = _nums(ops, 2)
                if m:
                    if op == "TD":
                        tl = -m[1]
                    tlm = _mul([1, 0, 0, 1, m[0], m[1]], tlm)
                    tm = tlm
            elif op == "Tm":
                m = _nums(ops, 6)
                if m:
                    tm = tlm = m
            elif op in ("T*", "'", '"'):
                tlm = _mul([1, 0, 0, 1, 0, -tl], tlm)
                tm = tlm
                if op != "T*" and ops and isinstance(ops[-1], bytes):
                    self._show(font, [ops[-1]], tm, ctm)
            elif op == "Tj" and ops and isinstance(ops[-1], bytes):
                self._show(font, [ops[-1]], tm, ctm)
            elif op == "TJ" and ops and isinstance(ops[-1], list):
                self._show(font, [x for x in ops[-1] if isinstance(x, bytes)], tm, ctm)
            elif op == "Do" and ops and depth < 6:
                xobjs = self.doc.resolve(resources.get("XObject")) if isinstance(resources, dict) else None
                xo = self.doc.resolve(xobjs.get(str(ops[-1]))) if isinstance(xobjs, dict) else None
                if isinstance(xo, Stream) and xo.dic.get("Subtype") == "Form":
                    mat = self.doc.resolve(xo.dic.get("Matrix"))
                    m = [float(self.doc.resolve(v)) for v in mat] if isinstance(mat, list) and len(mat) == 6 else IDENT
                    res = self.doc.resolve(xo.dic.get("Resources"))
                    self.run(self.doc.stream_data(xo), res if isinstance(res, dict) else resources,
                             _mul(m, ctm), depth + 1)
            elif op == "BI":
                d = lex.d
                idm = re.compile(rb"\sID\s").search(d, lex.p)
                if not idm:
                    break
                eim = re.compile(rb"\sEI(?=\s|$)").search(d, idm.end())
                lex.p = eim.end() if eim else len(d)
            ops = []

    def _show(self, font, strings, tm, ctm):
        for bs in strings:
            if font is None:
                self.unmapped += len(bs)
                continue
            text, unm = font.decode(bs)
            self.unmapped += unm
            if text:
                x, y = tm[4], tm[5]
                y = ctm[1] * x + ctm[3] * y + ctm[5]
                self.chunks.append((text, y))
                if text.strip():
                    self.ys.append(y)


class PDFInfo(object):
    def __init__(self):
        self.is_pdf = False
        self.version = ""
        self.pages = None
        self.fonts = []
        self.cmap_radicals = []     # (字体, 字符)
        self.text = None            # 提取出的文字，换行处有 "\n"；None 表示没能提取
        self.margin = None          # 与 text 逐字对应：这个字是否在页面上下边距里（页码只在这里放过）
        self.text_note = ""         # 没能提取或部分提取的原因
        self.unmapped = 0
        self.fill = None
        self.missing_tounicode = []
        self.not_embedded = []
        self.font_count = 0
        self.font_kinds = 0


MARGIN_BAND = 56.7   # pt（2 cm）：离上下纸边这么近、整行只有页码的那一行算页眉页脚


def page_band(doc, box):
    """页面上下页边的分界：(下界, 上界)，基线低于下界或高于上界的行可能是页眉页脚。读不出页面大小时返回 (None, None)。"""
    try:
        b = [float(doc.resolve(v)) for v in box]
    except (TypeError, ValueError):
        return None, None
    if len(b) != 4 or b[3] - b[1] <= 2 * MARGIN_BAND:
        return None, None
    return b[1] + MARGIN_BAND, b[3] - MARGIN_BAND


def analyze_pdf(data):
    info = PDFInfo()
    try:
        doc = PDFDoc(data)
    except PDFError:
        return info
    info.is_pdf = True
    info.version = doc.version
    if doc.trailer.get("Encrypt") is not None:
        info.text_note = "PDF 已加密，脚本无法读取文字层"
        info.pages = len(doc.pages()) or None
        return info
    try:
        pages = doc.pages()
        info.pages = len(pages)
        names = set()
        for _, fd in doc.fonts():
            fi = FontInfo(doc, fd)
            info.font_count += 1
            names.add(fi.base)
            if not fi.embedded and fi.base not in info.not_embedded:
                info.not_embedded.append(fi.base)
            for ch in set(fi.map.values()):
                for r in find_radicals(ch):
                    info.cmap_radicals.append((fi.base, r))
        info.font_kinds = len(names)
        run = TextRun(doc)
        last_ys = []
        last_box = None
        parts, marks = [], []
        for page in pages:
            contents = doc.resolve(page.get("Contents"))
            if isinstance(contents, Stream):
                contents = [contents]
            chunks = []
            for c in contents or []:
                c = doc.resolve(c)
                if isinstance(c, Stream):
                    chunks.append(doc.stream_data(c))
            res = doc.resolve(page.get("Resources"))
            start = len(run.ys)
            first = len(run.chunks)
            run.run(b"\n".join(chunks), res if isinstance(res, dict) else {}, IDENT)
            last_ys = run.ys[start:]
            last_box = doc.resolve(page.get("MediaBox"))
            bottom, top = page_band(doc, last_box)
            lines = []
            for text, y in run.chunks[first:]:
                if lines and abs(y - lines[-1][0]) <= 2:
                    lines[-1][1].append(text)
                else:
                    lines.append((y, [text]))
            for y, texts in lines:
                line = "".join(texts)
                footer = (bottom is not None and (y < bottom or y > top)
                          and bool(PAGE_NO_RE.match(squash(line))))
                parts.append(line)
                marks.extend([footer] * len(line))
                parts.append("\n")
                marks.append(False)
        info.fonts = run.used_fonts
        info.unmapped = run.unmapped
        info.missing_tounicode = sorted(run.missing_tounicode)
        info.text = "".join(parts)
        info.margin = marks
        if last_ys and isinstance(last_box, list) and len(last_box) == 4:
            box = [float(doc.resolve(v)) for v in last_box]
            height = box[3] - box[1]
            if height > 0:
                info.fill = max(0.0, min(1.0, (box[3] - min(last_ys)) / height))
    except (PDFError, ValueError, TypeError, KeyError, IndexError, AttributeError, zlib.error, RecursionError) as e:
        info.text = None
        info.text_note = "PDF 结构超出脚本能解析的范围（%s）" % (e.__class__.__name__ + (": %s" % e if str(e) else ""))
    return info


# ---------------------------------------------------------------------------
# 浏览器与打印
# ---------------------------------------------------------------------------

def browser_candidates():
    names = ["google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser",
             "microsoft-edge", "microsoft-edge-stable", "msedge"]
    paths = []
    if sys.platform == "darwin":
        for base in ("/Applications", os.path.expanduser("~/Applications")):
            for app, exe in (("Google Chrome", "Google Chrome"), ("Microsoft Edge", "Microsoft Edge"),
                             ("Chromium", "Chromium"), ("Google Chrome Canary", "Google Chrome Canary")):
                paths.append(os.path.join(base, app + ".app", "Contents", "MacOS", exe))
    elif sys.platform.startswith("win"):
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        for root in [r for r in roots if r]:
            paths += [os.path.join(root, "Google", "Chrome", "Application", "chrome.exe"),
                      os.path.join(root, "Microsoft", "Edge", "Application", "msedge.exe"),
                      os.path.join(root, "Chromium", "Application", "chrome.exe")]
    else:
        paths += ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/opt/google/chrome/chrome",
                  "/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium",
                  "/usr/bin/microsoft-edge", "/opt/microsoft/msedge/msedge"]
    for n in names:
        found = shutil.which(n)
        if found:
            paths.append(found)
    return paths


def _app_bundle_exe(path):
    p = Path(path)
    if p.suffix == ".app" and p.is_dir():
        macos = p / "Contents" / "MacOS"
        exe = macos / p.stem
        if exe.is_file():
            return str(exe)
        files = sorted(f for f in macos.iterdir() if f.is_file()) if macos.is_dir() else []
        if files:
            return str(files[0])
    return str(path)


def find_browser(explicit):
    if explicit:
        path = _app_bundle_exe(explicit)
        if not os.path.isfile(path):
            raise CannotRun("--browser 指定的浏览器不存在：%s" % explicit)
        return path
    for var in BROWSER_ENV_VARS:
        val = os.environ.get(var)
        if val:
            path = _app_bundle_exe(val)
            if not os.path.isfile(path):
                raise CannotRun("环境变量 %s 指定的浏览器不存在：%s" % (var, val))
            return path
    for path in browser_candidates():
        if os.path.isfile(path):
            return path
    raise CannotRun(
        "找不到可用的浏览器（Chrome、Edge 或 Chromium），没法打印 PDF",
        ["可以装 Google Chrome 或 Microsoft Edge 后重跑；",
         "装在非常见位置时，用 --browser <路径> 或环境变量 GETOFFER_BROWSER 指定；",
         "或者用宿主自带的 PDF 能力生成，再运行 --check-pdf <文件.pdf> --source <源稿.md> 核验。"])


def _kill_tree(proc):
    try:
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, ValueError):
        pass
    try:
        proc.kill()
    except OSError:
        pass


def print_pdf(browser, html_text, workdir, tag, timeout):
    page = workdir / ("page-%s.html" % tag)
    out = workdir / ("out-%s.pdf" % tag)
    page.write_text(html_text, encoding="utf-8")
    cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
           "--disable-extensions", "--disable-background-networking", "--disable-component-update",
           "--disable-sync", "--disable-default-apps", "--no-pings", "--use-mock-keychain",
           "--password-store=basic", "--user-data-dir=" + str(workdir / "profile"),
           "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--print-to-pdf=" + str(out), page.resolve().as_uri()]
    if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.insert(1, "--no-sandbox")
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if not sys.platform.startswith("win"):
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except OSError as e:
        raise CannotRun("浏览器启动失败：%s" % e, hint="确认 --browser 指向浏览器可执行文件")
    try:
        _, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        proc.communicate()
        raise CannotRun("浏览器打印超时（%d 秒）" % timeout, hint="关掉占用资源的程序后重试，或用 --timeout 调大")
    if not out.is_file() or out.stat().st_size == 0:
        tail = err.decode("utf-8", "replace").strip().splitlines()[-3:]
        raise CannotRun("浏览器没有生成 PDF（退出码 %s）" % proc.returncode, tail,
                        "可换 --browser 指定另一款浏览器，或用宿主的 PDF 能力生成后 --check-pdf 核验")
    return out.read_bytes()


def css_font_override(html_text, font):
    if not font:
        return html_text
    if re.search(r"[\"\\<>{};\r\n]", font):
        raise CannotRun("--font 字体名里不能有引号、反斜杠、尖括号、花括号或分号：%s" % font)
    m = re.search(r"body\s*\{[^}]*?font-family:\s*([^;}]+)", html_text)
    stack = m.group(1).strip() if m else "sans-serif"
    style = '<style>body { font-family: "%s", %s; }</style>' % (font, stack)
    idx = html_text.lower().rfind("</head>")
    return html_text[:idx] + style + html_text[idx:] if idx >= 0 else style + html_text


def add_base_href(html_text, base_dir):
    tag = '<base href="%s/">' % htmllib.escape(Path(base_dir).resolve().as_uri(), quote=True)
    m = re.search(r"<head[^>]*>", html_text, re.I)
    if re.search(r"<base\s", html_text, re.I):
        return html_text
    return html_text[:m.end()] + tag + html_text[m.end():] if m else tag + html_text


# ---------------------------------------------------------------------------
# 检查
# ---------------------------------------------------------------------------

def check_source_text(report, src_text):
    rads = find_radicals(src_text)
    if rads:
        report.problem("源稿本身含部首字符：%s" % "、".join(sorted(set(radical_label(r) for r in rads))),
                       "源稿", "把这些字符改成正常汉字（多半是从 PDF 复制时带进来的）")


def check_conservation(report, pieces, page, template=()):
    """template：模板自带的固定文字（每个文字节点一段），各在页面里占一处，不算多出来的内容。"""
    diff = compare_text(pieces, page.text, nfkc=False, template=template, margin=page.margin, strict_streams=True)
    total = sum(len(squash(p)) for _, p in pieces)
    ok = True
    if diff.missing:
        report.problem("页面丢了源稿内容：%s" % describe_missing(diff.missing), describe_lines(diff.lines),
                       "从源稿生成时是脚本的转换缺陷或源稿写法超出规则，先按 --help 调整写法；"
                       "手工改过的页面把这些字补回来，或者先改源稿再重新生成")
        ok = False
    if diff.broken:
        report.problem("页面里这些行和源稿不一致（字都在，但顺序或位置变了，例如数字对调）",
                       describe_lines(diff.broken),
                       "以源稿为准改回页面；确实要改内容就先改源稿，再重新生成或打印")
        ok = False
    if diff.order:
        report.problem("页面里这些行的位置和源稿不同（例如一条成果挪到了别的经历下）",
                       "从这里起和源稿对不上：" + describe_lines(diff.order) + "（被挪动的行可能在它们前面）",
                       "以源稿为准把它们放回原来的经历；确实要调整顺序就先改源稿，再重新生成或打印")
        ok = False
    if diff.fields:
        report.problem("页面里条目头的字段先后和源稿不同（例如公司和岗位对调）", describe_lines(diff.fields),
                       "按源稿的“名称｜岗位或专业｜时间”放回各自的位置；时间排在哪都行")
        ok = False
    if diff.extra:
        report.problem("页面里多出了源稿没有的文字（例如把一条成果多复制给了另一段经历）",
                       describe_extra(diff.extra),
                       "删掉多出来的内容；确实要加就先写进源稿，再重新生成或打印。"
                       "是自定义模板自带的固定文字时，加 --template 指定那份模板；"
                       "换过样式（例如成果版旁边的数字）时，复检加同一个 --style")
        ok = False

    if ok:
        report.check("通过", "内容守恒", "源稿 %d 个可见字符全部进入页面，每行原样连续出现，没有多出的文字" % total)
    else:
        report.check("问题", "内容守恒", "页面和源稿对不上")
    return set(ln for ln, _ in diff.problem_lines())


def body_gaps(res):
    """正文缺什么：一个栏目都没有，或者有栏目下面是空的。"""
    if not res.sections:
        return ["整份源稿只有页头，一个栏目都没有"]
    return ["栏目“%s”下面是空的（第 %d 行）" % (sec.title, sec.lineno) for sec in res.sections if not sec.items]


def check_final_source(report, src_text, res, sample=False):
    """正式稿的源稿检查。返回哪几类已经在这里判断过，页面和 PDF 层不再重复报。

    sample：演练稿的最终版。空位和页头草稿提示照查，“---”之后的虚构标记必须保留。
    """
    hits = []
    for ln, line in enumerate(src_text.splitlines(), 1):
        n = len(PENDING_RE.findall(line))
        if n:
            hits.append((ln, n))
    flagged = {"pending": False, "notice": False, "sample": False}
    gaps = body_gaps(res)
    if gaps:
        report.problem("正式稿的正文不完整：%s" % "；".join(gaps), "源稿",
                       "补上经历内容，或删掉空栏目；只有页头的稿子不能当投递稿")
    if hits:
        total = sum(n for _, n in hits)
        where = "、".join("第 %d 行%s" % (ln, "（%d 处）" % n if n > 1 else "") for ln, n in hits)
        report.problem("正式稿里还有 %d 处 [待确认：……] 空位" % total, where,
                       "向用户问清后填入真实内容，或删去这条主张；正式投递稿不能留空位")
        flagged["pending"] = True
    notes = [(ln, "页头“>”提示") for kind, _, ln in res.meta if kind == "note"]
    tail = [(ln, "“---”之后的标记") for _, ln in res.notices]
    if sample:
        flagged["sample"] = True
        if notes:
            report.problem("演练稿的最终版里还有草稿提示",
                           "、".join("第 %d 行（%s）" % (ln, k) for ln, k in notes),
                           "删除页头的“>”提示；演练稿只保留“---”之后的虚构标记")
            flagged["notice"] = True
        if not tail:
            report.problem("演练稿没有虚构标记", "源稿末尾",
                           "在源稿末尾加单独一行“---”，下面写一句虚构提示，例如“%s”" % SAMPLE_MARK_EXAMPLE)
            flagged["sample_reported"] = True
        elif not has_sample_mark(" ".join(t for t, _ in res.notices), notice=True):
            report.problem("演练稿的虚构标记没有写明是演练或虚构材料",
                           "、".join("第 %d 行" % ln for _, ln in res.notices),
                           "把“---”之后的内容改成一句明确的虚构提示，例如“%s”" % SAMPLE_MARK_EXAMPLE)
            flagged["sample_reported"] = True
    elif notes or tail:
        report.problem("正式稿里还有演练或草稿标记",
                       "、".join("第 %d 行（%s）" % (ln, k) for ln, k in notes + tail),
                       "真实投递稿删除页头的“>”提示和“---”之后的标记；"
                       "演练稿保留“---”之后的虚构标记，改用 --final --sample 检查")
        flagged["notice"] = True
    return flagged


# 整句就是一句声明时也算（“Do not submit.”“请勿投递。”单独成句）；句子里带着别的内容就不算。
STANDALONE_DECLARATIONS = ("donotsubmit", "pleasedonotsubmit", "notforsubmission", "勿投递", "请勿投递",
                           "仅供演练", "仅供练习", "演练材料", "虚构材料", "fictional", "fictitious")


def standalone_declarations(text):
    """按句号、问号、分号和换行切句，返回整句就是声明的那几句。"""
    out = []
    for seg in re.split(r"[.!?。！？;；\n]+", text):
        core = re.sub(r"[\s\W_]+", "", seg).lower()
        if core in STANDALONE_DECLARATIONS:
            out.append(seg.strip())
    return out


def has_sample_mark(text, notice=False):
    """notice=True 表示 text 就是末尾的虚构提示本身；否则是整份页面或 PDF 的文字，只认整句式的声明。"""
    return any(phrase_in(w, text) for w in (NOTICE_MARK_WORDS if notice else SAMPLE_PHRASES))


def phrase_in(phrase, text):
    """不分大小写、忽略空白地找说法：PDF 提取出的英文可能没有空格（“Donotsubmit”）。"""
    return squash(phrase).lower() in squash(text).lower()


_STYLE_DELIM = r"[\s｜|·•▪◦●■—–\-/:：()（）\[\]【】<>「」『』“”\"'‘’,，。；;！!？?]"


def _standalone_style(name, text):
    """样式名作为独立标签或“样式：xxx”出现，而非嵌在“完成经典单栏布局的可用性测试”这类真实经历句子里。"""
    pat = re.compile(r"(?:^|" + _STYLE_DELIM + r")" + re.escape(name) + r"(?=$|" + _STYLE_DELIM + r")")
    if pat.search(text):
        return True
    return bool(re.search(r"(?:样式|风格|模板)\s*[:：]?\s*" + re.escape(name), text))


def find_style_labels(text, expected=None, template=()):
    """找出作为内部样式标签出现的样式名：
    1. 模板自带固定文字里印了样式名且出现在页面/PDF 上；
    2. 有源稿对照（expected）时，页面/PDF 里样式名的出现次数多于源稿预期（模板或导出额外印出）；
    3. 样式名在文本里作为独立标签或“样式：xxx”出现。
    """
    flat = squash(text, True)
    tpl_flat = "".join(squash(t, True) for t in (template or ()))
    exp_flat = "".join(squash(p, True) for _, p in expected) if expected is not None else None
    found = []
    for name in STYLE_NAMES:
        key = squash(name, True)
        count = flat.count(key)
        if not count:
            continue
        if key in tpl_flat:
            found.append(name)
        elif exp_flat is not None and count > exp_flat.count(key):
            found.append(name)
        elif _standalone_style(name, text):
            found.append(name)
    return found


def check_labels(report, text, where_desc, skip_draft_words=False, sample=False, expected=None, template=()):
    """正式稿的用语检查。

    skip_draft_words：源稿的空位或演练标记已经报过，页面文字里那些标记的原文不再重复报。
    sample：演练稿里本来就有“虚构”“演练”这类说法，不查也不提醒；草稿用语照查。
    """
    found = find_style_labels(text, expected=expected, template=template)
    found += [label for label in INTERNAL_LABELS if phrase_in(label, text) and label not in found]
    found += sorted(set(FACT_ID_RE.findall(text)))
    exp_ids = sorted(set(EXP_ID_RE.findall(text)))
    if exp_ids:
        report.warn("%s里有像经历编号的%s；是经历库的内部编号就删掉，真实的型号、故障码等不用改" %
                    (where_desc, "、".join("“%s”" % e for e in exp_ids)))
    if not skip_draft_words:
        phrases = DRAFT_PHRASES if sample else DRAFT_PHRASES + SAMPLE_PHRASES
        found += [w for w in phrases if phrase_in(w, text)]
        if not sample:
            found += [d for d in standalone_declarations(text) if not any(phrase_in(f, d) for f in found)]
    if found:
        report.problem("页面文字里有内部标签或草稿、演练用语：%s" % "、".join("“%s”" % f for f in found), where_desc,
                       "删掉样式名、模板说明、经历编号和草稿用语，这些只放在单独记录里；"
                       "是演练稿就保留虚构声明，改用 --final --sample 并带上 --source 检查")
    if not skip_draft_words:
        covered = "".join(found)
        hints = [w for w in DRAFT_HINT_WORDS if phrase_in(w, text) and w not in covered.lower()
                 and not (sample and w in SAMPLE_HINT_WORDS + ("fictional", "do not submit"))]
        if hints:
            report.warn("%s里有这些词：%s。是草稿或演练用语就删掉再导出；属于真实经历（如“应急演练”“示例代码”）就不用改" %
                        (where_desc, "、".join("“%s”" % w for w in hints)))
    return bool(found)


def check_final_html(report, page, flagged, sample=False, expected=None, template=()):
    """正式稿的页面检查。报过的类别记进 flagged，PDF 文字层不再重复报。"""
    issues = False
    plain = len(PENDING_RE.findall(page.clean))
    if (page.pending or plain) and not flagged.get("pending"):
        where = []
        if page.pending:
            where.append("HTML 里 %d 处 class=\"pending\" 的元素" % page.pending)
        if plain:
            where.append("正文里 %d 处普通文字的 [待确认：……]" % plain)
        report.problem("页面里还有 %d 处待补空位" % (page.pending + plain), "、".join(where),
                       "填入真实内容或删去对应主张后重新生成")
        flagged["pending"] = True
        issues = True
    if sample:
        if page.draft_notes and not flagged.get("notice"):
            report.problem("演练稿的最终版里还有草稿提示", "信息行里的草稿提示（.draft-note）",
                           "删除这条提示；演练稿只保留页面末尾的虚构标记")
            issues = True
        if not flagged.get("sample") and not page.notices:
            report.problem("演练稿没有虚构标记", "页面末尾",
                           "在 </main> 前加一行 <p class=\"sample-notice\">%s</p>；"
                           "从源稿生成时，在源稿末尾加“---”和一句虚构提示" % SAMPLE_MARK_EXAMPLE)
            flagged["sample_reported"] = True
            issues = True
        elif not flagged.get("sample_reported") and page.notices and not has_sample_mark(page.notice_text, notice=True):
            report.problem("演练稿的虚构标记没有写明是演练或虚构材料",
                           "页面末尾的小字提示（.sample-notice）：“%s”" % page.notice_text.strip()[:30],
                           "改成一句明确的虚构提示，例如“%s”" % SAMPLE_MARK_EXAMPLE)
            flagged["sample_reported"] = True
            issues = True
    elif (page.notices or page.draft_notes) and not flagged.get("notice"):
        where = []
        if page.draft_notes:
            where.append("信息行里的草稿提示（.draft-note）")
        if page.notices:
            where.append("页面末尾的小字提示（.sample-notice）")
        report.problem("页面里还有演练或草稿提示", "、".join(where),
                       "真实投递稿删除这些提示；演练稿保留页面末尾的虚构标记，改用 --final --sample 检查")
        issues = True
    clean = PENDING_RE.sub("", page.clean) if flagged.get("pending") else page.clean
    flagged["style_labels"] = set(find_style_labels(clean, expected=expected, template=template))
    issues = check_labels(report, clean, "页面正文", sample=sample, expected=expected, template=template) or issues
    return issues


def evaluate_pdf(report, info, max_pages, expected=None, expected_desc="", final=False,
                 final_flagged=None, html_checked=False, page_hint="", sample=False, page_reported=(),
                 sample_marks=(), template=()):
    """page_reported：页面层已经报过的源稿行号，PDF 层同一行不再重复报。
    sample_marks：源稿或页面里末尾虚构提示的原文；给了就在 PDF 里找这句原文，没给才按声明用语找。
    """
    if not info.is_pdf:
        report.problem("文件不是 PDF", "文件开头没有 %PDF- 标记", "确认导出的是 PDF，而不是改了扩展名的其他文件")
        report.check("问题", "文件格式", "不是 PDF")
        return
    report.check("通过", "文件格式", "是 PDF %s" % info.version)

    if info.pages is None:
        report.warn("没能读出页数，请打开 PDF 人工确认页数")
        report.check("未做", "页数", "没能读出页数")
    elif info.pages > max_pages:
        report.problem("PDF 有 %d 页，超过上限 %d 页" % (info.pages, max_pages), "整份简历",
                       (page_hint or "先删重复和弱相关内容，再调合理间距；") +
                       "不要缩字号或整体缩印挤页。用户允许多页时用 --max-pages 放宽")
        report.check("问题", "页数", "%d 页（上限 %d）" % (info.pages, max_pages))
    else:
        report.check("通过", "页数", "%d 页（上限 %d）" % (info.pages, max_pages))

    if info.text is None:
        note = info.text_note or "没能从 PDF 提取文字"
        report.text_unverified = True
        report.problem("没能读取 PDF 的文字层（%s），文字、空位和声明都没核对" % note, "整份 PDF",
                       "不能当作已核验的成品：换未加密、结构正常的 PDF（例如用脚本或浏览器重新导出）后再查；"
                       "确实只能用这份时，用能解析 CID 字体的工具人工逐字核对")
        if info.cmap_radicals:
            _radical_problem(report, sorted(set(c for _, c in info.cmap_radicals)),
                             sorted(set(f for f, _ in info.cmap_radicals)), [])
            report.check("问题", "文字层部首字符", "ToUnicode 映射里有部首字符")
        else:
            report.check("未做", "文字层部首字符", note)
        report.check("未做", "文字与源稿一致", note)
        return

    text = info.text
    if not squash(text):
        report.problem("PDF 没有可提取的文字层", "全部页面",
                       "简历不能是整页图片；用浏览器打印 HTML 或其他能输出文字的工具重新导出")
        report.check("问题", "文字层", "提取不到文字")
        return

    if "{{" in text:
        report.problem("PDF 里残留了模板占位符 {{", "页面文字", "检查模板占位符是否都已替换")
        report.check("问题", "占位符", "残留 {{")
    else:
        report.check("通过", "占位符", "页面文字没有残留 {{")

    if info.missing_tounicode:
        report.problem("字体缺少 ToUnicode 映射：%s" % "、".join(info.missing_tounicode), "PDF 字体",
                       "招聘系统可能提取出乱码；换浏览器打印或换字体重新导出")

    text_rads = find_radicals(text)
    cmap_rads = [c for _, c in info.cmap_radicals]
    if text_rads or cmap_rads:
        fonts = sorted(set(f for f, _ in info.cmap_radicals)) or info.fonts
        examples = []
        for m in re.finditer("[\u2e80-\u2eff\u2f00-\u2fdf]", text):
            s, e = max(0, m.start() - 6), m.end() + 6
            examples.append(text[s:e].replace("\n", " "))
            if len(examples) >= 3:
                break
        _radical_problem(report, sorted(set(text_rads + cmap_rads)), fonts, examples)
        report.check("问题", "文字层部首字符", "有部首替代字符")
    else:
        report.check("通过", "文字层部首字符",
                     "%d 种字体（%d 个字体对象）的 ToUnicode 映射和提取出的文字里都没有部首字符" %
                     (info.font_kinds, info.font_count))

    if expected is None:
        report.check("未做", "文字与源稿一致", expected_desc or "没有源稿可对照（加 --source 才能核对）")
    else:
        diff = compare_text(expected, text, nfkc=True, template=template, margin=info.margin)
        total = sum(len(squash(p, True)) for _, p in expected)
        known = set(page_reported)
        if known and all(ln in known for ln, _ in diff.problem_lines()):
            if diff.missing or diff.problem_lines():
                report.check("问题", "文字与源稿一致", "和页面层同样的问题，见上方")
                diff = None
        bad = sum(diff.missing.values()) + len(diff.problem_lines()) if diff else 0
        if diff is None:
            pass
        elif not diff.missing and not diff.problem_lines():
            report.check("通过", "文字与源稿一致",
                         "%s的 %d 个字符在 PDF 文字层里都找得到，每行原样连续出现、先后一致，没有多出的文字（NFKC 归一后比较）" %
                         (expected_desc, total))
        elif info.unmapped and diff.missing and info.unmapped >= sum(diff.missing.values()):
            report.warn("PDF 里有 %d 个字形无法按 ToUnicode 解码，%s中有 %d 处没对上，"
                        "无法确定是缺字还是解码不全：请用能解析 CID 字体的工具人工核对" %
                        (info.unmapped, expected_desc, bad))
            report.check("未做", "文字与源稿一致", "有无法解码的字形，结果不可靠")
        else:
            if diff.missing:
                report.problem("PDF 文字层缺了%s里的字符：%s" % (expected_desc, describe_missing(diff.missing)),
                               describe_lines(diff.lines),
                               "检查是否被裁切、隐藏或字体缺字；换字体（--font）重新导出后再查")
            if diff.broken:
                report.problem("PDF 里这些行和%s不一致（字都在，但顺序或位置变了，例如数字对调）" % expected_desc,
                               describe_lines(diff.broken),
                               "以源稿为准改回页面后重新导出；确实要改内容就先改源稿")
            if diff.fields:
                report.problem("PDF 里条目头的字段先后和%s不同（例如公司和岗位对调）" % expected_desc,
                               describe_lines(diff.fields),
                               "按源稿的“名称｜岗位或专业｜时间”放回各自的位置后重新导出；时间排在哪都行")
            if diff.extra:
                report.problem("PDF 里多出了%s没有的文字（例如把一条成果多复制给了另一段经历）" % expected_desc,
                               describe_extra(diff.extra),
                               "删掉多出来的内容后重新导出；确实要加就先写进源稿。"
                               "是自定义模板自带的固定文字时，加 --template 指定那份模板；"
                               "换过样式（例如成果版旁边的数字、边栏的先后）时，复检加同一个 --style")
            if diff.order:
                report.problem("PDF 里这些行的位置和%s不同（例如一条成果挪到了别的经历下）" % expected_desc,
                               "从这里起和源稿对不上：" + describe_lines(diff.order) + "（被挪动的行可能在它们前面）",
                               "以源稿为准把它们放回原来的经历后重新导出；确实要调整顺序就先改源稿；"
                               "换过边栏或成果版等样式时，复检加同一个 --style")
            report.check("问题", "文字与源稿一致", "PDF 文字和%s对不上" % expected_desc)

    if info.not_embedded:
        report.warn("这些字体没有嵌入 PDF：%s；在别的电脑上可能显示成其他字体" % "、".join(info.not_embedded))

    if info.pages == 1 and info.fill is not None:
        pct = int(round(info.fill * 100))
        if info.fill < 0.75:
            report.warn("页面可能没写满：文字只到页面约 %d%% 高度处（不足 3/4）。"
                        "按逐条自查补内容，不靠调大字号或加空行撑满" % pct)
        report.fact("页面填充", "文字到页面约 %d%% 高度处" % pct)
    elif info.pages and info.pages > 1 and info.pages <= max_pages and info.fill is not None:
        pct = int(round(info.fill * 100))
        if info.fill < 0.2:
            report.warn("末页只有几行：文字只到末页约 %d%% 高度处。删掉重复和弱相关内容收回上一页，"
                        "或把偏薄的经历补厚到末页像样，不留孤零零几行" % pct)
        report.fact("页面填充", "共 %d 页，末页文字到约 %d%% 高度处" % (info.pages, pct))

    if final:
        # 空位和虚构标记在 PDF 文字层再查一遍：页面层可能被隐藏、裁掉，或者是别的工具导出的
        flagged = final_flagged if final_flagged is not None else {}
        skip = bool(flagged.get("pending") or flagged.get("notice"))
        if PENDING_RE.search(text) and not flagged.get("pending"):
            report.problem("PDF 里还有 [待确认：……] 空位", "页面文字", "填入真实内容或删去对应主张后重新导出")
        marks = [squash(m, True) for m in sample_marks if squash(m)]
        if marks:
            mark_ok = all(m in squash(text, True) for m in marks)
        else:
            mark_ok = has_sample_mark(text)
        if sample and not flagged.get("sample_reported") and not mark_ok:
            report.problem("演练稿里找不到虚构标记", "PDF 文字",
                           "在源稿末尾加单独一行“---”和一句虚构提示（例如“%s”）后重新导出；"
                           "源稿里有标记却没进 PDF 时，检查页面是否把它隐藏或裁掉了" % SAMPLE_MARK_EXAMPLE)
        if not html_checked:
            check_labels(report, text, "PDF 文字", skip_draft_words=skip, sample=sample,
                         expected=expected, template=template)
        else:
            extra_styles = [s for s in find_style_labels(text, expected=expected, template=template)
                            if s not in flagged.get("style_labels", set())]
            if extra_styles:
                report.problem("页面文字里有内部标签或草稿、演练用语：%s" % "、".join("“%s”" % s for s in extra_styles),
                               "PDF 文字", "删掉模板在正式稿上额外印出的样式名后重新导出")


def _radical_problem(report, chars, fonts, examples):
    where = "字体 %s" % "、".join(fonts) if fonts else "PDF 文字层"
    if examples:
        where += "；例如“%s”" % "”“".join(examples)
    report.problem("PDF 文字层里有部首替代字符：%s；招聘系统提取出来会是错字" % "、".join(radical_label(c) for c in chars),
                   where, "换一种中文字体重新导出（--font 字体名）；不指定 --font 时脚本会自动尝试候选字体")


def page_count_fact(info):
    return "%s 页" % info.pages if info.pages is not None else "未知"


def font_fact(info):
    return "、".join(info.fonts) + "（PDF 实际内嵌）" if info.fonts else "未能读出"


# ---------------------------------------------------------------------------
# 三种模式
# ---------------------------------------------------------------------------

def read_text(path, what):
    p = Path(path)
    if not p.is_file():
        raise CannotRun("%s不存在：%s" % (what, path))
    try:
        return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise CannotRun("%s不是 UTF-8 文本：%s" % (what, path), hint="另存为 UTF-8 编码后重试")


def resolve_out(args, default_from, inputs):
    """确定输出路径，并拒绝会覆盖输入或相互覆盖的组合。inputs 是 [(说明, 路径)]。"""
    out = Path(args.out) if args.out else Path(default_from).with_suffix(".pdf")
    if out.is_dir():
        raise CannotRun("--out 指向的是文件夹，请写成文件路径：%s" % out)
    if not out.parent.is_dir():
        raise CannotRun("输出目录不存在：%s" % out.parent)
    outputs = [("--out 输出的 PDF", out)]
    if getattr(args, "save_html", None):
        outputs.append(("--save-html 另存的页面", Path(args.save_html)))
    seen = [(desc, Path(p)) for desc, p in inputs if p]
    for desc, p in outputs:
        for other, q in seen:
            if same_file(p, q):
                raise CannotRun("%s和%s是同一个文件：%s" % (desc, other, p),
                                hint="换一个输出文件名；输出不能覆盖源稿、模板、页面或另一个输出")
        seen.append((desc, p))
    return out


def same_file(a, b):
    """两个路径是不是同一个文件。

    两边都存在时比文件本身（同一设备同一 inode），大小写不敏感的文件系统、硬链接、符号链接都算；
    有一边还不存在时比规范化后的路径，大小写不同也算同一个（宁可多拦）。
    """
    a, b = Path(a).expanduser(), Path(b).expanduser()
    try:
        if a.exists() and b.exists():
            return os.path.samefile(str(a), str(b))
    except OSError:
        pass
    ra, rb = str(a.resolve()), str(b.resolve())
    return os.path.normcase(ra).casefold() == os.path.normcase(rb).casefold()


HTML_TAG_RE = re.compile(r"<html\b([^>]*)>", re.I)
CLASS_ATTR_RE = re.compile(r"(?<![\w-])class\s*=\s*(\"([^\"]*)\"|'([^']*)')", re.I)


def html_density(html_text):
    """页面当前用的间距档：<html> 上带 compact 这个 class 就是紧凑，否则是标准。"""
    m = HTML_TAG_RE.search(html_text)
    c = CLASS_ATTR_RE.search(m.group(1)) if m else None
    classes = (c.group(2) or c.group(3) or "").split() if c else []
    return "compact" if "compact" in classes else "standard"


def supports_compact(html_text):
    """模板有没有定义紧凑间距（html.compact 的样式）。自带模板有；自定义模板可能没有。"""
    return bool(re.search(r"html\.compact\b", html_text))


def set_density(html_text, density):
    """把 <html> 的 class 改成指定的间距档；只增删 compact 这一个 class，其余不动。"""
    m = HTML_TAG_RE.search(html_text)
    if not m or html_density(html_text) == density:
        return html_text
    attrs = m.group(1)
    c = CLASS_ATTR_RE.search(attrs)
    classes = [x for x in ((c.group(2) or c.group(3) or "").split() if c else []) if x != "compact"]
    if density == "compact":
        classes.append("compact")
    new_class = ' class="%s"' % " ".join(classes) if classes else ""
    if c:
        attrs = attrs[:c.start()].rstrip() + new_class + attrs[c.end():]
    else:
        attrs = attrs.rstrip() + new_class
    if attrs and not attrs[0].isspace():
        attrs = " " + attrs
    return html_text[:m.start()] + "<html" + attrs + ">" + html_text[m.end():]


class Layout(object):
    """这次排版用的间距档、给人看的说明，以及页数超限时该怎么改。"""

    def __init__(self, density, note, hint):
        self.density = density
        self.note = note
        self.hint = hint


def print_fonts(args, report, browser, workdir, html_text, tag, fonts):
    """按字体候选逐个打印，直到文字层没有部首字符。返回 (PDF 数据, 解析结果, 用的字体)。"""
    tried = []
    first = None
    for i, font in enumerate(fonts):
        data = print_pdf(browser, css_font_override(html_text, font), workdir, "%s-%d" % (tag, i), args.timeout)
        info = analyze_pdf(data)
        rad = bool(info.cmap_radicals) or (info.text is not None and bool(find_radicals(info.text)))
        label = font or "模板默认字体"
        tried.append("%s → %s%s" % (label, "、".join(info.fonts) or "未知", "（有部首）" if rad else ""))
        if first is None:
            first = (data, info, font)
        if not rad or args.font or info.text is None:
            if i > 0:
                report.warn("模板默认字体导出后文字层有部首替代字符，已自动改用“%s”重新导出。尝试记录：%s" %
                            (font, "；".join(tried)))
            return data, info, font
    report.warn("自动换字体都没能消除部首字符。尝试记录：%s" % "；".join(tried))
    return first


def print_with_retries(args, report, html_text, base_dir=None):
    """打印并返回 (PDF 数据, 解析结果, 用的字体, Layout)。

    间距：--density 指定了就用那一档；没指定时保持页面原样，页数超过上限且模板有紧凑间距时，
    换紧凑间距再排一次，排得下才采用。字号任何时候都不动。
    """
    browser = find_browser(args.browser)
    if base_dir is not None:
        html_text = add_base_href(html_text, base_dir)
    fonts = [args.font] if args.font else [None] + candidate_fonts()
    wanted = getattr(args, "density", "auto") or "auto"
    can_compact = supports_compact(html_text)
    if wanted == "compact" and not can_compact:
        raise CannotRun("模板没有紧凑间距（找不到 html.compact 的样式）",
                        hint="换用技能自带的 assets/resume-navy.html，或去掉 --density compact")
    if wanted != "auto":
        html_text = set_density(html_text, wanted)
    density = html_density(html_text)
    workdir = Path(tempfile.mkdtemp(prefix="getoffer-pdf-"))
    try:
        data, info, font = print_fonts(args, report, browser, workdir, html_text, density, fonts)
        over = info.pages is not None and info.pages > args.max_pages
        note = DENSITY_NAMES[density]
        hint = ""
        if not can_compact and density == "standard":
            note = "模板自带间距（这份模板没有紧凑间距）"
        if over and density == "compact":
            hint = "已经是紧凑间距，间距不能再压：删掉重复和弱相关的内容，或合并写得散的要点；"
        elif over and wanted == "standard":
            hint = "先删重复和弱相关内容；仍排不下可去掉 --density standard，让脚本改用紧凑间距；"
        elif over and not can_compact:
            hint = "这份模板没有紧凑间距，脚本没法自动收紧：先删重复和弱相关内容，再调合理间距；"
        elif over:
            fonts2 = [font] if font else fonts
            data2, info2, font2 = print_fonts(args, report, browser, workdir,
                                              set_density(html_text, "compact"), "compact", fonts2)
            if info2.pages is not None and info2.pages <= args.max_pages:
                note = "紧凑（标准间距排成 %d 页，超过上限 %d 页，已自动改用紧凑间距，字号不变）" % (
                    info.pages, args.max_pages)
                data, info, font, density = data2, info2, font2, "compact"
            else:
                note = "标准（紧凑间距也要 %s 页，没有采用）" % (info2.pages if info2.pages is not None else "未知")
                hint = "紧凑间距脚本已经试过，仍然排不下：删掉重复和弱相关的内容，或合并写得散的要点；"
        return data, info, font, Layout(density, note, hint)
    finally:
        shutil.rmtree(str(workdir), ignore_errors=True)


def candidate_fonts():
    key = "darwin" if sys.platform == "darwin" else "win32" if sys.platform.startswith("win") else "linux"
    return FONT_CANDIDATES[key][:3]


def template_pieces(tpl):
    """模板自带的固定文字，每个文字节点一段（占位符和注释除外）。自定义模板可能写了“个人简历”这类标题。"""
    bare = re.sub(r"<!--.*?-->", "", tpl, flags=re.S)
    return [t for t in PageText.of(re.sub(r"\{\{\w+\}\}", "", bare)).parts if squash(t)]


def style_template(args):
    """(模板路径, 样式中文名)：--style 指定的样式，或 --template，或默认的墨蓝商务。"""
    if getattr(args, "style", None):
        sid, path, cname = find_style(args.style)
        return path, cname
    if args.template:
        return Path(args.template), ""
    return DEFAULT_TEMPLATE, "墨蓝商务"


def styled_default_name(source, cname):
    """换了非默认样式时默认文件名带样式名，不覆盖同版本已交付的墨蓝商务 PDF。"""
    src = Path(source)
    if not cname or cname == "墨蓝商务":
        return src
    return src.with_name("%s-%s%s" % (src.stem, cname, src.suffix or ".md"))


def font_note(tpl, info):
    """样式首选微软雅黑时，说明 PDF 实际用了什么字体。"""
    if not re.search(r"font-family:\s*\"Microsoft YaHei\"", tpl) or not info.fonts:
        return ""
    if any("yahei" in f.lower() for f in info.fonts):
        return "；样式首选的微软雅黑已嵌入"
    return "；样式首选微软雅黑，本机没有，实际用的是上面这些字体"


def run_markdown(args, report):
    src_text = read_text(args.source_md, "源稿")
    template_path, cname = style_template(args)
    tpl = read_text(template_path, "模板")
    out = resolve_out(args, styled_default_name(args.source_md, cname), [("源稿", args.source_md), ("模板", template_path)])
    res = parse_markdown(src_text)
    html_text = render_html(res, tpl, None if args.lang == "auto" else args.lang)
    for w in res.warnings:
        report.warn(w)
    if cname:
        report.fact("样式", cname)
    page = PageText.of(html_text)
    pieces = layout_pieces(src_text, res, template_layout(tpl))
    pending = len(PENDING_RE.findall(src_text))

    check_source_text(report, src_text)
    if "{{" in html_text:
        report.problem("生成的页面里残留 {{", "HTML", "检查模板占位符或源稿里的“{{”")
    fixed = template_pieces(tpl)
    page_reported = check_conservation(report, pieces, page, fixed)
    if not args.final:
        for gap in body_gaps(res):
            report.warn("正文不完整：%s；投递前要补上内容或删掉空栏目" % gap)
    flagged = {}
    final_before = len(report.problems)
    if args.final:
        flagged = check_final_source(report, src_text, res, args.sample)
        check_final_html(report, page, flagged, args.sample, expected=pieces, template=fixed)
    final_found = len(report.problems) - final_before

    data, info, font, layout = print_with_retries(args, report, html_text)
    if args.save_html:
        # 存的是实际打印用的页面（间距档和字体都和这份 PDF 一样），手工调整后再用 --html 打印，版面接得上
        saved = css_font_override(set_density(html_text, layout.density), font)
        Path(args.save_html).write_text(saved, encoding="utf-8")
        report.fact("HTML", str(Path(args.save_html).resolve()))
    report.fact("页数", page_count_fact(info))
    report.fact("间距", layout.note)
    report.fact("字体", font_fact(info) + ("；按 --font/候选字体“%s”排在最前" % font if font else "") + font_note(tpl, info))
    if pending:
        report.fact("空位", "%d 处 [待确认：……]%s" % (pending, "" if args.final else "，已用橙色标出（待补稿，不能投递）"))
    else:
        report.fact("空位", "0 处")
    pdf_before = len(report.problems)
    evaluate_pdf(report, info, args.max_pages, pieces, "源稿", args.final, flagged, html_checked=True,
                 page_hint=layout.hint, sample=args.sample, page_reported=page_reported,
                 sample_marks=[_strip_wrapper(t) for t, _ in res.notices], template=fixed)
    final_found += count_final_problems(report, pdf_before)
    final_status(report, args.final, final_found, args.sample)
    write_output(report, out, data)


FINAL_PDF_PROBLEMS = ("页面文字里有内部标签", "PDF 里还有 [待确认", "演练稿里找不到虚构标记")


def count_final_problems(report, start):
    """PDF 文字层报出的正式稿问题个数，计入“正式稿检查”那一行。"""
    return sum(1 for what, _, _ in report.problems[start:] if what.startswith(FINAL_PDF_PROBLEMS))


def final_status(report, final, found, sample=False):
    if final and getattr(report, "text_unverified", False):
        report.check("未做", "正式稿检查", "PDF 文字没能读取，没法确认没有空位、草稿提示和演练声明")
    elif not final:
        report.check("未做", "正式稿检查", "未带 --final，按初稿或待补稿处理")
    elif sample and found:
        report.check("问题", "正式稿检查", "空位、草稿提示、虚构标记或内部标签有 %d 项问题，见下方" % found)
    elif sample:
        report.check("通过", "正式稿检查", "没有空位、草稿提示和内部标签，虚构标记已保留")
    elif found:
        report.check("问题", "正式稿检查", "空位、演练标记或内部标签有 %d 项问题，见下方" % found)
    else:
        report.check("通过", "正式稿检查", "没有空位、演练标记和内部标签")
    if final and sample:
        report.fact("稿件", "演练稿（虚构材料），不能用于真实投递")


def failed_pdf_dir():
    """没通过检查的 PDF 放这里：系统临时目录下的固定文件夹。"""
    return Path(tempfile.gettempdir()) / "getoffer-failed-pdf"


def failed_pdf_path(out):
    """按正式文件的完整路径分开存：不同目录里的同名稿互不覆盖，同一份稿重跑时更新自己的那一份。"""
    key = hashlib.sha256(os.path.normcase(str(Path(out).resolve())).encode("utf-8")).hexdigest()[:10]
    return failed_pdf_dir() / key / (Path(out).stem + "-未通过.pdf")


def write_output(report, out, data):
    """通过检查才写正式文件。

    有问题时另存到临时目录并改名，免得没通过的稿子顶着正式文件名留在简历目录里被当成成品。
    """
    if not report.problems:
        out.write_bytes(data)
        report.facts.insert(0, ("输出", str(out.resolve())))
        return
    kept = None
    try:
        kept = failed_pdf_path(out)
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_bytes(data)
    except OSError:
        kept = None
    report.facts.insert(0, ("输出", "有问题，没有写入 %s" % out.resolve()))
    report.facts.insert(1, ("未通过的 PDF", "%s（只供查看，不是成品）" % kept if kept
                            else "没能另存到系统临时目录"))
    if out.is_file():
        report.warn("%s 是之前生成的旧文件，这次没有覆盖，内容和当前源稿不一定一致；修好后重跑会更新" % out.resolve())


def given_template_pieces(args):
    """--html、--check-pdf 时 --template 或 --style 指定的模板里自带的文字；没给就按自带模板（没有固定文字）。"""
    if getattr(args, "style", None):
        return template_pieces(read_text(find_style(args.style)[1], "模板"))
    if not args.template:
        return []
    return template_pieces(read_text(args.template, "模板"))


def given_layout(args):
    if getattr(args, "style", None):
        return template_layout(read_text(find_style(args.style)[1], "模板"))
    if args.template:
        return template_layout(read_text(args.template, "模板"))
    return frozenset()


def run_html(args, report):
    html_path = Path(args.html)
    html_text = read_text(html_path, "HTML 文件")
    fixed = given_template_pieces(args)
    out = resolve_out(args, html_path, [("--html 页面", html_path), ("--source 源稿", args.source),
                                        ("--template 模板", args.template)])
    page = PageText.of(html_text)
    pieces = None
    flagged = {}
    page_reported = set()
    if "{{" in html_text:
        report.problem("HTML 里还有没替换的 {{ 占位符", str(html_path), "把所有占位符替换成内容或删掉对应元素")
    if args.source:
        src_text = read_text(args.source, "源稿")
        try:
            pieces = layout_pieces(src_text, parse_markdown(src_text), template_layout(html_text))
        except CannotRun:
            pieces = source_pieces(src_text)
        check_source_text(report, src_text)
        page_reported = check_conservation(report, pieces, page, fixed)
    else:
        report.check("未做", "内容守恒", "没有 --source，无法对照源稿")
    final_before = len(report.problems)
    if args.final:
        if args.source:
            try:
                flagged = check_final_source(report, src_text, parse_markdown(src_text), args.sample)
            except CannotRun:
                report.warn("--source 的源稿结构超出脚本规则，正式稿检查只按页面做")
        check_final_html(report, page, flagged, args.sample, expected=pieces, template=fixed)
    final_found = len(report.problems) - final_before
    data, info, font, layout = print_with_retries(args, report, html_text, base_dir=html_path.parent)
    report.fact("页数", page_count_fact(info))
    report.fact("间距", layout.note)
    report.fact("字体", font_fact(info) + ("；按 --font/候选字体“%s”排在最前" % font if font else "")
                + font_note(html_text, info))
    report.fact("空位", "页面里 %d 处 .pending" % page.pending)
    pdf_before = len(report.problems)
    if pieces is not None:
        evaluate_pdf(report, info, args.max_pages, pieces, "源稿", args.final, flagged, html_checked=True,
                     page_hint=layout.hint, sample=args.sample, page_reported=page_reported,
                     sample_marks=[page.notice_text] if page.notices else (), template=fixed)
    else:
        evaluate_pdf(report, info, args.max_pages, page.pieces(), "HTML 页面文字", args.final, flagged,
                     html_checked=True, page_hint=layout.hint, sample=args.sample,
                     sample_marks=[page.notice_text] if page.notices else ())
    final_found += count_final_problems(report, pdf_before)
    final_status(report, args.final, final_found, args.sample)
    write_output(report, out, data)


def run_check_pdf(args, report):
    p = Path(args.check_pdf)
    if not p.is_file():
        raise CannotRun("PDF 文件不存在：%s" % args.check_pdf)
    info = analyze_pdf(p.read_bytes())
    fixed = given_template_pieces(args)
    report.fact("文件", str(p.resolve()))
    report.fact("页数", page_count_fact(info))
    report.fact("字体", font_fact(info))
    pieces = None
    flagged = {}
    marks = ()
    final_before = len(report.problems)
    if args.source:
        src_text = read_text(args.source, "源稿")
        try:
            pieces = layout_pieces(src_text, parse_markdown(src_text), given_layout(args))
        except CannotRun:
            pieces = source_pieces(src_text)
        check_source_text(report, src_text)
        final_before = len(report.problems)
        report.fact("空位", "源稿 %d 处 [待确认：……]" % len(PENDING_RE.findall(src_text)))
        if args.final:
            try:
                res = parse_markdown(src_text)
                flagged = check_final_source(report, src_text, res, args.sample)
                marks = [_strip_wrapper(t) for t, _ in res.notices]
            except CannotRun:
                report.warn("--source 的源稿结构超出脚本规则，演练标记只按 PDF 文字检查")
    final_found = len(report.problems) - final_before
    labels_before = len(report.problems)
    evaluate_pdf(report, info, args.max_pages, pieces, "源稿" if pieces else "",
                 args.final, flagged, html_checked=False, sample=args.sample, sample_marks=marks,
                 template=fixed)
    final_found += count_final_problems(report, labels_before)
    final_status(report, args.final, final_found, args.sample)


def print_report(report, title):
    lines = [title]
    for label, value in report.facts:
        lines.append("%s：%s" % (label, value))
    lines.append("检查结果：")
    for status, name, detail in report.checks:
        lines.append("  [%s] %s：%s" % (status, name, detail))
    if report.problems:
        lines.append("发现 %d 个问题：" % len(report.problems))
        for i, (what, where, fix) in enumerate(report.problems, 1):
            lines.append("  %d. %s" % (i, what))
            lines.append("     在哪：%s" % where)
            lines.append("     怎么修：%s" % fix)
    if report.warnings:
        lines.append("警告：")
        for w in report.warnings:
            lines.append("  - %s" % w)
    lines.append("结论：%s" % ("有问题待修（退出码 1）" if report.problems else "通过（退出码 0）"))
    print("\n".join(lines))


def build_parser():
    ap = argparse.ArgumentParser(
        prog="build_resume_pdf.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_md", nargs="?", help="简历 Markdown 源稿")
    ap.add_argument("--out", help="输出 PDF 路径（默认与输入同名，扩展名 .pdf）")
    ap.add_argument("--style", help="简历样式：navy 墨蓝商务（默认）、classic 经典单栏、cobalt 钴蓝边栏、cinnabar 朱砂时间轴、"
                                    "pine 松绿成果版、paper 暖纸书刊；也可写中文名或编号 1 到 5。"
                                    "非默认样式的默认文件名带样式名；复检这类 PDF 时加同一个 --style")
    ap.add_argument("--template", help="HTML 模板（默认 ../assets/resume-navy.html）；配合 --html、--check-pdf 时"
                                       "说明成品用的模板，模板自带的固定文字不算多出来的内容")
    ap.add_argument("--final", action="store_true", help="按正式投递稿检查：空位、演练标记、内部标签算问题")
    ap.add_argument("--sample", action="store_true",
                    help="配合 --final，用于演练稿（虚构材料）的最终版：其余照查，“---”之后的虚构标记必须保留")
    ap.add_argument("--html", help="直接打印这份已填好的 HTML，并做同样的成品检查")
    ap.add_argument("--check-pdf", dest="check_pdf", help="只检查这份 PDF，不生成")
    ap.add_argument("--source", help="配合 --html 或 --check-pdf，用来对照文字的源稿")
    ap.add_argument("--font", help="把这个字体排到正文字体栈最前面（指定后不再自动换字体）")
    ap.add_argument("--browser", help="浏览器可执行文件路径（也可用环境变量 GETOFFER_BROWSER）")
    ap.add_argument("--max-pages", dest="max_pages", type=int, default=1, help="页数上限，默认 1；用户允许多页时放宽")
    ap.add_argument("--density", choices=("auto", "standard", "compact"), default="auto",
                    help="间距：auto（默认）先用标准间距，超过页数上限再换紧凑；standard、compact 固定一档。字号不变")
    ap.add_argument("--timeout", type=int, default=60, help="每次打印的超时秒数，默认 60")
    ap.add_argument("--save-html", dest="save_html", help="另存实际打印用的 HTML（含实际用的间距和字体），方便手工调整后用 --html 打印")
    ap.add_argument("--lang", choices=("auto", "zh-CN", "en"), default="auto",
                    help="页面语言：auto（默认）源稿几乎没有中文时按英文；影响 lang 属性和文档标题")
    return ap


def setup_output():
    """输出被管道接走时固定用 UTF-8；终端里遇到显示不了的字用 ? 代替，不因编码中断。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            if stream.isatty():
                reconfigure(errors="replace")
            else:
                reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    modes = [m for m in (args.source_md, args.html, args.check_pdf) if m]
    try:
        if len(modes) != 1:
            raise CannotRun("请给出一个源稿，或者 --html、--check-pdf 其中之一", hint="运行 --help 查看用法")
        if args.source and not (args.html or args.check_pdf):
            raise CannotRun("--source 只配合 --html 或 --check-pdf 使用")
        if args.sample and not args.final:
            raise CannotRun("--sample 只配合 --final 使用",
                            hint="演练稿的最终版用 --final --sample；初稿和待补稿两个都不加")
        if args.max_pages < 1 or args.timeout < 1:
            raise CannotRun("--max-pages 和 --timeout 必须是正整数")
        if args.style and args.template:
            raise CannotRun("--style 和 --template 只能用一个", hint="自带样式用 --style，自己的模板用 --template")
        if args.style:
            find_style(args.style)
        if args.check_pdf and args.density != "auto":
            raise CannotRun("--density 只在生成或打印时有用，--check-pdf 不改版面")
        if args.check_pdf and args.sample and not args.source:
            raise CannotRun("只核验 PDF 时，--final --sample 必须配合 --source",
                            hint="演练稿是不是演练稿要看源稿末尾“---”之后的虚构提示，单看 PDF 里的词判断不了；"
                                 "加 --source 源稿.md 后重跑")
        if args.lang != "auto" and not args.source_md:
            raise CannotRun("--lang 只在从源稿生成时有用", hint="--html 页面的语言直接改 <html lang=…>")
        if args.save_html and not args.source_md:
            raise CannotRun("--save-html 只在从源稿生成时有用")
        report = Report()
        if args.check_pdf:
            run_check_pdf(args, report)
            title = "GetOffer 简历 PDF 核验"
        elif args.html:
            run_html(args, report)
            title = "GetOffer 简历 PDF：打印 HTML 并核验"
        else:
            run_markdown(args, report)
            title = "GetOffer 简历 PDF：生成并核验"
    except OSError as e:
        e = CannotRun("读写文件失败：%s" % e, hint="检查路径是否存在、是否有写入权限、文件是否被其他程序占用")
        print("无法运行：%s\n怎么办：%s\n结论：无法运行（退出码 2）" % (e.message, e.hint))
        return EXIT_CANNOT_RUN
    except CannotRun as e:
        lines = ["无法运行：%s" % e.message]
        lines += ["  - %s" % d for d in e.details]
        if e.hint:
            lines.append("怎么办：%s" % e.hint)
        lines.append("结论：无法运行（退出码 2）")
        print("\n".join(lines))
        return EXIT_CANNOT_RUN
    print_report(report, title)
    return EXIT_PROBLEM if report.problems else EXIT_OK


if __name__ == "__main__":
    setup_output()
    sys.exit(main())
