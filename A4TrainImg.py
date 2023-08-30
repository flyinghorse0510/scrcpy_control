import torch
import numpy as np
import os
from PIL import Image
import utils

rawFileLists = os.listdir("A4TrainImg")
fileList4 = []
fileListA = []
fileListU = []
for rawFile in rawFileLists:
    splittedFileName = rawFile.split("_")
    # print(splittedFileName)
    fileIndex = int(splittedFileName[0])
    fileType = splittedFileName[1][0]
    rawFilePath = os.path.join("A4TrainImg", rawFile)
    if fileType == "A":
        fileListA.append(rawFilePath)
    elif fileType == "4":
        fileList4.append(rawFilePath)
    elif fileType == "U":
        fileListU.append(rawFilePath)

trainRatio = 0.7

file4TrainCount = int(len(fileList4) * trainRatio)
fileATrainCount = file4TrainCount
fileUTrainCount = int(len(fileListU) * trainRatio)

file4TestCount = len(fileList4) - file4TrainCount
fileATestCount = file4TestCount
fileUTestCount = len(fileListU) - fileUTrainCount

print([file4TrainCount, fileATrainCount, fileUTrainCount])
print([file4TestCount, fileATestCount, fileUTestCount])

file4DataArray = []
fileADataArray = []
fileUDataArray = []

for fileA in fileListA:
    img = Image.open(fileA)
    data = utils.revert_binarize_pillow(img, 100)
    data = data.resize((46, 56))
    fileADataArray.append((np.array(data, dtype=np.float32) / 255.0).flatten())


for file4 in fileList4:
    img = Image.open(file4)
    data = utils.revert_binarize_pillow(img, 100)
    data = data.resize((46, 56))
    file4DataArray.append((np.array(data, dtype=np.float32) / 255.0).flatten())

for fileU in fileListU:
    img = Image.open(fileU)
    data = utils.revert_binarize_pillow(img, 100)
    data = data.resize((46, 56))
    fileUDataArray.append((np.array(data, dtype=np.float32) / 255.0).flatten())


file4DataArray = np.array(file4DataArray, dtype=np.float32)
print(file4DataArray.shape)
fileADataArray = np.array(fileADataArray, dtype=np.float32)
fileUDataArray = np.array(fileUDataArray, dtype=np.float32)

label4 = np.zeros((file4DataArray.shape[0], 1))
label4 += 2.0
labelA = np.zeros((fileADataArray.shape[0], 1))
labelA += 1.0
labelU = np.zeros((fileUDataArray.shape[0], 1))

file4DataArray = np.concatenate((file4DataArray, label4), axis=1)
fileADataArray = np.concatenate((fileADataArray, labelA), axis=1)
fileUDataArray = np.concatenate((fileUDataArray, labelU), axis=1)

np.random.shuffle(file4DataArray)
np.random.shuffle(fileADataArray)
np.random.shuffle(fileUDataArray)

trainDataSet = np.concatenate((file4DataArray[:file4TrainCount], fileADataArray[:fileATrainCount], fileUDataArray[:fileUTrainCount]), axis=0)
testDataSet = np.concatenate((file4DataArray[file4TrainCount:file4TrainCount+file4TestCount], fileADataArray[fileATrainCount:fileATrainCount+fileATestCount], fileUDataArray[fileUTrainCount:fileUTrainCount+fileUTestCount]), axis=0)
np.random.shuffle(trainDataSet)
np.random.shuffle(testDataSet)
print(trainDataSet.shape)
print(testDataSet.shape)

np.save("./A4Train/train.npy", trainDataSet)
np.save("./A4Train/test.npy", testDataSet)