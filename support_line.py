import sline

class SupportLine:
    def __init__(self, confirmCount: int = 3):
        self.core = sline.SupportLine(confirmCount)
    def reset_support_line(self):
        self.core.reset_support_line()
    def update_support_line(self, measurePoint: int) -> int:
        return self.core.update_support_line(measurePoint)
    def get_support_point(self) -> int:
        return self.core.get_support_point()
        