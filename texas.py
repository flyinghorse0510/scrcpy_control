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
import texas_activated
import texas_record
import A4TrainRef as a4_ref
from copy import deepcopy

tessPSM = PSM.SINGLE_LINE
tessSingleCharacterPSM = PSM.SINGLE_CHAR
tessL = "chi_sim"
realTime = False
videoSouce = "./texas/new_remote_texas_001000_004200.mp4"
DeltaPixel = -5


USER_NULL = -1
USER_THINKING = 0
USER_FOLD = 1
USER_ALL_IN = 2
USER_EMPTY = 3
USER_ADD_BET = 4
USER_C_BET = 5

BET_CONFIRM_COUNT = 4
RANK_CONFIRM_COUNT = 2

CARD_RANK_UNKNOWN = -1
CARD_RANK_A = 0
CARD_RANK_2 = 1
CARD_RANK_3 = 2
CARD_RANK_4 = 3
CARD_RANK_5 = 4
CARD_RANK_6 = 5
CARD_RANK_7 = 6
CARD_RANK_8 = 7
CARD_RANK_9 = 8
CARD_RANK_10 = 9
CARD_RANK_J = 10
CARD_RANK_Q = 11
CARD_RANK_K = 12

STATUS_WAIT_FOR_BEGIN = 0
STATUS_FIRST_ROUND = 1
STATUS_SECOND_ROUND = 2
STATUS_THIRD_ROUND = 3
STATUS_FOURTH_ROUND = 4
STATUS_END = 5
STATUS_PLAYING = 6
STATUS_NULL = -1

NUM_ENGLISH_OCR_PROC = 5
NUM_CHINESE_OCR_PROC = 2

FrameBottomBetFilter = sline.SupportLine(BET_CONFIRM_COUNT, 1000000000000)

BottomBetArea = (1084, 300, 1440, 340)
GameBeginArea = (1106, 484, 1430, 532)
GameInfoArea = (894, 636, 1606, 672)

frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=10)
remoteQueue = Queue(maxsize=100)

gameStatus = STATUS_NULL
playerList = []
playerActionList = []
playerNoActionList = []
playerBet = []
gameInfo = {"smallBlind": -1, "largeBlind": -1, "smallBlindIndex": -1, "largeBlindIndex": -1, "playerBottomBet": -1}
bottomBet = -1
currentPlayerIndex = -1
totalRoundCount = 0
playerExpectedBet = -1
currentGameRound = 0

UserStatusStringArray = ["USER_THINKING", "USER_FOLD", "USER_ALL_IN", "USER_EMPTY", "USER_ADD_BET", "USER_C_BET", "USER_NULL"]

PublicCardCalibrationArray = (
    (875 + DeltaPixel, 452),
    (1029 + DeltaPixel, 452),
    (1184 + DeltaPixel, 452),
    (1339 + DeltaPixel, 452),
    (1493 + DeltaPixel, 452)
)

PlayerCalibrationArray = (
    (749 + DeltaPixel, 253),
    (408 + DeltaPixel, 384),
    (350 + DeltaPixel, 713),
    (640 + DeltaPixel, 906),
    (1170 + DeltaPixel, 906),
    (1701 + DeltaPixel, 906),
    (1989 + DeltaPixel, 713),
    (1930 + DeltaPixel, 384),
    (1591 + DeltaPixel, 253)
)

PublicCardRankSize = (48, 60)
PublicCardRankOffset = (5, -4)

PublicCardSuitSize = (37, 41)
PublicCardSuitOffset = (10, 57)

PlayerCardRankSize = (46, 56)
PlayerCardRankOffsetArray = (
    (8, -178),
    (56, -178)
)

PlayerCardSuitSize = (37, 41)
PlayerCardSuitOffsetArray = (
    (12, -123),
    (62, -123)
)

PlayerStatusBlockSize = (108, 22)
PlayerStatusBlockOffset = (40, -207)

EmptySeatBlockSize = (69, 33)
EmptySeatBlockOffset = (49, -182)

PublicCardRankArray = []
for i in range(5):
    PublicCardRankArray.append(
        (
            PublicCardCalibrationArray[i][0] + PublicCardRankOffset[0],
            PublicCardCalibrationArray[i][1] + PublicCardRankOffset[1],
            PublicCardCalibrationArray[i][0] + PublicCardRankOffset[0] + PublicCardRankSize[0],
            PublicCardCalibrationArray[i][1] + PublicCardRankOffset[1] + PublicCardRankSize[1]
        )
    )
PublicCardRankArray = tuple(PublicCardRankArray)

PublicCardSuitArray = []
for i in range(5):
    PublicCardSuitArray.append(
        (
            PublicCardCalibrationArray[i][0] + PublicCardSuitOffset[0],
            PublicCardCalibrationArray[i][1] + PublicCardSuitOffset[1],
            PublicCardCalibrationArray[i][0] + PublicCardSuitOffset[0] + PublicCardSuitSize[0],
            PublicCardCalibrationArray[i][1] + PublicCardSuitOffset[1] + PublicCardSuitSize[1]
        )
    )

