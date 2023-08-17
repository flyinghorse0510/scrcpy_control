from PIL import Image, ImageOps

MAX_INT_NUMBER = 1000000000

def txt2int(txt: str) -> int:
    if len(txt) == 0:
        return 0
    number = 0
    multi = 1
    realTxt = txt
    if txt[-1] == "万":
        multi = 10000
        realTxt = realTxt[:-1]
    elif txt[-1] == "亿":
        multi = 100000000
        realTxt = realTxt[:-1]
    
    try:
        number = int(float(realTxt) * multi + 0.5)
    except ValueError as e1:
        number = -1
    except OverflowError as e2:
        number = -1
    except:
        print("Convert Error!")
        number = -1
    
    number = number if number < MAX_INT_NUMBER else -1
    return number

def is_chinese(txt: str) -> bool:
    for i in range(len(txt)):
        if txt[i] < '\u4e00' or txt[i] > '\u9fa5':
            return False
    return True

def pureTxt2int(txt: str) -> int:
    if len(txt) == 0:
        return 0
    try:
        number = int(txt)
    except ValueError as e:
        number = -1
    except:
        print("Convert Error!")
        number = -1
        
    number = number if number < MAX_INT_NUMBER else -1
    return number

def cleanStr(txt: str) -> str:
    return txt.replace(" ", "").replace("-","").replace("一","").strip("\n")

def binarize_pillow(img: Image.Image, threshold: int) -> Image.Image:
    outputImg = ImageOps.grayscale(img)
    return outputImg.point(lambda x: 0 if x > threshold else 255)

def filter_until_number(txt: str) -> str:
    txtLength = len(txt)
    for i in range(txtLength):
        if txt[i] <= "9" and txt[i] >= "0":
            return txt[i:]
    return ""

def card_rank_replace(rankTxt: str) -> str:
    replacedTxt = rankTxt.replace("O", "9").replace("T", "7").replace("?", "2")
    finalTxt = ""
    
    return replacedTxt
    

def revert_binarize_pillow(img: Image.Image, threshold: int) -> Image.Image:
    outputImg = ImageOps.grayscale(img)
    return outputImg.point(lambda x: 0 if x <= threshold else 255)