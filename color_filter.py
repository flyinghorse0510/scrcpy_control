import cv2
YelloFilter = [(20, 43, 46), (34, 255, 255)]
RedFilter = [(), ()]
img = cv2.imread("./dragon.png")
img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
filteredImg = cv2.inRange(img_hsv, YelloFilter[0], YelloFilter[1])
# cv2.imshow("filterd", filteredImg)
cv2.imwrite("filterd_tiger.png", filteredImg)
print(filteredImg.sum() / (255.0 * filteredImg.size))