PlayerCardRankArray = []
for i in range(9):
    PlayerCardRank = []
    for j in range(2):
        PlayerCardRank.append(
            (
                PlayerCalibrationArray[i][0] + PlayerCardRankOffsetArray[j][0],
                PlayerCalibrationArray[i][1] + PlayerCardRankOffsetArray[j][1],
                PlayerCalibrationArray[i][0] + PlayerCardRankOffsetArray[j][0] + PlayerCardRankSize[0],
                PlayerCalibrationArray[i][1] + PlayerCardRankOffsetArray[j][1] + PlayerCardRankSize[1]
            )
        )
    PlayerCardRank = tuple(PlayerCardRank)
    PlayerCardRankArray.append(PlayerCardRank)
PlayerCardRankArray = tuple(PlayerCardRankArray)

PlayerCardSuitArray = []
for i in range(9):
    PlayerCardSuit = []
    for j in range(2):
        PlayerCardSuit.append(
            (
                PlayerCalibrationArray[i][0] + PlayerCardSuitOffsetArray[j][0],
                PlayerCalibrationArray[i][1] + PlayerCardSuitOffsetArray[j][1],
                PlayerCalibrationArray[i][0] + PlayerCardSuitOffsetArray[j][0] + PlayerCardSuitSize[0],
                PlayerCalibrationArray[i][1] + PlayerCardSuitOffsetArray[j][1] + PlayerCardSuitSize[1]
            )
        )
    PlayerCardSuit = tuple(PlayerCardSuit)
    PlayerCardSuitArray.append(PlayerCardSuit)
PlayerCardSuitArray = tuple(PlayerCardSuitArray)

EmptySeatArray = []
for i in range(9):
    EmptySeatArray.append(
        (
            PlayerCalibrationArray[i][0] + EmptySeatBlockOffset[0],
            PlayerCalibrationArray[i][1] + EmptySeatBlockOffset[1],
            PlayerCalibrationArray[i][0] + EmptySeatBlockOffset[0] + EmptySeatBlockSize[0],
            PlayerCalibrationArray[i][1] + EmptySeatBlockOffset[1] + EmptySeatBlockSize[1],
        )
    )
EmptySeatArray = tuple(EmptySeatArray)


PlayerStatusArray = []
for i in range(9):
    PlayerStatusArray.append(
        (
            PlayerCalibrationArray[i][0] + PlayerStatusBlockOffset[0],
            PlayerCalibrationArray[i][1] + PlayerStatusBlockOffset[1],
            PlayerCalibrationArray[i][0] + PlayerStatusBlockOffset[0] + PlayerStatusBlockSize[0],
            PlayerCalibrationArray[i][1] + PlayerStatusBlockOffset[1] + PlayerStatusBlockSize[1],
        )
    )
PlayerStatusArray = tuple(PlayerStatusArray)

PlayerBetArray = (
    (873, 335, 963, 375),
    (702, 355, 792, 395),
    (635, 518, 725, 558),
    (698, 628, 788, 668),
    (983, 697, 1073, 737),
    (1514, 697, 1604, 737),
    (1800, 518, 1890, 558),
    (1734, 369, 1824, 409),
    (1543, 335, 1633, 375)
)

def get_info_template() -> dict:
    return deepcopy({
        "bottomBetActivated": False, 
        "gameBeginActivated": False, 
        "playerStatus": [
            USER_NULL,
            USER_NULL,
            USER_NULL,
            USER_NULL,
            USER_NULL,
            USER_NULL,
            USER_NULL,
            USER_NULL,
            USER_NULL
        ],
        "playerBet": [
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False
        ],
        "playerCardSuit": [
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
            [texas_suit.SUIT_UNKNOWN, texas_suit.SUIT_UNKNOWN],
        ],
        "playerCardRank": [
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN],
            [CARD_RANK_UNKNOWN, CARD_RANK_UNKNOWN]
        ],
        "publicCardSuit": [
            texas_suit.SUIT_UNKNOWN,
            texas_suit.SUIT_UNKNOWN,
            texas_suit.SUIT_UNKNOWN,
            texas_suit.SUIT_UNKNOWN,
            texas_suit.SUIT_UNKNOWN
        ],
        "publicCardRank": [
            CARD_RANK_UNKNOWN,
            CARD_RANK_UNKNOWN,
            CARD_RANK_UNKNOWN,
            CARD_RANK_UNKNOWN,
            CARD_RANK_UNKNOWN,
        ],
        "currentBottomBet": -1,
        "gameInfo": {"smallBlind": -1, "largeBlind": -1, "playerBottomBet": -1}
    })
    
    
def english_ocr_process(englishOcrQueue: Queue, ocrResultQueue: Queue):
    englishApi = PyTessBaseAPI(psm=tessPSM, lang = "eng")
    while True:
        task = englishOcrQueue.get()
        if task is None:
            englishOcrQueue.put(None)
            break
        englishApi.SetImage(task[1])
        englishTxt = utils.clean_str(englishApi.GetUTF8Text())
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
        chineseTxt = utils.clean_str(chineseApi.GetUTF8Text())
        ocrResultQueue.put([task[0], chineseTxt])
    chineseApi.End()
    print("Chinese OCR instance terminated!")    
    
