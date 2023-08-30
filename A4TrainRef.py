import joblib
from sklearn import svm
import utils
import numpy as np
import os
from PIL import Image

savedModel = joblib.load("./A4Train/savedModel")

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

CardIdentifyResultArray = [CARD_RANK_UNKNOWN, CARD_RANK_A, CARD_RANK_4]

if __name__ == "__main__":
    trainDataset = np.load("./A4Train/train.npy")
    tesetDataset = np.load("./A4Train/test.npy")

    trainData = trainDataset[:,:-1]
    trainLabel = trainDataset[:,-1]
    testData = tesetDataset[:,:-1]
    testLabel = tesetDataset[:,-1]

    trainAccuracy = 100.0 * (savedModel.predict(trainData) == trainLabel).sum() / len(trainLabel)
    testAccuracy = 100.0 * (savedModel.predict(testData) == testLabel).sum() / len(testLabel)
    print(trainAccuracy)
    print(testAccuracy)

def get_actual_card_rank(img: Image.Image) -> int:
    data = utils.revert_binarize_pillow(img, 100)
    data = data.resize((46, 56))
    data = (np.array(data, dtype=np.float32) / 255.0).flatten().reshape((1,-1))
    predictResult = int(savedModel.predict(data)[0])
    return CardIdentifyResultArray[predictResult]