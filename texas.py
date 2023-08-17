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

BottomBetArea = (1084, 300, 1440, 340)
GameBeginArea = (1106, 484, 1430, 532)

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

EmptySeatBlockOffset = (69, 33)
EmptySeatBlockSize = (49, -182)

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
    
    areaActivated = texas_activated.game_begin_activated(binarizedGameBeginImg)
    if areaActivated:
        chineseApi.SetImage(binarizedGameBeginImg)
        chineseTxt = utils.cleanStr(chineseApi.GetUTF8Text())
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
        publicCardRank = utils.card_rank_replace(utils.cleanStr(englishApi.GetUTF8Text()))
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
        ACardRank = utils.card_rank_replace(utils.cleanStr(englishApi.GetUTF8Text()))
        englishApi.SetImage(binarizedPlayerBCardRankImg)
        BCardRank = utils.card_rank_replace(utils.cleanStr(englishApi.GetUTF8Text()))
        print("Player Seat %d: %s%s, %s%s" %(playerSeat, texas_suit.SuitSymbolArray[ASuit], ACardRank, texas_suit.SuitSymbolArray[BSuit], BCardRank))
    else:
        print("No Cards Found for Player Seat %d!" %(playerSeat))
    
    return True


imgPath = "./texas/final_cards.png"
# game_begin_test(imgPath)
# bottom_bet_test(imgPath)
for i in range(5):
    public_card_test(imgPath, i)

for i in range(9):
    player_card_test(imgPath, i)

chineseApi.End()
englishApi.End()
englishCharacterApi.End()