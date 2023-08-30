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

USER_NULL = -1
USER_THINKING = 0
USER_FOLD = 1
USER_ALL_IN = 2
USER_EMPTY = 3
USER_ADD_BET = 4
USER_C_BET = 5

UserStatusArray = [USER_ALL_IN, USER_ADD_BET, USER_C_BET]

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

GameBeginColorFilter = (
    (0, 0, 153),
    (180, 102, 255)
)

AllInRef = np.array(Image.open("./imgData/ref_all_in.png"))
UserThinkingRef = np.array(Image.open("./imgData/ref_user_thinking.png"))
GameBeginRef = np.array(Image.open("./imgData/ref_game_begin.png"))
EmptySeatRef = np.array(Image.open("./imgData/ref_empty_seat.png"))
AddBetRef = np.array(Image.open("./imgData/ref_add_bet.png"))
CBetRef = np.array(Image.open("./imgData/ref_c_bet.png"))
LookBetRef = np.array(Image.open("./imgData/ref_look_bet.png"))

def bottom_bet_activated(img: Image.Image, saveImg: bool = False) -> bool:
    
    binarizedImg = utils.binarize_pillow(img, 90)
    
    imgArray = np.array(binarizedImg)
    weight = 1.0 - imgArray.sum() / (255.0 * imgArray.size)
    # print(weight)
    if weight >= 0.06 and weight <= 0.3:
        return True
    else:
        return False
    
def game_begin_activated(img: Image.Image, saveImg: bool = False) -> bool:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, GameBeginColorFilter[0], GameBeginColorFilter[1])

    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)

    if saveImg:
        filteredImg.save("./tmp/filtered_game_begin.png")
    
    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)

    if weight >= 0.08 and weight <= 0.27:
        return True

    return False
    
def empty_seat_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> bool:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, EmptySeatColorFilter[0], EmptySeatColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_empty_seat_%d.png" %(saveIndex))
    
    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)
    distance = np.power((EmptySeatRef - filteredImgArray).flatten(), 2).sum()
    # print(distance)
    # print(weight)
    if weight >= 0.2 and weight <= 0.7:
        distance = np.power((EmptySeatRef - filteredImgArray).flatten(), 2).sum()
        if distance <= 600:
            return True
    return False
    
def user_thinking_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> int:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, UserThinkingColorFilter[0], UserThinkingColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_user_thinking_%d.png" %(saveIndex))
    
    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)

    if weight >= 0.38 and weight <= 0.55:
        thinkingDistance = np.power((UserThinkingRef - filteredImgArray).flatten(), 2).sum()
        lookingDistance = np.power((LookBetRef - filteredImgArray).flatten(), 2).sum()
        distanceArray = [thinkingDistance, lookingDistance]

        minDistance = np.min(distanceArray)
        minIndex = np.argmin(distanceArray)

        if minDistance <= 600:
            if minIndex == 0:
                return USER_THINKING
            else:
                return USER_C_BET
            
    return USER_NULL
    
def user_fold_activated(globalBinarizedImg: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> bool:
    globalBinarizedImgArray = np.array(globalBinarizedImg)
    weight = 1.0 - globalBinarizedImgArray.sum() / (255.0 * globalBinarizedImgArray.size)

    if saveImg:
        globalBinarizedImg.save("./tmp/filtered_user_fold_%d.png" %(saveIndex))

    # print(weight)
    # print(weightFold)
    if weight <= 0.025:
        return True
    else:
        return False
    
def user_all_in_activated(img: Image.Image, saveImg: bool = False, saveIndex: int = 0) -> int:
    
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredCvImg = cv2.inRange(cvImg, UserAllInColorFilter[0], UserAllInColorFilter[1])
    
    filteredImg = Image.fromarray(filteredCvImg)
    filteredImgArray = np.array(filteredImg)
    if saveImg:
        filteredImg.save("./tmp/filtered_user_all_in_%d.png" %(saveIndex))

    weight = filteredImgArray.sum() / (255.0 * filteredImgArray.size)

    # print(weight)
    if weight >= 0.30 and weight <= 0.65:

        allInDistance = np.power((AllInRef - filteredImgArray).flatten(), 2).sum()
        addBetDistance = np.power((AddBetRef - filteredImgArray).flatten(), 2).sum()
        cBetDistance = np.power((CBetRef - filteredImgArray).flatten(), 2).sum()
        distanceArray = [allInDistance, addBetDistance, cBetDistance]

        minDistance = np.min(distanceArray)
        minIndex = np.argmin(distanceArray)

        if minDistance <= 600:
            return UserStatusArray[minIndex]

    return USER_NULL

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