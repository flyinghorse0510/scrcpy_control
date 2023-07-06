from PIL import Image, ImageOps
import cv2
from tesserocr import PyTessBaseAPI, PSM
from tesserocr import get_languages
tessPSM = PSM.SINGLE_LINE
tessL = "chi_sim"

DragonBetArea = (600, 350, 960, 406)
TigerBetArea = (1484, 350, 1816, 406)
EqualBetArea = (1076, 406, 1354, 462)
StatusArea = (1056, 320, 1268, 386)
CenterStatusArea = (1110, 320, 1320, 386)
LeftTime1Area = (1268, 320, 1310, 386)
LeftTime0Area = (1316, 320, 1358, 386)
DragonWinArea = (900, 718, 1068, 790)
TigerWinArea = (1356, 718, 1524, 790)

WINNER_ARRAY = ["龙","和","虎"]

FREE_STATE = 0
RESULT_STATE = 1
WATCH_STATE = 2
BET_STATE = 3
STOP_STATE = 4
UNKNOWN_STATE = 5

DRAGON_BET = 0
EQUAL_BET = 1
TIGER_BET = 2

DRAGON_WIN = 0
EQUAL_WIN = 1
TIGER_WIN = 2
NONE_WIN = 3

LEFT_TIME_THRESHOLD = 1
WAIT_FRAME_THRESHOLD = 0

FREE_TIME = 0
BET_TIME = 1
STOP_TIME = 2
UNKNOWN_TIME = 3

totalBet = 1000
totalGameCount = 0
totalWinCount = 0
totalLoseCount = 0
totalFrameCount = 0

currentDragonBet = 0
currentTigerBet = 0
currentEqualBet = 0
currentLeftTime = -1
currentWaitFrame = 0
currentBet = 0
currentBetChoice = DRAGON_BET
currentState = FREE_STATE

chineseApi = PyTessBaseAPI(psm=tessPSM, lang = tessL)
englishApi = PyTessBaseAPI(psm=tessPSM, lang = "eng")

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
        number = int(float(realTxt) * multi)
    except ValueError as e:
        number = -1
    
    return number

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

def recognize_chinese(img: Image.Image) -> str:
    chineseApi.SetImage(img)
    return cleanStr(chineseApi.GetUTF8Text())

def recognize_english(img: Image.Image) -> str:
    englishApi.SetImage(img)
    return cleanStr(englishApi.GetUTF8Text())

def get_status(gameScreen: Image.Image) -> int:
    statusImg = gameScreen.crop(StatusArea)
    statusTxt = recognize_chinese(statusImg)
    # print(statusTxt)
    if statusTxt == "空闲时间":
        return FREE_TIME
    elif statusTxt == "下注时间":
        return BET_TIME
    centerStatusImg = gameScreen.crop(CenterStatusArea)
    centerStatusTxt = recognize_chinese(centerStatusImg)
    # print(centerStatusTxt)
    if centerStatusTxt == "停止下注":
        return STOP_TIME
    return UNKNOWN_TIME

def get_bet(gameScreen: Image.Image) -> tuple[int, int, int]:
    dragonBetImg = gameScreen.crop(DragonBetArea)
    tigerBetImg = gameScreen.crop(TigerBetArea)
    equalBetImg = gameScreen.crop(EqualBetArea)
    # Dragon Bet(Left)
    chineseApi.SetImage(dragonBetImg)
    dragonBetTxt = cleanStr(chineseApi.GetUTF8Text())
    dragonBet = txt2int(dragonBetTxt)
    # dragonBetImg.save("dragon.png")
    # print(dragonBetTxt)
    # Equal Bet(Center)
    chineseApi.SetImage(equalBetImg)
    equalBetTxt = cleanStr(chineseApi.GetUTF8Text())
    equalBet = txt2int(equalBetTxt)
    # equalBetImg.save("equal.png")
    # print(equalBetTxt)
    # Tiger Bet(Right)
    chineseApi.SetImage(tigerBetImg)
    tigerBetTxt = cleanStr(chineseApi.GetUTF8Text())
    tigerBet = txt2int(tigerBetTxt)
    # print(tigerBetTxt)
    # tigerBetImg.save("tiger.png")
    # Result
    return (dragonBet, equalBet, tigerBet)

def get_left_time(gameScreen: Image.Image) -> int:
    leftTime1Img = gameScreen.crop(LeftTime1Area)
    leftTime0Img = gameScreen.crop(LeftTime0Area)
    englishApi.SetImage(leftTime1Img)
    leftTime1Txt = cleanStr(englishApi.GetUTF8Text())
    englishApi.SetImage(leftTime0Img)
    leftTime0Txt = cleanStr(englishApi.GetUTF8Text())
    leftTimeTxt = leftTime1Txt + leftTime0Txt
    leftTime = pureTxt2int(leftTimeTxt)
    return leftTime
    
def get_winner(gameScreen: Image.Image) -> int:
    dragonWinImg = gameScreen.crop(DragonWinArea)
    dragonWinTxt = recognize_chinese(dragonWinImg)
    tigerWinImg = gameScreen.crop(TigerWinArea)
    tigerWinTxt = recognize_chinese(tigerWinImg)
    if dragonWinTxt == "利不" or tigerWinTxt == "初雪":
        return EQUAL_WIN
    elif dragonWinTxt == "伟下":
        return DRAGON_WIN
    elif tigerWinTxt == "虚两":
        return TIGER_WIN
    return NONE_WIN

