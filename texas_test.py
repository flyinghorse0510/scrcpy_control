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

tessPSM = PSM.SINGLE_LINE
tessSingleCharacterPSM = PSM.SINGLE_CHAR
tessL = "chi_sim"
pixelDelta = -5


USER_NULL = -1
USER_THINKING = 0
USER_FOLD = 1
USER_ALL_IN = 2
USER_EMPTY = 3

BET_CONFIRM_COUNT = 6

BottomBetArea = (1084, 300, 1440, 340)
GameBeginArea = (1106, 484, 1430, 532)
GameInfoArea = (894, 636, 1606, 672)

frameQueue = Queue(maxsize=15)
infoQueue = Queue(maxsize=10)
remoteQueue = Queue(maxsize=100)

PublicCardCalibrationArray = (
    (875 + pixelDelta, 452),
    (1029 + pixelDelta, 452),
    (1184 + pixelDelta, 452),
    (1339 + pixelDelta, 452),
    (1493 + pixelDelta, 452)
)

PlayerCalibrationArray = (
    (749 + pixelDelta, 253),
    (408 + pixelDelta, 384),
    (350 + pixelDelta, 713),
    (640 + pixelDelta, 906),
    (1170 + pixelDelta, 906),
    (1701 + pixelDelta, 906),
    (1989 + pixelDelta, 713),
    (1930 + pixelDelta, 384),
    (1591 + pixelDelta, 253)
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

chineseApi = PyTessBaseAPI(psm=tessPSM, lang = tessL)
englishApi = PyTessBaseAPI(psm=tessPSM, lang = "eng")
englishCharacterApi = PyTessBaseAPI(psm=tessSingleCharacterPSM, lang = "eng")

def bottom_bet_test(imgPath: str) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    bottomBetImg = originalImg.crop(BottomBetArea)
    binarizedBottomImg = utils.binarize_pillow(bottomBetImg, 90)
    
    bottomBetImg.save("./tmp/bottomBet.png")
    binarizedBottomImg.save("./tmp/binarizedBottomBet.png")
    
    areaActivated = texas_activated.bottom_bet_activated(binarizedBottomImg)
    if areaActivated:
        chineseApi.SetImage(binarizedBottomImg)
        chineseTxt = utils.cleanStr(chineseApi.GetUTF8Text())
        print(chineseTxt)
        print(utils.filter_until_number(chineseTxt))
    else:
        print("No Bottom Bet Found!")
    
    return True

def game_begin_test(imgPath: str) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    gameBeginImg = originalImg.crop(GameBeginArea)
    gameBeginImg.save("./tmp/gameBegin.png")
    
    binarizedGameBeginImg = utils.binarize_pillow(gameBeginImg, 130)
    binarizedGameBeginImg.save("./tmp/binarizedGameBegin.png")
    
    areaActivated = texas_activated.game_begin_activated(gameBeginImg, True)
    if areaActivated:
        chineseApi.SetImage(binarizedGameBeginImg)
        chineseTxt = utils.clean_str(chineseApi.GetUTF8Text())
        print(chineseTxt)
    else:
        print("No Game Begin Found!")
    
    return True

def public_card_test(imgPath: str, cardRank: int = 0) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    publicCardRankImg = originalImg.crop(PublicCardRankArray[cardRank])
    publicCardSuitImg = originalImg.crop(PublicCardSuitArray[cardRank])
    
    binarizedPublicCardRankImg = utils.revert_binarize_pillow(publicCardRankImg, 100)
    
    publicCardRankImg.save("./tmp/public_card_rank_%d.png" %(cardRank))
    binarizedPublicCardRankImg.save("./tmp/binarized_public_card_rank_%d.png" %(cardRank))
    publicCardSuitImg.save("./tmp/public_card_suit_%d.png" %(cardRank))
    
    suit = texas_suit.find_suit(publicCardSuitImg)
    if suit != texas_suit.SUIT_UNKNOWN:
        englishApi.SetImage(binarizedPublicCardRankImg)
        publicCardRank = utils.card_rank_replace(utils.clean_str(englishApi.GetUTF8Text()))
        print("%s%s" %(texas_suit.SuitSymbolArray[suit], publicCardRank))
    else:
        print("No Cards Found for %d Position!" %(cardRank))
        
    return True

def player_card_test(imgPath: str, playerSeat: int = 0):
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    playerACardRankImg = originalImg.crop(PlayerCardRankArray[playerSeat][0])
    playerBCardRankImg = originalImg.crop(PlayerCardRankArray[playerSeat][1])
    playerACardSuitImg = originalImg.crop(PlayerCardSuitArray[playerSeat][0])
    playerBCardSuitImg = originalImg.crop(PlayerCardSuitArray[playerSeat][1])
    
    binarizedPlayerACardRankImg = utils.revert_binarize_pillow(playerACardRankImg, 100)
    binarizedPlayerBCardRankImg = utils.revert_binarize_pillow(playerBCardRankImg, 100)
    
    playerACardRankImg.save("./tmp/player_%d_card_rank_0.png" %(playerSeat))
    playerBCardRankImg.save("./tmp/player_%d_card_rank_1.png" %(playerSeat))
    playerACardSuitImg.save("./tmp/player_%d_card_suit_0.png" %(playerSeat))
    playerBCardSuitImg.save("./tmp/player_%d_card_suit_1.png" %(playerSeat))
    
    binarizedPlayerACardRankImg.save("./tmp/binarized_player_%d_card_rank_0.png" %(playerSeat))
    binarizedPlayerBCardRankImg.save("./tmp/binarized_player_%d_card_rank_1.png" %(playerSeat))
    
    ASuit = texas_suit.find_suit(playerACardSuitImg)
    BSuit = texas_suit.find_suit(playerBCardSuitImg)
    if ASuit != texas_suit.SUIT_UNKNOWN and BSuit != texas_suit.SUIT_UNKNOWN:
        englishApi.SetImage(binarizedPlayerACardRankImg)
        ACardRank = utils.card_rank_replace(utils.clean_str(englishApi.GetUTF8Text()))
        englishApi.SetImage(binarizedPlayerBCardRankImg)
        BCardRank = utils.card_rank_replace(utils.clean_str(englishApi.GetUTF8Text()))
        print("Player Seat %d: %s%s, %s%s" %(playerSeat, texas_suit.SuitSymbolArray[ASuit], ACardRank, texas_suit.SuitSymbolArray[BSuit], BCardRank))
    else:
        print("No Cards Found for Player Seat %d!" %(playerSeat))
    
    return True

def empty_seat_test(imgPath: str, playerSeat: int = 0) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    playerSeatImg = originalImg.crop(EmptySeatArray[i])
    playerSeatImg.save("./tmp/empty_seat_%d.png" %(playerSeat))
    
    areaActivated = texas_activated.empty_seat_activated(playerSeatImg, True, playerSeat)
    if areaActivated:
        print("Player Seat %d is Empty" %(playerSeat))
    else:
        print("Person Found on Seat %d" %(playerSeat))
    
    return True

def game_info_test(imgPath: str) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    gameInfoImg = originalImg.crop(GameInfoArea)
    binarizedGameInfoImg = utils.binarize_pillow(gameInfoImg, 90)
    
    gameInfoImg.save("./tmp/gameInfo.png")
    binarizedGameInfoImg.save("./tmp/binarized_game_info.png")
    
    chineseApi.SetImage(binarizedGameInfoImg)
    chineseTxt = utils.clean_str(chineseApi.GetUTF8Text())
    print(chineseTxt)
    
    return True

def player_status_test(imgPath: str, playerSeat: int = 0) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    globalBinarizedImg = utils.binarize_pillow(originalImg, 105)
    
    playerStatusImg = originalImg.crop(PlayerStatusArray[i])
    playerStatusImg.save("./tmp/player_status_%d.png" %(playerSeat))

    binarizedPlayerStatusImg = globalBinarizedImg.crop(PlayerStatusArray[i])
    
    userThinkingActivated = texas_activated.user_thinking_activated(playerStatusImg, True, playerSeat)
    userFoldActivated = texas_activated.user_fold_activated(binarizedPlayerStatusImg, True, playerSeat)
    userAllInActivated = texas_activated.user_all_in_activated(playerStatusImg, True, playerSeat)
    if userThinkingActivated:
        print("User %d is Thinking" %(playerSeat))
    elif userFoldActivated:
        print("User %d has Folded" %(playerSeat))
    elif userAllInActivated:
        print("User %d has All-In!" %(playerSeat))
    
    return True

def player_bet_test(imgPath: str, playerSeat: int = 0) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    playerBetImg = originalImg.crop(PlayerBetArray[playerSeat])
    playerBetImg.save("./tmp/player_bet_%d.png" %(playerSeat))
    
    playerBetActivated = texas_activated.player_bet_activated(playerBetImg, True, playerSeat)
    if playerBetActivated:
        print("Player %d has betted" %(playerSeat))
    return True


if __name__ == "__main__":
    imgPath = "./texas/remote_fake_fold.png"
    # game_begin_test(imgPath)
    # bottom_bet_test(imgPath)
    # for i in range(5):
    #     public_card_test(imgPath, i)

    for i in range(9):
        # player_card_test(imgPath, i)
        empty_seat_test(imgPath, i)
        # player_status_test(imgPath, i)
        # player_bet_test(imgPath, i)
    # print(EmptySeatArray)
    # game_info_test(imgPath)
        
    # print(PlayerStatusArray)    


chineseApi.End()
englishApi.End()
englishCharacterApi.End()