def submit_ocr(task: list, ocrQueue: Queue):
    try:
        ocrQueue.put(task, block=False)
    except queue.Full:
        print("OCR too slow! Blocking")
        ocrQueue.put(task, block=True)
        print("OCR Queue unblocked!")
        
def submit_bottom_bet_ocr(bottomBetImg: Image.Image, chineseOcrQueue: Queue):
    binarizedBottomBetImg = utils.binarize_pillow(bottomBetImg, 90)
    submit_ocr(["currentBottomBet", binarizedBottomBetImg], chineseOcrQueue)

def submit_game_info_ocr(gameInfoImg: Image.Image, chineseOcrQueue: Queue):
    binarizedGameInfoImg = utils.binarize_pillow(gameInfoImg, 90)
    submit_ocr(["gameInfo", binarizedGameInfoImg], chineseOcrQueue)
    
def get_game_info_ocr(gameInfoTxt: str) -> dict:
    beginIndex = gameInfoTxt.find("桌")
    if beginIndex == -1:
        beginIndex = gameInfoTxt.find("号")
    if beginIndex == -1:
        return {"smallBlind": -1, "largeBlind": -1, "playerBottomBet": -1}
    
    for i in range(beginIndex-1, len(gameInfoTxt)):
        if gameInfoTxt[i] <= "9" and gameInfoTxt[i] >= "0":
            smallBlindIndex = i
            break
    # smallBlind
    smallBlindTxt = ""
    smallBlindEndIndex = -1
    for i in range(smallBlindIndex, len(gameInfoTxt)):
        if gameInfoTxt[i] <= "9" and gameInfoTxt[i] >= "0":
            smallBlindTxt += gameInfoTxt[i]
        else:
            smallBlindEndIndex = i + 1
            smallBlindTxt += gameInfoTxt[i]
            break
    
    for i in range(smallBlindEndIndex, len(gameInfoTxt)):
        if gameInfoTxt[i] <= "9" and gameInfoTxt[i] >= "0":
            largeBlindIndex = i
            break
    # Large Blind    
    largeBlindTxt = ""
    largeBlindEndIndex = ""
    for i in range(largeBlindIndex, len(gameInfoTxt)):
        if gameInfoTxt[i] <= "9" and gameInfoTxt[i] >= "0":
            largeBlindTxt += gameInfoTxt[i]
        else:
            largeBlindEndIndex = i + 1
            largeBlindTxt += gameInfoTxt[i]
            break
    
    for i in range(largeBlindEndIndex, len(gameInfoTxt)):
        if gameInfoTxt[i] <= "9" and gameInfoTxt[i] >= "0":
            playerBottomBetIndex = i
            break
    # Player Bottom Bet
    playerBottomBetTxt = ""
    for i in range(playerBottomBetIndex, len(gameInfoTxt)):
        if gameInfoTxt[i] <= "9" and gameInfoTxt[i] >= "0":
            playerBottomBetTxt += gameInfoTxt[i]
        else:
            playerBottomBetTxt += gameInfoTxt[i]
            break
    
    smallBlind = utils.txt2int(smallBlindTxt)
    largeBlind = utils.txt2int(largeBlindTxt)
    playerBottomBet = utils.txt2int(playerBottomBetTxt)
    
    if smallBlind * 2 != largeBlind or playerBottomBet <= largeBlind:
        smallBlind = -1
        largeBlind = -1
        playerBottomBet = -1
    
    return {"smallBlind": smallBlind, "largeBlind": largeBlind, "playerBottomBet": playerBottomBet}

def valid_game_info(gameInfo: dict) -> bool:
    if gameInfo["smallBlind"] != -1 and gameInfo["largeBlind"] != -1 and gameInfo["playerBottomBet"] != -1:
        return True
    return False
 
def submit_card_rank_ocr(cardRankImg: Image.Image, englishOcrQueue: Queue, uuid: str):
    binarizedCardRankImg = utils.revert_binarize_pillow(cardRankImg, 100)
    submit_ocr([uuid, binarizedCardRankImg], englishOcrQueue)
    
def get_bottom_bet(bottomBetTxt: str) -> int:
    filteredBottomBetTxt = utils.filter_until_number(utils.clean_str(bottomBetTxt))
    return utils.txt2int(filteredBottomBetTxt)

