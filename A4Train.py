from sklearn import svm
import numpy as np
import joblib

trainDataset = np.load("./A4Train/train.npy")
tesetDataset = np.load("./A4Train/test.npy")

trainData = trainDataset[:,:-1]
trainLabel = trainDataset[:,-1]
testData = tesetDataset[:,:-1]
testLabel = tesetDataset[:,-1]

model = svm.SVC()
print("Training SVM")
model.fit(trainData, trainLabel)
print(trainLabel)
print("Finished Training")

joblib.dump(model, "./A4Train/savedModel")

predictLabel = model.predict(testData)
print(predictLabel)
predictResult = predictLabel == testLabel
print(predictResult)


