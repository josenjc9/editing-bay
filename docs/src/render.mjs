// 把 docs/src/card-*.html 渲染成 docs/card-*.jpg（1080×1350，2 倍解析度，JPEG）
// 用法：node docs/src/render.mjs    需要 playwright（npm i playwright）與本機 Chrome；字體用 Noto Sans CJK TC。
import {chromium} from 'playwright'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
const here=path.dirname(fileURLToPath(import.meta.url))
const b=await chromium.launch({channel:'chrome',headless:true})
for (const n of ['workflow','exits','tracks']){
  const p=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:2})
  await p.goto('file://'+path.join(here,`card-${n}.html`)); await p.waitForTimeout(300)
  await p.screenshot({path:path.join(here,'..',`card-${n}.jpg`),quality:92})
}
await b.close()