def get_card_rank(cardRankTxt: str) -> int:
    filteredCardRankTxt = utils.card_rank_replace(utils.clean_str(cardRankTxt))
    if filteredCardRankTxt <= "9" and filteredCardRankTxt >= "0":
        try:
            rank = int(filteredCardRankTxt) - 1
            if rank < 0 or rank > 12:
                return CARD_RANK_UNKNOWN
            return rank
        except:
            # print("UNKNOWN CARD RANK ==> %s" %(filteredCardRankTxt))
            return CARD_RANK_UNKNOWN
    if filteredCardRankTxt == "A":
        return CARD_RANK_A
    elif filteredCardRankTxt == "J":
        return CARD_RANK_J
    elif filteredCardRankTxt == "Q":
        return CARD_RANK_Q
    elif filteredCardRankTxt == "K":
        return CARD_RANK_K
    
    # print("UNKNOWN CARD RANK ==> %s" %(filteredCardRankTxt))
    return CARD_RANK_UNKNOWN

def get_player_status(playerStatusImg: Image.Image, playerEmptySeatImg: Image.Image, globalBinarizedStatusImg: Image.Image, debug: bool = False, saveIndex: int = 0) -> int:
    if texas_activated.empty_seat_activated(playerEmptySeatImg, debug, saveIndex):
        return USER_EMPTY
    
    if texas_activated.user_fold_activated(globalBinarizedStatusImg, debug, saveIndex):
        return USER_FOLD
    
    userThinkingStatus = texas_activated.user_thinking_activated(playerStatusImg, debug, saveIndex)
    if userThinkingStatus != USER_NULL:
        return userThinkingStatus
    
    userAllInStatus = texas_activated.user_all_in_activated(playerStatusImg, debug, saveIndex)
    if userAllInStatus != USER_NULL:
        return userAllInStatus
    
    return USER_NULL

def frame_filter_process(frameQueue: Queue, infoQueue: Queue, chineseOcrQueue: Queue, englishOcrQueue: Queue, ocrResultQueue: Queue):
    print("Frame Filter started!")
    infoBuffer = get_info_template()
    debugCount = 0
    while True:
   
        frame = frameQueue.get(block = True)
        if frame is None:
            infoQueue.put(None)
            chineseOcrQueue.put(None)
            englishOcrQueue.put(None)
            break
        debugCount += 1
        info = deepcopy(infoBuffer)
        originalFrame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        globalBinarizedFrame = utils.binarize_pillow(originalFrame, 105)
        
        gameBeginAreaImg = originalFrame.crop(GameBeginArea)
        bottomBetAreaImg = originalFrame.crop(BottomBetArea)
        # gameBeginAreaImg.save("./tmp/gameBeginImg.png")
        # bottomBetAreaImg.save("./tmp/bottomBetAreaImg.png")
        
        gameBeginActivated = texas_activated.game_begin_activated(gameBeginAreaImg)
        bottomBetActivated = texas_activated.bottom_bet_activated(bottomBetAreaImg)
        info["gameBeginActivated"] = gameBeginActivated
        info["bottomBetActivated"] = bottomBetActivated
        # print("[%s] %d %d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), gameBeginActivated, bottomBetActivated))
        ocrResult = {}
        ocrResultCount = 0
        # Game Begin
        if gameBeginActivated and (not bottomBetActivated):
            info = get_info_template()
            info["gameBeginActivated"] = gameBeginActivated
            if valid_game_info(infoBuffer["gameInfo"]):
                info["gameInfo"] = deepcopy(infoBuffer["gameInfo"])
            else:
                # Game Info
                submit_game_info_ocr(originalFrame.crop(GameInfoArea), chineseOcrQueue)
                ocrResultCount += 1
            
            for i in range(ocrResultCount):
                result = ocrResultQueue.get()
                ocrResult[result[0]] = result[1]
            
            if ocrResultCount > 0:
                info["gameInfo"] = get_game_info_ocr(ocrResult["gameInfo"])
            
            infoBuffer = info
            try:
                infoQueue.put(deepcopy(info), block=False)
            except queue.Full:
                print("Status control too slow! Dropping info...")

            continue
        
        # Bottom Bet
        if bottomBetActivated:
            submit_bottom_bet_ocr(bottomBetAreaImg, chineseOcrQueue)
            ocrResultCount += 1
            
        # Player
        for i in range(9):
            if info["playerStatus"][i] == USER_EMPTY or info["playerStatus"][i] == USER_FOLD:
                continue
            # Status
            if info["playerStatus"][i] != USER_EMPTY and info["playerStatus"][i] != USER_FOLD and info["playerStatus"][i] != USER_ALL_IN:
                playerStatus = get_player_status(originalFrame.crop(PlayerStatusArray[i]), originalFrame.crop(EmptySeatArray[i]), globalBinarizedFrame.crop(PlayerStatusArray[i]))
                info["playerStatus"][i] = playerStatus
                # if i == 5 and info["playerStatus"][i] != USER_THINKING:
                #     originalFrame.save("./tmp/original_%d.png" %(debugCount))
                #     originalFrame.crop(PlayerStatusArray[i]).save("./tmp/player_status_%d.png" %(debugCount))
                if playerStatus == USER_EMPTY or playerStatus == USER_FOLD:
                    continue
                        
            # Player Card and Suit
            for j in range(2):
                suit = texas_suit.find_suit(originalFrame.crop(PlayerCardSuitArray[i][j]))
                
                if suit != texas_suit.SUIT_UNKNOWN:
                    info["playerCardSuit"][i][j] = suit
                    submit_card_rank_ocr(originalFrame.crop(PlayerCardRankArray[i][j]), englishOcrQueue, "player_%d%d" %(i, j))
                    ocrResultCount += 1

        # Player Initial Bet
        playerBetValid = False
        for i in range(9):
            if info["playerStatus"][i] == USER_THINKING:
                playerBetValid = True
                break

        if playerBetValid:
            for i in range(9):
                # Bet
                if (not info["playerBet"][i]) and info["playerStatus"][i] != USER_EMPTY and info["playerStatus"][i] != USER_FOLD:
                    info["playerBet"][i] = texas_activated.player_bet_activated(originalFrame.crop(PlayerBetArray[i]))
            
        # Public
        for i in range(5):
            suit = texas_suit.find_suit(originalFrame.crop(PublicCardSuitArray[i]))

            if suit != texas_suit.SUIT_UNKNOWN:
                info["publicCardSuit"][i] = suit
                submit_card_rank_ocr(originalFrame.crop(PublicCardRankArray[i]), englishOcrQueue, "public_%d" %(i))
                ocrResultCount += 1
            
                
        # Collect OCR Results
        for i in range(ocrResultCount):
            result = ocrResultQueue.get()
            ocrResult[result[0]] = result[1]
            
        # Process BottomBet
        if "currentBottomBet" in ocrResult:
            info["currentBottomBet"] = get_bottom_bet(ocrResult["currentBottomBet"])
            del ocrResult["currentBottomBet"]
            

        # Process Card Rank
        for key in ocrResult:
            if key[:6] == "player":
                i = int(key[7])
                j = int(key[8])
                rank = get_card_rank(ocrResult[key])

                if rank == CARD_RANK_A:
                    rank = a4_ref.get_actual_card_rank(originalFrame.crop(PlayerCardRankArray[i][j]))

                if rank != CARD_RANK_UNKNOWN:
                    info["playerCardRank"][i][j] = rank
                else:
                    info["playerCardSuit"][i][j] = infoBuffer["playerCardSuit"][i][j]

            elif key[:6] == "public":
                i = int(key[7])
                rank = get_card_rank(ocrResult[key])

                if rank == CARD_RANK_A:
                    rank = a4_ref.get_actual_card_rank(originalFrame.crop(PublicCardRankArray[i]))
                
                if rank != CARD_RANK_UNKNOWN:
                    info["publicCardRank"][i] = rank
                else:
                    info["publicCardSuit"][i] = infoBuffer["publicCardSuit"][i]

        
        # Check Queue
        if not ocrResultQueue.empty():
            print("Fatal Error! Unknown remaining result!")
            break
        
        # Save Buffer
        infoBuffer = info
        
        # Add to infoQueue
        try:
            infoQueue.put(deepcopy(info), block=False)
        except:
            print("Status control too slow! Dropping info...")
        
            
            
    print("Frame Filter Terminated!")    
        
    return True

