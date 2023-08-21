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

tessPSM = PSM.SINGLE_LINE
tessSingleCharacterPSM = PSM.SINGLE_CHAR
tessL = "chi_sim"


PLAYER_NULL = -1
PLAYER_THINKING = 0
PLAYER_FOLD = 1
PLAYER_ALL_IN = 2
PLAYER_EMPTY = 3

BET_CONFIRM_COUNT = 3
RANK_CONFIRM_COUNT = 4

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
STATUS_NULL = -1

NUM_ENGLISH_OCR_PROC = 1
NUM_CHINESE_OCR_PROC = 1

BottomBetArea = (1084, 300, 1440, 340)
GameBeginArea = (1106, 484, 1430, 532)
GameInfoArea = (894, 636, 1606, 672)

frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=10)
remoteQueue = Queue(maxsize=100)

gameStatus = STATUS_NULL
playerList = []
playerBet = []
gameInfo = {"smallBlind": -1, "largeBlind": -1, "smallBlindIndex": -1, "largeBlindIndex": -1, "playerBottomBet": -1}
bottomBet = -1
currentPlayerIndex = -1
totalRoundCount = 0

PublicCardCalibrationArray = (
    (875, 452),
    (1029, 452),
    (1184, 452),
    (1339, 452),
    (1493, 452)
)

