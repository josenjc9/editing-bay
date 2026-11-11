# Security Policy

## 範圍

這個 repo 是一份 agent skill（文件）加幾個本機執行的小工具，**不連網、不收集資料、不需要帳號或金鑰**：

- `skill/editing-bay/tools/` 的腳本只讀寫你指定的檔案；沒有 `eval`、`exec`、`os.system` 或 `shell=True`。
- `deliver.sh` 不覆蓋既有檔案；`safe_trash.sh` 只把檔案移進垃圾桶，不直接刪除、不清空垃圾桶。
- `ocr_check.py` 第一次執行會在本機編譯同資料夾的 `ocr.swift`（macOS 內建 Vision，不下載、不外送）。
- `examples/` 的 HTML 會從 CDN 載入 GSAP 或 Three.js（已固定版本）；離線使用請自行下載到本機。

## 回報問題

請在這個 repo 開 [Security Advisory（私密回報）](https://github.com/josenjc9/editing-bay/security/advisories/new)，或開一般 Issue（不含敏感細節的問題）。請附上：受影響的檔案、重現步驟、你的作業系統。

## 使用提醒

- 裝任何 skill 或工具前，先讀過內容；這份 skill 的 SKILL.md 也要求 agent「裝任何新工具前先查來源與授權、問過使用者再裝」。
- 不要把客戶或家人的私人素材、帳號密碼放進 `examples/` 或你的公開 fork。
