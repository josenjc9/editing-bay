# tools：剪輯用的小工具

都是單檔，Python 部分只用標準庫（只有 `capcut_export.py` 寫草稿時需要自己裝 `pycapcut`）、唯讀或「不覆蓋」設計。需要 `ffmpeg`（PATH 裡找得到，或用環境變數 `FFMPEG=/path/to/ffmpeg` 指定）。

| 工具 | 做什麼 | 需要 |
|---|---|---|
| `qa_video.py` | 任何 mp4 的機檢：解析度／fps／整數幀、聲軌有無與長度、爆音、響度、黑畫面、凍結、換鏡前後各抽一格、分享版 ≤9MB、`--compare` 比兩支畫面雜湊 | ffmpeg |
| `cuts_sheet.py` | 切點連續性接觸圖：每個切點抽 t-2f…t+2f 共 5 格、一切點一列 | ffmpeg |
| `storyboard.py` | 從影片抽 N 格拼成分鏡板／接觸圖（`--times` 指定秒數、`--count N` 平均抽、`--every N` 每 N 秒一格） | ffmpeg |
| `find_frame.py` | 拿一張截圖，找出它是哪支影片的第幾秒 | ffmpeg |
| `hf_lint.py` | HyperFrames `index.html` 的地雷掃描（靜態查，不渲染）：檔案截斷、變數撞名、媒體元素缺屬性、選擇器選不到、set 蓋 from、缺 immediateRender、小字級 | python3 |
| `ocr_check.py` | 成片畫面上的字 vs 原稿，用 macOS 內建文字辨識逐句核；另列「成片有、原稿沒有」的字 | macOS、swiftc（第一次跑自己編 `ocr.swift`） |
| `deliver.sh` | 合音效、壓輕量版、複製到交付資料夾、md5 核對；同名檔不覆蓋 | ffmpeg |
| `capcut_export.py` | 把「分軌時間表」json 寫成 CapCut（剪映國際版）草稿：畫面、字卡、配樂、音效各自一軌，帶去剪映細修（輸出 B）。`--dry-run` 只檢查不寫檔 | python3；寫草稿另需自己安裝 `pycapcut` |
| `safe_trash.sh` | 檔案或資料夾移垃圾桶，同名不靜默略過、逐個印結果，不清空垃圾桶 | macOS 或 Linux |

每支用 `--help` 或不帶參數看用法。

## 限制（要知道）

- `capcut_export.py`：只放素材、字卡、音訊與簡單推近／調光，**不重現遮罩聚焦、定位框、自製調色**；草稿開起來的樣子請你自己在剪映確認；一律建新草稿，同名會報錯；寫之前剪映必須完全退出；字卡字級 5 約等於 1080p 畫面上的 48px，預設不放文字入場動畫（那是剪映的雲端資源，沒下載過會顯示「動畫遺失」）；剪映只連得到 `~/Movies` 底下的素材，所以工具會把素材複製（macOS 用不佔額外空間的 APFS 複製）到那裡。這支是 macOS 剪映的做法，其他平台的草稿位置請自行調整。

- `qa_video.py`：換鏡偵測靠畫面差異，淡入淡出可能漏；動態很大的片可能多抓（調高 `--scene`）。凍結只抓「逐像素幾乎不變」。**不判斷畫面好不好看，圖要自己看。**
- `hf_lint.py`：只看字面字串選擇器，用變數拼出來的看不到；沒查節奏、色彩；沒有實際渲染。
- `ocr_check.py`：辨識會漏讀、錯讀，標出來的句子一定要回頭看畫面，不要直接判錯或判對；只核「抽到的那幾格」。**文字對得上不等於內容正確。**
- `deliver.sh` 與 `safe_trash.sh` 在 macOS 與 Linux 都能用（自動選 `md5` 或 `md5sum`、對應的垃圾桶資料夾）；`ocr_check.py` 仍需要 macOS。
