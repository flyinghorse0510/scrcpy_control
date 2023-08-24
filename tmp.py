import texas_suit
import texas_activated
from PIL import Image
import numpy as np
a = Image.open("/home/lowell/Downloads/game_begin_failure_5608.png")
distance = np.power((texas_activated.GameBeginRef - a).flatten(), 2).sum()
b = np.array(a)
weight = 1.0 - b.sum() / (255.0 * b.size)
print(weight)
print(distance)