def frame_source_process(frameQueue: Queue, videoSouce: str = "/dev/video0", realTime: bool = True):
    cap = cv2.VideoCapture(videoSouce)
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
    frameQueue.put(None)
    print("Frame Reader terminated!")

def find_next_player(currentPlayerIndex: int, totalPlayer: int) -> int:
    return (currentPlayerIndex + 1) % totalPlayer

def find_last_player(currentPlayerIndex: int, totalPlayer: int) -> int:
    return (currentPlayerIndex + totalPlayer - 1) % totalPlayer

def clean_game() -> bool:
    global playerList
    global playerActionList
    global playerBet
    global playerExpectedBet
    global gameInfo
    global bottomBet
    global currentPlayerIndex
    global FrameBottomBetFilter
    global playerNoActionList
    global currentGameRound
    playerList = []
    playerActionList = []
    playerNoActionList = []
    playerBet = []
    gameInfo = {"smallBlind": -1, "largeBlind": -1, "smallBlindIndex": -1, "largeBlindIndex": -1, "playerBottomBet": -1}
    bottomBet = -1
    currentPlayerIndex = -1
    playerExpectedBet = -1
    currentGameRound = -1
    FrameBottomBetFilter.reset_support_line()

    
def process_frame(infoDict: dict, recordFile: texas_record.TexasRecord, remoteQueue: Queue, remoteLock: Lock, realTime: bool = True) -> bool:
    global gameStatus
    global playerList
    global playerActionList
    global playerNoActionList
    global playerBet
    global playerExpectedBet
    global gameInfo
    global bottomBet
    global currentPlayerIndex
    global totalRoundCount
    global FrameBottomBetFilter
    global currentGameRound
    gameBeginActivated = infoDict["gameBeginActivated"]
    bottomBetActivated = infoDict["bottomBetActivated"]
    playerStatus = infoDict["playerStatus"]
    currentplayerBet = infoDict["playerBet"]
    currentBottomBet = infoDict["currentBottomBet"]
    currentGameInfo = infoDict["gameInfo"]
    originalPlayerIndex = -1
    frameBottomBetFilterUpdated = False
    while True:
        if gameStatus == STATUS_NULL:
            # print("[%s] %d %d %d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), gameBeginActivated, bottomBetActivated, currentBottomBet))
            if gameBeginActivated and not bottomBetActivated:
                gameStatus = STATUS_WAIT_FOR_BEGIN
                print("<<<<<<<<< %d >>>>>>>>>" %(totalRoundCount + 1))
                print("[%s] Waiting for game to begin..." %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                totalRoundCount += 1
                continue
            break
        elif gameStatus == STATUS_WAIT_FOR_BEGIN:
            
            # Normal Trace
            if (not gameBeginActivated) and bottomBetActivated and currentBottomBet != -1:
                # Bottom Bet Filter
                bottomBet = FrameBottomBetFilter.update_support_line(currentBottomBet)
                frameBottomBetFilterUpdated = True
                # Find First Player
                for i in range(9):
                    if playerStatus[i] == USER_THINKING:
                        originalPlayerIndex = i
                        print("Current Player Confirmed: %d" %(originalPlayerIndex))
                
                if valid_game_info(currentGameInfo) and (not valid_game_info(gameInfo)):
                    gameInfo["largeBlind"] = currentGameInfo["largeBlind"]
                    gameInfo["smallBlind"] = currentGameInfo["smallBlind"]
                    gameInfo["playerBottomBet"] = currentGameInfo["playerBottomBet"]
                    print("Basic Game Info Confirmed!  ", end="")
                    print(currentGameInfo)
                
                if originalPlayerIndex != -1 and valid_game_info(currentGameInfo) and bottomBet > 0:
                    
                    for i in range(9):
                        if playerStatus[8-i] != USER_EMPTY and playerStatus[8-i] != USER_FOLD:
                            playerList.append(8-i)
                            playerBet.append(0)
                    
                    currentPlayerIndex = playerList.index(originalPlayerIndex)
                    
                    # Confirm Pre-Bet Player
                    totalBet = 0
                    for i in range(len(playerList)):
                        if playerStatus[playerList[i]] != USER_EMPTY and playerStatus[playerList[i]] != USER_FOLD:
                            if currentplayerBet[playerList[i]]:
                                playerBet[i] = gameInfo["largeBlind"]
                                totalBet += gameInfo["largeBlind"]
                            totalBet += gameInfo["playerBottomBet"]
                    
                    # Construct Player Action List
                    for i in range(currentPlayerIndex, currentPlayerIndex + len(playerList)):
                        index = i % len(playerList)
                        playerActionList.append(index)

                    if totalBet != bottomBet and totalBet - bottomBet != gameInfo["smallBlind"]:
                        print("[%s] Warning! Bottom Bet Mismatch!" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))

                    print(
                        "[%s] Game Started!\n[\n\tPlayer Count: %d\n\tSmall Blind: %d\n\tLarge Blind: %d\n\tPlayer Bottom Bet: %d\n\tTotal Bottom Bet: %d\n\tPlayer Bet: "
                        %(
                            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            len(playerList),
                            gameInfo["smallBlind"],
                            gameInfo["largeBlind"],
                            gameInfo["playerBottomBet"],
                            bottomBet
                        ), end=""
                    )
                    print(playerBet)
                    print("\tPlayer List: ", end="")
                    print(playerList)
                    print("\tPlayer Action List: ", end="")
                    print(playerActionList)
                    print("]")
                    gameStatus = STATUS_PLAYING
                    FrameBottomBetFilter.access_support_point()
                    playerExpectedBet = gameInfo["largeBlind"]
                    currentGameRound = 1
                    # Create New Record
                    recordFile.new_round(len(playerList))
                    recordFile.update_game_info(gameInfo)
                    print("[%s] Begin Round %d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), currentGameRound))
                    continue
            break
        
        elif gameStatus == STATUS_PLAYING:

            # Update filter
            if bottomBetActivated and not frameBottomBetFilterUpdated:
                FrameBottomBetFilter.update_support_line(currentBottomBet)
                frameBottomBetFilterUpdated = True

            # Force Reset
            if gameBeginActivated and not bottomBetActivated:
                # Update Player Card
                for i in range(len(playerList)):
                    originalPlayerIndex = playerList[i]
                    for j in range(2):
                        recordFile.update_player_card(i, j, infoDict["playerCardRank"][originalPlayerIndex][j], infoDict["playerCardSuit"][originalPlayerIndex][j])
                # Update Public Card
                for i in range(5):
                    recordFile.update_public_card(i, infoDict["publicCardRank"][i], infoDict["publicCardSuit"][i])
                print("<<<<<<<<<< [ERROR] >>>>>>>>>>")
                print("[%s] Force Reset!" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                print("<<<<<<<<<< [ERROR] >>>>>>>>>>")
                print("[%s] Syncing Record Data" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                recordFile.end_round(True)
                print("[%s] Waiting for Next Game..." %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                gameStatus = STATUS_NULL
                clean_game()
                continue
                
            # End Round
            if (len(playerNoActionList) == len(playerList)) or (len(playerNoActionList) == len(playerList) - 1 and len(playerActionList) == 0) or (len(playerActionList) == 0 and currentGameRound == 4):
                print("[%s] All Rounds Ended!" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                print("[%s] Waiting for Game to End..." %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                gameStatus = STATUS_END
                continue
            
            # Waiting for Second Round
            if len(playerActionList) == 0 and currentGameRound != 4:
                currentPlayerIndex = -1
                # Find Next Round's First Player
                for i in range(len(playerList)):
                    if playerStatus[playerList[i]] == USER_THINKING:
                        currentPlayerIndex = i
                        print("Next Round Player Confirmed: %d" %(i))
                # Begin Next round
                if currentPlayerIndex != -1:
                    currentGameRound += 1
                    print("[%s] Begin Round %d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), currentGameRound))
                    # Construct Player Action List
                    for i in range(currentPlayerIndex, currentPlayerIndex + len(playerList)):
                        index = i % len(playerList)
                        playerActionList.append(index)
                    # New Record Line
                    print(playerActionList)
                    recordFile.new_record_line()
                    recordFile.new_record_line()
                    continue
                break
            
            # if playerActionList[0] == 1 and currentGameRound != 1:
            #     print("%d %d %d(%d) %d" %(gameBeginActivated, bottomBetActivated, currentBottomBet, bottomBet, playerStatus[playerList[playerActionList[0]]]))

            # Operation Track
            if (not gameBeginActivated) and bottomBetActivated and currentBottomBet != -1:
                status = playerStatus[playerList[playerActionList[0]]]
                currentTotalBet = 0
                for i in range(len(playerList)):
                    currentTotalBet += playerBet[i] + gameInfo["playerBottomBet"]
                effectBottomBet = min(bottomBet, currentTotalBet)
                if status == USER_THINKING:
                    if currentPlayerIndex != playerActionList[0]:
                        currentPlayerIndex = playerActionList[0]
                        print("[%s] Player %d(Thinking)" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0]))
                    break
                elif status == USER_FOLD or status == USER_EMPTY:
                    try: 
                        playerNoActionList.index(playerActionList[0])
                    except:
                        playerNoActionList.append(playerActionList[0])
                        # Update Current Player Index
                        currentPlayerIndex = playerActionList[0]
                        if not recordFile.update_player_operation(playerActionList[0], "F"):
                            return False
                    # New Record Line
                    if len(playerActionList) > 1 and playerActionList[0] > playerActionList[1]:
                        recordFile.new_record_line()
                    print("[%s] Player %d(FOLD) ==> " %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0]), end="")
                    # Update Player Action List
                    playerActionList.pop(0)
                    print(playerActionList)
                    continue
                elif status == USER_ALL_IN:
                    try:
                        playerNoActionList.index(playerActionList[0])
                    except:
                        if FrameBottomBetFilter.get_support_point() - effectBottomBet <= 5 * gameInfo["largeBlind"] and FrameBottomBetFilter.is_support_point_accessed():
                            break

                        playerNoActionList.append(playerActionList[0])

                        # Update Bet
                        FrameBottomBetFilter.access_support_point()
                        playerBet[playerActionList[0]] += FrameBottomBetFilter.get_support_point() - effectBottomBet
                        bottomBet = FrameBottomBetFilter.get_support_point()
                        
                        if playerBet[playerActionList[0]] - gameInfo["largeBlind"] >= playerExpectedBet:
                            # Update Player Action List
                            lastPlayer = playerActionList[-1]
                            playerExpectedBet = playerBet[playerActionList[0]]
                            for i in range(len(playerList) - len(playerActionList)):
                                playerActionList.append((lastPlayer + i + 1) % len(playerList))

                        # Update Current Player Index
                        currentPlayerIndex = playerActionList[0]
                        # Record
                        playerBetEqualTimes =  int(float(playerBet[playerActionList[0]]) / float(gameInfo["largeBlind"]) + 0.5)
                        if not recordFile.update_player_operation(playerActionList[0], "A%d" %(playerBetEqualTimes)):
                            return False
                        
                    # New Record Line
                    if len(playerActionList) > 1 and playerActionList[0] > playerActionList[1]:
                        recordFile.new_record_line()
                    print("[%s] Player %d(ALL-IN) ==> " %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0]), end="")
                    # Update Player Action List
                    playerActionList.pop(0)
                    print(playerActionList)
                    continue
                elif (status == USER_ADD_BET) or (status == USER_C_BET) :
                    if playerExpectedBet - playerBet[playerActionList[0]] > FrameBottomBetFilter.get_support_point() - effectBottomBet + gameInfo["largeBlind"] or (FrameBottomBetFilter.is_support_point_accessed() and FrameBottomBetFilter.get_support_point() != currentBottomBet):
                        break

                    print("Player %d(%s) ==> %d, %d(%d)" %(playerActionList[0], UserStatusStringArray[status], FrameBottomBetFilter.get_support_point(), bottomBet, effectBottomBet))
                    
                    if (not FrameBottomBetFilter.is_support_point_accessed()) and FrameBottomBetFilter.get_support_point() - effectBottomBet <= gameInfo["largeBlind"]:
                        # Record
                        betTimes = int(playerExpectedBet / gameInfo["largeBlind"])
                        print("[%s] Player %d C%d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0], betTimes))
                        if not recordFile.update_player_operation(playerActionList[0], "C%d" %(betTimes)):
                            return False
                        playerBet[playerActionList[0]] = playerExpectedBet
                        bottomBet = FrameBottomBetFilter.get_support_point()
                        FrameBottomBetFilter.access_support_point()
                    else:
                        # C or B
                        playerBet[playerActionList[0]] += FrameBottomBetFilter.get_support_point() - effectBottomBet
                        bottomBet = FrameBottomBetFilter.get_support_point()
                        
                        playerBetEqualTimes = int(float(playerBet[playerActionList[0]]) / float(gameInfo["largeBlind"]) + 0.5)
                        playerExpectedBetEqualTimes = int(float(playerExpectedBet) / float(gameInfo["largeBlind"]) + 0.5)

                        if ((((playerBet[playerActionList[0]] - playerExpectedBet <= gameInfo["largeBlind"]) or (playerExpectedBetEqualTimes == playerBetEqualTimes)) and (not FrameBottomBetFilter.is_support_point_accessed())) or (status == USER_C_BET)) and (status != USER_ADD_BET):
                            # C
                            playerBet[playerActionList[0]] = playerExpectedBet
                            # Record
                            betTimes = playerExpectedBetEqualTimes
                            print("[%s] Player %d C%d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0], betTimes))
                            if not recordFile.update_player_operation(playerActionList[0], "C%d" %(betTimes)):
                                return False
                            FrameBottomBetFilter.access_support_point()
                        elif status == USER_ADD_BET and (playerBetEqualTimes - playerExpectedBetEqualTimes >= 6 or not FrameBottomBetFilter.is_support_point_accessed()):
                            # B
                            playerExpectedBet = playerBet[playerActionList[0]]
                            # Update Player Action List
                            lastPlayer = playerActionList[-1]
                            for i in range(len(playerList) - len(playerActionList)):
                                playerActionList.append((lastPlayer + i + 1) % len(playerList))
                            # Record
                            betTimes = playerBetEqualTimes
                            print("[%s] Player %d B%d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0], betTimes))
                            if not recordFile.update_player_operation(playerActionList[0], "B%d" %(betTimes)):
                                return False
                            FrameBottomBetFilter.access_support_point()
                        else:
                            break
                    print(playerBet)
                    # Update Current Player Index
                    currentPlayerIndex = playerActionList[0]
                    # New Record Line
                    if len(playerActionList) > 1 and playerActionList[0] > playerActionList[1]:
                        recordFile.new_record_line()
                    # Update Player Action List
                    playerActionList.pop(0)
                    print(playerActionList)
                    continue
                else:
                    # print("[%s] Warning! Waiting for Player %d to Think!" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), playerActionList[0]))
                    break
            break
        elif gameStatus == STATUS_END:
            if gameBeginActivated and not bottomBetActivated:
                print("[%s] Syncing Record Data" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                recordFile.end_round()
                print("[%s] Waiting for Next Game..." %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                gameStatus = STATUS_NULL
                clean_game()
                continue
            # Update Player Card
            for i in range(len(playerList)):
                originalPlayerIndex = playerList[i]
                for j in range(2):
                    recordFile.update_player_card(i, j, infoDict["playerCardRank"][originalPlayerIndex][j], infoDict["playerCardSuit"][originalPlayerIndex][j])
            # Update Public Card
            for i in range(5):
                recordFile.update_public_card(i, infoDict["publicCardRank"][i], infoDict["publicCardSuit"][i])
            break
        
        return False
    return True

def status_control_process(infoQueue: Queue, remoteQueue: Queue, remoteLock: Lock, realTime: bool = True):
    print("Status Control process started!")
    texasRecord = texas_record.TexasRecord()
    while True:
        infoDict = infoQueue.get()
        if infoDict is None:
            break
        if not process_frame(infoDict, texasRecord, remoteQueue, remoteLock, realTime):
            break
    print("Status Control process terminated!")

frameQueue = Queue(maxsize=60)
infoQueue = Queue(maxsize=60)
remoteQueue = Queue(maxsize=15)
chineseOcrQueue = Queue(maxsize=20)
englishOcrQueue = Queue(maxsize=20)
ocrResultQueue = Queue(maxsize=30)

remoteLock = Lock()

if __name__ == "__main__":

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

    # remoteControlProcess = Process(target=remote_control_process, args=(remoteQueue, remoteLock))
    # remoteControlProcess.start()

    frameSourceProcess = Process(target=frame_source_process, args=(frameQueue, videoSouce, realTime))
    frameSourceProcess.start()


    while True:
        time.sleep(1)