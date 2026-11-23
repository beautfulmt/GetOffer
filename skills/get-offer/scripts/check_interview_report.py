#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查面试复盘或模拟面试点评的网页版是否符合 references/report-html.md 的结构规则。

用法：
  python3 check_interview_report.py <报告.html> [--md <报告.md> | --no-md] [--type review|mock]

退出码：
  0  没有错误（可以有提醒）
  1  有错误，修完才能交付
  2  没法运行：参数错误、文件不存在或读不了、不是面试报告模板生成的页面

只用 Python 3 标准库，兼容 Python 3.8 及以上。
"""
import argparse
import os
import re
import sys
import unicodedata
from html.parser import HTMLParser
from urllib.parse import unquote

LABELS = (("good", "答得好"), ("improve", "需补强"), ("redo", "要重练"))
LABEL_OF = dict(LABELS)
KIND_OF = dict((v, k) for k, v in LABELS)

UNCHECKABLE = [
    "实际渲染：宽屏下左右两栏并排、窄屏下上下排列（用浏览器分别看一次）。",
    "同号的标记、“问题在哪”和“改了什么”说的是否真是同一处问题（脚本只核对引用的原话落在同号标记里）。",
    "左栏是否还有没标出的问题说法；左栏是否是完整回答、删节有没有改意思（脚本只做长度提醒）。",
    "追问是否都放在所属卡片里、换了话题是否另起一张；事务性问答是否合并（脚本只按题目关键词提醒）。",
    "处理标签定得对不对；考察点、点评和改进答法本身是否正确，改进答法是否只用已确认的事实。",
    "一句话结论是否按本轮标准；优点和问题是否说清了对面试官判断的影响；“先改这三题”的理由是否成立。",
    "反问环节里说话人标注之外的语义（候选人的问题是否被整理成了面试官的话）。",
    "网页与 Markdown 除题号和标签以外的内容是否一致。",
    "页眉的岗位、轮次、日期、材料来源和评价基准是否齐全准确。",
    "原话和用户材料是否先转义再加标记（脚本只能看到最终页面）。",
]

# ---------------------------------------------------------------- 解析

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
CLOSES_P = {"address", "article", "aside", "blockquote", "details", "div", "dl", "fieldset",
            "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr",
            "main", "nav", "ol", "p", "pre", "section", "summary", "table", "ul"}
P_BOUNDARY = {"div", "section", "td", "th", "li", "details", "summary", "article", "blockquote",
              "body", "main", "header", "footer", "table", "button"}
BLOCKS = {"address", "article", "aside", "blockquote", "br", "details", "div", "dl", "dd", "dt",
          "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main",
          "ol", "p", "pre", "section", "summary", "table", "tr", "td", "th", "ul"}


class Node(object):
    __slots__ = ("tag", "attrs", "children", "parent", "line", "idx", "end")

    def __init__(self, tag, attrs, parent, line):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.parent = parent
        self.line = line
        self.idx = 0
        self.end = 0

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def has_class(self, name):
        return name in self.classes

    def elements(self):
        stack = list(reversed([c for c in self.children if isinstance(c, Node)]))
        while stack:
            node = stack.pop()
            yield node
            stack.extend(reversed([c for c in node.children if isinstance(c, Node)]))

    def find_all(self, pred):
        return [n for n in self.elements() if pred(n)]

    def find(self, pred):
        for n in self.elements():
            if pred(n):
                return n
        return None

    def child_elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def contains(self, other):
        return self.idx < other.idx <= self.end

    def ancestor(self, pred):
        node = self.parent
        while node is not None:
            if pred(node):
                return node
            node = node.parent
        return None


class TreeBuilder(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Node("#root", {}, None, 1)
        self.stack = [self.root]
        self.comments = []

    def _close(self, tag, boundary):
        for i in range(len(self.stack) - 1, 0, -1):
            name = self.stack[i].tag
            if name == tag:
                del self.stack[i:]
                return
            if name in boundary:
                return

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        values = {}
        for key, value in attrs:
            values[key.lower()] = value if value is not None else ""
        if tag in CLOSES_P:
            self._close("p", P_BOUNDARY)
        if tag == "li":
            self._close("li", {"ul", "ol"})
        if tag in ("td", "th"):
            self._close("td", {"tr", "table"})
            self._close("th", {"tr", "table"})
        if tag == "tr":
            self._close("tr", {"table", "tbody", "thead"})
        node = Node(tag, values, self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID and self.stack[-1].tag == tag.lower():
            self.stack.pop()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_comment(self, data):
        self.comments.append((self.getpos()[0], data))


def build_tree(source):
    builder = TreeBuilder()
    builder.feed(source)
    builder.close()
    counter = [0]

    def number(node):
        counter[0] += 1
        node.idx = counter[0]
        for child in node.children:
            if isinstance(child, Node):
                number(child)
        node.end = counter[0]

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
    number(builder.root)
    return builder.root, builder.comments


def raw_text(node, skip=None, lines=False):
    parts = []

    def walk(n):
        for c in n.children:
            if not isinstance(c, Node):
                parts.append(c)
                continue
            if c.tag in ("script", "style", "template"):
                continue
            if skip is not None and skip(c):
                continue
            brk = lines and c.tag in BLOCKS
            if brk:
                parts.append("\n")
            walk(c)
            if brk:
                parts.append("\n")

    walk(node)
    return "".join(parts)


def text(node, skip=None):
    if node is None:
        return ""
    return re.sub(r"\s+", " ", raw_text(node, skip)).strip()


def text_lines(node, skip=None):
    out = []
    for line in raw_text(node, skip, True).split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            out.append(line)
    return out


# ---------------------------------------------------------------- 文本工具

ELLIPSIS_RE = re.compile(r"……|…|\.{3,}|⋯+|。{3,}")
OPEN_CLOSE = {"「": "」", "『": "』", "“": "”"}
ARROW_RE = re.compile(r"^\s*(→|->|—>|=>|⟶|➜|➔|⇒|－>)\s*$")
QREF_RE = re.compile(r"(?<![A-Za-z])Q\s?0*(\d{1,3})(?:-0*(\d{1,3}))?(?!\d)")
TIME_RE = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?::(\d{2}))?(?!\d)")
CIRCLED = dict((chr(0x2460 + i), i + 1) for i in range(20))


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(ch for ch in s if unicodedata.category(ch)[0] in "LN").lower()


def found_in(quote, haystack):
    """忽略空白和标点，省略号处分段，按顺序在 haystack 里找到每一段。"""
    target = norm(haystack)
    segments = [norm(x) for x in ELLIPSIS_RE.split(quote)]
    segments = [x for x in segments if x]
    if not segments:
        return False
    pos = 0
    for seg in segments:
        i = target.find(seg, pos)
        if i < 0:
            return False
        pos = i + len(seg)
    return True


def clip(s, n=26):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def qkey(s):
    m = QREF_RE.search(s or "")
    if not m:
        return None
    return "Q%d" % int(m.group(1)) + ("-%d" % int(m.group(2)) if m.group(2) else "")


def qrefs(s):
    return ["Q%d" % int(a) + ("-%d" % int(b) if b else "") for a, b in QREF_RE.findall(s or "")]


def parse_number(s):
    s = (s or "").strip()
    m = re.match(r"^(\d+)", s)
    if m:
        return int(m.group(1))
    if s[:1] in CIRCLED:
        return CIRCLED[s[:1]]
    return None


def quoted_spans(s):
    spans, i = [], 0
    while i < len(s):
        close = OPEN_CLOSE.get(s[i])
        if close:
            j = s.find(close, i + 1)
            if j < 0:
                break
            spans.append((i, j + 1, s[i + 1:j]))
            i = j + 1
        else:
            i += 1
    return spans


def quote_pairs(s):
    spans = quoted_spans(s)
    pairs = []
    for a, b in zip(spans, spans[1:]):
        if ARROW_RE.match(s[a[1]:b[0]]):
            pairs.append((a[2], b[2]))
    rest = s
    for start, end, _ in reversed(spans):
        rest = rest[:start] + " " + rest[end:]
    return spans, pairs, norm(re.sub(r"(→|->|—>|=>|⟶|➜|➔|⇒)", " ", rest))


def join_nums(nums):
    return "、".join(str(n) for n in nums)


# ---------------------------------------------------------------- 结果收集

class Issues(object):
    def __init__(self):
        self.order = []
        self.items = {}

    def group(self, name):
        if name not in self.items:
            self.order.append(name)
            self.items[name] = []

    def err(self, group, problem, fix, common=None):
        """common：同一类问题去掉题内细节后的说法，多张卡片都有时按它合并成一条。"""
        self.group(group)
        self.items[group].append(("错误", problem, fix, common or problem))

    def warn(self, group, problem, fix, common=None):
        self.group(group)
        self.items[group].append(("提醒", problem, fix, common or problem))

    def count(self, level):
        return sum(1 for g in self.order for item in self.items[g] if item[0] == level)


class Card(object):
    def __init__(self, node, position):
        self.node = node
        self.position = position
        kinds = [k for k, _ in LABELS if node.has_class(k)]
        self.kind = kinds[0] if len(kinds) == 1 else None
        self.kinds = kinds
        self.id = node.attrs.get("id", "")
        qno = node.find(lambda n: n.has_class("q-no"))
        self.qno_text = text(qno)
        self.key = qkey(self.qno_text) or qkey(self.id.upper())
        name = self.qno_text or (self.key or "第 %d 张卡片" % position)
        self.group = "%s（#%s）" % (name, self.id) if self.id else name
        self.name = name


class NotReport(Exception):
    pass


# ---------------------------------------------------------------- 正则

HEADER_BAD_RE = re.compile(r"get[\s_-]?offer|(?<![A-Za-z])v\d+(?:\.\d+){1,2}(?![\d.])|版本号|skill\s*version|技能版本", re.I)
SPEAKER_START_RE = re.compile(
    r"^[\s*#>\-]*(?:(?:候选人|面试者|求职者|应聘者|面试官|追问|反问|HR)[^\s：:（(，。！？]{0,6}|你|我|问|答|回答|Q|A)"
    r"(?:\s*[（(][^）)]{0,12}[）)])?\s*[：:]")
SPEAKER_MID_RE = re.compile(r"(?:^|[。！？!?；;（(\s])(候选人|面试者|面试官|求职者)[^\s：:，。]{0,6}\s*[：:]")
ASK_BACK_RE = re.compile(r"反问|(有什么|有没有|还有什么|有啥)(想|要)?(问|了解)(我|的)|问题(要|想)?问(我|我们)")
ADMIN_RE = re.compile(r"到岗|入职时间|实习多久|实习时长|能实习|每周.{0,4}(几|多少)天|一周.{0,4}(几|多少)天|"
                      r"几轮|后续(流程|安排|还有)|什么时候.{0,6}(结果|通知)|薪资|薪酬|期望.{0,2}(工资|薪)")
GRADE_RE = re.compile(r"评分|打分|总评|及格|综合得分|(?<![\d.])\d{1,3}(?:\.\d)?\s*/\s*(?:10|100)(?![\d.])\s*分?|"
                      r"(?<![\d.:])\d{1,3}(?:\.\d)?\s*分(?![钟析工母子类布成别享组散层支])|"
                      r"(大概率|应该能|肯定能|很可能)(通过|过|拿到\s*offer|进下一轮)|稳过|会挂")
PRIORITY_HEAD_RE = re.compile(r"先改这?\s*[一二两三1-3]?\s*题")
WHO_CAND_RE = re.compile(r"^(你|候选人|我)")
WHO_INTERVIEWER_RE = re.compile(r"^(追问|面试官|HR|主管|面试官回应)")
CLOSING_TITLES = (("下一轮怎么准备", ("下次先练", "下一步怎么准备")),
                  ("可以写进简历的新素材", ("写进简历",)),
                  ("材料与说明", ("材料说明", "材料和说明")))
REVIEW_CARD_LIMIT = 25   # 30 分钟的面试超过这个数才提醒，更长的面试按时长放宽
MOCK_CARD_LIMIT = 14     # 模拟面试各轮的整场提问上限最多 14 问左右，卡片比这还多说明追问被拆开了
EXTERNAL_TAGS = {"img": ("src", "srcset"), "source": ("src", "srcset"), "video": ("src", "poster"),
                 "audio": ("src",), "iframe": ("src",), "embed": ("src",), "object": ("data",),
                 "track": ("src",), "input": ("src",), "image": ("href", "xlink:href"),
                 "use": ("href", "xlink:href")}


def is_inline_ref(value):
    v = (value or "").strip().lower()
    return v == "" or v.startswith("data:") or v.startswith("#") or v.startswith("about:")


# ---------------------------------------------------------------- 检查

class Checker(object):
    def __init__(self, source, path, md_path, md_explicit, report_type):
        self.source = source
        self.path = path
        self.md_path = md_path
        self.md_explicit = md_explicit
        self.forced_type = report_type
        self.R = Issues()
        for name in ("整页", "页眉", "整体评价", "覆盖情况"):
            self.R.group(name)
        self.root, self.comments = build_tree(source)
        self.all = list(self.root.elements())
        self.placeholders = sorted(set(re.findall(r"\{\{\s*([^{}]*?)\s*\}\}", source)))
        self.cards = []
        self.report_type = None
        self.md_note = None

    # -- 入口
    def run(self):
        nodes = self.all
        has_card = any(n.has_class("qcard") for n in nodes)
        looks = has_card or "{{questions}}" in self.source or any(
            n.has_class("report-header") or n.has_class("verdict") for n in nodes)
        if not looks:
            raise NotReport()
        self.cards = [Card(n, i + 1) for i, n in enumerate(n for n in nodes if n.has_class("qcard"))]
        for card in self.cards:
            self.R.group(card.group)
        self.R.group("结尾")
        self.R.group("Markdown 比对")
        self.ids = {}
        self.dup_ids = []
        for n in nodes:
            i = n.attrs.get("id")
            if i is None or i == "":
                continue
            if i in self.ids:
                self.dup_ids.append((i, n))
            else:
                self.ids[i] = n
        self.card_keys = dict((c.key, c) for c in self.cards if c.key)
        self.h2s = [n for n in nodes if n.tag == "h2"]
        self.check_page()
        self.detect_type()
        self.check_header()
        self.locate_regions()
        if "questions" not in self.placeholders:
            self.check_cards()
        if "overview" not in self.placeholders:
            self.check_overview()
            self.check_coverage()
        if "closing" not in self.placeholders:
            self.check_closing()
        self.check_links()
        self.check_markdown()
        self.collapse_repeats()
        return self.R

    # -- 整页
    def check_page(self):
        R, g = self.R, "整页"
        if self.placeholders:
            R.err(g, "还有没替换的占位符：%s。" % "、".join("{{%s}}" % p for p in self.placeholders),
                  "把每个占位符换成实际内容（document_title、header、overview、questions、closing 各一次），页面里不能再出现 {{。")
        elif "{{" in self.source:
            line = self.source[:self.source.index("{{")].count("\n") + 1
            R.err(g, "第 %d 行残留 “{{”。" % line, "删掉残留的模板标记。")
        for line, body in self.comments:
            if "示例" in body or "正式报告删除" in body or "{{" in body:
                R.err(g, "第 %d 行残留模板注释（嵌套示意）。" % line, "正式报告删除整段 <!-- … --> 注释。")
            else:
                R.err(g, "第 %d 行有 HTML 注释：%s" % (line, clip(body, 30)), "正式报告删除注释。")
        scripts = [n for n in self.all if n.tag == "script"]
        inline = "\n".join(raw_text_script(n) for n in scripts if not n.attrs.get("src"))
        if "hashchange" not in inline or ".open" not in inline:
            R.err(g, "缺少模板自带的跳转展开脚本（openTarget：通过链接跳到卡片时自动展开）。",
                  "把模板 <script> 里 openTarget 函数和 hashchange、DOMContentLoaded 两行原样放回。")
        if "beforeprint" not in inline:
            R.err(g, "缺少模板自带的打印前展开全部卡片的脚本（beforeprint）。",
                  "把模板 <script> 里 beforeprint 那段原样放回。")
        for n in self.all:
            what = None
            if n.tag == "script" and n.attrs.get("src"):
                what = "外部脚本 %s" % n.attrs["src"]
            elif n.tag == "link" and n.attrs.get("href") and not is_inline_ref(n.attrs["href"]):
                what = "外部资源 <link href=\"%s\">" % n.attrs["href"]
            elif n.tag in EXTERNAL_TAGS:
                for attr in EXTERNAL_TAGS[n.tag]:
                    if n.attrs.get(attr) and not is_inline_ref(n.attrs[attr]):
                        what = "<%s %s=\"%s\">" % (n.tag, attr, clip(n.attrs[attr], 60))
                        break
            if what:
                R.err(g, "第 %d 行引用了%s，单个文件离线打不开。" % (n.line, what),
                      "删掉外部引用；图片不需要，脚本和样式只用模板内联的那份。")
        css = "\n".join(raw_text_script(n) for n in self.all if n.tag == "style")
        css += "\n" + "\n".join(n.attrs.get("style", "") for n in self.all if n.attrs.get("style"))
        for m in re.finditer(r"@import[^;]*|url\(\s*['\"]?([^)'\"]*)", css):
            if m.group(0).startswith("@import") or not is_inline_ref(m.group(1)):
                R.err(g, "样式里引用了外部文件：%s。" % clip(m.group(0), 60),
                      "删掉 @import / url() 外部引用（含字体），只用模板自带样式。")
        for i, n in self.dup_ids:
            if not n.has_class("qcard"):
                R.err(g, "第 %d 行的 id=\"%s\" 与前面的元素重复。" % (n.line, i), "改成唯一的 id。")
        if "questions" not in self.placeholders and not self.cards:
            R.err(g, "页面里没有任何题目卡片（class=\"qcard …\"）。",
                  "按模板注释的嵌套示意，每个主问题生成一张 <details class=\"qcard …\">。")

    def detect_type(self):
        R = self.R
        if self.forced_type:
            self.report_type = self.forced_type
            return
        title = text(self.root.find(lambda n: n.tag == "title"))
        h1 = text(self.root.find(lambda n: n.tag == "h1"))
        head = title + " " + h1
        base = os.path.basename(self.path)
        if "复盘" in head:
            self.report_type = "review"
        elif "模拟" in head:
            self.report_type = "mock"
        elif "模拟" in base and "复盘" not in base:
            self.report_type = "mock"
        elif "复盘" in base:
            self.report_type = "review"
        elif self.find_coverage_table() is not None:
            self.report_type = "mock"
        else:
            self.report_type = None
            if "header" not in self.placeholders:
                R.warn("页眉", "判断不了这是面试复盘还是模拟面试点评（标题和文件名里没有“复盘”或“模拟”）。",
                       "标题写明“复盘”或“模拟面试点评”，或运行时加 --type review / --type mock；模拟面试点评要有覆盖情况表。")

    def check_header(self):
        R, g = self.R, "页眉"
        title = self.root.find(lambda n: n.tag == "title")
        if "document_title" not in self.placeholders:
            if title is None or not text(title):
                R.err(g, "<title> 为空。", "填上与 h1 一致的报告标题。")
            elif HEADER_BAD_RE.search(text(title)):
                R.warn(g, "<title> 里出现技能名或版本号：%s。" % clip(text(title), 40), "标题只写公司、岗位、轮次和报告类型。")
        if "header" in self.placeholders:
            return
        header = self.root.find(lambda n: n.has_class("report-header")) or self.root.find(lambda n: n.tag == "header")
        if header is None:
            R.err(g, "没有页眉 <header class=\"report-header\">。", "按模板写 h1 和 div.meta。")
            return
        h1 = header.find(lambda n: n.tag == "h1")
        if h1 is None or not text(h1):
            R.err(g, "页眉没有 h1 标题。", "写成 <h1>公司 · 岗位 · 轮次 面试复盘</h1>。")
        if header.find(lambda n: n.has_class("meta")) is None:
            R.warn(g, "页眉没有 .meta 信息行。", "按模板加 <div class=\"meta\"><p>日期｜材料来源｜评价基准</p></div>。")
        m = HEADER_BAD_RE.search(text(header))
        if m:
            R.err(g, "页眉里出现技能名或版本号“%s”。" % m.group(0),
                  "页眉只写岗位、轮次、日期、材料来源和评价基准，删掉技能名和版本号。")

    # -- 区域
    def h2_named(self, names, after=0):
        for n in self.h2s:
            if n.idx > after and any(x in text(n) for x in names):
                return n
        return None

    def locate_regions(self):
        self.ov_h2 = self.h2_named(("整体评价",))
        self.qa_h2 = self.h2_named(("逐题对照", "逐题复盘", "逐题点评"))
        start = self.ov_h2.idx if self.ov_h2 else 0
        end = None
        if self.qa_h2 is not None and self.qa_h2.idx > start:
            end = self.qa_h2.idx
        if self.cards and (end is None or self.cards[0].node.idx < end):
            end = self.cards[0].node.idx
        if end is None:
            end = 10 ** 9
        self.ov_range = (start, end)
        self.closing_start = max([c.node.end for c in self.cards] + [0])

    def in_overview(self, n):
        return self.ov_range[0] < n.idx < self.ov_range[1]

    # -- 卡片
    def check_cards(self):
        R = self.R
        seen_ids = {}
        seen_keys = {}
        for card in self.cards:
            g, n = card.group, card.node
            if n.ancestor(lambda a: a.has_class("qcard")) is not None:
                R.err(g, "这张卡片嵌在另一张卡片里面。", "每张卡片独立放在逐题对照下，不要嵌套。")
            if n.tag != "details":
                R.err(g, "卡片用的是 <%s>，不是模板规定的 <details>，没法折叠展开。" % n.tag,
                      "改成 <details class=\"qcard …\" id=\"…\">，题目行用 <summary class=\"q-head\">。")
            if card.kind is None:
                R.err(g, "卡片类名是 “%s”，应当是 qcard good / qcard improve / qcard redo 之一。" % " ".join(n.classes),
                      "按处理标签只保留一个：good（答得好）、improve（需补强）、redo（要重练）。")
            if not card.id:
                R.err(g, "卡片没有 id，链接跳不过来。", "加上 id，例如 id=\"q03\"。")
            elif card.id in seen_ids:
                R.err(g, "id=\"%s\" 与 %s 重复。" % (card.id, seen_ids[card.id].name), "每张卡片用唯一的 id。")
            else:
                seen_ids[card.id] = card
            if card.key and card.key in seen_keys:
                R.err(g, "题号 %s 与前面一张卡片重复。" % card.name, "题号按顺序 Q01、Q02… 各用一次。")
            elif card.key:
                seen_keys[card.key] = card
            self.check_card(card)
        self.check_card_sequence()

    def check_card_sequence(self):
        R = self.R
        cards = self.cards
        subs = [c for c in cards if c.key and "-" in c.key]
        if subs:
            R.warn("整页", "%d 张卡片用了子题号（%s 等），疑似把追问拆成了单独卡片。" % (len(subs), subs[0].name),
                   "规则是一个主问题一张卡片，追问写在同一张卡片左栏的对话里；换了话题才另起一张，并按 Q01、Q02… 连续编号。")
        else:
            nums = [int(c.key[1:]) for c in cards if c.key]
            if nums and nums != list(range(1, len(nums) + 1)):
                R.warn("整页", "题号不是从 Q01 起连续递增：%s。" % "、".join("Q%02d" % x for x in nums[:30]),
                       "按页面顺序重新编号，并同步整体评价、新素材表和 Markdown 里的题号。")
        for c in cards:
            if c.key and c.id:
                idkey = qkey(c.id.upper())
                if idkey and idkey != c.key:
                    R.warn(c.group, "id “%s” 与题号 %s 不一致，链接文字和跳转目标容易对不上。" % (c.id, c.name),
                           "让 id 与题号对应，例如 Q03 用 id=\"q03\"。")
        if self.report_type == "mock":
            if len(cards) > MOCK_CARD_LIMIT:
                R.warn("整页", "共 %d 张卡片，明显偏多（模拟面试一个主问题一张，通常 6 到 10 张）。" % len(cards),
                       "检查是否把追问拆成了单独卡片；用户要求加题的长练习就保留。")
        else:
            limit = REVIEW_CARD_LIMIT
            minutes = self.interview_minutes()
            if minutes:
                limit = max(limit, int(minutes * float(REVIEW_CARD_LIMIT) / 30 + 0.999))
            if len(cards) > limit:
                extra = "，按最后的时间点这场约 %d 分钟" % minutes if minutes else ""
                R.warn("整页", "共 %d 张卡片，明显偏多（30 分钟左右的面试通常 15 到 20 张%s）。" % (len(cards), extra),
                       "检查是否把追问或事务性问答拆成了单独卡片；确实是长面试就保留。")
        lengths = [len(norm(c_text)) for c_text in (self.candidate_text(c) for c in cards) if c_text is not None]
        if len(lengths) >= 4:
            lengths.sort()
            median = lengths[len(lengths) // 2]
            if median < 40:
                R.warn("整页", "左栏回答整体很短（中位数约 %d 字），像是只摘了一句。" % median,
                       "左栏写出每一轮的完整回答，只删口头语、重复和无关枝节，删处用“……”。")

    def interview_minutes(self):
        best = 0
        for n in self.all:
            if n.has_class("q-time") or n.has_class("who"):
                for m in TIME_RE.finditer(text(n)):
                    if m.group(3):
                        mins = int(m.group(1)) * 60 + int(m.group(2))
                    else:
                        mins = int(m.group(1))
                    best = max(best, mins)
        return best

    def parts(self, card):
        n = card.node
        p = {}
        p["head"] = n.find(lambda x: x.has_class("q-head"))
        p["focus"] = n.find(lambda x: x.has_class("q-focus"))
        p["answer"] = n.find(lambda x: x.has_class("q-answer"))
        p["advice"] = n.find(lambda x: x.has_class("q-advice"))
        return p

    def turns(self, card):
        answer = self.parts(card)["answer"]
        if answer is None:
            return []
        return answer.find_all(lambda x: x.has_class("turn"))

    def candidate_text(self, card):
        answer = self.parts(card)["answer"]
        if answer is None:
            return None
        turns = [t for t in self.turns(card) if not t.has_class("ask")]
        if turns:
            return " ".join(turn_text(t) for t in turns)
        if self.turns(card):
            return ""
        return text(answer, skip=lambda x: x.tag in ("h4", "sup"))

    def check_card(self, card):
        R, g, n = self.R, card.group, card.node
        p = self.parts(card)
        head = p["head"]
        question = ""
        if head is None:
            R.err(g, "没有题目行 .q-head。", "按模板写 <summary class=\"q-head\">：q-no、q-time（可选）、h3 问题原文、chip 标签。")
        else:
            if n.tag == "details" and head.tag != "summary":
                R.err(g, "题目行用的是 <%s>，不是 <summary>，点题目展开不了。" % head.tag, "改成 <summary class=\"q-head\">。")
            if head.find(lambda x: x.has_class("q-no")) is None:
                R.err(g, "题目行没有题号 span.q-no。", "加 <span class=\"q-no\">Q03</span>。")
            h3 = head.find(lambda x: x.tag == "h3")
            question = text(h3)
            if not question:
                R.err(g, "题目行没有问题原文（h3）。", "在 h3 里写面试官的问题原文。")
            chips = [c for c in head.find_all(lambda x: x.has_class("chip")) if not c.has_class("small")]
            if len(chips) != 1:
                R.err(g, "题目右边应当正好一个处理标签，现在有 %d 个。" % len(chips),
                      "保留一个 <span class=\"chip good|improve|redo\">。")
            elif card.kind:
                ck = [k for k, _ in LABELS if chips[0].has_class(k)]
                if ck != [card.kind]:
                    R.err(g, "标签类名（chip %s）与卡片类名（qcard %s）不一致。" % (" ".join(ck) or "无", card.kind),
                          "两处都改成同一个：%s。" % "、".join("%s=%s" % kv for kv in LABELS))
        for chip in n.find_all(lambda x: x.has_class("chip")):
            self.check_chip(g, chip)
        if n.tag == "details" and card.kind:
            is_open = "open" in n.attrs
            if card.kind == "good" and is_open:
                R.err(g, "“答得好”的卡片带了 open，应当默认收起。", "去掉 <details> 上的 open。")
            if card.kind != "good" and not is_open:
                R.err(g, "“%s”的卡片没有 open，应当默认展开。" % LABEL_OF[card.kind], "给 <details> 加上 open。")
        focus = p["focus"]
        if focus is None:
            R.err(g, "没有“面试官想考察”（.q-focus）。", "每题都写一到两项考察点：<div class=\"q-focus\"><strong>面试官想考察：</strong><ul><li>…</li></ul></div>。")
        else:
            items = focus.find_all(lambda x: x.tag == "li")
            if not items and not norm(text(focus, skip=lambda x: x.tag in ("strong", "b")).replace("面试官想考察", "")):
                R.err(g, "“面试官想考察”是空的。", "写一到两项考察点。")
            elif len(items) > 2:
                R.warn(g, "考察点写了 %d 项，规则是一到两项。" % len(items), "合并或删到最关键的一两项。")
        if ASK_BACK_RE.search(question) is None and ADMIN_RE.search(question):
            R.warn(g, "题目“%s”像是事务性问答（到岗、轮次、结果通知等），疑似单独成卡。" % clip(question),
                   "事务性问答合进相邻卡片或写进结尾“材料与说明”，不单独占一张。")
        answer, advice = p["answer"], p["advice"]
        if answer is None:
            R.err(g, "没有左栏“你的回答”（section.q-answer）。", "按模板写左栏，每一轮回答一个 div.turn。")
        if advice is None:
            R.err(g, "没有右栏“怎么改”（section.q-advice）。", "按模板写右栏点评。")
        marks = self.check_turns(card, answer, question) if answer is not None else {}
        if advice is not None:
            self.check_advice(card, advice, marks, answer)

    def check_chip(self, g, chip):
        kinds = [k for k, _ in LABELS if chip.has_class(k)]
        t = text(chip)
        words = [w for _, w in LABELS if w in t]
        if len(kinds) != 1:
            self.R.err(g, "标签“%s”的类名缺少 good / improve / redo。" % clip(t), "类名写成 chip good、chip improve 或 chip redo。")
        elif words != [LABEL_OF[kinds[0]]]:
            self.R.err(g, "标签类名是 chip %s，文字却是“%s”。" % (kinds[0], clip(t)),
                       "文字与类名对应：good=答得好、improve=需补强、redo=要重练。")

    def check_turns(self, card, answer, question):
        R, g = self.R, card.group
        turns = self.turns(card)
        cand = [t for t in turns if not t.has_class("ask")]
        if not cand or not any(norm(turn_text(t)) for t in cand):
            if not turns and norm(text(answer, skip=lambda x: x.tag == "h4")):
                R.err(g, "左栏没有按 div.turn 分轮写回答。", "每一轮回答写成 <div class=\"turn\"><p class=\"who\">你</p><p>完整回答</p></div>，追问用 turn ask。")
            else:
                R.err(g, "左栏没有候选人的回答。", "至少写出一轮完整回答。")
        h4 = answer.find(lambda x: x.tag == "h4")
        if h4 is not None and "节选" in text(h4):
            R.warn(g, "左栏标题写着“节选”。", "左栏要写每一轮的完整回答，不能只摘一句；改完把“节选”删掉。")
        ctext = self.candidate_text(card) or ""
        if cand:
            marked = "".join(text(m, skip=lambda x: x.tag == "sup") for t in cand
                             for m in t.find_all(lambda x: x.tag == "mark"))
            if len(norm(ctext)) < 15:
                R.warn(g, "左栏候选人的回答只有 %d 个字，像是一句节选。" % len(norm(ctext)),
                       "确认这就是完整原答；不是的话补全每一轮回答。")
            elif len(cand) >= 2 and norm(marked) == norm(ctext):
                R.warn(g, "左栏每一轮回答都整段是标记，像是只摘了被点评的句子。", "确认写的是完整回答，标记只覆盖被点评的那几句。")
        ask_back = bool(ASK_BACK_RE.search(question)) or any(
            "面试官回应" in turn_who(t) for t in turns if t.has_class("ask"))
        flagged = set()
        for i, t in enumerate(turns, 1):
            who = turn_who(t)
            body = turn_text(t)
            is_ask = t.has_class("ask")
            if t.find(lambda x: x.has_class("who")) is None:
                hint = ""
                if re.match(r"^(面试官|追问|你|候选人)", body):
                    hint = "（说话人写在了正文开头：“%s”）" % clip(body, 12)
                R.err(g, "左栏第 %d 轮没有说话人 p.who%s。" % (i, hint),
                      "每轮第一行写 <p class=\"who\">你</p>、<p class=\"who\">追问 时间</p> 或 <p class=\"who\">面试官回应</p>，正文里不再写说话人。")
                flagged.add(i)
                continue
            if is_ask and (WHO_CAND_RE.match(who) or "候选人" in who or ("反问" in who and "面试官" not in who)):
                R.err(g, "左栏第 %d 轮标成了面试官的话（turn ask），说话人却是“%s”，说话人标反了。" % (i, clip(who, 16)),
                      "候选人的话用 <div class=\"turn\"><p class=\"who\">你</p>…；turn ask 只放面试官的追问或回应。")
                flagged.add(i)
            elif not is_ask and WHO_INTERVIEWER_RE.match(who):
                R.err(g, "左栏第 %d 轮说话人是“%s”，却没有用 turn ask。" % (i, clip(who, 16)),
                      "面试官的话写成 <div class=\"turn ask\">。")
                flagged.add(i)
            elif ask_back and is_ask and "面试官" not in who:
                R.err(g, "反问环节左栏第 %d 轮标成了“%s”。反问环节提问的是候选人，面试官的回答要标“面试官回应”，不当追问。" % (i, clip(who, 16)),
                      "把这一轮的 p.who 改成“面试官回应”；如果这一轮其实是候选人的提问，改成 turn 并标“你”。")
                flagged.add(i)
        if ask_back:
            cand_text = " ".join(turn_text(t) for t in cand)
            if cand and not re.search(r"[？?吗呢]", cand_text):
                R.warn(g, "这张是反问环节的卡片，但标“你”的几轮里看不到问句。", "核对说话人：候选人的提问标“你”，面试官的回答标“面试官回应”。")
            for i, t in enumerate(turns, 1):
                if t.has_class("ask") and i not in flagged and re.search(r"[？?]\s*$", turn_text(t)):
                    R.warn(g, "反问环节左栏第 %d 轮标为面试官回应，内容却以问号结尾，可能把候选人的提问标成了面试官。" % i,
                           "核对这一轮是谁说的。")
        # 编号标记
        marks = {}
        fix_marks = answer.find_all(lambda x: x.tag == "mark" and x.has_class("fix"))
        order = []
        for k, m in enumerate(fix_marks, 1):
            sups = m.find_all(lambda x: x.tag == "sup")
            num = parse_number(text(sups[0])) if sups else None
            snippet = text(m, skip=lambda x: x.tag == "sup")
            if num is None:
                R.err(g, "左栏第 %d 个红色标记“%s”没有编号。" % (k, clip(snippet, 16)),
                      "在 mark 末尾加 <sup>编号</sup>，并在“问题在哪”和“改了什么”写同号条目。")
                continue
            order.append(num)
            marks.setdefault(num, []).append(snippet)
        dups = sorted(x for x in marks if len(marks[x]) > 1)
        if dups:
            R.err(g, "左栏有重复编号的标记：%s 号各出现不止一次。" % join_nums(dups),
                  "每处有问题的说法单独编号；同一个号只对应一处原话。")
        if marks and sorted(marks) != list(range(1, len(marks) + 1)):
            R.err(g, "左栏标记编号不是从 1 连续：现为 %s。" % join_nums(sorted(marks)),
                  "按出现顺序改成 1、2、3…，右栏“问题在哪”“改了什么”同步改号。")
        elif order and order != sorted(order):
            R.warn(g, "左栏标记编号没有按出现顺序排列：%s。" % join_nums(order), "按左栏出现顺序编号，右栏同步。")
        if card.kind in ("improve", "redo") and not fix_marks:
            R.err(g, "“%s”的卡片左栏没有任何红色问题标记（mark.fix）。" % LABEL_OF[card.kind],
                  "把“问题在哪”指的每处原话用 <mark class=\"fix\">…<sup>1</sup></mark> 标出来。")
        stray = [m for m in card.node.find_all(lambda x: x.tag == "mark" and x.has_class("fix")) if not answer.contains(m)]
        if stray:
            R.warn(g, "左栏以外有 %d 处 mark.fix。" % len(stray), "红色编号标记只用在左栏原答里。")
        return marks

    def check_advice(self, card, advice, marks, answer):
        R, g = self.R, card.group
        secs = advice_sections(advice)
        missing_heads = secs.pop("_missing_heads")
        for name in missing_heads:
            R.err(g, "右栏有 %s 列表，但缺少对应的 h5 小标题。" % name, "按模板在列表前加小标题。")
        better_node = secs.get("better")
        better_text = ""
        if better_node is not None:
            if secs.get("better_loose"):
                R.err(g, "“改进后的答法”没有放在 div.better 里。", "写成 <div class=\"better\"><h5>改进后的答法</h5><p>…</p></div>。")
            better_text = "\n".join("\n".join(text_lines(b, skip=lambda x: x.tag == "h5")) for b in better_node)
        kind = card.kind
        nums = sorted(marks)
        if kind in ("improve", "redo"):
            if not norm(better_text):
                R.err(g, "缺少“改进后的答法”。", "写一段可以直接说出口的完整回答，有追问时连追问的答法一起写。")
            if secs.get("fix") is None or not secs["fix"]:
                R.err(g, "缺少“问题在哪”。", "按左栏编号逐条写缺什么、为什么影响判断：<ol class=\"fix-list\"><li><span class=\"n\">1</span> …</li></ol>。")
            if secs.get("changes") is None or not secs["changes"]:
                R.err(g, "缺少“改了什么”。", "按编号逐条写 「左栏同号标记的原话」→「改进答法里的新说法」：为什么这样改。")
        if kind == "good":
            if not secs.get("keep"):
                R.err(g, "“答得好”的卡片没有“好在哪”。", "写出具体做法：<h5>好在哪</h5><ul class=\"keep-list\"><li>…</li></ul>。")
            if not secs.get("more"):
                R.err(g, "“答得好”的卡片没有“还能更好的一处”。", "写一处可以更好的地方，同样引用原话：「原话」→「新说法」：为什么。")
        for sec, title in (("fix", "问题在哪"), ("changes", "改了什么")):
            items = secs.get(sec)
            if not items:
                continue
            got = []
            no_num = 0
            for item in items:
                num, _ = item_number(item)
                if num is None:
                    no_num += 1
                else:
                    got.append(num)
            if no_num:
                R.err(g, "“%s”有 %d 条没有编号，没法与左栏标记对应%s。" % (
                    title, no_num, "（左栏有 %s 号）" % join_nums(nums) if nums else ""),
                      "每条写成 <li><span class=\"n\">编号</span> …</li>，与左栏标记同号，一个编号一条。",
                      common="“%s”的条目没有编号，没法与左栏标记对应。" % title)
                continue
            dups = sorted(set(x for x in got if got.count(x) > 1))
            if dups:
                R.err(g, "“%s”里编号 %s 重复。" % (title, join_nums(dups)), "一个编号只写一条。")
            lacking = [x for x in nums if x not in got]
            extra = sorted(set(x for x in got if x not in marks))
            if lacking:
                R.err(g, "左栏 %s 号标记在“%s”里没有对应条目。" % (join_nums(lacking), title),
                      "给每个左栏编号补一条同号的“%s”。" % title)
            if extra:
                R.err(g, "“%s”第 %s 条在左栏找不到同号的红色标记。" % (title, join_nums(extra)),
                      "在左栏把对应原话标成 <mark class=\"fix\">…<sup>编号</sup></mark>，或删掉多出的条目。")
        # 改了什么：引用核对
        answer_text = self.candidate_text(card) or ""
        unquoted, no_reason = [], []
        for pos, item in enumerate(secs.get("changes") or [], 1):
            num, body = item_number(item)
            label = str(num) if num is not None else "%d（无编号，按位置）" % pos
            spans, pairs, rest = quote_pairs(body)
            if not pairs:
                unquoted.append((label, body, bool(spans)))
                continue
            if len(rest) < 2:
                no_reason.append(label)
            for orig, new in pairs:
                self.check_quote(g, label, orig, new, marks.get(num), answer_text, better_text)
        if unquoted:
            labels = join_nums([u[0] for u in unquoted])
            sample = unquoted[0][1]
            R.err(g, "“改了什么”第 %s 条没有写成「原话」→「新说法」的引用（例：“%s”）。" % (labels, clip(sample, 22)),
                  "每条改成：「左栏同号标记里的原话」→「改进答法里对应的新说法」：为什么这样改。不写只有概括的条目。",
                  common="“改了什么”有条目没有写成「原话」→「新说法」的引用。")
        if no_reason:
            R.err(g, "“改了什么”第 %s 条只有引用，没写为什么这样改。" % join_nums(no_reason), "在引用后加“：为什么这样改”。",
                  common="“改了什么”有条目只有引用，没写为什么这样改。")
        if kind == "good":
            bad = []
            for item in secs.get("more") or []:
                num, body = item_number(item)
                spans, pairs, rest = quote_pairs(body)
                if not spans:
                    bad.append(body)
                    continue
                if not any(found_in(s[2], answer_text) for s in spans):
                    R.err(g, "“还能更好的一处”引用的「%s」在左栏回答里找不到。" % clip(spans[0][2], 20),
                          "引用左栏里的原话（可用“……”省略中间部分），不要改写。")
                for orig, new in pairs:
                    if better_text and not found_in(new, better_text):
                        R.warn(g, "“还能更好的一处”里的新说法「%s」在改进后的答法里找不到。" % clip(new, 20),
                               "让新说法与改进答法一致，或直接引用改进答法里的句子。")
            if bad:
                R.err(g, "“还能更好的一处”没有引用原话（例：“%s”）。" % clip(bad[0], 22),
                      "写成「左栏原话」→「更好的说法」：为什么，原话要能在左栏找到。",
                      common="“还能更好的一处”没有引用原话。")
        if better_node is not None:
            self.check_better(g, better_node, better_text)
        if kind in ("improve", "redo"):
            practice = advice.find(lambda x: x.has_class("practice"))
            if practice is None and "下次怎么练" not in text(advice):
                R.err(g, "“%s”的卡片没有“下次怎么练”。" % LABEL_OF[kind],
                      "加 <p class=\"practice\"><strong>下次怎么练：</strong>一个练习动作或可能的追问</p>。",
                      common="需补强或要重练的卡片没有“下次怎么练”。")
            elif practice is not None and len(norm(text(practice).replace("下次怎么练", ""))) < 4:
                R.err(g, "“下次怎么练”是空的。", "写一个练习动作或可能的追问。")

    def check_quote(self, g, label, orig, new, mark_texts, answer_text, better_text):
        R = self.R
        if len(norm(orig)) < 2:
            R.err(g, "“改了什么”第 %s 条引用的原话「%s」太短，看不出是哪一句。" % (label, orig), "引用左栏同号标记里的完整原话。")
        elif mark_texts:
            ok = any(found_in(orig, m) for m in mark_texts)
            if not ok:
                ok = any(norm(m) and norm(m) in norm(orig) for m in mark_texts) and found_in(orig, answer_text)
            if not ok:
                where = "在左栏其他位置" if found_in(orig, answer_text) else "在左栏里找不到"
                R.err(g, "“改了什么”第 %s 条引用的原话「%s」不在左栏 %s 号标记里（%s）；%s 号标记是“%s”。"
                      % (label, clip(orig, 20), label, where, label, clip(mark_texts[0], 20)),
                      "让同号的标记、问题和改动说同一处原话：要么引用 %s 号标记里的原话，要么把标记移到这句话上。" % label)
        elif not found_in(orig, answer_text):
            R.err(g, "“改了什么”第 %s 条引用的原话「%s」在左栏里找不到。" % (label, clip(orig, 20)),
                  "原样引用左栏的原话，省略处用“……”。")
        if len(norm(new)) < 2:
            R.err(g, "“改了什么”第 %s 条的新说法「%s」太短。" % (label, new), "引用改进答法里对应的完整新说法。")
        elif not better_text:
            pass
        elif not found_in(new, better_text):
            R.err(g, "“改了什么”第 %s 条的新说法「%s」在改进后的答法里找不到。" % (label, clip(new, 20)),
                  "新说法要原样摘自改进后的答法（可用“……”省略），或把改进答法改成一致。")

    def check_better(self, g, nodes, better_text):
        R = self.R
        found = []
        for b in nodes:
            if b.find(lambda x: x.has_class("who") or x.has_class("turn")) is not None:
                found.append("混入了左栏的 turn / who 结构")
            for line in text_lines(b, skip=lambda x: x.tag == "h5"):
                m = SPEAKER_START_RE.match(line) or SPEAKER_MID_RE.search(line)
                if m:
                    found.append("“%s”" % clip(line, 18))
        if found:
            R.err(g, "改进后的答法里有说话人标签：%s。" % "；".join(found[:3]),
                  "只写回答本身，删掉“候选人：”“面试官：”“追问：”“你：”这类标签；"
                  "有追问时每个追问的答法另起一段，段首用 <strong> 写追问原文，后面直接接回答。")
        sentences = [norm(s) for s in re.split(r"[。！？!?；;\n]", better_text)]
        seen, dups = set(), []
        for s in sentences:
            if len(s) >= 8:
                if s in seen and s not in dups:
                    dups.append(s)
                seen.add(s)
        if dups:
            R.err(g, "改进后的答法里有重复的句子（%d 句），例：“%s”。" % (len(dups), clip(dups[0], 18)),
                  "删掉重复的句子。")

    # -- 整体评价
    def overview_nodes(self, pred):
        return [n for n in self.all if self.in_overview(n) and pred(n)]

    def check_overview(self):
        R, g = self.R, "整体评价"
        if self.ov_h2 is None:
            R.err(g, "没有“整体评价”这个 h2。", "保留模板里的 <h2>整体评价</h2>。")
        panel = self.overview_nodes(lambda n: n.has_class("panel"))
        if not panel:
            R.err(g, "整体评价没有 section.panel。", "按模板注释写 <section class=\"panel\">…</section>。")
        verdict = self.overview_nodes(lambda n: n.has_class("verdict"))
        if not verdict or not norm(text(verdict[0])):
            R.err(g, "缺少一句话结论（p.verdict）。", "写 <p class=\"verdict\">按本轮的标准，一句话结论。</p>。")
        else:
            refs = [r for r in qrefs(text(verdict[0])) if r not in self.card_keys]
            if refs:
                R.warn(g, "一句话结论提到的 %s 没有对应卡片。" % "、".join(refs), "核对题号。")
        panel_text = " ".join(text(p) for p in panel)
        m = GRADE_RE.search(panel_text)
        if m:
            R.warn(g, "整体评价里出现像打分、总评等级或预测结果的说法：“%s”。" % m.group(0),
                   "规则是不打分、不给总评等级、不预测结果；确认这不是评分（例如只是引用的数字）后再保留。")
        self.check_label_summary(g)
        for cls, title in (("strengths", "最突出的优点"), ("issues", "最要害的问题")):
            self.check_points(g, cls, title)
        self.check_priority(g)

    def check_label_summary(self, g):
        R = self.R
        box = self.overview_nodes(lambda n: n.has_class("label-summary"))
        if box:
            chips = box[0].find_all(lambda x: x.has_class("chip"))
        else:
            chips = self.overview_nodes(lambda n: n.has_class("chip") and re.search(r"(答得好|需补强|要重练)\s*\d+", text(n)))
            if chips:
                R.err(g, "标签统计没有放在 div.label-summary 里。", "写成 <div class=\"label-summary\"><span class=\"chip good\">答得好 N</span>…</div>。")
        if not chips:
            R.err(g, "缺少标签统计。", "按模板写三种标签各几张卡片：<div class=\"label-summary\">…</div>。")
            return
        actual = dict((k, 0) for k, _ in LABELS)
        for c in self.cards:
            if c.kind:
                actual[c.kind] += 1
        stated = {}
        for chip in chips:
            self.check_chip(g, chip)
            t = text(chip)
            for k, w in LABELS:
                m = re.search(w + r"\s*(\d+)", t)
                if m:
                    stated[k] = int(m.group(1))
        missing = [LABEL_OF[k] for k, _ in LABELS if k not in stated]
        if missing:
            R.err(g, "标签统计缺少：%s 的数字。" % "、".join(missing), "三种标签都写，0 张也写 0。")
        wrong = ["%s 写 %d、实际 %d" % (LABEL_OF[k], stated[k], actual[k]) for k, _ in LABELS
                 if k in stated and stated[k] != actual[k]]
        if wrong:
            R.err(g, "标签统计与卡片数不一致：%s。" % "；".join(wrong),
                  "改成 答得好 %d、需补强 %d、要重练 %d（按卡片类名数出）。" % (actual["good"], actual["improve"], actual["redo"]))

    def check_points(self, g, cls, title):
        R = self.R
        box = self.overview_nodes(lambda n: n.has_class(cls))
        if not box:
            h4 = self.overview_nodes(lambda n: n.tag in ("h4", "h3", "h5") and title in text(n))
            box = [h4[0].parent] if h4 else []
            if box:
                R.err(g, "“%s”没有放在 div.%s 里。" % (title, cls), "按模板放进 <div class=\"overview-grid\"> 的 <div class=\"%s\">。" % cls)
        if not box:
            R.err(g, "缺少“%s”这一块。" % title, "按模板写 <div class=\"%s\"><h4>%s</h4><ul><li>…，附题号</li></ul></div>。" % (cls, title))
            return
        box = box[0]
        heading = box.find(lambda x: x.tag in ("h4", "h3", "h5"))
        if heading is None or title not in text(heading):
            R.err(g, "“%s”这一块没有小标题。" % title, "加 <h4>%s</h4>。" % title)
        items = box.find_all(lambda x: x.tag == "li") or [p for p in box.find_all(lambda x: x.tag == "p")]
        if not items:
            R.err(g, "“%s”是空的。" % title, "写一两条，每条附题号。")
            return
        if len(items) > 2:
            R.warn(g, "“%s”写了 %d 条，规则是一两条。" % (title, len(items)), "只留最突出或最要害的一两条。")
        for i, li in enumerate(items, 1):
            refs = qrefs(text(li))
            if not refs:
                R.err(g, "“%s”第 %d 条没附题号：“%s”。" % (title, i, clip(text(li), 20)), "在这条里写明出自哪题，例如 Q06。")
            bad = [r for r in refs if r not in self.card_keys]
            if bad:
                R.err(g, "“%s”第 %d 条提到的 %s 没有对应的卡片。" % (title, i, "、".join(bad)), "改成实际存在的题号。")

    def check_priority(self, g):
        R = self.R
        heads = self.overview_nodes(lambda n: n.tag in ("h4", "h3", "h5") and PRIORITY_HEAD_RE.search(text(n)))
        lists = self.overview_nodes(lambda n: n.has_class("priority"))
        need = min(3, sum(1 for c in self.cards if c.kind in ("improve", "redo")))
        if need == 0:
            if heads or lists:
                R.err(g, "没有需补强或要重练的卡片，却写了“先改这三题”。", "全部答得好时删掉“先改这三题”的小标题和列表。")
            return
        if not lists and heads:
            lists = [n for n in self.all if n.tag in ("ol", "ul") and n.idx > heads[0].idx and self.in_overview(n)][:1]
            if lists:
                R.err(g, "“先改这三题”的列表没有用 ol.priority。", "写成 <ol class=\"priority\">。")
        if not heads:
            R.err(g, "缺少“先改这三题”的小标题。", "加 <h4>先改这三题</h4>。")
        if not lists:
            R.err(g, "缺少“先改这三题”列表。", "写 <ol class=\"priority\"><li><a href=\"#q12\">Q12 …</a>：为什么先改</li>…</ol>。")
            return
        items = lists[0].find_all(lambda x: x.tag == "li")
        if len(items) != need:
            why = "" if need == 3 else "（需补强和要重练的卡片一共只有 %d 张）" % need
            R.err(g, "“先改这三题”列了 %d 题，应当是 %d 题%s。" % (len(items), need, why),
                  "从需补强和要重练的卡片里选最该先改的 %d 题，不足三题就有几题写几题。" % need)
        targets = []
        for i, li in enumerate(items, 1):
            links = li.find_all(lambda x: x.tag == "a" and (x.attrs.get("href") or "").startswith("#"))
            if not links:
                R.err(g, "“先改这三题”第 %d 条没有跳转链接。" % i, "写成 <a href=\"#q12\">Q12 题目简称</a>。")
            else:
                a = links[0]
                target_id = unquote(a.attrs["href"][1:])
                el = self.ids.get(target_id)
                card = None
                if el is not None:
                    card_node = el if el.has_class("qcard") else el.ancestor(lambda x: x.has_class("qcard"))
                    card = next((c for c in self.cards if c.node is card_node), None)
                if el is None:
                    R.err(g, "“先改这三题”第 %d 条链接 #%s 指向不存在的 id。" % (i, target_id), "改成对应卡片的 id。")
                elif card is None:
                    R.err(g, "“先改这三题”第 %d 条链接 #%s 指向的不是题目卡片。" % (i, target_id), "改成对应卡片的 id。")
                else:
                    if card.kind == "good":
                        R.err(g, "“先改这三题”第 %d 条指向 %s，这是“答得好”的卡片。" % (i, card.name),
                              "先改的题应从需补强或要重练的卡片里选。")
                    shown = qkey(text(a))
                    if shown and card.key and shown != card.key:
                        R.err(g, "“先改这三题”第 %d 条链接文字写 %s，实际跳到 %s。" % (i, shown, card.name),
                              "让链接文字和 href 指向同一题。")
                    if card.node in targets:
                        R.err(g, "“先改这三题”第 %d 条与前面重复指向 %s。" % (i, card.name), "三题各不相同。")
                    targets.append(card.node)
            reason = norm(text(li, skip=lambda x: x.tag == "a"))
            if len(reason) < 4:
                R.err(g, "“先改这三题”第 %d 条没写为什么先改。" % i, "链接后加一句理由：为什么这题最该先改。")

    # -- 覆盖情况
    def find_coverage_table(self):
        start, end = self.ov_range if hasattr(self, "ov_range") else (0, 10 ** 9)
        if self.cards:
            end = min(end, self.cards[0].node.idx)
        for n in self.all:
            if n.tag == "table" and n.idx < end:
                header = n.find(lambda x: x.tag == "tr")
                if header is not None and "能力" in text(header):
                    return n
        return None

    def check_coverage(self):
        R, g = self.R, "覆盖情况"
        if self.report_type != "mock":
            return
        table = self.find_coverage_table()
        if table is None:
            R.err(g, "模拟面试点评缺少覆盖情况表。", "在整体评价后、逐题对照前加 <h2>覆盖情况</h2> 和表格：能力｜类型｜在哪题考到｜表现；没考到的写“未考到，未知”。")
            return
        rows = table.find_all(lambda x: x.tag == "tr")
        head = text(rows[0])
        miss = [c for c in ("能力", "类型", "在哪题考到", "表现") if c not in head]
        if miss:
            R.err(g, "覆盖情况表缺少列：%s。" % "、".join(miss), "表头写成：能力｜类型｜在哪题考到｜表现。")
        if len(rows) < 2:
            R.err(g, "覆盖情况表没有内容行。", "按覆盖计划逐项填写硬技能和软技能。")
        heads = [norm(text(c)) for c in rows[0].find_all(lambda x: x.tag in ("th", "td"))]
        col = {}
        for name in ("能力", "类型", "在哪题考到", "表现"):
            for i, h in enumerate(heads):
                if name in h:
                    col[name] = i
                    break
        for n, r in enumerate(rows[1:], 1):
            raw = [text(c) for c in r.find_all(lambda x: x.tag in ("th", "td"))]
            cells = [norm(c) for c in raw]
            label = "第 %d 行%s" % (n, "“%s”" % clip(cells[col["能力"]], 12)
                                     if "能力" in col and col["能力"] < len(cells) and cells[col["能力"]] else "")
            empty = [name for name, i in sorted(col.items(), key=lambda kv: kv[1])
                     if i >= len(cells) or not cells[i]]
            if empty:
                R.err(g, "覆盖情况表%s的%s是空的。" % (label, "、".join(empty)),
                      "每行写齐能力、类型（硬技能或软技能）、在哪题考到（题号）和表现；没考到的写“未考到”，表现写“未知”。")
                continue
            if "类型" in col and not any(w in cells[col["类型"]] for w in ("硬", "软")):
                R.warn(g, "覆盖情况表%s的类型写成了“%s”。" % (label, clip(cells[col["类型"]], 10)),
                       "类型写“硬技能”或“软技能”。")
            if "在哪题考到" in col:
                where = cells[col["在哪题考到"]]
                if not qrefs(raw[col["在哪题考到"]]) and "未考到" not in where:
                    R.err(g, "覆盖情况表%s的“在哪题考到”既没有题号也没写“未考到”：“%s”。" % (label, clip(where, 12)),
                          "写实际考到的题号，如 Q03；整轮没问到就写“未考到”。")
                elif "未考到" in where and "表现" in col and "未知" not in cells[col["表现"]]:
                    R.err(g, "覆盖情况表%s没考到，表现却写了“%s”。" % (label, clip(cells[col["表现"]], 12)),
                          "没考到的能力表现写“未知”，不凭简历推断。")
            bad = [x for x in qrefs(text(r)) if x not in self.card_keys]
            if bad:
                R.err(g, "覆盖情况表“%s”一行提到的 %s 没有对应卡片。" % (clip(text(r), 12), "、".join(bad)), "改成实际存在的题号。")

    # -- 结尾
    def check_closing(self):
        R, g = self.R, "结尾"
        after = self.closing_start
        found = []
        for title, old_names in CLOSING_TITLES:
            h2 = self.h2_named((title,), after=after)
            if h2 is None:
                renamed = self.h2_named(old_names, after=after) if old_names else None
                if renamed is not None:
                    R.err(g, "结尾的“%s”标题写成了“%s”。" % (title, clip(text(renamed), 16)),
                          "复盘和模拟点评用同一组标题，改成 <h2>%s</h2>。" % title)
                    h2 = renamed
                elif self.h2_named((title,)) is not None:
                    R.err(g, "“%s”放在了卡片前面。" % title, "结尾各块放在最后一张卡片之后。")
                    continue
                else:
                    R.err(g, "缺少结尾的“%s”。" % title, "按模板在最后一张卡片后写 <h2>%s</h2> 和对应内容。" % title)
                    continue
            found.append((title, h2))
        idxs = [h.idx for _, h in found]
        if idxs != sorted(idxs):
            R.err(g, "结尾各块顺序不对：现为 %s。" % "→".join(t for t, _ in sorted(found, key=lambda x: x[1].idx)),
                  "依次为：下一轮怎么准备 → 可以写进简历的新素材 → 材料与说明。")
        h2_after = [n for n in self.h2s if n.idx > after]
        for title, h2 in found:
            nxt = [n.idx for n in h2_after if n.idx > h2.idx]
            stop = nxt[0] if nxt else 10 ** 9
            body = [n for n in self.all if h2.end < n.idx < stop and n.parent is not None and not (h2.end < n.parent.idx < stop)]
            content = " ".join(text(n) for n in body)
            if not norm(content):
                R.err(g, "“%s”下面是空的。" % title, "写上实际内容；新素材没有时写“无”。")
                continue
            if title == "可以写进简历的新素材":
                self.check_material(g, body)

    def check_material(self, g, body):
        R = self.R
        tables = [n for b in body for n in ([b] if b.tag == "table" else b.find_all(lambda x: x.tag == "table"))]
        if not tables:
            if re.search(r"^\s*(无|没有)", " ".join(text(b) for b in body)):
                return
            R.err(g, "“可以写进简历的新素材”不是表格。",
                  "写成表格：来源题号与原话｜对应经历｜候选改写｜确认状态；没有新素材写“无”。")
            return
        rows = tables[0].find_all(lambda x: x.tag == "tr")
        if not rows:
            R.err(g, "新素材表是空的。", "按表头填写，或删掉表格写“无”。")
            return
        head = text(rows[0])
        miss = [c for c, keys in (("来源题号与原话", ("来源",)), ("对应经历", ("经历",)), ("候选改写", ("改写",)), ("确认状态", ("确认",)))
                if not all(k in head for k in keys)]
        if miss:
            R.err(g, "新素材表缺少列：%s。" % "、".join(miss), "表头写成：来源题号与原话｜对应经历｜候选改写｜确认状态。")
        for i, r in enumerate(rows[1:], 1):
            cells = r.find_all(lambda x: x.tag in ("td", "th"))
            first = text(cells[0]) if cells else ""
            refs = qrefs(first)
            if not refs:
                R.err(g, "新素材表第 %d 行的来源没写题号：“%s”。" % (i, clip(first, 16)), "来源写成“Q07 原话……”。")
            bad = [x for x in refs if x not in self.card_keys]
            if bad:
                R.err(g, "新素材表第 %d 行的来源 %s 没有对应卡片。" % (i, "、".join(bad)), "改成实际存在的题号。")

    # -- 链接
    def check_links(self):
        R = self.R
        for a in self.all:
            href = a.attrs.get("href") if a.tag == "a" else None
            if not href or not href.startswith("#") or len(href) < 2:
                continue
            target = unquote(href[1:])
            if target in self.ids:
                continue
            card_node = a.ancestor(lambda x: x.has_class("qcard"))
            card = next((c for c in self.cards if c.node is card_node), None)
            if card is not None:
                g = card.group
            elif self.in_overview(a):
                g = "整体评价"
            elif a.idx > self.closing_start and self.cards:
                g = "结尾"
            else:
                g = "整页"
            if g == "整体评价" and a.ancestor(lambda x: x.has_class("priority")) is not None:
                continue  # 已在“先改这三题”里报过
            R.err(g, "链接 %s（“%s”）指向不存在的 id。" % (href, clip(text(a), 16)), "改成页面里实际存在的卡片 id。")

    # -- Markdown
    def check_markdown(self):
        R, g = self.R, "Markdown 比对"
        if self.md_path is None or not self.cards:
            if self.md_path is None and not self.md_explicit and self.cards:
                R.warn(g, "旁边没有同名 Markdown 报告，没有比对题数和标签。",
                       "规则要求网页和 Markdown 同名、内容一致；如果 Markdown 在别处，用 --md 指定。")
            return
        try:
            md = read_text(self.md_path)
        except (IOError, OSError, UnicodeDecodeError) as exc:
            R.warn(g, "读不了 Markdown 报告：%s。" % exc, "确认文件是 UTF-8 文本。")
            return
        sections = parse_markdown(md)
        if not sections:
            R.warn(g, "Markdown 里没认出题目标题（应为“### Q01：问题原文”这类），没有比对。",
                   "Markdown 按模板写题目标题和“处理标签”后再运行。")
            return
        md_keys = [k for k, _ in sections]
        html_keys = [c.key for c in self.cards if c.key]
        dup = sorted(set(k for k in md_keys if md_keys.count(k) > 1))
        if dup:
            R.err(g, "Markdown 里题号重复：%s。" % "、".join(dup), "Markdown 每题一个标题，题号不重复。")
        only_html = [k for k in html_keys if k not in md_keys]
        only_md = [k for k in md_keys if k not in html_keys]
        if len(md_keys) != len(html_keys) or only_html or only_md:
            detail = []
            if only_html:
                detail.append("网页有、Markdown 没有：%s" % "、".join(only_html[:12]))
            if only_md:
                detail.append("Markdown 有、网页没有：%s" % "、".join(only_md[:12]))
            R.err(g, "题数不一致：网页 %d 题，Markdown %d 题。%s" % (len(html_keys), len(md_keys), "；".join(detail)),
                  "两份报告按同一套题目和编号输出。")
        md_labels = dict(sections)
        unknown = []
        for c in self.cards:
            if not c.key or c.key not in md_labels or not c.kind:
                continue
            label = md_labels[c.key]
            if label is None:
                unknown.append(c.key)
            elif KIND_OF[label] != c.kind:
                R.err(c.group, "处理标签与 Markdown 不一致：网页是“%s”，Markdown 是“%s”。" % (LABEL_OF[c.kind], label),
                      "两份报告用同一个标签，并同步标签统计。")
        if unknown:
            R.warn(g, "Markdown 里这些题没认出处理标签，没有比对：%s。" % "、".join(unknown[:12]),
                   "Markdown 每题写“- **处理标签：**需补强”。")

    # -- 汇总重复
    def collapse_repeats(self):
        R = self.R
        card_groups = [c.group for c in self.cards]
        if len(card_groups) < 5:
            return
        tally, order = {}, []
        for gname in card_groups:
            seen = set()
            for level, problem, fix, common in R.items.get(gname, []):
                key = (level, common, fix)
                if key in seen:
                    continue
                seen.add(key)
                if key not in tally:
                    tally[key] = []
                    order.append(key)
                tally[key].append((gname, problem))
        for key in order:
            hits = tally[key]
            if len(hits) < 5:
                continue
            level, common, fix = key
            for gname, _ in hits:
                R.items[gname] = [x for x in R.items[gname] if (x[0], x[3], x[2]) != key]
            names = "、".join(g.split("（")[0] for g, _ in hits)
            problem = "%d 张卡片都有同一问题（%s）：%s" % (len(hits), names, common)
            first_group, first_problem = hits[0]
            if first_problem != common:
                problem += "例如 %s：%s" % (first_group.split("（")[0], first_problem)
            R.items["整页"].append((level, problem, fix, common))


def raw_text_script(node):
    return "".join(c for c in node.children if not isinstance(c, Node))


def turn_who(turn):
    who = turn.find(lambda x: x.has_class("who"))
    return text(who, skip=lambda x: x.has_class("chip")) if who is not None else ""


def turn_text(turn):
    return text(turn, skip=lambda x: x.has_class("who") or x.tag == "sup")


def item_number(item):
    n = item.find(lambda x: x.has_class("n"))
    if n is not None:
        return parse_number(text(n)), text(item, skip=lambda x: x.has_class("n"))
    body = text(item)
    m = re.match(r"^\s*(\d+|[①-⑳])\s*[\.、．:：)）]?\s*", body)
    if m:
        return parse_number(m.group(1)), body[m.end():]
    return None, body


def classify_heading(t):
    if "好在哪" in t:
        return "keep"
    if "问题在哪" in t:
        return "fix"
    if "改了什么" in t:
        return "changes"
    if "还能更好" in t:
        return "more"
    if "改进后的答法" in t or "改进答法" in t:
        return "better_head"
    if "下次怎么练" in t:
        return "practice"
    return "other"


def advice_sections(advice):
    secs = {"keep": None, "fix": None, "changes": None, "more": None, "better": None,
            "better_loose": False, "_missing_heads": []}
    current = None
    loose = []
    for c in advice.child_elements():
        if c.tag == "h4":
            continue
        if c.tag in ("h5", "h6"):
            current = classify_heading(text(c))
            if current in ("keep", "fix", "changes", "more") and secs[current] is None:
                secs[current] = []
            continue
        if c.has_class("better"):
            secs["better"] = (secs["better"] or []) + [c]
            current = None
            continue
        if c.has_class("practice"):
            current = None
            continue
        if current in ("keep", "fix", "changes", "more"):
            if c.tag in ("ul", "ol"):
                secs[current].extend(x for x in c.child_elements() if x.tag == "li")
            elif norm(text(c)):
                secs[current].append(c)
        elif current == "better_head":
            loose.append(c)
        elif c.tag in ("ol", "ul"):
            if c.has_class("fix-list") and secs["fix"] is None:
                secs["fix"] = [x for x in c.child_elements() if x.tag == "li"]
                secs["_missing_heads"].append("fix-list（问题在哪）")
            elif c.has_class("changes") and secs["changes"] is None and secs["more"] is None:
                secs["changes"] = [x for x in c.child_elements() if x.tag == "li"]
                secs["_missing_heads"].append("changes（改了什么）")
    if secs["better"] is None and loose:
        secs["better"] = loose
        secs["better_loose"] = True
    return secs


# ---------------------------------------------------------------- Markdown

MD_Q_RE = re.compile(r"^\s{0,3}(#{1,6})\s*Q\s*0*(\d{1,3})(?:\s*-\s*0*(\d{1,3}))?(?=[\s：:　.、]|$)")
MD_HEAD_RE = re.compile(r"^\s{0,3}(#{1,6})\s")
MD_LABEL_FIELD_RE = re.compile(r"处理标签\s*\**\s*[：:]\s*\**\s*(答得好|需补强|要重练)")
MD_LABEL_START_RE = re.compile(r"^[\s>*\-]*\**\s*(答得好|需补强|要重练)")


def parse_markdown(md):
    sections = []
    current = None
    fence = None
    for line in md.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            kind = marker.group(1)[0]
            fence = None if fence == kind else (kind if fence is None else fence)
            continue
        if fence:
            continue
        mq = MD_Q_RE.match(line)
        mh = MD_HEAD_RE.match(line)
        if mq:
            key = "Q%d" % int(mq.group(2)) + ("-%d" % int(mq.group(3)) if mq.group(3) else "")
            current = {"key": key, "level": len(mq.group(1)), "lines": []}
            sections.append(current)
            continue
        if mh and current is not None and len(mh.group(1)) <= current["level"]:
            current = None
            continue
        if current is not None:
            current["lines"].append(line)
    result = []
    for s in sections:
        label = None
        for line in s["lines"]:
            m = MD_LABEL_FIELD_RE.search(line)
            if m:
                label = m.group(1)
                break
        if label is None:
            first = next((x for x in s["lines"] if x.strip()), "")
            m = MD_LABEL_START_RE.match(first)
            if m:
                label = m.group(1)
        result.append((s["key"], label))
    return result


# ---------------------------------------------------------------- 输出

def read_text(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if b"\x00" in data[:4096]:
        raise UnicodeDecodeError("utf-8", data[:1], 0, 1, "二进制文件")
    return data.decode("utf-8-sig")


def render(checker, path):
    R = checker.R
    cards = checker.cards
    counts = dict((k, 0) for k, _ in LABELS)
    for c in cards:
        if c.kind:
            counts[c.kind] += 1
    errors, warns = R.count("错误"), R.count("提醒")
    kind = {"review": "面试复盘", "mock": "模拟面试点评"}.get(checker.report_type, "类型未判定")
    lines = []
    lines.append("%s：%d 张卡片（答得好 %d、需补强 %d、要重练 %d），%s，错误 %d 条，提醒 %d 条。"
                 % (os.path.basename(path), len(cards), counts["good"], counts["improve"], counts["redo"], kind, errors, warns))
    if errors or warns:
        lines.append("错误是规则写死的结构要求，修完才能交付；提醒是启发式判断，可能有例外，请再看一眼后自己决定。")
    for gname in R.order:
        items = R.items[gname]
        if not items:
            continue
        lines.append("")
        lines.append("【%s】" % gname)
        for level, problem, fix, _ in sorted(items, key=lambda x: 0 if x[0] == "错误" else 1):
            lines.append("  %s：%s" % (level, problem))
            lines.append("    修法：%s" % fix)
    if not errors:
        lines.append("")
        lines.append("没有发现结构错误。" + ("上面的提醒请逐条确认。" if warns else ""))
        lines.append("以下事项脚本查不了，交付前仍需自己看：")
        for i, item in enumerate(UNCHECKABLE, 1):
            lines.append("  %d. %s" % (i, item))
    return "\n".join(lines)


class ChineseArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("参数错误：%s\n用法：check_interview_report.py <报告.html> [--md 报告.md | --no-md] [--type review|mock]\n" % message)
        sys.exit(2)


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
    parser = ChineseArgumentParser(
        prog="check_interview_report.py",
        description="检查面试复盘 / 模拟面试点评网页是否符合 report-html.md 的结构规则。退出码：0 无错误，1 有错误，2 无法运行。")
    parser.add_argument("report", help="要检查的报告 .html")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--md", help="同名 Markdown 报告；默认自动找网页旁边的同名 .md")
    group.add_argument("--no-md", action="store_true", help="不比对 Markdown")
    parser.add_argument("--type", choices=("review", "mock"), help="报告类型：review 面试复盘，mock 模拟面试点评；默认按标题和文件名判断")
    args = parser.parse_args(argv)

    path = args.report
    if not os.path.isfile(path):
        sys.stderr.write("没法运行：找不到文件 %s\n" % path)
        return 2
    try:
        source = read_text(path)
    except (IOError, OSError) as exc:
        sys.stderr.write("没法运行：读不了 %s（%s）\n" % (path, exc))
        return 2
    except UnicodeDecodeError:
        sys.stderr.write("没法运行：%s 不是 UTF-8 文本，不像本模板生成的网页。\n" % path)
        return 2
    md_path = None
    md_explicit = bool(args.md) or args.no_md
    if args.md:
        if not os.path.isfile(args.md):
            sys.stderr.write("没法运行：找不到 Markdown 文件 %s\n" % args.md)
            return 2
        md_path = args.md
    elif not args.no_md:
        guess = os.path.splitext(path)[0] + ".md"
        if os.path.isfile(guess):
            md_path = guess
    try:
        checker = Checker(source, path, md_path, md_explicit, args.type)
        checker.run()
    except NotReport:
        sys.stderr.write("没法运行：%s 不像面试报告模板生成的页面（没有 qcard 卡片、report-header 页眉或模板占位符）。"
                         "请确认传入的是 assets/interview-report.html 生成的报告。\n" % path)
        return 2
    except Exception as exc:  # 结构偏差太大导致的意外，不给堆栈
        sys.stderr.write("没法运行：解析 %s 时出错（%s: %s）。页面结构可能与模板差别太大。\n" % (path, type(exc).__name__, exc))
        return 2
    print(render(checker, path))
    return 1 if checker.R.count("错误") else 0


if __name__ == "__main__":
    setup_output()
    sys.exit(main())
