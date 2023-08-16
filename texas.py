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

tessPSM = PSM.SINGLE_LINE
tessSingleCharacterPSM = PSM.SINGLE_CHAR
tessL = "chi_sim"

BottomBetArea = (1084, 300, 1440, 340)
GameBeginArea = (1106, 484, 1430, 532)

PlayerStatusAreaArray = (
    (768, 24, 918, 68),
    (424, 154, 574, 198),
    (368, 484, 518, 528),
    (658, 678, 808, 722),
    (1192, 678, 1342, 722),
    (1720, 678, 1870, 722),
    (2008, 484, 2158, 528),
    (1948, 154, 2098, 198),
    (1608, 24, 1758, 68)
)

CardCharacterAreaArray = (
    (878, 448, 930, 508),
    (1032, 448, 1084, 508),
    (1188, 448, 1240, 508),
    (1342, 448, 1394, 508),
    (1498, 448, 1550, 508)
)

CardSuitAreaArray = (
    (883, 507, 923, 551),
    (1038, 507, 1078, 551),
    (1192, 507, 1232, 551),
    (1347, 507, 1387, 551),
    (1501, 507, 1541, 551)
)




chineseApi = PyTessBaseAPI(psm=tessPSM, lang = tessL)
englishApi = PyTessBaseAPI(psm=tessPSM, lang = "eng")
englishCharacterApi = PyTessBaseAPI(psm=tessSingleCharacterPSM, lang = "eng")

def bottom_bet_test(imgPath: str) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    bottomBetImg = originalImg.crop(BottomBetArea)
    bottomBetImg.save("./tmp/bottomBet.png")
    binarizedBottomImg = utils.binarizePillow(bottomBetImg, 90)
    binarizedBottomImg.save("./tmp/binarizedBottomBet.png")
    chineseApi.SetImage(binarizedBottomImg)
    chineseTxt = utils.cleanStr(chineseApi.GetUTF8Text())
    print(chineseTxt)
    print(utils.truncateUntilNumber(chineseTxt))
    return True
    # bottomBetImg.show()

def card_test(imgPath: str, cardRank: int = 0) -> bool:
    cvImg = cv2.imread(imgPath)
    originalImg = Image.fromarray(cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB))
    
    cardCharacterImg = originalImg.crop(CardCharacterAreaArray[cardRank])
    binarizedCardCharacterImg = utils.revertBinarizePillow(cardCharacterImg, 100)
    cardSuitImg = originalImg.crop(CardSuitAreaArray[cardRank])
    
    cardCharacterImg.save("./tmp/cardCharacter_%d.png" %(cardRank))
    binarizedCardCharacterImg.save("./tmp/binarizedCardCharacter_%d.png" %(cardRank))
    cardSuitImg.save("./tmp/cardSuit_%d.png" %(cardRank))
    
    englishCharacterApi.SetImage(binarizedCardCharacterImg)
    englishChar = utils.cleanStr(englishCharacterApi.GetUTF8Text())
    
    
    suit = texas_suit.findSuit(cardSuitImg)
    suitSymbol = texas_suit.SuitSymbolArray[suit]
    
    if suit != texas_suit.SUIT_UNKNOWN:
        print("%s%s" %(suitSymbol, englishChar))
    return True

imgPath = "./texas/first_three_cards.png"
bottom_bet_test(imgPath)
# card_test("./texas/first_three_cards.png", 2)
for i in range(5):
    card_test(imgPath, i)

chineseApi.End()
englishApi.End()
englishCharacterApi.End()