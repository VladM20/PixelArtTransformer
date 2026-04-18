import cv2 as cv
import numpy as np

EGA_color_palette = {
    "#000000", "#0000aa", "#00aa00", "#00aaaa",
    "#aa0000", "#aa00aa", "#aa5500", "#aaaaaa",
    "#555555", "#5555ff", "#55ff55", "#55ffff",
    "#ff5555", "#ff55ff", "#ffff55", "#ffffff"
}

def hex2rgb(hex):
    rgb = []
    hex = hex.lstrip('#')
    for color in EGA_color_palette:
        r = int(hex[0:2], 16)
        g = int(hex[2:4], 16)
        b = int(hex[4:6], 16)
        rgb.append((r,g,b))
    return np.array(rgb)

# noinspection PyTypeChecker,PyShadowingNames
def readImage(filePath):
    img = cv.imread(filePath)
    if img is None:
        raise Exception("No image")
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    return img

def downscale(img, newWidth, newHeight, keepAspectRatio=False):
    height, width = img.shape[:2]
    if keepAspectRatio:
        newHeight = int(newWidth * (height / width))
    img_small = cv.resize(img,(newHeight,newWidth),interpolation=cv.INTER_AREA)
    return img_small

def upscale(img, newHeight, newWidth, keepAspectRatio=False):
    height, width = img.shape[:2]
    if keepAspectRatio:
        newHeight = int(newWidth * (height / width))
    img_large = cv.resize(img,(newHeight,newWidth),interpolation=cv.INTER_NEAREST_EXACT)
    return img_large


if __name__ == '__main__':
    img = cv.imread("dontjoke.jpg")
    img = downscale(img, 50, 10000, keepAspectRatio=True)
    cv.imshow("test", img)
    key = cv.waitKey(0)

if key == ord("q"):
    cv.destroyAllWindows()