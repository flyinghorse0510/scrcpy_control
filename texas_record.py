from PIL import Image, ImageOps
import cv2
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Lock
import queue
import remote_control
import random
import time
import time_converter
import sys
import support_line as sline
import utils
import texas_suit
from copy import deepcopy


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

CardRankIndexArray = (
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K"
)

class TexasRecord:
    def __init__(self, filePath: str = "./texas_record.csv"):
        self.recordFile = open(filePath, "w", encoding='utf-8-sig')
        self.playing = False
        self.table = []
        self.currentPlayerCount = 0
        self.lineIndex = 0
        self.roundError = False
        self.gameInfo = {"smallBlind": -1, "largeBlind": -1, "smallBlindIndex": -1, "largeBlindIndex": -1, "playerBottomBet": -1}
        
        
    def new_record_line(self) -> bool:
        if not self.playing:
            return False
        
        newLine = ["-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1"]
        newLine = newLine[:self.currentPlayerCount]
        self.table.append(newLine)
        self.lineIndex += 1
        return True
        
    def new_round(self, playerCount: int = 9) -> bool:
        if self.playing:
            return False
        self.currentPlayerCount = playerCount
        self.playing = True
        self.table = [
            [
                ["公共牌", ["?", "?"], ["?", "?"], ["?", "?"], ["?", "?"], ["?", "?"]]
            ]
        ]
        for i in range(playerCount):
            self.table[0].append(["玩家%d" %(i+1), ["?", "?"], ["?", "?"]])
        self.table[0].append(["时间", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())])
        self.new_record_line()
        return True
    
    def update_player_card(self, playerIndex: int, cardIndex: int, cardRank: int = CARD_RANK_UNKNOWN, cardSuit: int = texas_suit.SUIT_UNKNOWN) -> bool:
        if not self.playing:
            return False
        
        if cardSuit != texas_suit.SUIT_UNKNOWN:
            self.table[0][playerIndex + 1][cardIndex + 1][0] = texas_suit.SuitSymbolArray[cardSuit]
        if cardRank != CARD_RANK_UNKNOWN:
            self.table[0][playerIndex + 1][cardIndex + 1][1] = CardRankIndexArray[cardRank]
        return True
    
    def update_public_card(self, cardIndex: int, cardRank: int = CARD_RANK_UNKNOWN, cardSuit: int = texas_suit.SUIT_UNKNOWN) -> bool:
        if not self.playing:
            return False
        
        if cardSuit != texas_suit.SUIT_UNKNOWN:
            self.table[0][0][cardIndex + 1][0] = texas_suit.SuitSymbolArray[cardSuit]
        if cardRank != CARD_RANK_UNKNOWN:
            self.table[0][0][cardIndex + 1][1] = CardRankIndexArray[cardRank]
        return True
    
    def update_player_operation(self, playerIndex: int, operation: str) -> bool:
        if not self.playing:
            return False
        
        if self.lineIndex == 0:
            return False
        
        if self.table[self.lineIndex][playerIndex] != "-1":
            return False
        
        self.table[self.lineIndex][playerIndex] = operation
        
        return True
    
    def update_game_info(self, gameInfo: dict) -> bool:
        if not self.playing:
            return False
        
        self.gameInfo = deepcopy(gameInfo)
    
    def write_plain_table(self, plainTable: list) -> bool:
        if not self.playing:
            return False
        
        for line in plainTable:
            for i in range(len(line)):
                if i < len(line) - 1:
                    self.recordFile.write("%s," %(line[i]))
                else:
                    self.recordFile.write("%s\n" %(line[i]))
        
        self.recordFile.flush()
        
        return True
                
    
    def end_round(self, error = False) -> bool:
        if not self.playing:
            return False
        
        self.roundError = error

        plainTable = [
            [
                "" for _ in range(2 + self.currentPlayerCount)
            ] for _ in range(max(len(self.table), 30))
        ]
        # Record Title
        for i in range(2 + self.currentPlayerCount):
            plainTable[0][i] = self.table[0][i][0]
    
        # Time 
        plainTable[1][-1] = self.table[0][-1][1]
        
        # Player Card
        for i in range(self.currentPlayerCount):
            plainTable[0][i+1] += "(" + "%s%s:%s%s" %(self.table[0][i+1][1][0], self.table[0][i+1][1][1], self.table[0][i+1][2][0], self.table[0][i+1][2][1]) + ")"
        
        
        # Public Card
        for i in range(5):
            plainTable[i+1][0] = "%s%s" %(self.table[0][0][i+1][0], self.table[0][0][i+1][1])
            
        
        # Player Operation
        for i in range(len(self.table) - 1):
            for j in range(self.currentPlayerCount):
                if self.table[i+1][j] != "-1":
                    plainTable[i+1][j+1] = str(self.table[i+1][j])

        # Force Error Reset
        if self.roundError:
            plainTable[9][0] = "[ERROR] <<<错误>>>"
        # Game Info
        plainTable[6][0] = str(self.gameInfo["smallBlind"])
        plainTable[7][0] = str(self.gameInfo["largeBlind"])
        plainTable[8][0] = str(self.gameInfo["playerBottomBet"])
        if not self.roundError:
            self.write_plain_table(plainTable)
        
        self.playing = False
        self.table = []
        self.currentPlayerCount = 0
        self.lineIndex = 0
        self.roundError = False
        self.gameInfo = {"smallBlind": -1, "largeBlind": -1, "smallBlindIndex": -1, "largeBlindIndex": -1, "playerBottomBet": -1}
        
        return True

if __name__ == "__main__":
    testFile = TexasRecord("./tmp/record.csv")
    testFile.new_round()
    testFile.new_record_line()
    testFile.end_round()