PlayerCalibrationArray = (
    (749, 253),
    (408, 384),
    (350, 713),
    (640, 906),
    (1170, 906),
    (1701, 906),
    (1989, 713),
    (1930, 384),
    (1591, 253)
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
    return {
        "bottomBetActivated": False, 
        "gameBeginActivated": False, 
        "playerStatus": [
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL,
            PLAYER_NULL
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
    }
    
    
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
    
    if smallBlind * 2 != largeBlind:
        smallBlind = -1
        largeBlind = -1
    
    return {"smallBlind": smallBlind, "largeBlind": largeBlind, "playerBottomBet": playerBottomBet}

def valid_game_info(gameInfo: dict) -> bool:
    if gameInfo["smallBlind"] != -1 and gameInfo["largeBlind"] != -1 and gameInfo["playerBottomBet"] != -1:
        return True
    return False
 
def submit_card_rank_ocr(cardRankImg: Image.Image, englishOcrQueue: Queue, uuid: str):
    binarizedCardRankImg = utils.revert_binarize_pillow(cardRankImg, 100)
    submit_ocr([uuid, binarizedCardRankImg], englishOcrQueue)
    
def get_bottom_bet(bottomBetTxt: str) -> int:
    filteredBottomBetTxt = utils.filter_until_number(bottomBetTxt)
    return utils.txt2int(filteredBottomBetTxt)

def get_card_rank(cardRankTxt: str) -> int:
    filteredCardRankTxt = utils.card_rank_replace(cardRankTxt)
    if filteredCardRankTxt <= "9" and filteredCardRankTxt >= "0":
        try:
            rank = int(filteredCardRankTxt) - 1
            return rank
        except:
            print("UNKNOWN CARD RANK ==> %s" %(filteredCardRankTxt))
            return CARD_RANK_UNKNOWN
    if filteredCardRankTxt == "A":
        return CARD_RANK_A
    elif filteredCardRankTxt == "J":
        return CARD_RANK_J
    elif filteredCardRankTxt == "Q":
        return CARD_RANK_Q
    elif filteredCardRankTxt == "K":
        return CARD_RANK_K
    
    print("UNKNOWN CARD RANK ==> %s" %(filteredCardRankTxt))
    return CARD_RANK_UNKNOWN

def get_player_status(playerStatusImg: Image.Image) -> int:
    
    if texas_activated.empty_seat_activated(playerStatusImg):
        return PLAYER_EMPTY

def frame_filter_process(frameQueue: Queue, infoQueue: Queue, chineseOcrQueue: Queue, englishOcrQueue: Queue, ocrResultQueue: Queue):
    print("Frame Filter started!")
    infoBuffer = get_info_template()
    lastFrameTime = time.time()
    # bottomBetFilter = sline.SupportLine(BET_CONFIRM_COUNT)
    publicRankFilterArray = [
        sline.RankLine(RANK_CONFIRM_COUNT),
        sline.RankLine(RANK_CONFIRM_COUNT),
        sline.RankLine(RANK_CONFIRM_COUNT),
        sline.RankLine(RANK_CONFIRM_COUNT),
        sline.RankLine(RANK_CONFIRM_COUNT)
    ]
    playerRankFilterArray = [
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)],
        [sline.RankLine(RANK_CONFIRM_COUNT), sline.RankLine(RANK_CONFIRM_COUNT)]
    ]
    
    while True:
        # try:
        #     frame = frameQueue.get(block=False)
        # except queue.Empty:
        #     deltaTime = time.time() - lastFrameTime
        #     if deltaTime >= 0.036:
        #         try:
        #             # Update player card with last rank
        #             for i in range(9):
        #                 for j in range(2):
        #                     infoBuffer["playerCardRank"][i][j] = playerRankFilterArray[i][j].update_with_last_rank()
        #             # Update public card with last rank
        #             for i in range(5):
        #                 infoBuffer["publicCardRank"][i] = publicRankFilterArray[i].update_with_last_rank()
                        
        #             infoQueue.put(infoBuffer.copy(), block=False)
        #         except queue.Full:
        #             print("Status control too slow! Dropping info...")
        #         lastFrameTime = time.time()
        #     time.sleep(0.001)
        #     continue
        frame = frameQueue.get(block = True)
        lastFrameTime = time.time()
        if frame is None:
            infoQueue.put(None)
            chineseOcrQueue.put(None)
            englishOcrQueue.put(None)
            break
        
        info = infoBuffer.copy()
        originalFrame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
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
                info["gameInfo"] = infoBuffer["gameInfo"].copy()
            else:
                # Game Info
                submit_game_info_ocr(originalFrame.crop(GameInfoArea), chineseOcrQueue)
                ocrResultCount += 1
            
            # reset player card rank
            for i in range(9):
                for j in range(2):
                    infoBuffer["playerCardRank"][i][j] = playerRankFilterArray[i][j].reset_rank()
            # reset public card rank
            for i in range(5):
                infoBuffer["publicCardRank"][i] = publicRankFilterArray[i].reset_rank()
            
            for i in range(ocrResultCount):
                result = ocrResultQueue.get()
                ocrResult[result[0]] = result[1]
            
            if ocrResultCount > 0:
                info["gameInfo"] = get_game_info_ocr(ocrResult["gameInfo"])
            
            infoBuffer = info
            try:
                infoQueue.put(info.copy(), block=False)
            except queue.Full:
                print("Status control too slow! Dropping info...")
            continue
        
        # Bottom Bet
        if bottomBetActivated:
            submit_bottom_bet_ocr(bottomBetAreaImg, chineseOcrQueue)
            ocrResultCount += 1
            
        # Player
        for i in range(9):
            if info["playerStatus"][i] == PLAYER_EMPTY or info["playerStatus"][i] == PLAYER_FOLD:
                continue
            # Status
            if info["playerStatus"][i] == PLAYER_NULL or info["playerStatus"][i] == PLAYER_THINKING:
                playerStatus = get_player_status(originalFrame.crop(PlayerStatusArray[i]))
                info["playerStatus"][i] = playerStatus
                if playerStatus == PLAYER_EMPTY or playerStatus == PLAYER_FOLD:
                    continue
            
            # Bet
            if not info["playerBet"] and info["playerStatus"][i] != PLAYER_EMPTY and info["playerStatus"][i] != PLAYER_FOLD:
                info["playerBet"] = texas_activated.player_bet_activated(originalFrame.crop(PlayerBetArray[i]))
                            
            # Player Card and Suit
            for j in range(2):
                if info["playerCardSuit"][i][j] == texas_suit.SUIT_UNKNOWN:
                    info["playerCardSuit"][i][j] = texas_suit.find_suit(originalFrame.crop(PlayerCardSuitArray[i][j]))
                    
                if info["playerCardSuit"][i][j] != texas_suit.SUIT_UNKNOWN and info["playerCardRank"][i][j] == CARD_RANK_UNKNOWN:
                    submit_card_rank_ocr(originalFrame.crop(PlayerCardRankArray[i][j]), englishOcrQueue, "player_%d%d" %(i, j))
                    ocrResultCount += 1
            
        # Public
        for i in range(5):
            if info["publicCardSuit"][i] == texas_suit.SUIT_UNKNOWN:
                info["publicCardSuit"][i] = texas_suit.find_suit(originalFrame.crop(PublicCardSuitArray[i]))
            
            if info["publicCardSuit"][i] != texas_suit.SUIT_UNKNOWN and info["publicCardRank"][i] == CARD_RANK_UNKNOWN:
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
                info["playerCardRank"][i][j] = playerRankFilterArray[i][j].update_rank(get_card_rank(ocrResult[key]))
            elif key[:6] == "public":
                i = int(key[7])
                info["publicCardRank"][i] = publicRankFilterArray[i].update_rank(get_card_rank(ocrResult[key]))
        
        # Check Queue
        if not ocrResultQueue.empty():
            print("Fatal Error! Unknown remaining result!")
            break
        
        # Save Buffer
        infoBuffer = info
        
        # Add to infoQueue
        try:
            infoQueue.put(info.copy(), block=False)
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
    print("Frame Reader terminated!")

def find_next_player(currentPlayerIndex: int, totalPlayer: int) -> int:
    return (currentPlayerIndex + 1) % totalPlayer

def find_last_player(currentPlayerIndex: int, totalPlayer: int) -> int:
    return (currentPlayerIndex + totalPlayer - 1) % totalPlayer

