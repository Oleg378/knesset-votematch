import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
// usage: crop <in.png> <out.png> <x> <y> <w> <h>  (device pixels)
let a = CommandLine.arguments
let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: a[1]) as CFURL, nil)!
let img = CGImageSourceCreateImageAtIndex(src, 0, nil)!
let r = CGRect(x: Int(a[3])!, y: Int(a[4])!, width: Int(a[5])!, height: Int(a[6])!)
let out = img.cropping(to: r)!
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: a[2]) as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(dest, out, nil)
print(CGImageDestinationFinalize(dest) ? "ok \(out.width)x\(out.height)" : "fail")
