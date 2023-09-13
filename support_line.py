import sline

MAX_BET_INCREMENT = 50000000

class SupportLine:
    def __init__(self, confirmCount: int = 3, maxBetIncrement: int = MAX_BET_INCREMENT):
        self.core = sline.SupportLine(confirmCount, maxBetIncrement)
    def reset_support_line(self):
        self.core.reset_support_line()
    def update_support_line(self, measurePoint: int) -> int:
        return self.core.update_support_line(measurePoint)
    def get_support_point(self) -> int:
        return self.core.get_support_point()
    def update_with_last_point(self) -> int:
        return self.core.update_with_last_point()
    def is_support_point_accessed(self) -> bool:
        return self.core.is_support_point_accessed()
    def access_support_point(self):
        self.core.access_support_point()
        
class RankLine:
    def __init__(self, confirmCount: int = 5):
        self.core = sline.RankLine(confirmCount)
    def reset_rank(self):
        self.core.reset_rank()
    def get_rank(self) -> int:
        return self.core.get_rank()
    def update_rank(self, measureRank: int) -> int:
        return self.core.update_rank(measureRank)
    def update_with_last_rank(self) -> int:
        return self.core.update_with_last_rank()