def clean_game() -> bool:
    global playerList
    global playerBet
    global gameInfo
    global bottomBet
    global currentPlayerIndex
    playerList = []
    playerBet = []
    gameInfo = {"smallBlind": -1, "largeBlind": -1, "smallBlindIndex": -1, "largeBlindIndex": -1, "playerBottomBet": -1}
    bottomBet = -1
    currentPlayerIndex = -1

    
def process_frame(infoDict: dict, recordFile: texas_record.TexasRecord, remoteQueue: Queue, remoteLock: Lock, realTime: bool = True) -> bool:
    global gameStatus
    global playerList
    global playerBet
    global gameInfo
    global bottomBet
    global currentPlayerIndex
    global totalRoundCount
    gameBeginActivated = infoDict["gameBeginActivated"]
    bottomBetActivated = infoDict["bottomBetActivated"]
    playerStatus = infoDict["playerStatus"]
    currentplayerBet = infoDict["playerBet"]
    currentBottomBet = infoDict["currentBottomBet"]
    currentGameInfo = infoDict["gameInfo"]
    while True:
        if gameStatus == STATUS_NULL:
            print("[%s] %d %d %d" %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), gameBeginActivated, bottomBetActivated, currentBottomBet))
            if gameBeginActivated and not bottomBetActivated:
                gameStatus = STATUS_WAIT_FOR_BEGIN
                print("<<<<<<<<< %d >>>>>>>>>" %(totalRoundCount + 1))
                print("[%s] Waiting for game to begin..." %(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                totalRoundCount += 1
                continue
            break
        elif gameStatus == STATUS_WAIT_FOR_BEGIN:
            if (not gameBeginActivated) and bottomBetActivated and currentBottomBet >= bottomBet and currentBottomBet != -1:
                bottomBet = currentBottomBet
                for i in range(9):
                    if len(playerList) == 0 and playerStatus[8-i] != PLAYER_EMPTY:
                        playerList.append(8-i)
                        playerBet.append(-1)
                    if playerStatus[8-i] == PLAYER_THINKING:
                        currentPlayerIndex = 8 - i
                
                if valid_game_info(currentGameInfo) and (not valid_game_info(gameInfo)):
                    gameInfo["largeBlind"] = currentGameInfo["largeBlind"]
                    gameInfo["smallBlind"] = currentGameInfo["smallBlind"]
                    gameInfo["playerBottomBet"] = currentGameInfo["playerBottomBet"]
                
                if currentPlayerIndex != -1 and valid_game_info(currentGameInfo):
                    gameInfo["largeBlindIndex"] = find_last_player(currentPlayerIndex, len(playerList))
                    gameInfo["smallBlindIndex"] = find_last_player(gameInfo["largeBlindIndex"], len(playerList))
                    
                    totalBet = 0
                    for i in range(9):
                        if playerStatus[i] != PLAYER_EMPTY and playerStatus[i] != PLAYER_FOLD:
                            if currentplayerBet[i]:
                                playerBet[i] = gameInfo["largeBlind"]
                                totalBet += gameInfo["largeBlind"]
                            totalBet += gameInfo["playerBottomBet"]
                    
                    while totalBet < bottomBet:
                        totalBet += gameInfo["playerBottomBet"]
                    
                    if totalBet != bottomBet:
                        if totalBet - bottomBet == gameInfo["smallBlind"]:
                            playerBet[gameInfo["smallBlindIndex"]] = gameInfo["smallBlind"]
                        else:
                            print("Fatal Bet Detection Error! Process Frame Terminated!")
                            return False
                    print(
                        "[%s] Game Started!\n[\n\tPlayer Count: %d\n\tSmall Blind: %d\n\tLarge Blind: %d\n\tBottom Bet: %d\n]\n"
                        %(
                            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            len(playerList),
                            gameInfo["smallBlind"],
                            gameInfo["largeBlind"],
                            gameInfo["playerBottomBet"]
                        )
                    )
                    gameStatus = STATUS_FIRST_ROUND
                    return True
            break
        # elif gameStatus == STATUS_FIRST_ROUND:
            
        # elif gameStatus == STATUS_SECOND_ROUND:
        # elif gameStatus == STATUS_THIRD_ROUND:
        # elif gameStatus == STATUS_FOURTH_ROUND:
        # elif gameStatus == STATUS_END:
    
    return True    

def status_control_process(infoQueue: Queue, remoteQueue: Queue, remoteLock: Lock, realTime: bool = True):
    print("Status Control process started!")
    texasRecord = texas_record.TexasRecord()
    while True:
        infoDict = infoQueue.get()
        if infoDict is None:
            break
        process_frame(infoDict, texasRecord, remoteQueue, remoteLock, realTime)
    print("Status Control process terminated!")

frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=15)
remoteQueue = Queue(maxsize=5)
chineseOcrQueue = Queue(maxsize=10)
englishOcrQueue = Queue(maxsize=10)
ocrResultQueue = Queue(maxsize=15)

remoteLock = Lock()

realTime = False
videoSouce = "./texas/texas.mp4"

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