#!/usr/bin/env python3
"""Validate the atlas data and generate a GitHub Pages-ready static site."""
import html
import json
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {"sage", "peach", "lavender"}
SHAPES = {
    "orbit": '<circle cx="150" cy="130" r="78" stroke="currentColor" stroke-width="2"/><circle cx="150" cy="130" r="49" stroke="currentColor" stroke-width="2"/><circle cx="150" cy="130" r="20" fill="currentColor"/><circle cx="212" cy="83" r="12" fill="currentColor"/><path d="M63 130h174M150 43v174" stroke="currentColor" opacity=".22"/>',
    "layers": '<rect x="71" y="66" width="108" height="108" fill="currentColor" opacity=".16"/><rect x="96" y="86" width="108" height="108" fill="none" stroke="currentColor" stroke-width="2"/><rect x="121" y="106" width="108" height="108" fill="currentColor"/><path d="M148 160h53m-26-26v53" stroke="var(--paper)" stroke-width="2"/>',
    "path": '<path d="M62 60h176v143H62V98h137v67H100v-29h62" fill="none" stroke="currentColor" stroke-width="13"/><circle cx="162" cy="136" r="8" fill="currentColor"/><path d="M221 39l17 21-23 15" stroke="currentColor" stroke-width="3" fill="none"/>',
    "grid": '<g fill="currentColor"><circle cx="92" cy="92" r="19"/><circle cx="138" cy="92" r="19"/><circle cx="92" cy="138" r="19"/><circle cx="138" cy="138" r="19"/></g><g fill="none" stroke="currentColor" stroke-width="2"><circle cx="218" cy="92" r="19"/><circle cx="218" cy="138" r="19"/><path d="M73 191h84m42 0h38"/></g>',
    "balance": '<path d="M150 59v145M83 204h134M61 98h178" stroke="currentColor" stroke-width="3"/><circle cx="150" cy="59" r="10" fill="currentColor"/><path d="M87 98l-27 62h54zm126 0-27 62h54z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M60 160a27 27 0 0 0 54 0m72 0a27 27 0 0 0 54 0" fill="currentColor"/>',
    "focus": '<circle cx="150" cy="130" r="75" fill="currentColor" opacity=".12"/><circle cx="150" cy="130" r="43" fill="currentColor"/><path d="M63 90V53h37m100 0h37v37m0 80v37h-37m-100 0H63v-37" stroke="currentColor" stroke-width="3"/><path d="M129 130h42m-21-21v42" stroke="var(--paper)" stroke-width="2"/>',
}
ENTRY_FIELDS = {"slug", "order", "title", "english", "category", "summary", "illustration", "definition", "explanation", "comparison", "checklist", "sources"}


def escape(value):
    return html.escape(str(value), quote=True)


def fail(where, message):
    raise ValueError(f"{where}: {message}")


def fields(value, expected, where):
    if not isinstance(value, dict):
        fail(where, "必須是物件")
    missing, extra = expected - value.keys(), value.keys() - expected
    if missing or extra:
        fail(where, f"缺少欄位 {sorted(missing)}；未定義欄位 {sorted(extra)}")


def text(value, minimum, maximum, where):
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        fail(where, f"必須是 {minimum}–{maximum} 字的非空白文字")


def slug(value, where):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", value):
        fail(where, "使用小寫英文與數字，以單一連字號分隔")


