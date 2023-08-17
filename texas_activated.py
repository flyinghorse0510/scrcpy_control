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
import utils
import texas_suit

def bottom_bet_activated(img: Image.Image) -> bool:
    imgArray = np.array(img)
    weight = 1.0 - imgArray.sum() / (255.0 * imgArray.size)
    # print(weight)
    if weight >= 0.06 and weight <= 0.3:
        return True
    else:
        return False
    
def game_begin_activated(img: Image.Image) -> bool:
    imgArray = np.array(img)
    weight = 1.0 - imgArray.sum() / (255.0 * imgArray.size)
    # print(weight)
    if weight >= 0.06 and weight <= 0.3:
        return True
    else:
        return False