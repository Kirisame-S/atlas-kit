# 觀念圖鑑 — Atlas Kit

一套可以持續新增內容的繁體中文圖鑑網站基板。視覺方向參考 [Laws of UX](https://lawsofux.com/)，延伸我先前「選擇的背面」的原創設計，將單檔網頁整理為「專案規則＋內容資料＋共用模板＋自動建置」。

[瀏覽網站](https://kirisame-s.github.io/atlas-kit/) · [使用基板指南](https://kirisame-s.github.io/atlas-kit/guide.html) · [AI 開發規則](AGENTS.md)

目前有設計心理、介面觀察、寫作練習三類，共六篇示範內容。每篇都有幾何封面、觀念說明、前後對照、檢核清單與來源；首頁支援搜尋和分類。沒有後端、追蹤或 API 金鑰，JavaScript 關閉時仍可閱讀所有內容。

## 開始使用

需要 Python 3.9 以上，不必安裝套件。在專案目錄執行：

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --directory docs
```

開啟 <http://localhost:8000>。也可以直接用瀏覽器開啟 `docs/index.html`；網站沒有 fetch 或模組載入限制。

## 重用為另一個專案

這個 Repository 已設定為 GitHub Template。點選 **Use this template → Create a new repository**，即可複製整套目錄與檔案。接著修改 `content/site.json` 的站名、首頁文案與分類，替換 `content/entries/` 的示範內容，再重新建置。新 Repository 需自行啟用 main 分支 `/docs` 的 GitHub Pages，並更新 README 的網站連結。

操作方式依 [GitHub Template 官方文件](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)。

## 讓 AI 新增一篇內容

先閱讀 [AGENTS.md](AGENTS.md)，再複製 [內容範本](templates/entry.example.json) 到 `content/entries/<slug>.json`。修改標題、分類、說明、對照與來源，指定不重複的 slug 與 order，重新執行建置與檢查即可。

例如：

> 請先閱讀 AGENTS.md 與 templates/entry.example.json，新增一篇「清楚的按鈕文案」圖鑑，放在「寫作練習」分類。請用原創前後對照與三項檢核問題，維持既有配色、卡片與內頁版型。使用尚未占用的 order，執行建置、連結檢查與測試，並說明修改的檔案與驗證結果。

不用複製 HTML、不用手動新增首頁卡片，也不需要改搜尋程式。分類數量、卡片索引、獨立網址與上一篇／下一篇導覽都會從資料產生。刪除內容後重建，也會移除舊頁面。

## 專案結構

```text
AGENTS.md                    AI 開發規則與驗收條件
content/site.json            站名、首頁文案、分類配色
content/entries/*.json       每篇圖鑑的唯一內容來源
templates/*.html             共用頁面模板
templates/entry.example.json 可複製的新增範本
assets/                      共用樣式、互動程式、網站圖示
scripts/build.py             資料驗證與靜態建置
scripts/check.py             內部連結、錨點與索引檢查
tests/test_build.py           新增、刪除、資料驗證與安全跳脫測試
tests/browser.cjs            選用的瀏覽器驗證
docs/                        已產生，可直接發布的網站
```

一般新增內容只改 JSON；整站調整改 site.json；版型調整改 templates 與 assets。請勿直接改 docs，因為下一次建置會覆蓋生成結果。

## GitHub Pages

本專案使用 main 分支的 `/docs` 作為發布來源：Repository → Settings → Pages → Deploy from a branch → main → /docs → Save。發布根目錄包含 `.nojekyll`，網站內部使用相對路徑，可以部署到 Repository 子路徑。

每次修改內容後，請先重新建置與檢查，再把來源及 docs 一起提交。Pages 會從更新後的 docs 發布，不在正式網站執行 Python。

操作方式依 [GitHub Pages 官方文件](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

## 驗證方式

Python 測試會在暫存目錄加入第七篇圖鑑，驗證新卡片、內容頁與導覽會自動出現，也會驗證刪除內容後舊頁面不再留下。另檢查重複名稱、排序、未登記分類、遺漏欄位、危險來源網址和文字跳脫。

選用的瀏覽器測試需要 Playwright 與可用的 Chromium：安裝後執行 `node tests/browser.cjs`。可用 `ATLAS_CHROME_PATH` 指定本機 Chrome，或以 `ATLAS_BASE_URL` 測試已發布網站。它檢查 360／768／1440px 版面、搜尋與分類交集、零結果重設、鍵盤切換對照、無 JavaScript 閱讀與執行錯誤，並將截圖輸出至不納入版控的 screenshots。

## 參考與原創範圍

- 視覺方向：[Laws of UX](https://lawsofux.com/)。沒有複製其插圖、品牌標誌或文章。
- 設計心理觀念：各篇附 Laws of UX 原始參考頁面。
- 介面觀察觀念：[Deceptive Patterns](https://deceptive.design/types/)，各篇附對應分類頁。
- 寫作練習、對照情境、幾何 SVG、基板程式與專案規則為本專案整理及製作，AI 協助實作。
- 延伸作者先前的「選擇的背面」視覺方向；這次新增多主題資料結構、共用模板、自動建置、可驗證的規範與新增內容流程。

網站中的活動、價格與訊息均為虛構教學例子，不代表真實品牌或活動。外部概念以自己的文字整理，寫作練習明確標為原創建議。
