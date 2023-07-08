dataFile = open("./filtered_record.csv", "r", encoding="utf-8-sig")
data = dataFile.readlines()[1:]
TigerSmallWin = 0
TigerLargeWin = 0
TigerEqualWin = 0
DragonSmallWin = 0
DragonLargeWin = 0
DragonEqualWin = 0
DragonLarge = 0
TigerLarge = 0
EqualEqualWin = 0
LargeWin = 0
SmallWin = 0
SplitWin = 0
gameCount = len(data)

dragonWinUnderDragonLarge = 0
dragonWinUnderTigerLarge = 0
tigerWinUnderDragonLarge = 0
tigerWinUnderTigerLarge = 0
for line in data:
    rowData = line.strip("\n").split(",")
    if rowData[4] == "龙":
        if int(rowData[1]) > int(rowData[3]):
            DragonLargeWin += 1
            LargeWin += 1
        elif int(rowData[1]) < int(rowData[3]):
            DragonSmallWin += 1
            SmallWin += 1
        else:
            DragonEqualWin += 1
    elif rowData[4] == "虎":
        if int(rowData[1]) < int(rowData[3]):
            TigerLargeWin += 1
            LargeWin += 1
        elif int(rowData[1]) > int(rowData[3]):
            TigerSmallWin += 1
            SmallWin += 1
        else:
            TigerEqualWin += 1
    else:
        SplitWin += 1
        if int(rowData[1]) == int(rowData[3]):
            EqualEqualWin += 1
    
    if int(rowData[1]) > int(rowData[3]):
        DragonLarge += 1
        if rowData[4] == "龙":
            dragonWinUnderDragonLarge += 1
        elif rowData[4] == "虎":
            tigerWinUnderDragonLarge += 1
    elif int(rowData[1]) < int(rowData[3]):
        TigerLarge += 1
        if rowData[4] == "龙":
            dragonWinUnderTigerLarge += 1
        elif rowData[4] == "虎":
            tigerWinUnderTigerLarge += 1

assert(LargeWin + SmallWin + SplitWin + TigerEqualWin + DragonEqualWin == gameCount)
print("P(龙小于虎|龙赢): %.3lf%%" %((DragonSmallWin / float(DragonSmallWin + DragonLargeWin + DragonEqualWin))*100))
print("P(龙大于虎|龙赢): %.3lf%%" %((DragonLargeWin / float(DragonSmallWin + DragonLargeWin + DragonEqualWin))*100))
print("P(虎小于龙|虎赢): %.3lf%%" %((TigerSmallWin / float(TigerSmallWin + TigerLargeWin + TigerEqualWin))*100))
print("P(虎大于龙|虎赢): %.3lf%%" %((TigerLargeWin / float(TigerSmallWin + TigerLargeWin + TigerEqualWin))*100))
print("\n")
print("P(虎赢|虎大于龙): %.3lf%%" %((tigerWinUnderTigerLarge / float(TigerLarge))*100))
print("P(虎赢|虎小于龙): %.3lf%%" %((tigerWinUnderDragonLarge / float(DragonLarge))*100))
print("P(龙赢|龙大于虎): %.3lf%%" %((dragonWinUnderDragonLarge / float(DragonLarge))*100))
print("P(龙赢|龙小于虎): %.3lf%%" %((dragonWinUnderTigerLarge / float(TigerLarge))*100))
print("\n")
print("P(龙虎中大的赢|龙虎赢): %.3lf%%" %((LargeWin / float(gameCount - SplitWin))*100))
print("P(龙虎中小的赢|龙虎赢): %.3lf%%" %((SmallWin / float(gameCount - SplitWin))*100))
print("\n")
print("P(龙赢|龙虎下注相同): %.3lf%%" %((DragonEqualWin / float(DragonEqualWin + TigerEqualWin + EqualEqualWin))*100))
print("P(虎赢|龙虎下注相同) %.3lf%%" %((TigerEqualWin / float(DragonEqualWin + TigerEqualWin + EqualEqualWin))*100))
print("P(和赢|龙虎下注相同): %.3lf%%" %((EqualEqualWin / float(DragonEqualWin + TigerEqualWin + EqualEqualWin))*100))
print("\n")
print("P(龙虎赢): %.3lf%%" %(((gameCount - SplitWin) / float(gameCount))*100))
print("P(和赢): %.3lf%%" %((SplitWin / float(gameCount))*100))
print("总局数: %d" %(gameCount))