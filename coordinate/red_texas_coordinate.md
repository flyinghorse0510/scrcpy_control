## 1. Global Region
1. bottom bet: `(1084, 300, 1440, 340)`
2. game begin: `(1106, 484, 1430, 532)`

### 1.1 Public Card Calibration Point
1. `(875, 452)`
2. `(1029, 452)`
3. `(1184, 452)`
4. `(1339, 452)`
5. `(1493, 452)`

### 1.2 Public Card Offset
Card Rank Size: `(48, 60)`
Card Rank Offset: `(5, -4)`

Card Suit Size:`(37, 41)`
Card Suit Offset:`(10, 57)`

<!-- ### 1.2 Public Card Character
Card Character Size: `(52, 60)`
1. `(878, 448, 930, 508)`
2. `(1032, 448, 1084, 508)`
3. `(1188, 448, 1240, 508)`
4. `(1342, 448, 1394, 508)`
5. `(1498, 448, 1550, 508)`
### 1.2 Public Card Color
Card Color Size: `(40, 44)`
1. `(883, 507, 923, 551)`
2. `(1038, 507, 1078, 551)`
3. `(1192, 507, 1232, 551)`
4. `(1347, 507, 1387, 551)`
5. `(1501, 507, 1541, 551)` -->

### 1.3 Private Card Offset
Card Rank Size: `(46, 56)`
Card Rank Offset: `(8, -178)`, `(56, -178)`

Card Suit Size: `(37, 41)`
Card Suit Offset: `(12, -123)`, `(62, -123)`

### 1.4 Private Status Offset
Status Block Size: `(108, 22)`
Status Offset: `(40, -207)`

### 1.5 Empty Seat Offset
Empty Seat Block Size: `(69, 33)`
Empty Seat Offset: `(49, -182)`


## 2. Private Region
### 2.1 Private Calibration Point
Calibration Block Size: `(188, 46)`
Calibration Point:
- 1st:`(749, 253)`
- 2nd:`(408, 384)`
- 3rd:`(350, 713)`
- 4th:`(640, 906)`
- 5th:`(1170, 906)`
- 6th:`(1701, 906)`
- 7th:`(1989, 713)`
- 8th:`(1930, 384)`
- 9th:`(1591, 253)`

## 3. Template Region
- Player Size Out-Bound: `(208, 296)`
- Player Size Inner-Bound: `(168, 268)`

- Experimental Empty Seat Filter Range: `(22, 100, 100)` ==> `(45, 255, 255)`
- Experimental User Thinking Filter Range: `(84, 100, 100)` ==> `(114, 255, 255)`
- Experimental User Fold Filter Range: `(0, 8, 38)` ==> `(180, 76, 90)`
- Experimental User All-in Filter Range: `()` ==> `()`