from PIL import Image, ImageOps
import cv2
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
from tesserocr import PyTessBaseAPI, PSM
from tesserocr import get_languages
import queue
import threading
import remote_control
import random
import time

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

WINNER_ARRAY = ["龙","和","虎"]
frameQueue = Queue(maxsize=30)
infoQueue = Queue(maxsize=10)
remoteQueue = Queue(maxsize=100)

NUM_ENGLISH_OCR_PROC = 1
NUM_CHINESE_OCR_PROC = 3

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

LEFT_TIME_THRESHOLD = 5
WAIT_FRAME_THRESHOLD = 0

BET_FIRST_THRESHOLD = 3000
BET_SECOND_THRESHOLD = 1000
REVERT_RATIO_UPPER_LIMIT = 0.6
REVERT_RATIO_LOWER_LIMIT = 0.5

FREE_TIME = 0
BET_TIME = 1
STOP_TIME = 2
UNKNOWN_TIME = 3

BET_SIZE = 100

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
currentState = FREE_STATE

realTime = True


infoTemplate = {"leftTime": -1, "statusId": UNKNOWN_TIME, "currentBet": [-1, -1, -1], "myBet": [-1, -1], "winner": NONE_WIN}

def get_info_template() -> dict:
    return {"leftTime": -1, "statusId": UNKNOWN_TIME, "currentBet": [-1, -1, -1], "myBet": [-1, -1], "winner": NONE_WIN}



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
    except ValueError as e:
        number = -1
    
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
    
def get_bet_ocr(dragonBetTxt: str, equalBetTxt: str, tigerBetTxt: str) -> tuple[int, int, int]:
    # Dragon Bet(Left)
    dragonBet = txt2int(dragonBetTxt)
    # Equal Bet(Center)
    equalBet = txt2int(equalBetTxt)
    # Tiger Bet(Right)
    tigerBet = txt2int(tigerBetTxt)
    # Result
    return (dragonBet, equalBet, tigerBet)
    
def submit_time_ocr(gameScreen: Image.Image, englishOcrQueue: Queue):
    leftTimeImg = gameScreen.crop(LeftTimeArea)
    submit_ocr(["leftTime", leftTimeImg], englishOcrQueue)
    
def get_time_ocr(leftTimeTxt: str) -> int:
    leftTime = pureTxt2int(leftTimeTxt)
    return leftTime
    
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
    remote_switch_bet(BET_SIZE)
    betCount = int(targetBet / BET_SIZE)
    for i in range(betCount):
        ret = remote_control.long_click_screen(AddDragonBetPosition[0], AddDragonBetPosition[1])
        time.sleep(0.15)
        if ret != 0:
            return ret
    return 0

def remote_add_tiger_bet(targetBet: int) -> int:
    remote_switch_bet(BET_SIZE)
    betCount = int(targetBet / BET_SIZE)
    for i in range(betCount):
        ret = remote_control.long_click_screen(AddTigerBetPosition[0], AddTigerBetPosition[1])
        time.sleep(0.15)
        if ret != 0:
            return ret
    return 0

