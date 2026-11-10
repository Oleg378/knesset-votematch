import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
let a = CommandLine.arguments
func load(_ p: String) -> CGImage { let s = CGImageSourceCreateWithURL(URL(fileURLWithPath: p) as CFURL, nil)!; return CGImageSourceCreateImageAtIndex(s, 0, nil)! }
let l = load(a[1]), r = load(a[2]); let gap = 40, pad = 20
let w = l.width + r.width + gap + pad*2, h = max(l.height, r.height) + pad*2
let cs = CGColorSpaceCreateDeviceRGB()
let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0, space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.setFillColor(CGColor(red: 0.86, green: 0.86, blue: 0.86, alpha: 1)); ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
ctx.draw(l, in: CGRect(x: pad, y: pad, width: l.width, height: l.height))
ctx.draw(r, in: CGRect(x: pad + l.width + gap, y: pad, width: r.width, height: r.height))
let out = ctx.makeImage()!
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[3]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, out, nil); CGImageDestinationFinalize(dest)
