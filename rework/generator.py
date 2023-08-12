from rand import Rand48
import math
from process import Process


class Generator(object):
    def __init__(self, lambda_: int, upperBound: int, seed: int):
        self.lambda_ = lambda_
        self.randomizer = Rand48()
        self.randomizer.srand(seed)
        self.upperBound = upperBound

    def next_exp(self) -> float:
        """
        exponential distribution as a function of random variable r
        if next_exp > self.ubound, we continue generating numbers until we find one <= self.ubound
        """
        num = self.upperBound
        while num > self.upperBound - 1:
            num = int(-math.log(self.randomizer.drand()) / self.lambda_)
        return num + 1

    def next_process(self, isIOBound: bool, id: str):
        """
        @returns a new Process P with an initial arrival time and a number of cpu bursts, each of which
                    has the same burst time. All io wait times for the process also have the same value.
        """
        arrivalTime = math.ceil(self.next_exp()) - 1
        numCPUBursts = math.ceil(64 * self.randomizer.drand())
        intervals = []
        for _ in range(numCPUBursts - 1):
            burstTime = math.ceil(self.next_exp())
            ioBurstTime = math.ceil(self.next_exp()) * 10
            if not isIOBound:
                burstTime *= 4
                ioBurstTime //= 8
            intervals.append(burstTime)
            intervals.append(ioBurstTime)

        burstTime = math.ceil(self.next_exp())
        if not isIOBound:
            burstTime *= 4
        intervals.append(burstTime)

        return Process(arrivalTime, numCPUBursts, intervals, isIOBound, id)
