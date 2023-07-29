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

tessPSM = PSM.SINGLE_LINE
tessL = "chi_sim"

DragonBetArea = (600, 350, 960, 406)
TigerBetArea = (1484, 350, 1816, 406)
EqualBetArea = (1076, 406, 1354, 462)
StatusArea = (1056, 320, 1268, 386)
CenterStatusArea = (1110, 320, 1320, 386)
LeftTime1Area = (1268, 320, 1310, 386)
LeftTime0Area = (1316, 320, 1358, 386)
LeftTimeArea = (1268, 320, 1358, 386)
DragonWinArea = (900, 718, 1068, 790)
TigerWinArea = (1356, 718, 1524, 790)
YelloFilter = [(20, 43, 46), (34, 255, 255)]
Bet100Position = (846, 980)
Bet1000Position = (1030, 980)
Bet1wPosition = (1210, 980)
Bet10wPosition = (1392, 980)
Bet100wPosition = (1568, 980)
AddDragonBetPosition = (780, 550)
AddTigerBetPosition = (1650, 550)
BetSize = (1000000, 100000, 10000, 1000, 100)
DealerBetArea = (1104, 100, 1224, 140)

WINNER_ARRAY = ["龙","和","虎"]
frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=10)
remoteQueue = Queue(maxsize=100)

NUM_ENGLISH_OCR_PROC = 1
NUM_CHINESE_OCR_PROC = 6

FREE_STATE = 0
RESULT_STATE = 1
WATCH_STATE = 2
BET_STATE = 3
STOP_STATE = 4
UNKNOWN_STATE = 5

MAX_BET_CLICK = 6

DRAGON_WIN = 0
EQUAL_WIN = 1
TIGER_WIN = 2
NONE_WIN = 3

FREE_TIME = 0
BET_TIME = 1
STOP_TIME = 2
UNKNOWN_TIME = 3

DRAGON_SIDE = 0
TIGER_SIDE = 1
NONE_SIDE = 2

CALIBRATION_LIMIT = 120

BET_SIZE = 100
TEST_BET_SCALE = 10000

BET_CONFIRM_COUNT = 6


totalBet = 1000
totalGameCount = 0
totalWinCount = 0
totalLoseCount = 0
totalFrameCount = 0

currentDragonBet = 0
currentTigerBet = 0
currentEqualBet = 0
currentLeftTime = 15
currentWaitFrame = 0
expectedLeastBet = [0, 0]
currentSelfBet = [0, 0]
currentExpectedBet = [0, 0]
currentState = FREE_STATE
currentBetChoice = NONE_SIDE
currentDealer = ""

realTime = True
MAX_INT_NUMBER = 1000000000

infoTemplate = {"leftTime": -1, "statusId": UNKNOWN_TIME, "currentBet": [-1, -1, -1], "myBet": [-1, -1], "winner": NONE_WIN, "currentDealer": ""}

def get_info_template() -> dict:
    return {"leftTime": -1, "statusId": UNKNOWN_TIME, "currentBet": [-1, -1, -1], "myBet": [-1, -1], "winner": NONE_WIN, "currentDealer": ""}



def txt2int(txt: str) -> int:
    if len(txt) == 0:
        return 0
    number = 0
    multi = 1
    realTxt = txt
    if txt[-1] == "万":
        multi = 10000
        realTxt = realTxt[:-1]
    elif txt[-1] == "亿":
        multi = 100000000
        realTxt = realTxt[:-1]
    
    try:
        number = int(float(realTxt) * multi + 0.5)
    except ValueError as e1:
        number = -1
    except OverflowError as e2:
        number = -1
    except:
        print("Convert Error!")
        number = -1
    
    number = number if number < MAX_INT_NUMBER else -1
    return number

def is_chinese(txt: str) -> bool:
    for i in range(len(txt)):
        if txt[i] < '\u4e00' or txt[i] > '\u9fa5':
            return False
    return True

def is_yello_activated(img: Image.Image) -> bool:
    cvImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
    filteredImg = cv2.inRange(cvImg, YelloFilter[0], YelloFilter[1])
    yelloWeight = filteredImg.sum() / (255.0 * filteredImg.size)
    if yelloWeight >= 0.20:
        return True
    return False

def pureTxt2int(txt: str) -> int:
    if len(txt) == 0:
        return 0
    try:
        number = int(txt)
    except ValueError as e:
        number = -1
    except:
        print("Convert Error!")
        number = -1
        
    number = number if number < MAX_INT_NUMBER else -1
    return number

def cleanStr(txt: str) -> str:
    return txt.replace(" ", "").replace("-","").replace("一","").strip("\n")

def binarizePillow(img: Image.Image, threshold: int) -> Image.Image:
    outputImg = ImageOps.grayscale(img)
    return outputImg.point(lambda x: 0 if x > threshold else 255)

