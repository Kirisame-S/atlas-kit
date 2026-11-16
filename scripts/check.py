#!/usr/bin/env python3
"""Check every generated local link, fragment, and content page."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build import ROOT, load_content


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.duplicates = [], set(), []
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicates.append(attrs["id"])
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


def check(root=ROOT):
    output = root / "docs"
    _, entries = load_content(root)
    pages = {path.resolve(): Document(path.read_text(encoding="utf-8")) for path in output.rglob("*.html")}
    errors = []
    for path, document in pages.items():
        errors.extend(f"{path.name}: 重複 ID {item}" for item in document.duplicates)
        for link in document.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if url.path.startswith("/"):
                errors.append(f"{path.name}: 不可使用根目錄絕對網址 {link}")
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(output.resolve()):
                errors.append(f"{path.name}: 連結超出發布目錄 {link}")
            elif not target.is_file():
                errors.append(f"{path.name}: 找不到 {link}")
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f"{path.name}: 找不到錨點 {link}")
    expected = {f'{entry["slug"]}.html' for entry in entries}
    actual = {path.name for path in (output / "entries").glob("*.html")}
    if expected != actual:
        errors.append("內容資料與輸出頁面不一致，請重新建置")
    index = output / "index.html"
    if not index.is_file():
        errors.append("缺少首頁")
    else:
        for entry in entries:
            if f'entries/{entry["slug"]}.html' not in pages[index.resolve()].links:
                errors.append(f"首頁缺少 {entry['slug']} 入口")
    if not (output / "guide.html").is_file():
        errors.append("缺少指南")
    if errors:
        raise ValueError("\n".join(errors))
    return len(pages)


if __name__ == "__main__":
    try:
        print(f"檢查成功：{check()} 個頁面的內部連結、錨點與內容索引一致")
    except (ValueError, OSError) as error:
        raise SystemExit(f"檢查失敗：{error}")
