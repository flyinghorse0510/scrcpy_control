import scontrol


def begin_session() -> int:
    return scontrol.begin_session()

def end_session() -> int:
    return scontrol.end_session()

def press_screen(x: int, y: int) -> int:
    return scontrol.press_screen(x, y)

def long_press_screen(x: int, y: int, pressMilliseconds: int = 10) -> int:
    return scontrol.long_press_screen(x, y, pressMilliseconds)

def release_screen(x: int, y: int) -> int:
    return scontrol.release_screen(x, y)

def long_click_screen(x: int, y: int, pressMilliseconds: int = 10) -> int:
    return scontrol.long_click_screen(x, y, pressMilliseconds)

def move_finger(x: int, y: int) -> int:
    return scontrol.move_finger(x, y)

def long_press_move_finger(beginX: int, beginY: int, endX: int, endY: int, pressMilliseconds: int, durationMilliseconds: int) -> int:
    return scontrol.long_press_move_finger(beginX, beginY, endX, endY, pressMilliseconds, durationMilliseconds)