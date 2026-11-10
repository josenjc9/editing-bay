# short-video-skill

讓你的 AI agent 學會剪短影音的一套作業手冊與工具。
An agent skill that teaches your AI agent a complete short-video editing workflow, plus a few small QA tools.

適用：剪輯短影音、廣告片、解說片、口播片、預告片混剪、Reels。以真實素材為主，可混動畫與字卡。

## 這是什麼

- `skill/short-video-edit/SKILL.md`：agent 讀的主文件。流程是「前期三關（事實文案、風格包、鏡頭表）→ 製作 → 後製 → 交片前檢查表 → 結案」，每條規則都來自實際做片時被退件的教訓。
- `skill/short-video-edit/references/`：剪輯語法、跨鏡頭連續性、聲畫與調色、退件與驗收格式、技法與工具目錄（每項標明實測或常見做法）。
- `skill/short-video-edit/tools/`：8 個小工具（機檢、切點接觸圖、分鏡板、找截圖出處、字卡地雷掃描、文字比對、交付、安全移垃圾桶）。

這是教學與分享用的整理版，不綁特定專案。

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

- 這份流程預設「使用者點頭才算過關」，agent 會在關鍵節點停下來問你。
- 檢查工具只核「能算的」（解析度、爆音、黑畫面…），畫面好不好看仍要人看圖。
- 沒實測過的做法，SKILL.md 都有標註，請不要當保證。
- 授權：MIT。

---

## English summary

A self-contained skill (`SKILL.md` + references + small stdlib-only Python/shell tools) that gives an AI coding agent a gated workflow for editing short videos: confirm facts/copy → style pack → shot list → build → grade/mix → pre-delivery checklist → wrap-up. It is written in Traditional Chinese because the checklists include CJK title-card and subtitle typography rules. The tools need `ffmpeg`; a few are macOS-only. Install by copying `skill/short-video-edit/` into your agent's skills directory. MIT licensed.