def validate(site, entries):
    fields(site, {"name", "english", "tagline", "description", "categories"}, "site.json")
    for key in ("name", "english", "tagline", "description"):
        text(site[key], 2, 300, f"site.{key}")
    if not isinstance(site["categories"], list) or not site["categories"]:
        fail("site.categories", "至少需要一個分類")
    categories = set()
    for category in site["categories"]:
        fields(category, {"id", "title", "palette"}, "category")
        slug(category["id"], "category.id")
        text(category["title"], 2, 16, "category.title")
        if category["id"] in categories:
            fail("category.id", "分類 ID 重複")
        if category["palette"] not in PALETTES:
            fail("category.palette", "僅允許 sage、peach、lavender")
        categories.add(category["id"])
    if not entries:
        fail("entries", "至少需要一篇圖鑑")
    ids, orders = set(), set()
    for entry in entries:
        fields(entry, ENTRY_FIELDS, "entry")
        where = entry["slug"]
        slug(where, "entry.slug")
        if where in ids:
            fail(where, "slug 重複")
        ids.add(where)
        order = entry["order"]
        if type(order) is not int or order < 1 or order in orders:
            fail(where, "order 必須是唯一正整數")
        orders.add(order)
        for key, minimum, maximum in [("title", 2, 24), ("english", 2, 70), ("summary", 12, 90), ("definition", 20, 200), ("explanation", 40, 500)]:
            text(entry[key], minimum, maximum, f"{where}.{key}")
        if entry["category"] not in categories:
            fail(where, "category 尚未登記於 site.json")
        if entry["illustration"] not in SHAPES:
            fail(where, f"illustration 必須選自 {', '.join(SHAPES)}")
        fields(entry["comparison"], {"context", "before", "after", "lesson"}, f"{where}.comparison")
        for key, value in entry["comparison"].items():
            text(value, 8, 600, f"{where}.comparison.{key}")
        checklist = entry["checklist"]
        if not isinstance(checklist, list) or not 3 <= len(checklist) <= 5:
            fail(where, "checklist 需要 3–5 項")
        for item in checklist:
            text(item, 8, 100, f"{where}.checklist")
        if not isinstance(entry["sources"], list):
            fail(where, "sources 必須是陣列")
        for source in entry["sources"]:
            fields(source, {"title", "url"}, f"{where}.source")
            text(source["title"], 2, 150, f"{where}.source.title")
            text(source["url"], 10, 2000, f"{where}.source.url")
            url = urlsplit(source["url"])
            if url.scheme != "https" or not url.netloc or url.username or url.password or re.search(r'[\s<>"\x00-\x1f]', source["url"]):
                fail(where, "來源必須是沒有帳密的有效 HTTPS 網址")


def load_content(root=ROOT):
    site = json.loads((root / "content/site.json").read_text(encoding="utf-8"))
    entries = []
    for path in sorted((root / "content/entries").glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entry, dict) or entry.get("slug") != path.stem:
            fail(path.name, "檔名必須與 slug 相同")
        entries.append(entry)
    validate(site, entries)
    return site, sorted(entries, key=lambda entry: entry["order"])


def illustration(key):
    return '<svg viewBox="0 0 300 260" fill="none" aria-hidden="true">' + SHAPES[key] + '</svg>'


def hero_art():
    return '''<svg viewBox="0 0 520 340" aria-hidden="true"><defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0 0v8" stroke="#214d3b" stroke-width="2"/></pattern></defs><path d="M0 170h520M260 0v340" stroke="#c4cbbb"/><circle cx="260" cy="162" r="109" fill="#214d3b"/><path d="M260 53a109 109 0 0 1 0 218Z" fill="#d5eb87"/><circle cx="260" cy="162" r="53" fill="#e1e5d7"/><path d="M260 109a53 53 0 0 1 0 106Z" fill="url(#hatch)"/><circle cx="102" cy="83" r="13" fill="#214d3b"/><rect x="398" y="233" width="24" height="24" fill="none" stroke="#214d3b" stroke-width="2"/><path d="M394 67h30m-15-15v30M91 245h24M218 298h84m-9-6 9 6-9 6" stroke="#214d3b" stroke-width="2" fill="none"/></svg>'''


def render(project_root, template_name, **values):
    return Template((project_root / "templates" / template_name).read_text(encoding="utf-8")).substitute(values)