def add_bet(bet: list[int]) -> bool:
    return True

def clean_game():
    global currentDragonBet
    global currentTigerBet
    global currentEqualBet
    global currentLeftTime
    global currentWaitFrame
    global currentBet
    global currentBetChoice
    currentDragonBet = 0
    currentTigerBet = 0
    currentEqualBet = 0
    currentLeftTime = -1
    currentWaitFrame = 0
    currentBet = 0
    currentBetChoice = DRAGON_BET
    
def process_frame(gameScreen: Image.Image) -> bool:
    global totalGameCount
    global currentWaitFrame
    global currentLeftTime
    global currentState
    global currentDragonBet
    global currentEqualBet
    global currentTigerBet
    
    statusId = get_status(gameScreen)
    leftTime = get_left_time(gameScreen)
    currentLeftTime = currentLeftTime if leftTime == -1 else leftTime
    
    
    while True:
        if currentState == FREE_STATE:
            if statusId == FREE_TIME:
                break
            elif statusId == BET_TIME:
                print("<<<<<<<< Game Count: %d >>>>>>>>" %(totalGameCount))
                currentState = WATCH_STATE
                continue
            else:
                break
        elif currentState == WATCH_STATE:
            if statusId == STOP_TIME:
                currentState = STOP_STATE
                print("Stop Bet")
                break
            elif currentLeftTime <= LEFT_TIME_THRESHOLD and currentLeftTime > 0:
                currentState = BET_STATE
                print("Begin Bet")
                continue
            else:
                currentBet = get_bet(gameScreen)
                currentDragonBet = currentDragonBet if currentBet[0] == -1 else currentBet[0]
                currentEqualBet = currentEqualBet if currentBet[1] == -1 else currentBet[1]
                currentTigerBet = currentTigerBet if currentBet[2] == -1 else currentBet[2]
                break
        elif currentState == BET_STATE:
            if statusId == STOP_TIME:
                currentState = STOP_STATE
                print("Stop Bet")
                continue
            else:
                currentBet = get_bet(gameScreen)
                currentDragonBet = currentDragonBet if currentBet[0] == -1 else currentBet[0]
                currentEqualBet = currentEqualBet if currentBet[1] == -1 else currentBet[1]
                currentTigerBet = currentTigerBet if currentBet[2] == -1 else currentBet[2]
                if currentWaitFrame == WAIT_FRAME_THRESHOLD:
                    add_bet([currentDragonBet, currentEqualBet, currentTigerBet])
                if currentBet[0] != -1 and currentBet[1] != -1 and currentBet[2] != -1:
                    currentWaitFrame += 1
                break
        elif currentState == STOP_STATE:
            if statusId == UNKNOWN_TIME:
                currentState = RESULT_STATE
                print("Wait Result")
                break
            else:
                currentBet = get_bet(gameScreen)
                currentDragonBet = currentDragonBet if currentBet[0] == -1 else currentBet[0]
                currentEqualBet = currentEqualBet if currentBet[1] == -1 else currentBet[1]
                currentTigerBet = currentTigerBet if currentBet[2] == -1 else currentBet[2]
                break
        elif currentState == RESULT_STATE:
            if statusId == FREE_TIME:
                currentState = FREE_STATE
                print("******** Miss Result ********")
                break
            else:
                winner = get_winner(gameScreen)
                if winner != NONE_WIN:
                    print("Result Received!")
                    currentState = FREE_STATE
                    totalGameCount += 1
                    print("Dragon Bet: %d\nEqual Bet: %d\nTiger Bet: %d\nWinner: %s" %(currentDragonBet, currentEqualBet, currentTigerBet, WINNER_ARRAY[winner]))
                    recordFile.write("%d,%d,%d,%d,%s\n" %(totalGameCount+1, currentDragonBet, currentEqualBet, currentTigerBet, WINNER_ARRAY[winner]))
                    recordFile.flush()
                    clean_game()
                break
        else:
            print("Fatal Error! Undefined State!\n")
            
    return True 


# gameScreen = Image.open("./tiger_video/test2_equal_win.jpg")
# gameScreen = binarizePillow(gameScreen, 156)
# gameScreen.save("gameScreen.png")
# print(get_winner(gameScreen))


# statusId = get_status(gameScreen)
# leftTime = get_left_time(gameScreen)
# print("Status ID")
# print(statusId)
# print("Left Time")
# print(leftTime)
# print("Bet")
# print(get_bet(gameScreen))
# print("Winner")
# print(get_winner(gameScreen))

recordFile = open("record.csv", "w", encoding='utf-8-sig')
recordFile.write("局数,龙,和,虎,赢\n")
recordFile.flush()

totalFrame = 0
cap = cv2.VideoCapture("./tiger_video/test.mp4")
if not cap.isOpened():
    print("Fatal error! Open Video file failed!\n")
    chineseApi.End()
    englishApi.End()

while cap.isOpened():
    ret, frame = cap.read()
    if ret == True:
        gameScreen = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        gameScreen = binarizePillow(gameScreen, 156)
        process_frame(gameScreen)
        totalFrame += 1
        # if totalFrame % 300 == 0:
        #     print("Video Time: %ds" %(totalFrame/60))
    else:
        break


cap.release()



chineseApi.End()
englishApi.End()