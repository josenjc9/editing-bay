// 讀圖上的文字（Mac 內建 Vision，不下載、不外送）。用法：ocr <圖1> <圖2> ...
// 輸出：每張圖一段，「## 路徑」後面接每行辨識結果。語言修正關掉（不要把原文「修正」成別的字）。
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("## \(path)")
        print("!!ERR 讀不到圖")
        continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["zh-Hant", "en-US"]
    req.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: cg).perform([req])
    print("## \(path)")
    print((req.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n"))
}