def add_bet(bet: list[int], remoteQueue: Queue, remoteCompleteQueue: Queue, remoteCancelQueue: Queue, realTime: bool = True) -> bool:
    global currentLeftTime
    global expectedLeastBet
    global currentSelfBet
    global currentLeftTime
    minBet = min(bet[0], bet[2])
    maxBet = max(bet[0], bet[2])
    if not remoteCompleteQueue.empty():
        return
    if (currentLeftTime > 1 and maxBet >= BET_FIRST_THRESHOLD) or (currentLeftTime <= 1 and maxBet >= BET_SECOND_THRESHOLD):
        if maxBet * REVERT_RATIO_LOWER_LIMIT > minBet:
            betRatio = random.uniform(REVERT_RATIO_LOWER_LIMIT+0.05, REVERT_RATIO_UPPER_LIMIT)
            try:
                if bet[0] < bet[2]:
                    if realTime and expectedLeastBet[0] < minBet:
                        expectedBet = int((maxBet * betRatio - minBet) / BET_SIZE) * BET_SIZE
                        expectedBet = min(expectedBet, currentLeftTime * BET_SIZE * 6)
                        expectedLeastBet[0] = minBet + expectedBet
                        currentSelfBet[0] += expectedBet
                        expectedBetCount = int(expectedBet / BET_SIZE)
                        remoteCmd = [remote_switch_bet, BET_SIZE]
                        for i in range(expectedBetCount):
                            remoteCmd.append(remote_add_dragon_bet)
                            remoteCmd.append(BET_SIZE)
                        remoteQueue.put(remoteCmd, block=False)
                        print("remote_add_dragon_bet: %.2lf (ratio: %.4lf)" %(expectedBet, betRatio))
                else:
                    if realTime and expectedLeastBet[1] < minBet:
                        expectedBet = int((maxBet * betRatio - minBet) / BET_SIZE) * BET_SIZE
                        expectedBet = min(expectedBet, currentLeftTime * BET_SIZE * 6)
                        expectedLeastBet[1] = minBet + expectedBet
                        currentSelfBet[1] += expectedBet
                        expectedBetCount = int(expectedBet / BET_SIZE)
                        remoteCmd = [remote_switch_bet, BET_SIZE]
                        for i in range(expectedBetCount):
                            remoteCmd.append(remote_add_tiger_bet)
                            remoteCmd.append(BET_SIZE)
                        remoteQueue.put(remoteCmd, block=False)
                        print("remote_add_tiger_bet: %.2lf (ratio: %.4lf)" %(expectedBet, betRatio))
            except queue.Full:
                print("Fatal Error! REMOTE QUEUE FULL!")
                return False
    return True

def returnValidMedium(buffer: list[int]) -> int:
    # _--^
    if buffer[0] <= buffer[1] and buffer[1] <= buffer[2]:
        return buffer[1]
    
    # -x- or --x
    if buffer[0] == buffer[1] or buffer[0] == buffer[2]:
        return buffer[0]
    # x--
    if buffer[1] == buffer[2]:
        return buffer[1]
    
    # ^-_
    if buffer[0] >= buffer[1] and buffer[1] >= buffer[2]:
        return buffer[2]
    
    # ^_^
    if buffer[0] >= buffer[1] and buffer[2] >= buffer[1]:
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
    currentDragonBet = 0
    currentTigerBet = 0
    currentEqualBet = 0
    currentLeftTime = 15
    currentWaitFrame = 0
    currentSelfBet = [0, 0]
    expectedLeastBet = [0, 0]
    
