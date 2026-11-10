import Foundation
import CoreGraphics
import ImageIO
// usage: bbox2 <png> <scale> <x0> <y0> <x1> <y1> [label]  (rect in 1x css px) → leftmost non-background pixel columns per colour class, in css px
let a = CommandLine.arguments
let url = URL(fileURLWithPath: a[1])
let s = Double(a[2])!
let src = CGImageSourceCreateWithURL(url as CFURL, nil)!
let img = CGImageSourceCreateImageAtIndex(src, 0, nil)!
let w = img.width, h = img.height
let cs = CGColorSpaceCreateDeviceRGB()
var data = [UInt8](repeating: 0, count: w*h*4)
let ctx = CGContext(data: &data, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w*4, space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.draw(img, in: CGRect(x: 0, y: 0, width: w, height: h))
let x0 = Int(Double(a[3])!*s), y0 = Int(Double(a[4])!*s), x1 = min(w, Int(Double(a[5])!*s)), y1 = min(h, Int(Double(a[6])!*s))
func bbox(_ pred: (Int,Int,Int)->Bool) -> String {
  var minx = Int.max, miny = Int.max, maxx = -1, maxy = -1, n = 0
  for y in y0..<y1 { for x in x0..<x1 {
    let i = (y*w + x)*4; let r = Int(data[i]), g = Int(data[i+1]), b = Int(data[i+2])
    if pred(r,g,b) { n += 1; minx = min(minx,x); miny = min(miny,y); maxx = max(maxx,x); maxy = max(maxy,y) }
  }}
  if n == 0 { return "none" }
  return String(format: "x %.2f–%.2f  y %.2f–%.2f  n %d", Double(minx)/s, Double(maxx+1)/s, Double(miny)/s, Double(maxy+1)/s, n)
}
let label = a.count > 7 ? a[7] : ""
print(label)
print("  any non-white : " + bbox { r,g,b in r < 235 || g < 235 || b < 235 })
print("  dark (text)   : " + bbox { r,g,b in r < 120 && g < 120 })
print("  blue (accent) : " + bbox { r,g,b in r < 90 && g < 140 && b > 120 })
print("  grey (faint)  : " + bbox { r,g,b in r >= 120 && r < 200 && abs(r-g) < 12 && abs(g-b) < 16 })
print("  light tint    : " + bbox { r,g,b in !(r < 90 && g < 140 && b > 120) && !(r > 245 && g > 245 && b > 245) && (b - r) > 6 && r > 200 })
