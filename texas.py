from PIL import Image, ImageOps
import cv2
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Lock
# from tesserocr import PyTessBaseAPI, PSM
# from tesserocr import get_languages
import queue
import remote_control
import random
import time
import time_converter
import sys
import support_line as sline
import utils

BottomBetArea = (1084, 300, 1440, 340)
GameBeginArea = (1106, 484, 1430, 532)

PlayerStatusArea = (
    (768, 24, 918, 68),
    (424, 154, 574, 198),
    (368, 484, 518, 528),
    (658, 678, 808, 722),
    (1192, 678, 1342, 722),
    (1720, 678, 1870, 722),
    (2008, 484, 2158, 528),
    (1948, 154, 2098, 198),
    (1608, 24, 1758, 68)
)





def bottom_bet_test(imgPath: str) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    bottomBetImg = originalImg.crop(BottomBetArea)
    bottomBetImg.save("./tmp/bottomBet.png")
    binarizedBottomImg = utils.binarizePillow(bottomBetImg, 90)
    binarizedBottomImg.save("./tmp/binarizedBottomBet.png")
    # bottomBetImg.show()
    

bottom_bet_test("./texas/user_thinking.png")