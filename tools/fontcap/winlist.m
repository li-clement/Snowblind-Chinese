// 列出 xemu 窗口 id（供 screencapture -l 精确抓窗，不依赖焦点/遮挡）
#import <CoreGraphics/CoreGraphics.h>
#import <Foundation/Foundation.h>
int main(int argc, char **argv) {
    @autoreleasepool {
        NSString *needle = argc > 1 ? [NSString stringWithUTF8String:argv[1]] : @"xemu";
        CFArrayRef wl = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID);
        for (CFIndex i = 0; i < CFArrayGetCount(wl); i++) {
            NSDictionary *w = (__bridge NSDictionary *)CFArrayGetValueAtIndex(wl, i);
            NSString *owner = w[@"kCGWindowOwnerName"] ?: @"";
            if ([owner rangeOfString:needle options:NSCaseInsensitiveSearch].location == NSNotFound) continue;
            NSDictionary *b = w[@"kCGWindowBounds"];
            printf("%d\t%s\t%dx%d\n", [w[@"kCGWindowNumber"] intValue], [owner UTF8String],
                   (int)[b[@"Width"] doubleValue], (int)[b[@"Height"] doubleValue]);
        }
    }
    return 0;
}
