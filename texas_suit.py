from PIL import Image, ImageOps
import cv2
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Lock
import queue
import remote_control
import random
import time
import time_converter
import sys
import support_line as sline
import utils

SUIT_UNKNOWN = -1
SUIT_SPADE = 0
SUIT_CLUB = 1
SUIT_HEART = 2
SUIT_DIAMOND = 3

MAX_VALID_DISTANCE = 320000

SuitSymbolArray = (
    "♠",
    "♣",
    "♥",
    "♦"
)

SuitSpadeRef = np.array(Image.open("./imgData/ref_suit_spade.png"))
SuitClubRef = np.array(Image.open("./imgData/ref_suit_club.png"))
SuitHeartRef = np.array(Image.open("./imgData/ref_suit_heart.png"))
SuitDiamondRef = np.array(Image.open("./imgData/ref_suit_diamond.png"))
SuitRef = (
    SuitSpadeRef,
    SuitClubRef,
    SuitHeartRef,
    SuitDiamondRef
)
def find_suit(img: Image.Image) -> int:
    imgArray = np.array(img)
    distanceArray = np.zeros(4, dtype=np.float32)
    for i in range(4):
        distanceArray[i] = np.power((SuitRef[i] - imgArray).flatten(), 2).sum()
    minDistance = np.min(distanceArray)
    minIndex = np.argmin(distanceArray)
    minIndex = minIndex if minDistance <= MAX_VALID_DISTANCE else SUIT_UNKNOWN
    return minIndex