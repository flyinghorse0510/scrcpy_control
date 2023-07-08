dataFile = open("../record.csv", "r", encoding="utf-8-sig")
filteredFile = open("filtered_record.csv", "w", encoding="utf-8-sig")
data = dataFile.readlines()
index = 0
for line in data:
    index += 1
    rowData = line.strip("\n").split(",")
    if index != 1:
        rowData[0] = str(index-1)
        rowData[1] = str(int((int(rowData[1]) + 1) / 100) * 100)
        rowData[2] = str(int((int(rowData[2]) + 1) / 100) * 100)
        rowData[3] = str(int((int(rowData[3]) + 1) / 100) * 100)
        if len(rowData) <= 5:
            rowData.append("0")
            rowData.append("0")
    else:
        if len(rowData) <= 5:
            rowData.append("下注(龙)")
            rowData.append("下注(虎)")
    filteredFile.write("%s,%s,%s,%s,%s,%s,%s\n" %(rowData[0], rowData[1], rowData[2], rowData[3], rowData[4], rowData[5], rowData[6]))