def build(root=ROOT):
    site, entries = load_content(root)
    categories = {category["id"]: category for category in site["categories"]}
    counts = Counter(entry["category"] for entry in entries)

    def page(body, title, description, prefix="", current=""):
        return render(root, "base.html", body=body, title=escape(title), description=escape(description), root=prefix,
                      name=escape(site["name"]), english=escape(site["english"]),
                      home_current='aria-current="page"' if current == "home" else "",
                      guide_current='aria-current="page"' if current == "guide" else "")

    with tempfile.TemporaryDirectory(prefix=".build-", dir=root) as temp:
        output = Path(temp) / "docs"
        (output / "entries").mkdir(parents=True)
        shutil.copytree(root / "assets", output / "assets")
        shutil.copyfile(root / "AGENTS.md", output / "AGENTS.md")
        shutil.copyfile(root / "templates/entry.example.json", output / "entry.example.json")
        (output / ".nojekyll").touch()
        cards = []
        for index, entry in enumerate(entries):
            category = categories[entry["category"]]
            number = f"{index + 1:02d}"
            cards.append(f'''<a class="card" data-entry data-category="{escape(entry['category'])}" data-search="{escape(' '.join([entry['title'], entry['english'], entry['summary']]))}" href="entries/{entry['slug']}.html"><div class="poster {category['palette']}"><div class="poster-top"><span>FIG. {number}</span><span>{escape(category['title'])}</span></div>{illustration(entry['illustration'])}<span class="poster-arrow" aria-hidden="true">↗</span></div><p class="card-meta">IDEA {number} / {escape(category['title'])}</p><h3>{escape(entry['title'])}</h3><p class="card-english">{escape(entry['english'])}</p><p class="card-summary">{escape(entry['summary'])}</p></a>''')
            sources = ''.join(f'<a class="source-link" href="{escape(source["url"])}" target="_blank" rel="noopener noreferrer">{escape(source["title"])}<span aria-hidden="true">↗</span></a>' for source in entry["sources"])
            if not sources:
                sources = '<span class="original-label">原創練習</span><p class="source-note">這篇是本專案整理的寫作練習建議，並非學術定律。</p>'
            previous = entries[index - 1] if index > 0 else None
            following = entries[index + 1] if index + 1 < len(entries) else None
            previous_link = f'<a href="{previous["slug"]}.html"><small>← PREVIOUS</small>{escape(previous["title"])}</a>' if previous else '<span></span>'
            next_link = f'<a href="{following["slug"]}.html"><small>NEXT →</small>{escape(following["title"])}</a>' if following else '<span></span>'
            body = render(root, "entry.html", category=escape(category["title"]), number=number, entry_title=escape(entry["title"]),
                          entry_english=escape(entry["english"]), definition=escape(entry["definition"]), palette=category["palette"],
                          illustration=illustration(entry["illustration"]), explanation=escape(entry["explanation"]),
                          **{key: escape(value) for key, value in entry["comparison"].items()},
                          checklist=''.join(f'<li>{escape(item)}</li>' for item in entry["checklist"]), sources=sources,
                          previous=previous_link, next=next_link)
            (output / "entries" / f'{entry["slug"]}.html').write_text(page(body, f'{entry["title"]} — {site["name"]}', entry["summary"], "../"), encoding="utf-8")
        filters = ''.join(f'<button class="filter" data-category="{escape(category["id"])}" aria-pressed="false">{escape(category["title"])} <span>{counts[category["id"]]}</span></button>' for category in site["categories"])
        headline = '<br>'.join(escape(line) if i == 0 else f'<em>{escape(line)}</em>' for i, line in enumerate(site["tagline"].splitlines()))
        body = render(root, "home.html", headline=headline, intro=escape(site["description"]), count=len(entries),
                      category_count=len(categories), hero_art=hero_art(), cards=''.join(cards), filters=filters)
        (output / "index.html").write_text(page(body, f'{site["name"]} — {site["english"]}', site["description"], current="home"), encoding="utf-8")
        body = render(root, "guide.html", count=len(entries), category_count=len(categories), agents=escape((root / "AGENTS.md").read_text(encoding="utf-8")))
        (output / "guide.html").write_text(page(body, f'使用這個基板 — {site["name"]}', "了解圖鑑基板的設計規則、內容範本與新增流程。", current="guide"), encoding="utf-8")
        # docs is generated output only; rebuild removes pages for deleted entries.
        destination = root / "docs"
        if destination.exists():
            if destination.is_symlink():
                fail("docs", "不可為符號連結")
            shutil.rmtree(destination)
        shutil.move(str(output), str(destination))
    return len(entries)


if __name__ == "__main__":
    try:
        total = build()
        print(f"建置成功：{total} 篇圖鑑、首頁與指南 → docs/")
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(f"建置失敗：{error}")