def process_frame(infoDict: dict, recordFile, remoteQueue: Queue, remoteCompleteQueue: Queue, remoteCancelQueue: Queue, realTime: bool = True) -> bool:
    global totalGameCount
    global currentWaitFrame
    global currentLeftTime
    global currentState
    global currentDragonBet
    global currentEqualBet
    global currentTigerBet
    global currentSelfBet
        
    statusId = infoDict["statusId"]
    leftTime = infoDict["leftTime"]
    currentBet = infoDict["currentBet"]
    winner = infoDict["winner"]
    
    while True:
        if currentState == FREE_STATE:
            if statusId == FREE_TIME:
                break
            elif statusId == BET_TIME:
                print("<<<<<<<< Game Count: %d >>>>>>>>" %(totalGameCount+1))
                currentState = WATCH_STATE
                continue
            else:
                break
        elif currentState == WATCH_STATE:
            currentLeftTime = currentLeftTime if leftTime < 0 or leftTime > currentLeftTime else leftTime
            
            if statusId == STOP_TIME:
                currentState = STOP_STATE
                print("Stop Bet")
                break
            elif currentLeftTime <= LEFT_TIME_THRESHOLD and currentLeftTime > 0:
                currentState = BET_STATE
                print("Begin Bet")
                continue
            else:
                currentDragonBet = currentDragonBet if currentBet[0] <= currentDragonBet else int(currentBet[0] / 100) * 100
                currentEqualBet = currentEqualBet if currentBet[1] <= currentEqualBet else int(currentBet[1] / 100) * 100
                currentTigerBet = currentTigerBet if currentBet[2] <= currentTigerBet else int(currentBet[2] / 100) * 100
                break
        elif currentState == BET_STATE:
            currentLeftTime = currentLeftTime if leftTime < 0 or leftTime > currentLeftTime else leftTime
            
            if statusId == STOP_TIME:
                currentState = STOP_STATE
                print("Stop Bet")
                continue
            else:
                newDragonBet = currentDragonBet if currentBet[0] <= currentDragonBet else int(currentBet[0] / 100) * 100
                newEqualBet = currentEqualBet if currentBet[1] <= currentEqualBet else int(currentBet[1] / 100) * 100
                newTigerBet = currentTigerBet if currentBet[2] <= currentTigerBet else int(currentBet[2] / 100) * 100
                add_bet([newDragonBet, newEqualBet, newTigerBet], remoteQueue=remoteQueue, remoteCompleteQueue=remoteCompleteQueue, remoteCancelQueue=remoteCancelQueue, realTime = realTime)
                currentDragonBet = newDragonBet
                currentEqualBet = newEqualBet
                currentTigerBet = newTigerBet
                break
        elif currentState == STOP_STATE:
            if statusId == UNKNOWN_TIME:
                currentState = RESULT_STATE
                print("Wait Result")
                break
            else:
                currentDragonBet = currentDragonBet if currentBet[0] <= currentDragonBet else int(currentBet[0] / 100) * 100
                currentEqualBet = currentEqualBet if currentBet[1] <= currentEqualBet else int(currentBet[1] / 100) * 100
                currentTigerBet = currentTigerBet if currentBet[2] <= currentTigerBet else int(currentBet[2] / 100) * 100
                break
        elif currentState == RESULT_STATE:
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
                    recordFile.write("%d,%d,%d,%d,%s,%d,%d\n" %(totalGameCount, currentDragonBet, currentEqualBet, currentTigerBet, WINNER_ARRAY[winner], currentSelfBet[0], currentSelfBet[1]))
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
        if task == None:
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
        if task == None:
            chineseOcrQueue.put(None)
            break
        chineseApi.SetImage(task[1])
        englishTxt = cleanStr(chineseApi.GetUTF8Text())
        ocrResultQueue.put([task[0], englishTxt])
    chineseApi.End()
    print("Chinese OCR instance terminated!")

def status_control_process(infoQueue: Queue, remoteQueue: Queue, remoteCompleteQueue: Queue, remoteCancelQueue: Queue, realTime: bool = True):
    print("Status Control process started!")
    recordFile = open("record.csv", "w", encoding='utf-8-sig')
    recordFile.write("局数,龙,和,虎,赢,下注(龙),下注(虎)\n")
    recordFile.flush()
    while True:
        infoDict = infoQueue.get()
        if infoDict == None:
            break
        process_frame(infoDict, recordFile, remoteQueue, remoteCompleteQueue, remoteCancelQueue, realTime)
    print("Status Control process terminated!")
        
    
def remote_control_process(remoteQueue: Queue, remoteCompleteQueue: Queue, remoteCancelQueue: Queue):
    ret = remote_control.begin_session()
    if ret != 0:
        print("Error start remote session!")
        return
    while True:
        cmd = remoteQueue.get()
        if cmd == None:
            break
        cmdLength = len(cmd)
        if cmdLength % 2 != 0:
            break
        cmdLength = int(cmdLength / 2)
        for i in range(cmdLength):
            if not remoteCancelQueue.empty():
                print("Bet half canceled!")
                remoteCancelQueue.get()
                break
            ret = cmd[2*i](cmd[2*i+1])
            if ret != 0:
                print("Error execute remote instruction! Skip...")
                break
        try:
            remoteCompleteQueue.get(block=False)
        except queue.Empty:
            print("Remote control fatal error!")
            break
        
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
                print("Computation side too slow! Dropping frame...")
        else:
            break
    cap.release()
    print("Frame Reader terminated!")
    
