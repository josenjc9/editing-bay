# short-video-skill

把你的 AI agent 變成會剪短影音的好幫手。
*An agent skill that gives your AI agent a clear, step-by-step way to edit short videos.*

**[⬇ 直接下載 skill（ZIP，不需要 GitHub 帳號）](https://github.com/josenjc9/short-video-skill/releases/latest/download/short-video-edit.zip)**　｜　[下載整個專案（含範例與測試）](https://github.com/josenjc9/short-video-skill/archive/refs/heads/main.zip)

下載、放進 agent 的 skills 資料夾，對它說一句「幫我剪一支短影音」，它就會照著一套完整流程，從確認需求、排鏡頭、做字卡，到檢查成片、整理交付，一步一步陪你做完。

適合：短影音、廣告片、解說片、口播片、預告片混剪、Reels。用你自己的真實素材為主，也能加上動畫與字卡。

![剪輯流程：8 個步驟，每個關卡都等你點頭](docs/workflow.svg)

## 用起來會是這樣

- **先對齊，再動手**：agent 會在幾個關鍵點停下來，請你確認事實、風格和鏡頭表。你點頭的版本，就是它往下做的依據。
- **做完會自己先看一輪**：解析度、爆音、黑畫面、字幕有沒有壓到臉，先由工具和檢查表篩過一遍，再交給你。
- **做不到的，會直接告訴你**：沒驗證過的做法會標明，不會把嘗試說成保證。
- **每一次都留得下來**：交付資料夾、分鏡板、原始碼、覆盤都有固定位置，下一支片可以接著用。

## 裡面有什麼

| 位置 | 內容 |
|---|---|
| `skill/short-video-edit/SKILL.md` | agent 讀的主文件：從前期到結案的完整流程與規矩 |
| `skill/short-video-edit/references/` | 13 份參考：剪輯語法、跨鏡頭連續性、聲畫與調色、退件格式、**技法庫**（畫中畫、蒙太奇、變速…）、**轉場指南**、**動態圖形與 3D**、技法與工具目錄，以及 5 種情境的做法（口播、預告片、時間流逝、角色動畫、圖卡轉動態） |
| `skill/short-video-edit/tools/` | 8 個小工具：成片機檢、切點接觸圖、分鏡板、截圖找出處、字卡地雷掃描、文字比對、交付、安全移垃圾桶 |
| `examples/` | 3 個可直接渲染的 HyperFrames 範例：動態圖形技法、轉場、Three.js 3D |
| `tests/smoke.sh` | 煙霧測試：用合成影片跑 tools 與文件裡的 ffmpeg 指令（含 58 種 `xfade` 轉場） |

### 範例畫面（都是用 `examples/` 的原始碼渲染、逐格看過的結果）

| 動態圖形技法 | 轉場 | Three.js 3D |
|---|---|---|
| ![](docs/demo-motion-techniques.jpg) | ![](docs/demo-transitions.jpg) | ![](docs/demo-three-dive.jpg) |

數字滾動、前後對比拉桿、打字輸入框加進度條、逐字模糊進場；模糊交換、從點擊處開圈、甩鏡、暗角切、整片換色；Three.js 鏡頭穿越。

## 安裝

**不用 GitHub**：點上面的「直接下載 skill」，解壓縮，把 `short-video-edit` 資料夾放進你的 agent 的 skills 資料夾（Claude Code 是 `~/.claude/skills/`；其他 agent 的路徑請查它的說明），然後對它說「幫我剪一支短影音」。

**用 git**：
```bash
git clone https://github.com/josenjc9/short-video-skill.git
mkdir -p ~/.claude/skills
cp -R short-video-skill/skill/short-video-edit ~/.claude/skills/
```

## 需要什麼

- 必要：`ffmpeg`、`python3`
- 選用：`ocr_check.py` 需要 macOS 與 `swiftc`；字卡與動畫範例用 [HyperFrames](https://hyperframes.heygen.com)（需要 Node.js 22+）；去人聲、找切點、剪氣口依 SKILL.md 說明另外安裝。**裝任何工具前請先確認來源與授權。**

## 驗證了什麼、沒驗證什麼

| 項目 | 驗證方式 |
|---|---|
| 8 個工具、技法庫的 ffmpeg 指令、58 種 `xfade` 轉場 | `bash tests/smoke.sh`，23 項全部通過（每次推送由 GitHub Actions 自動跑） |
| 動態圖形、轉場、Three.js 範例 | 用 HyperFrames 渲染，逐格看過畫面；Three.js 同一時間點渲染兩次，截圖雜湊相同 |
| PySceneDetect、Auto-Editor、librosa | 用合成素材驗功能（切點偵測、剪空白、BPM 誤差 2% 內） |
| 用在你的真素材上好不好看 | **沒有**，工具只負責「能算的」，畫面好不好看請用你的眼睛 |

文件裡每個技法都標了狀態（實測／指令已跑過／畫面已驗）。

## 使用提醒

- 流程以你的點頭為準，agent 會在關鍵節點停下來和你確認。
- 工具負責能算的部分（解析度、爆音、黑畫面…），畫面好不好看，留給你的眼睛。
- 授權：MIT。回報問題與資安事項見 [SECURITY.md](SECURITY.md)；版本紀錄見 [CHANGELOG.md](CHANGELOG.md)。

---

## English summary

A self-contained skill (`SKILL.md` + 14 reference docs + 8 small tools) that gives an AI coding agent a gated workflow for editing short videos: confirm goal → script → shot list → inventory and tests → rough cut → build → self-check → deliver. Every gate waits for the user's approval. Includes a technique library (picture-in-picture, montage, speed ramps…), a transitions guide (all 58 ffmpeg `xfade` types run in the smoke test), motion-graphics and 3D (Three.js) notes, three renderable HyperFrames examples, and a smoke-test suite run by CI. Written in Traditional Chinese because the checklists include CJK title-card and subtitle typography rules. Download the ZIP from the Releases page and drop `short-video-edit/` into your agent's skills folder. MIT licensed.