def submit_ocr(task: list, ocrQueue: Queue):
    try:
        ocrQueue.put(task, block=False)
    except queue.Full:
        print("OCR too slow! Blocking")
        ocrQueue.put(task, block=True)
        print("OCR Queue unblocked!")

def submit_status_ocr(gameScreen: Image.Image, chineseOcrQueue: Queue):
    sideStatusImg = gameScreen.crop(StatusArea)
    submit_ocr(["sideStatus", sideStatusImg], chineseOcrQueue)
    centerStatusImg = gameScreen.crop(CenterStatusArea)
    submit_ocr(["centerStatus", centerStatusImg], chineseOcrQueue)
    
def get_status_ocr(sideStatusTxt: str, centerStatusTxt: str) -> int:
    # print(statusTxt)
    if sideStatusTxt == "空闲时间":
        return FREE_TIME
    elif sideStatusTxt == "下注时间":
        return BET_TIME
    
    # print(centerStatusTxt)
    if centerStatusTxt == "停止下注":
        return STOP_TIME
    return UNKNOWN_TIME

def submit_bet_ocr(gameScreen: Image.Image, chineseOcrQueue: Queue):
    dragonBetImg = gameScreen.crop(DragonBetArea)
    tigerBetImg = gameScreen.crop(TigerBetArea)
    equalBetImg = gameScreen.crop(EqualBetArea)
    submit_ocr(["dragonBet", dragonBetImg], chineseOcrQueue)
    submit_ocr(["equalBet", equalBetImg], chineseOcrQueue)
    submit_ocr(["tigerBet", tigerBetImg], chineseOcrQueue)
    
def get_bet_ocr(dragonBetTxt: str, equalBetTxt: str, tigerBetTxt: str) -> list[int, int, int]:
    # Dragon Bet(Left)
    dragonBet = txt2int(dragonBetTxt)
    # Equal Bet(Center)
    equalBet = txt2int(equalBetTxt)
    # Tiger Bet(Right)
    tigerBet = txt2int(tigerBetTxt)
    # Result
    return [dragonBet, equalBet, tigerBet]
    
def submit_time_ocr(gameScreen: Image.Image, englishOcrQueue: Queue):
    leftTimeImg = gameScreen.crop(LeftTimeArea)
    submit_ocr(["leftTime", leftTimeImg], englishOcrQueue)
    
def get_time_ocr(leftTimeTxt: str) -> int:
    leftTime = pureTxt2int(leftTimeTxt)
    return leftTime

def submit_dealer_ocr(gameScreen: Image.Image, chineseOcrQueue: Queue):
    dealerBetImg = gameScreen.crop(DealerBetArea)
    submit_ocr(["dealerBet", dealerBetImg], chineseOcrQueue)
    
def get_dealer_ocr(dealerTxt: str) -> str:
    if dealerTxt.find("888") != -1:
        return "萌萌哒"
    return ""
    
def get_winner(gameScreen: Image.Image) -> int:
    dragonWinImg = gameScreen.crop(DragonWinArea)
    tigerWinImg = gameScreen.crop(TigerWinArea)
    dragonActivated = is_yello_activated(dragonWinImg)
    tigerActivated = is_yello_activated(tigerWinImg)
    if dragonActivated and tigerActivated:
        return EQUAL_WIN
    elif dragonActivated:
        return DRAGON_WIN
    elif tigerActivated:
        return TIGER_WIN
    return NONE_WIN
 

def remote_switch_bet(bet: int) -> int:
    if bet == 100:
        remote_control.long_click_screen(Bet100Position[0], Bet100Position[1])
    elif bet == 1000:
        remote_control.long_click_screen(Bet1000Position[0], Bet1000Position[1])
    elif bet == 10000:
        remote_control.long_click_screen(Bet1wPosition[0], Bet1wPosition[1])
    elif bet == 100000:
        remote_control.long_click_screen(Bet10wPosition[0], Bet10wPosition[1])
    elif bet == 1000000:
        remote_control.long_click_screen(Bet100wPosition[0], Bet100wPosition[1])
    else:
        return -1
    return 0

def remote_add_dragon_bet(targetBet: int) -> int:
    betCount = int(targetBet / BET_SIZE)
    for i in range(betCount):
        ret = remote_control.long_click_screen(AddDragonBetPosition[0], AddDragonBetPosition[1])
        time.sleep(0.12)
        if ret != 0:
            return ret
    return 0

def remote_add_tiger_bet(targetBet: int) -> int:
    betCount = int(targetBet / BET_SIZE)
    for i in range(betCount):
        ret = remote_control.long_click_screen(AddTigerBetPosition[0], AddTigerBetPosition[1])
        time.sleep(0.12)
        if ret != 0:
            return ret
    return 0

