# 來源與授權說明

本專案本身是 MIT（見 `LICENSE`）。這份檔案列出：用了誰的軟體、借了誰的想法，以及你使用時要自己確認的授權。

## 方法與想法的來源（只取思路，沒有複製檔案、文字或模板）

| 來源 | 授權 | 我們取了什麼 |
|---|---|---|
| [auto-edit-workspace](https://github.com/dean9703111/auto-edit-workspace) | 程式碼 MIT；情境模板與字卡動態 CC BY 4.0；示範影片與講稿為作者所有 | 口播剪輯流程的停點設計、錄影標註與運鏡的節奏規則、「工具算秒數、AI 做判斷」的分工；改寫後放在 `references/情境_螢幕錄影產品展示片.md` 與 `SKILL.md` 的「停下來問的格式」 |
| [rea-video](https://github.com/JuneYaooo/rea-video) | Apache-2.0 | 逐鏡判定與聲音拆解的做法思路（我們自己重寫，未安裝、未複製程式碼） |
| [OpenMontage](https://github.com/OpenMontageInc/OpenMontage) | AGPL-3.0 | 審查意見的寫法（準確、完整、建設性）、交付承諾核對、參考片五面向拆解、錄影或合成畫面的分法、花費上限；只讀文件取思路，沒有複製任何程式碼或 skill 文字（AGPL 會牽動授權義務） |

若你直接複製對方的模板或素材，請依對方授權標示來源；本專案沒有這麼做。

## 範例與文件會用到的外部軟體（需你自己安裝，授權由各自專案決定）

| 軟體 | 用在哪 | 授權（以對方官方頁為準） |
|---|---|---|
| ffmpeg | 全部工具與技法庫指令 | 依你安裝的版本與編譯選項（LGPL 或 GPL） |
| PySceneDetect | 找切點（選用） | BSD-3-Clause |
| Auto-Editor | 剪空白氣口（選用） | Unlicense |
| librosa | 抓拍點與 BPM（選用） | ISC |
| pycapcut | `capcut_export.py` 寫剪映草稿（選用） | 套件中繼資料未標授權，請裝前自己到其倉庫確認 |
| HyperFrames | 字卡與動畫範例（選用） | 見其官方網站與倉庫 |
| GSAP、Three.js | `examples/` 內由 CDN 載入 | 見各自官方授權條款 |

## 提醒

- 裝任何外部工具前，先確認來源與授權；來路不明的執行檔與腳本，先讀過再跑。
- 你自己的素材、字型、配樂與音效，授權由你負責。免費素材庫（例如 Mixkit）的條款會隨時間變，使用前請重看一次。
- 這份清單由人工整理，可能過時；發現錯誤請開 issue。
