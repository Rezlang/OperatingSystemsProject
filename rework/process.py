from copy import deepcopy
from math import ceil

class Process(object):

    def __init__(self, arrivalTime: int, numCPUBursts: int, intervals: list, isIOBound: bool, id: str):
        # Initialize process attributes
        self.arrivalTime: int = arrivalTime
        self.numCPUBursts: int = numCPUBursts
        self.intervals: list = deepcopy(intervals)
        self.OG_intervals: list = deepcopy(intervals)
        self.tauBursts: list = list()
        self.intervalIndex: int = 0
        self.isIOBound: bool = isIOBound
        self.id: str = id
        self.burstIndex: int = 0
        self.OGTauBursts: list = list()

    def calcTau(self, lambda_: float, alpha: float):
        # Calculate tau values based on intervals for calculating priorities
        for i in range(0, len(self.intervals), 2):
            if i == 0:
                self.tauBursts.append(ceil(1 / lambda_))
            else:
                self.tauBursts.append(
                    ceil(alpha * self.intervals[i - 2] + (1 - alpha) * self.tauBursts[-1]))
        self.OGTauBursts = deepcopy(self.tauBursts)

    # Various methods for accessing and manipulating process attributes

    def currentOGBurst(self):
        # Get the current original CPU burst time
        if self.burstIndex > len(self.tauBursts) - 1:
            raise IndexError("Process has completed bursts.")
        return self.OG_intervals[2 * self.burstIndex]

    def currentBurst(self):
        # Get the current CPU or I/O burst time
        if self.burstIndex > len(self.tauBursts) - 1:
            raise IndexError("Process has completed bursts.")
        return self.intervals[2 * self.burstIndex]

    # ... Similar methods for currentTau(), currentOGTau(), currentIOBurst() ...

    def finishBurst(self):
        # Move to the next burst index
        self.burstIndex += 1

    def burstsRemaining(self):
        # Calculate remaining bursts
        return self.numCPUBursts - self.burstIndex

    def finished(self):
        # Check if all bursts are completed
        return self.burstIndex > len(self.tauBursts) - 1

    def run__(self, t):
        # Update burst and tau times after running a burst
        if self.burstIndex > len(self.tauBursts) - 1:
            raise IndexError("Process has completed bursts.")
        self.intervals[2 * self.burstIndex] -= t
        self.tauBursts[self.burstIndex] = max(0, self.tauBursts[self.burstIndex] - t)

    def print(self):
        # Print process information
        print(
            "{}-bound process {}: arrival time {}ms; {} CPU bursts:".format("I/O" if self.isIOBound else "CPU", self.id,
                                                                            self.arrivalTime, self.numCPUBursts))
        for i in range(0, len(self.intervals) - 1):
            if i % 2 == 0:
                print("--> CPU burst {}ms".format(self.intervals[i]), end=" ")
            else:
                print("--> I/O burst {}ms".format(self.intervals[i]))
        print("--> CPU burst {}ms".format(self.intervals[-1]))

    def __str__(self):
        # Return a formatted string representation of the process
        return "{}-bound process {}: arrival time {}ms; {} CPU bursts".format("I/O" if self.isIOBound else "CPU", self.id, self.arrivalTime, self.numCPUBursts)
