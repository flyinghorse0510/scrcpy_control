from PIL import Image, ImageOps
import cv2
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Lock
from tesserocr import PyTessBaseAPI, PSM
from tesserocr import get_languages
import queue
import remote_control
import random
import time
import time_converter
import sys
import support_line as sline

BottomBetArea = (1114, 296, 1414, 344)



def bottom_bet_test(imgPath: str) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    bottomBetImg = originalImg.crop(BottomBetArea)
    bottomBetImg.show()
    

bottom_bet_test("./texas/user_thinking.png")