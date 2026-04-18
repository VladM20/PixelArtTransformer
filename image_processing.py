import cv2 as cv
import numpy as np
import matplotlib.pyplot as plot

EGA_color_palette = [
    "#000000", "#0000aa", "#00aa00", "#00aaaa",
    "#aa0000", "#aa00aa", "#aa5500", "#aaaaaa",
    "#555555", "#5555ff", "#55ff55", "#55ffff",
    "#ff5555", "#ff55ff", "#ffff55", "#ffffff"
]

def hex2rgb(hex):
    rgb = []
    for color in hex:
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        rgb.append((r,g,b))
    return np.array(rgb).astype(np.uint8)

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

def upscale(img, newWidth, newHeight, keepAspectRatio=False):
    height, width = img.shape[:2]
    if keepAspectRatio:
        newHeight = int(newWidth * (height / width))
    img_large = cv.resize(img,(newHeight,newWidth),interpolation=cv.INTER_NEAREST_EXACT)
    return img_large

def colorProcessing(img, palette):
    height, width, channels = img.shape
    pixels = img.reshape(-1, channels).astype(np.float32)
    palette = hex2rgb(palette).astype(np.float32)

    print(pixels)
    # calculating the difference between the original color values and the palette ones
    diff = pixels[:,np.newaxis,:] - palette[np.newaxis,:,:]
    # calculating the squared distance
    # we only need the minimum distance so there is no point in calculating square root
    square_distance = np.sum(diff ** 2, axis=2)
    # extracting the index of the closest color
    new_colors = np.argmin(square_distance, axis=1)
    new_pixels = palette[new_colors]
    new_img = new_pixels.reshape((height,width,channels))
    return new_img.astype(np.uint8)


if __name__ == '__main__':
    img = readImage("dontjoke.jpg")
    height, width = img.shape[:2]
    # noinspection PyTypeChecker
    img = downscale(img, 50, 100, keepAspectRatio=True)
    img = colorProcessing(img, palette=EGA_color_palette)
    img = upscale(img, 500, 600, keepAspectRatio=True)
    img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    cv.imshow("img", img)
    key = cv.waitKey(0)
    if key == ord("q"):
        cv.destroyAllWindows()