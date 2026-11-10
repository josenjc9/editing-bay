# examples

三個 [HyperFrames](https://hyperframes.heygen.com) 範例（HTML 渲染成影片），對應 `references/` 裡標「畫面已驗」的技法。內容全是合成圖形，沒有任何人物或私人素材。

| 資料夾 | 展示 |
|---|---|
| `motion-techniques/` | 數字滾動（tabular-nums）、前後對比拉桿（clip-path）、打字輸入框加進度條、逐字模糊進場 |
| `transitions/` | 同機位推近、模糊交換、從點擊處開圈、甩鏡、暗角切、整片換色 |
| `three-dive/` | Three.js 鏡頭穿越，用 `hf-seek` 由時間決定每一格（決定性渲染） |

## 怎麼跑

需要 Node.js 22+ 與 ffmpeg。

```bash
npx hyperframes init demo        # 建一個空專案
cp examples/transitions/index.html demo/index.html
cd demo
npx hyperframes lint             # 檢查
npx hyperframes snapshot --at 1,3,5   # 抽格看畫面
npx hyperframes render --quality draft --output out.mp4
```

範例會從 CDN 載入 GSAP 3.15.0（three-dive 另載 Three.js 0.160.0）。