def frame_filter_process(frameQueue: Queue, infoQueue: Queue, chineseOcrQueue: Queue, englishOcrQueue: Queue, ocrResultQueue: Queue):
    print("Frame Filter started!")
    frameBufferList = [get_info_template(), get_info_template(), get_info_template()]
    
    while True:
        frame = frameQueue.get()
        if frame == None:
            infoQueue.put(None)
            chineseOcrQueue.put(None)
            englishOcrQueue.put(None)
            break
        
        originalFrame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        binarizedFrame = binarizePillow(originalFrame, 156)
        
        # submit ocr task
        submit_bet_ocr(binarizedFrame, chineseOcrQueue)
        submit_time_ocr(binarizedFrame, englishOcrQueue)
        submit_status_ocr(binarizedFrame, chineseOcrQueue)
        
        # get_winner
        winner = get_winner(originalFrame)
        
        # update frameBufferList
        frameBufferList = frameBufferList[1:]
        frameBufferList.append(get_info_template())
        info = get_info_template()
        ocrResult = {}
        
        # collect ocr result
        for i in range(6):
            result = ocrResultQueue.get()
            ocrResult[result[0]] = result[1]
        
        if not ocrResultQueue.empty():
            print("Fatal Error! Unknown remaining result!")
            break
        
        statusId = get_status_ocr(sideStatusTxt=ocrResult["sideStatus"], centerStatusTxt=ocrResult["centerStatus"])

        frameBufferList[-1]["statusId"] = statusId
        info["statusId"] = statusId
        info["winner"] = winner
        
        if statusId != FREE_TIME:
            if statusId != STOP_TIME:
                frameBufferList[-1]["leftTime"] = get_time_ocr(ocrResult["leftTime"])
                info["leftTime"] = frameBufferList[-1]["leftTime"]
            
            if statusId != UNKNOWN_TIME:
                frameBufferList[-1]["currentBet"] = get_bet_ocr(dragonBetTxt=ocrResult["dragonBet"], equalBetTxt=ocrResult["equalBet"], tigerBetTxt=ocrResult["tigerBet"])
                info["currentBet"][0] = returnValidMedium([frameBufferList[0]["currentBet"][0], frameBufferList[1]["currentBet"][0], frameBufferList[2]["currentBet"][0]])
                info["currentBet"][1] = returnValidMedium([frameBufferList[0]["currentBet"][1], frameBufferList[1]["currentBet"][1], frameBufferList[2]["currentBet"][1]])
                info["currentBet"][2] = returnValidMedium([frameBufferList[0]["currentBet"][2], frameBufferList[1]["currentBet"][2], frameBufferList[2]["currentBet"][2]])
            
        infoQueue.put(info)
        
        
    print("Frame Filter Terminated!")
    

frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=15)
remoteQueue = Queue(maxsize=5)
remoteCompleteQueue = Queue(maxsize=2)
remoteCancelQueue = Queue(maxsize=2)
chineseOcrQueue = Queue(maxsize=10)
englishOcrQueue = Queue(maxsize=10)
ocrResultQueue = Queue(maxsize=15)

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

statusControlProcess = Process(target=status_control_process, args=(infoQueue, remoteQueue, remoteCompleteQueue, remoteCancelQueue, realTime))
statusControlProcess.start()

remoteControlProcess = Process(target=remote_control_process, args=(remoteQueue, remoteCompleteQueue, remoteCancelQueue))
remoteControlProcess.start()

frameSourceProcess = Process(target=frame_source_process, args=(frameQueue, realTime))
frameSourceProcess.start()


while True:
    time.sleep(1)



