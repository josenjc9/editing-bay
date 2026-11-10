# short-video-skill

把你的 AI agent 變成會剪短影音的好幫手。
An agent skill that gives your AI agent a clear, step-by-step way to edit short videos.

下載、放進 skills 資料夾，對 agent 說一句「幫我剪一支短影音」，它就會照著一套完整流程，從確認需求、排鏡頭、做字卡，到檢查成片、整理交付，一步一步陪你做完。

適合：短影音、廣告片、解說片、口播片、預告片混剪、Reels。用你自己的真實素材為主，也能加上動畫與字卡。

## 用起來會是這樣

- **先對齊，再動手**：agent 會在幾個關鍵點停下來，請你確認事實、風格和鏡頭表。你點頭的版本，就是它往下做的依據。
- **做完會自己先看一輪**：解析度、爆音、黑畫面、字幕有沒有壓到臉，先由工具和檢查表篩過一遍，再交給你。
- **做不到的，會直接告訴你**：沒驗證過的做法會標明，不會把嘗試說成保證。
- **每一次都留得下來**：交付資料夾、分鏡板、原始碼、覆盤都有固定位置，下一支片可以接著用。

## 裡面有什麼

- `skill/short-video-edit/SKILL.md`：agent 讀的主文件，從前期到結案的完整流程，另有口播、預告片混剪、角色動畫、圖卡轉動態等情境的做法。
- `skill/short-video-edit/references/`：剪輯語法、跨鏡頭連續性、聲畫與調色、退件與驗收格式、技法與工具目錄（每項標明實測或常見做法）。
- `skill/short-video-edit/tools/`：8 個小工具，包含成片機檢、切點接觸圖、分鏡板、截圖找出處、字卡地雷掃描、文字比對、交付與安全移垃圾桶。

這是分享與教學用的整理版，歡迎照你的作法調整。

## 安裝（Claude Code）

```bash
git clone https://github.com/<你的帳號>/short-video-skill.git
mkdir -p ~/.claude/skills
cp -R short-video-skill/skill/short-video-edit ~/.claude/skills/
```

重開 Claude Code，對 agent 說「幫我剪一支短影音」或「做一支預告片」，它會自動載入。
其他支援 SKILL.md 的 agent，把 `skill/short-video-edit/` 整個資料夾放到它的 skills 目錄即可。

## 需要什麼

- 必要：`ffmpeg`、`python3`
- 選用：`ocr_check.py` 需要 macOS 與 `swiftc`；`hf_lint.py` 只在用 HyperFrames 做字卡時需要；去人聲、找切點、剪氣口等輔助工具（demucs、PySceneDetect、Auto-Editor）依 SKILL.md 內說明另外安裝。**裝任何工具前請先確認來源與授權。**

## 使用提醒

- 流程以你的點頭為準，agent 會在關鍵節點停下來和你確認。
- 檢查工具負責能算的部分（解析度、爆音、黑畫面…），畫面好不好看，留給你的眼睛。
- 還沒實測過的做法，SKILL.md 都有標註，先當作可以試試看的選項。
- 授權：MIT。

---

## English summary

A self-contained skill (`SKILL.md` + references + small stdlib-only Python/shell tools) that gives an AI coding agent a gated workflow for editing short videos: confirm facts/copy → style pack → shot list → build → grade/mix → pre-delivery checklist → wrap-up. It is written in Traditional Chinese because the checklists include CJK title-card and subtitle typography rules. The tools need `ffmpeg`; a few are macOS-only. Install by copying `skill/short-video-edit/` into your agent's skills directory. MIT licensed.
