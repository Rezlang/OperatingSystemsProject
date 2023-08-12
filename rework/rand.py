class Rand48:
    # class to handle rand48 style of random number generation
    # source: Dietrich Epp on stackoverflow
    def __init__(self):
        self.n = 0

    def srand(self, seed):
        self.n = (seed << 16) + 0x330e

    def next(self):
        self.n = (25214903917 * self.n + 11) & (2 ** 48 - 1)
        return self.n

    def drand(self):
        return self.next() / 2 ** 48
