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

EmptySeatColorFilter = (
    (22, 100, 100),
    (45, 255, 255)
)
UserThinkingColorFilter = (
    (84, 100, 100),
    (114, 255, 255)
)

UserFoldColorFilter = (
    (0, 8, 38),
    (180, 76, 90)
)

UserAllInColorFilter = (
    (12, 100, 150),
    (20, 255, 255)
)

PlayerBetColorFilter = (
    (5, 100, 150),
    (30, 255, 255)
)

AllInRef = np.array(Image.open("./imgData/ref_all_in.png"))
UserThinkingRef = np.array(Image.open("./imgData/ref_user_thinking.png"))

def bottom_bet_activated(img: Image.Image, saveImg: bool = False) -> bool:
    imgArray = np.array(img)
    weight = 1.0 - imgArray.sum() / (255.0 * imgArray.size)
    # print(weight)
    if weight >= 0.06 and weight <= 0.3:
        return True
    else:
        return False
    
def game_begin_activated(img: Image.Image, saveImg: bool = False) -> bool:
    imgArray = np.array(img)
    weight = 1.0 - imgArray.sum() / (255.0 * imgArray.size)
    # print(weight)
    if weight >= 0.06 and weight <= 0.3:
        return True
    else:
        return False
    
def empty_seat_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> bool:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, EmptySeatColorFilter[0], EmptySeatColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_empty_seat_%d.png" %(saveIndex))
    
    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)
    if weight >= 0.3 and weight <= 0.6:
        return True
    else:
        return False
    
def user_thinking_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> bool:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, UserThinkingColorFilter[0], UserThinkingColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_user_thinking_%d.png" %(saveIndex))
    
    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)
    if weight >= 0.42 and weight <= 0.55:
        distance = np.power((UserThinkingRef - filteredImgArray).flatten(), 2).sum()
        if distance <= 700:
            return True
    return False
    
def user_fold_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> bool:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    # print(cvImg.shape)
    filteredCvImg = cv2.inRange(cvImg, UserFoldColorFilter[0], UserFoldColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_user_fold_%d.png" %(saveIndex))

    weight = cvImg[:,:,2].sum() / (255.0 * cvImg.size)
    weightFold = filteredImgArray.sum() / (255.0 * filteredImgArray.size)
    if (weightFold >= 0.30 and weightFold <= 0.48) or weight <= 0.064:
        return True
    else:
        return False
    
def user_all_in_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> bool:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, UserAllInColorFilter[0], UserAllInColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_user_all_in_%d.png" %(saveIndex))

    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)
    if weight >= 0.35 and weight <= 0.65:
        distance = np.power((AllInRef - filteredImgArray).flatten(), 2).sum()
        if distance <= 600:
            return True
        else:
            return False
    return False

def player_bet_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0)-> bool:
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, PlayerBetColorFilter[0], PlayerBetColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_player_bet_%d.png" %(saveIndex))

    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)
    if weight >= 0.12:
        return True
    else:
        return False