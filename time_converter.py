import time
# print(round(time.time()))
calibrationTime = 0
def get_current_left_time(calibrationValue: int = 0, calibration: bool = False) -> int:
    global calibrationTime
    currentTime = 15 - (int(time.time()) - calibrationTime) % 35
    if calibration:
        calibrationTime = calibrationValue - currentTime
        currentTime = calibrationValue
    return currentTime

def get_current_unix_time() -> int:
    return int(time.time())
    
# while True:
#     print(get_current_left_time())
#     time.sleep(0.99)