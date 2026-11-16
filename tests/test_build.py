import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build import build, load_content, validate
from check import check


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.site, self.entries = load_content(ROOT)

    def test_duplicate_slug_and_order_are_rejected(self):
        duplicate = copy.deepcopy(self.entries[0])
        with self.assertRaisesRegex(ValueError, "slug 重複"):
            validate(self.site, self.entries + [duplicate])
        duplicate["slug"] = "another-idea"
        with self.assertRaisesRegex(ValueError, "order 必須是唯一正整數"):
            validate(self.site, self.entries + [duplicate])

    def test_missing_fields_unknown_category_and_unsafe_source_are_rejected(self):
        for change, message in [
            (lambda e: e.pop("definition"), "缺少欄位"),
            (lambda e: e.update(category="unregistered"), "尚未登記"),
            (lambda e: e.update(sources=[{"title": "Unsafe", "url": "javascript:alert(1)"}]), "HTTPS"),
            (lambda e: e.update(slug="../escape"), "小寫英文"),
        ]:
            with self.subTest(message=message):
                entries = copy.deepcopy(self.entries)
                change(entries[0])
                with self.assertRaisesRegex(ValueError, message):
                    validate(self.site, entries)

    def test_template_can_be_added_without_changing_shared_code(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "atlas"
            shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns("docs", "__pycache__", ".git", "screenshots", ".build-*"))
            sample = json.loads((project / "templates/entry.example.json").read_text())
            sample["title"] = '按鈕 <script> & 文案'
            sample["order"] = max(entry["order"] for entry in self.entries) + 10
            target = project / "content/entries" / f'{sample["slug"]}.json'
            target.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(build(project), len(self.entries) + 1)
            self.assertEqual(check(project), len(self.entries) + 3)
            generated = (project / "docs/entries" / f'{sample["slug"]}.html').read_text()
            self.assertIn("按鈕 &lt;script&gt; &amp; 文案", generated)
            self.assertNotIn("<script> & 文案", generated)
            homepage = (project / "docs/index.html").read_text()
            self.assertIn(f'entries/{sample["slug"]}.html', homepage)
            # Deleting content must not leave a stale public page behind.
            target.unlink()
            build(project)
            self.assertFalse((project / "docs/entries" / f'{sample["slug"]}.html').exists())
            check(project)

    def test_filename_must_match_public_slug(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "content/entries").mkdir(parents=True)
            (project / "content/site.json").write_text(json.dumps(self.site))
            (project / "content/entries/wrong-name.json").write_text(json.dumps(self.entries[0]))
            with self.assertRaisesRegex(ValueError, "檔名必須與 slug 相同"):
                load_content(project)


if __name__ == "__main__":
    unittest.main()
