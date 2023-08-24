import texas_suit
import texas_activated
from PIL import Image
import numpy as np
import utils
# a = Image.open("/home/lowell/Downloads/game_begin_failure_5608.png")
# distance = np.power((texas_activated.GameBeginRef - a).flatten(), 2).sum()
# b = np.array(a)
# weight = 1.0 - b.sum() / (255.0 * b.size)
# print(weight)
# print(distance)
original = Image.open("./texas/user_all_in.png")
for i in range(30):
    binarizedOriginal = utils.binarize_pillow(original, 50 + i * 5)
    binarizedOriginal.save("./tmp/binarized_global_%d.png" %(50 + i * 5))