BetRatio1stLevel = [0.75, 0.9, 1.20]
BetRatio2ndLevel = [0.70, 0.9, 1.25]
BetRatio3rdLevel = [0.60, 0.9, 1.50]
def get_bet_ratio(bet: int, level: int = 0) -> float:
    if bet >= 60000000 / TEST_BET_SCALE:
        return BetRatio1stLevel[level]
    if bet >= 30000000 / TEST_BET_SCALE and bet < 60000000 / TEST_BET_SCALE:
        return BetRatio2ndLevel[level]
    if bet >= 10000000 / TEST_BET_SCALE and bet < 30000000 / TEST_BET_SCALE:
        return BetRatio3rdLevel[level]
    return None

BetAdditionList = [remote_add_dragon_bet, remote_add_tiger_bet]
def add_bet(bet: list[int], remoteQueue: Queue, remoteLock: Lock, realTime: bool = True) -> bool:
    global currentLeftTime
    global expectedLeastBet
    global currentSelfBet
    global currentLeftTime
    global currentBetChoice
    global currentExpectedBet
    minBet = min(bet[0], bet[2])
    maxBet = max(bet[0], bet[2])
    minIndex = DRAGON_SIDE if minBet == bet[0] else TIGER_SIDE
    maxIndex = 1 - minIndex
    deltaBet = maxBet - minBet
    if currentBetChoice == NONE_SIDE:
        betRatio = get_bet_ratio(deltaBet)
        expectedBet = 0
        if betRatio is None:
            if deltaBet > 5000000 / TEST_BET_SCALE:
                expectedBet = int((deltaBet - 5000000 / TEST_BET_SCALE) / BET_SIZE) * BET_SIZE
        elif maxBet * betRatio > minBet:
            expectedBet = int((maxBet * betRatio - minBet) / BET_SIZE) * BET_SIZE
            
        if expectedBet == 0:
            return True
        currentExpectedBet[minIndex] = expectedBet
        expectedLeastBet[minIndex] = minBet + expectedBet
        remoteCmd = [remote_switch_bet, BET_SIZE, BetAdditionList[minIndex], BET_SIZE]
        # trigger bet
        remoteQueue.put(remoteCmd)
        currentBetChoice = minIndex
        currentSelfBet[minIndex] += BET_SIZE
        print("#[Initial]# Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d, current_dragon_bet: %d, current_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1], bet[0], bet[2]))
    else:
        currentChoiceBet = bet[0] if currentBetChoice == DRAGON_SIDE else bet[2]
        currentOppoBet = bet[2] if currentBetChoice == DRAGON_SIDE else bet[0]
        calibratedDeltaBet = deltaBet + currentSelfBet[currentBetChoice]
        lowestBetRatio = get_bet_ratio(calibratedDeltaBet)
        mediumBetRatio = get_bet_ratio(calibratedDeltaBet, 1)
        highestBetRatio = get_bet_ratio(calibratedDeltaBet, 2)
        # calibratedDeltaBet between 500w ~ 1000w
        if lowestBetRatio is None:
            if deltaBet <= 5000000 / TEST_BET_SCALE or currentChoiceBet > currentOppoBet:
                expectedLeastBet[currentBetChoice] = expectedLeastBet[currentBetChoice] - currentExpectedBet[currentBetChoice] + currentSelfBet[currentBetChoice]
                currentExpectedBet[currentBetChoice] = currentSelfBet[currentBetChoice]
                # print("Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1]))
                return
            if currentChoiceBet >= expectedLeastBet[currentBetChoice]:
                expectedBet = int((deltaBet - 5000000 / TEST_BET_SCALE) / BET_SIZE) * BET_SIZE
                currentExpectedBet[currentBetChoice] = currentSelfBet[currentBetChoice] + expectedBet
                expectedLeastBet[currentBetChoice] = currentChoiceBet + expectedBet
                if expectedBet > 0:
                    print("#[Minimum]# Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d, current_dragon_bet: %d, current_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1], bet[0], bet[2]))
            if currentSelfBet[currentBetChoice] < currentExpectedBet[currentBetChoice]:
                # trigger bet
                lockSuccess = remoteLock.acquire(block=False)
                if lockSuccess:
                    remoteCmd = [BetAdditionList[currentBetChoice], BET_SIZE]
                    remoteQueue.put(remoteCmd)
                    currentSelfBet[currentBetChoice] += BET_SIZE
                    remoteLock.release()
            return
                    
        # [BET] < lowest bet ratio, continue add bet
        if currentOppoBet * lowestBetRatio > currentChoiceBet:
            # stop current-oppo-choice side
            expectedLeastBet[1-currentBetChoice] = expectedLeastBet[1-currentBetChoice] - currentExpectedBet[1-currentBetChoice] + currentSelfBet[1-currentBetChoice]
            currentExpectedBet[1-currentBetChoice] = currentSelfBet[1-currentBetChoice]
            # continue add bet(enlarge scale)
            if currentChoiceBet >= expectedLeastBet[currentBetChoice]:
                expectedBet = int((currentOppoBet * lowestBetRatio - currentChoiceBet) / BET_SIZE) * BET_SIZE
                currentExpectedBet[currentBetChoice] = currentSelfBet[currentBetChoice] + expectedBet
                expectedLeastBet[currentBetChoice] = currentChoiceBet + expectedBet
                if expectedBet > 0:
                    print("#[Lowest]# Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d, current_dragon_bet: %d, current_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1], bet[0], bet[2]))
            # add bet(keep scale)
            if currentSelfBet[currentBetChoice] < currentExpectedBet[currentBetChoice]:
                # trigger bet
                lockSuccess = remoteLock.acquire(block=False)
                if lockSuccess:
                    remoteCmd = [BetAdditionList[currentBetChoice], BET_SIZE]
                    remoteQueue.put(remoteCmd)
                    currentSelfBet[currentBetChoice] += BET_SIZE
                    remoteLock.release()
        # lowest bet ratio < [BET] < medium bet ratio
        elif currentOppoBet * mediumBetRatio > currentChoiceBet and deltaBet >= 5000000 / TEST_BET_SCALE:
            # stop both-current-side
            expectedLeastBet[currentBetChoice] = expectedLeastBet[currentBetChoice] - currentExpectedBet[currentBetChoice] + currentSelfBet[currentBetChoice]
            currentExpectedBet[currentBetChoice] = currentSelfBet[currentBetChoice]
            expectedLeastBet[1-currentBetChoice] = expectedLeastBet[1-currentBetChoice] - currentExpectedBet[1-currentBetChoice] + currentSelfBet[1-currentBetChoice]
            currentExpectedBet[1-currentBetChoice] = currentSelfBet[1-currentBetChoice]
            # print("Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1]))
        # medium bet ratio < [BET] < highest bet ratio
        elif currentOppoBet * highestBetRatio > currentChoiceBet or deltaBet < 5000000 / TEST_BET_SCALE:
            # stop current-bet-choice side
            expectedLeastBet[currentBetChoice] = expectedLeastBet[currentBetChoice] - currentExpectedBet[currentBetChoice] + currentSelfBet[currentBetChoice]
            currentExpectedBet[currentBetChoice] = currentSelfBet[currentBetChoice]
            # continue add bet(enlarge scale)
            if currentOppoBet >= expectedLeastBet[1-currentBetChoice]:
                expectedBet = max(int((currentChoiceBet / mediumBetRatio - currentOppoBet) / BET_SIZE) * BET_SIZE, int((5000000 / TEST_BET_SCALE - deltaBet) / BET_SIZE) * BET_SIZE)
                currentExpectedBet[1-currentBetChoice] = currentSelfBet[1-currentBetChoice] + expectedBet
                expectedLeastBet[1-currentBetChoice] = currentOppoBet + expectedBet
                if expectedBet > 0:
                    print("#[Medium]# Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d, current_dragon_bet: %d, current_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1], bet[0], bet[2]))
            # add bet(keep scale)
            if currentSelfBet[currentBetChoice] > currentSelfBet[1-currentBetChoice] and currentSelfBet[1-currentBetChoice] < currentExpectedBet[1-currentBetChoice]:
                lockSuccess = remoteLock.acquire(block=False)
                if lockSuccess:
                    remoteCmd = [BetAdditionList[1-currentBetChoice], BET_SIZE]
                    remoteQueue.put(remoteCmd)
                    currentSelfBet[1-currentBetChoice] += BET_SIZE
                    remoteLock.release()
        # [BET] > highest bet ratio
        elif currentChoiceBet >= currentOppoBet * highestBetRatio:
            # stop current-bet-choice side
            expectedLeastBet[currentBetChoice] = expectedLeastBet[currentBetChoice] - currentExpectedBet[currentBetChoice] + currentSelfBet[currentBetChoice]
            currentExpectedBet[currentBetChoice] = currentSelfBet[currentBetChoice]
            # continue add bet(enlarge scale)
            if currentOppoBet >= expectedLeastBet[1-currentBetChoice]:
                expectedBet = int((currentChoiceBet / highestBetRatio - currentOppoBet) / BET_SIZE) * BET_SIZE
                currentExpectedBet[1-currentBetChoice] = currentSelfBet[1-currentBetChoice] + expectedBet
                expectedLeastBet[1-currentBetChoice] = currentOppoBet + expectedBet
                if expectedBet > 0:
                    print("#[Highest]# Current bet: Dragon-->%.2lf, Tiger-->%.2lf (expected_dragon_bet: %d, expected_tiger_bet: %d, current_dragon_bet: %d, current_tiger_bet: %d)" %(currentSelfBet[0], currentSelfBet[1], currentExpectedBet[0], currentExpectedBet[1], bet[0], bet[2]))
            # add bet(keep scale)
            if currentSelfBet[1-currentBetChoice] < currentExpectedBet[1-currentBetChoice]:
                lockSuccess = remoteLock.acquire(block=False)
                if lockSuccess:
                    remoteCmd = [BetAdditionList[1-currentBetChoice], BET_SIZE]
                    remoteQueue.put(remoteCmd)
                    currentSelfBet[1-currentBetChoice] += BET_SIZE
                    remoteLock.release()
        else:
            print("Add bet fatal error!")
            return False
        
    return True

def returnValidMedium(buffer: list[int]) -> int:
    # # _--^
    if buffer[0] < buffer[1] and buffer[1] < buffer[2]:
        return buffer[1]
    
    return min(buffer)    

def clean_game():
    global currentDragonBet
    global currentTigerBet
    global currentEqualBet
    global currentLeftTime
    global currentWaitFrame
    global currentSelfBet
    global expectedLeastBet
    global currentBetChoice
    global currentExpectedBet
    global currentDealer
    currentDragonBet = 0
    currentTigerBet = 0
    currentEqualBet = 0
    currentLeftTime = 15
    currentWaitFrame = 0
    currentSelfBet = [0, 0]
    expectedLeastBet = [0, 0]
    currentExpectedBet = [0, 0]
    currentBetChoice = NONE_SIDE
    currentDealer = ""
    

EnterBetLimit = [
    5000000 / TEST_BET_SCALE, # 0s
    5000000 / TEST_BET_SCALE, # 1s
    10000000 / TEST_BET_SCALE, # 2s
    10000000 / TEST_BET_SCALE, # 3s
    10000000 / TEST_BET_SCALE, # 4s
    15000000 / TEST_BET_SCALE, # 5s
    20000000 / TEST_BET_SCALE, # 6s
    25000000 / TEST_BET_SCALE, # 7s
    30000000 / TEST_BET_SCALE, # 8s
    35000000 / TEST_BET_SCALE, # 9s
    40000000 / TEST_BET_SCALE] # 10s
def enter_bet_state(leftTime: int, deltaBet: int) -> bool:
    global EnterBetLimit
    if leftTime >= 11:
        return False
    if deltaBet >= EnterBetLimit[leftTime]:
        return True
    
    return False

def process_frame(infoDict: dict, recordFile, remoteQueue: Queue, remoteLock: Lock, realTime: bool = True) -> bool:
    global totalGameCount
    global currentWaitFrame
    global currentLeftTime
    global currentState
    global currentDragonBet
    global currentEqualBet
    global currentTigerBet
    global currentSelfBet
    global currentDealer
        
    statusId = infoDict["statusId"]
    leftTime = infoDict["leftTime"]
    currentBet = infoDict["currentBet"]
    winner = infoDict["winner"]
    currentDealer = currentDealer if currentDealer == "萌萌哒" else infoDict["currentDealer"]
    
    while True:
        if currentState == FREE_STATE:
            if statusId == FREE_TIME:
                break
            elif statusId == BET_TIME:
                print("<<<<<<<< Game Count: %d >>>>>>>>" %(totalGameCount+1))
                if currentDealer == "萌萌哒":
                    print("Current Dealer: 萌萌哒 --> NORMAL MODE")
                else:
                    print("******** WARNING: UNKNOWN DEALER ********")
                    print("*****************************************")
                    print("WATCH ONLY MODE")
                    print("*****************************************")
                    print("******** WARNING: UNKNOWN DEALER ********")
                currentState = WATCH_STATE
                continue
            else:
                break
        elif currentState == WATCH_STATE:
            currentLeftTime = currentLeftTime if leftTime < 0 or leftTime > currentLeftTime else leftTime
            deltaBet = abs(currentDragonBet - currentTigerBet)
            if statusId == STOP_TIME:
                currentState = STOP_STATE
                print("Stop Bet --> Time: %d, Delta: %d" %(currentLeftTime, deltaBet))
                break
            elif currentLeftTime >= 0:
                if enter_bet_state(currentLeftTime, deltaBet) and currentDealer == "萌萌哒":
                    currentState = BET_STATE
                    print("Begin Bet --> Time: %d, Delta: %d" %(currentLeftTime, deltaBet))
                    continue
                if currentBet[0] < currentDragonBet and currentBet[0] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentDragonBet, int(currentBet[0] / 100) * 100))
                    sys.stderr.flush()
                if currentBet[1] < currentEqualBet and currentBet[1] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentEqualBet, int(currentBet[1] / 100) * 100))
                    sys.stderr.flush()
                if currentBet[2] < currentTigerBet and currentBet[2] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentTigerBet, int(currentBet[2] / 100) * 100))
                    sys.stderr.flush()
                currentDragonBet = currentDragonBet if currentBet[0] < 0 else int(currentBet[0] / 100) * 100
                currentEqualBet = currentEqualBet if currentBet[1] < 0 else int(currentBet[1] / 100) * 100
                currentTigerBet = currentTigerBet if currentBet[2] < 0 else int(currentBet[2] / 100) * 100
                break
        elif currentState == BET_STATE:
            currentLeftTime = currentLeftTime if leftTime < 0 or leftTime > currentLeftTime else leftTime
            
            if statusId == STOP_TIME:
                currentState = STOP_STATE
                print("Stop Bet")
                continue
            else:
                if currentBet[0] < currentDragonBet and currentBet[0] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentDragonBet, int(currentBet[0] / 100) * 100))
                    sys.stderr.flush()
                if currentBet[1] < currentEqualBet and currentBet[1] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentEqualBet, int(currentBet[1] / 100) * 100))
                    sys.stderr.flush()
                if currentBet[2] < currentTigerBet and currentBet[2] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentTigerBet, int(currentBet[2] / 100) * 100))
                    sys.stderr.flush()
                currentDragonBet = currentDragonBet if currentBet[0] < 0 else int(currentBet[0] / 100) * 100
                currentEqualBet = currentEqualBet if currentBet[1] < 0 else int(currentBet[1] / 100) * 100
                currentTigerBet = currentTigerBet if currentBet[2] < 0 else int(currentBet[2] / 100) * 100
                add_bet([currentDragonBet, currentEqualBet, currentTigerBet], remoteQueue, remoteLock, realTime = realTime)
                break
        elif currentState == STOP_STATE:
            if statusId == UNKNOWN_TIME:
                currentState = RESULT_STATE
                print("Wait Result")
                break
            else:
                if currentBet[0] < currentDragonBet and currentBet[0] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentDragonBet, int(currentBet[0] / 100) * 100))
                    sys.stderr.flush()
                if currentBet[1] < currentEqualBet and currentBet[1] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentEqualBet, int(currentBet[1] / 100) * 100))
                    sys.stderr.flush()
                if currentBet[2] < currentTigerBet and currentBet[2] >= 0:
                    sys.stderr.write("[RESCUE]: %d --> %d" %(currentTigerBet, int(currentBet[2] / 100) * 100))
                    sys.stderr.flush()
                currentDragonBet = currentDragonBet if currentBet[0] < 0 else int(currentBet[0] / 100) * 100
                currentEqualBet = currentEqualBet if currentBet[1] < 0 else int(currentBet[1] / 100) * 100
                currentTigerBet = currentTigerBet if currentBet[2] < 0 else int(currentBet[2] / 100) * 100
                break
        elif currentState == RESULT_STATE:
            # if not remoteCompleteQueue.empty():
            #     remoteCancelQueue.put(None)
            
            if statusId == FREE_TIME:
                currentState = FREE_STATE
                print("******** Miss Result ********")
                break
            else:
                if winner != NONE_WIN:
                    print("Result Received!")
                    currentState = FREE_STATE
                    totalGameCount += 1
                    print("Dragon Bet: %d\nEqual Bet: %d\nTiger Bet: %d\nWinner: %s\nMy Expected Dragon Bet: %d\nMy Expected Tiger Bet: %d\n" %(currentDragonBet, currentEqualBet, currentTigerBet, WINNER_ARRAY[winner], currentSelfBet[0], currentSelfBet[1]))
                    recordFile.write("%d,%d,%d,%d,%s,%d,%d,%s\n" %(totalGameCount, currentDragonBet, currentEqualBet, currentTigerBet, WINNER_ARRAY[winner], currentSelfBet[0], currentSelfBet[1], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                    recordFile.flush()
                    clean_game()
                break
        else:
            print("Fatal Error! Undefined State!\n")
            
    return True 


# gameScreen = Image.open("./tiger_video/test2_dragon_win.jpg")
# print(get_winner(gameScreen))
# gameScreen = binarizePillow(gameScreen, 156)
# gameScreen.save("gameScreen.png")

def english_ocr_process(englishOcrQueue: Queue, ocrResultQueue: Queue):
    englishApi = PyTessBaseAPI(psm=tessPSM, lang = "eng")
    while True:
        task = englishOcrQueue.get()
        if task is None:
            englishOcrQueue.put(None)
            break
        englishApi.SetImage(task[1])
        englishTxt = cleanStr(englishApi.GetUTF8Text())
        ocrResultQueue.put([task[0], englishTxt])
    englishApi.End()
    print("English OCR instance terminated!")


def chinese_ocr_process(chineseOcrQueue: Queue, ocrResultQueue: Queue):
    chineseApi = PyTessBaseAPI(psm=tessPSM, lang = tessL)
    while True:
        task = chineseOcrQueue.get()
        if task is None:
            chineseOcrQueue.put(None)
            break
        chineseApi.SetImage(task[1])
        englishTxt = cleanStr(chineseApi.GetUTF8Text())
        ocrResultQueue.put([task[0], englishTxt])
    chineseApi.End()
    print("Chinese OCR instance terminated!")

def status_control_process(infoQueue: Queue, remoteQueue: Queue, remoteLock: Lock, realTime: bool = True):
    print("Status Control process started!")
    recordFile = open("record.csv", "w", encoding='utf-8-sig')
    recordFile.write("局数,龙,和,虎,赢,下注(龙),下注(虎),开牌时间\n")
    recordFile.flush()
    while True:
        infoDict = infoQueue.get()
        if infoDict is None:
            break
        process_frame(infoDict, recordFile, remoteQueue, remoteLock, realTime)
    print("Status Control process terminated!")
        
    
def remote_control_process(remoteQueue: Queue, remoteLock: Lock):
    ret = remote_control.begin_session()
    if ret != 0:
        print("Error start remote session!")
        return
    while True:
        cmd = remoteQueue.get()
        remoteLock.acquire()
        if cmd is None:
            break
        cmdLength = len(cmd)
        if cmdLength % 2 != 0:
            break
        cmdLength = int(cmdLength / 2)
        for i in range(cmdLength):
            ret = cmd[2*i](cmd[2*i+1])
            if ret != 0:
                print("Error execute remote instruction! Skip...")
                break
        remoteLock.release()
        
        
    remote_control.end_session()
    print("Remote session terminated!")
    

def frame_source_process(frameQueue: Queue, realTime: bool = True):
    cap = cv2.VideoCapture("/dev/video0")
    if not cap.isOpened():
        print("Fatal error! Open Video file failed!\n")
    print("Frame Reader started!")
    while cap.isOpened():
        ret, frame = cap.read()
        if ret == True:
            try:
                frameQueue.put(frame, block=not realTime)
            except queue.Full:
                frameQueue.get()
                frameQueue.put(frame, block=not realTime)
                sys.stderr.write("Computation side too slow! Dropping buffered frame...\n")
                sys.stderr.flush()
        else:
            break
    cap.release()
    print("Frame Reader terminated!")

def clock_calibration_hit(timeBuffer: list[int]) -> bool:
    if timeBuffer[2] == timeBuffer[0] - 1:
        if timeBuffer[0] == timeBuffer[1] or timeBuffer[1] == timeBuffer[2]:
            if timeBuffer[2] <= 14 and timeBuffer[2] >= 0:
                return True
    return False

def return_valid_time(timeBuffer: list[int]) -> int:
    if timeBuffer[0] == timeBuffer[1] or timeBuffer[0] == timeBuffer[2]:
        return timeBuffer[0]
    
    if timeBuffer[1] == timeBuffer[2]:
        return timeBuffer[1]
    
    return -1

def frame_filter_process(frameQueue: Queue, infoQueue: Queue, chineseOcrQueue: Queue, englishOcrQueue: Queue, ocrResultQueue: Queue):
    print("Frame Filter started!")
    frameBufferList = [get_info_template(), get_info_template(), get_info_template()]
    clockCalibrated = False
    clockCalibrationTag = 0
    lastInfo = get_info_template()
    lastFrameTime = time.time()
    dragonBetFilter = sline.SupportLine(BET_CONFIRM_COUNT)
    equalBetFilter = sline.SupportLine(BET_CONFIRM_COUNT)
    tigerBetFilter = sline.SupportLine(BET_CONFIRM_COUNT)
    
    while True:
        try:
            frame = frameQueue.get(block=False)
        except queue.Empty:
            deltaTime = time.time() - lastFrameTime
            if deltaTime >= 0.036:
                try:
                    if lastInfo["statusId"] != FREE_TIME and lastInfo["statusId"] != UNKNOWN_TIME:
                        lastInfo["currentBet"][0] = dragonBetFilter.update_support_line(frameBufferList[-1]["currentBet"][0])
                        lastInfo["currentBet"][1] = equalBetFilter.update_support_line(frameBufferList[-1]["currentBet"][1])
                        lastInfo["currentBet"][2] = tigerBetFilter.update_support_line(frameBufferList[-1]["currentBet"][2])
                    infoQueue.put(lastInfo, block=False)
                except queue.Full:
                    print("Status control too slow! Dropping info...")
                lastFrameTime = time.time()
            time.sleep(0.001)
            continue
                
                
        lastFrameTime = time.time()
        if frame is None:
            infoQueue.put(None)
            chineseOcrQueue.put(None)
            englishOcrQueue.put(None)
            break
        
        originalFrame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        binarizedFrame = binarizePillow(originalFrame, 150)
        
        # submit status task
        # submit_bet_ocr(binarizedFrame, chineseOcrQueue)
        submit_status_ocr(binarizedFrame, chineseOcrQueue)
        
        
        # update frameBufferList
        frameBufferList = frameBufferList[1:]
        frameBufferList.append(get_info_template())
        info = get_info_template()
        ocrResult = {}
        
        
        
        # collect statusId ocr result
        for i in range(2):
            result = ocrResultQueue.get()
            ocrResult[result[0]] = result[1]
        
        
        statusId = get_status_ocr(sideStatusTxt=ocrResult["sideStatus"], centerStatusTxt=ocrResult["centerStatus"])

        frameBufferList[-1]["statusId"] = statusId
        info["statusId"] = statusId
        
                
        resultCount = 0
        if statusId != FREE_TIME:
            if statusId == BET_TIME:
                if not clockCalibrated:
                    submit_time_ocr(binarizedFrame, englishOcrQueue)
                    resultCount += 1                  
                    
            if statusId != UNKNOWN_TIME:
                submit_bet_ocr(binarizedFrame, chineseOcrQueue)
                resultCount += 3
        else:
            if frameBufferList[-2]["currentDealer"] != "萌萌哒":
                submit_dealer_ocr(binarizedFrame, chineseOcrQueue)
                resultCount += 1
            else:
                frameBufferList[-1]["currentDealer"] = "萌萌哒"
            dragonBetFilter.reset_support_line()
            equalBetFilter.reset_support_line()
            tigerBetFilter.reset_support_line()
                
        # get_winner
        winner = get_winner(originalFrame)
        info["winner"] = winner
        
        # invalidate clock calibration if necessary
        if clockCalibrated:
            frameBufferList[-1]["leftTime"] = time_converter.get_current_left_time()
            info["leftTime"] = frameBufferList[-1]["leftTime"]  
            if statusId == FREE_TIME and time_converter.get_current_unix_time() - clockCalibrationTag >= CALIBRATION_LIMIT:
                print("Clock calibration invalidated!")
                clockCalibrated = False
        
        # collect for other ocr results
        for i in range(resultCount):
            result = ocrResultQueue.get()
            ocrResult[result[0]] = result[1]
        
        if not ocrResultQueue.empty():
            print("Fatal Error! Unknown remaining result!")
            break
        
        
        if statusId != FREE_TIME:
            if statusId == BET_TIME:
                # calibrate time
                if not clockCalibrated:
                    frameBufferList[-1]["leftTime"] = get_time_ocr(ocrResult["leftTime"])
                    timeBuffer = [frameBufferList[0]["leftTime"], frameBufferList[1]["leftTime"], frameBufferList[2]["leftTime"]]
                    if clock_calibration_hit(timeBuffer):
                        clockCalibrationTag = time_converter.get_current_unix_time()
                        clockCalibrated = True
                        print("Clock calibration hit! %d --> %d" %(time_converter.get_current_left_time(), frameBufferList[-1]["leftTime"]))
                        info["leftTime"] = time_converter.get_current_left_time(frameBufferList[-1]["leftTime"], True)
                    else:
                        info["leftTime"] = return_valid_time(timeBuffer)
                        
            # get bet
            if statusId != UNKNOWN_TIME:
                frameBufferList[-1]["currentBet"] = get_bet_ocr(dragonBetTxt=ocrResult["dragonBet"], equalBetTxt=ocrResult["equalBet"], tigerBetTxt=ocrResult["tigerBet"])
                info["currentBet"][0] = dragonBetFilter.update_support_line(frameBufferList[-1]["currentBet"][0])
                info["currentBet"][1] = equalBetFilter.update_support_line(frameBufferList[-1]["currentBet"][1])
                info["currentBet"][2] = tigerBetFilter.update_support_line(frameBufferList[-1]["currentBet"][2])
        elif frameBufferList[-1]["currentDealer"] != "萌萌哒":
            dealer = get_dealer_ocr(ocrResult["dealerBet"])
            frameBufferList[-1]["currentDealer"] = dealer
            info["currentDealer"] = dealer
        try:
            lastInfo = info.copy()
            infoQueue.put(info, block=False)
        except:
            print("Status control too slow! Dropping info...")
        
        
    print("Frame Filter Terminated!")
    

frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=15)
remoteQueue = Queue(maxsize=5)
chineseOcrQueue = Queue(maxsize=10)
englishOcrQueue = Queue(maxsize=10)
ocrResultQueue = Queue(maxsize=15)
remoteLock = Lock()
chineseOcrProcessPool = []
for i in range(NUM_CHINESE_OCR_PROC):
    chineseOcrProcessPool.append(Process(target=chinese_ocr_process, args=(chineseOcrQueue, ocrResultQueue)))
    chineseOcrProcessPool[i].start()
print("Successfully start chinese ocr process (%d in total)!" %(NUM_CHINESE_OCR_PROC))

englishOcrProcessPool = []
for i in range(NUM_ENGLISH_OCR_PROC):
    englishOcrProcessPool.append(Process(target=english_ocr_process, args=(englishOcrQueue, ocrResultQueue)))
    englishOcrProcessPool[i].start()
print("Successfully start english ocr process (%d in total)!" %(NUM_ENGLISH_OCR_PROC))


frameFilterProcess = Process(target=frame_filter_process, args=(frameQueue, infoQueue, chineseOcrQueue, englishOcrQueue, ocrResultQueue))
frameFilterProcess.start()

statusControlProcess = Process(target=status_control_process, args=(infoQueue, remoteQueue, remoteLock, realTime))
statusControlProcess.start()

remoteControlProcess = Process(target=remote_control_process, args=(remoteQueue, remoteLock))
remoteControlProcess.start()

frameSourceProcess = Process(target=frame_source_process, args=(frameQueue, realTime))
frameSourceProcess.start()


while True:
    time.sleep(1)



