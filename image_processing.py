import cv2 as cv



def downscale(img, newWidth, newHeight, keepAspectRatio=False):
    if img is None:
        raise Exception("No image")
    # downscale
    height, width = img.shape[:2]
    if keepAspectRatio:
        newHeight = int(newWidth * (height / width))
    img_small = cv.resize(img,(newHeight,newWidth),interpolation=cv.INTER_AREA)
    # TODO: Color processing
    # upscale
    img_large = cv.resize(img_small,(height,width),interpolation=cv.INTER_NEAREST_EXACT)
    return img_large

img = cv.imread("dontjoke.jpg")
img = downscale(img, 10, 10, keepAspectRatio=False)
cv.imshow("test", img)
key = cv.waitKey(0)

if key == ord("q"):
    cv.destroyAllWindows()