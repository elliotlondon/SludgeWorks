class GlobalClock():
    """Global clock and tic system to define the global clock and keep track of animation frames."""

    def __init__(self):
        self.tic: int = 0

    def current_tic(self):
        return self.tic

    def toc(self):
        if self.tic >= 4096:
            self.tic = 0
        else:
            self.tic += 1

