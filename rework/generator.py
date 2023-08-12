from rand import Rand48
import math
from process import Process


class Generator(object):
    def __init__(self, lamda: int, ubound: int, seed: int):
        self.lamda = lamda
        self.randomizer = Rand48()
        self.randomizer.srand(seed)
        self.ubound = ubound

    def next_exp(self) -> float:
        """
        exponential distribution as a function of random variable r
        if next_exp > self.ubound, we continue generating numbers until we find one <= self.ubound
        """
        num = self.ubound
        while num > self.ubound - 1:
            num = int(-math.log(self.randomizer.drand()) / self.lamda)
        return num + 1

    def next_process(self, io_bound: bool, pid: str):
        """
        @returns a new Process P with an initial arrival time and a number of cpu bursts, each of which
                    has the same burst time. All io wait times for the process also have the same value.
        """
        initial_arrival_time = math.ceil(self.next_exp()) - 1
        cpu_bursts = math.ceil(64 * self.randomizer.drand())
        intervals = []
        for _ in range(cpu_bursts - 1):
            cpu_burst_time = math.ceil(self.next_exp())
            io_time = math.ceil(self.next_exp()) * 10
            if not io_bound:
                cpu_burst_time *= 4
                io_time //= 8
            intervals.append(cpu_burst_time)
            intervals.append(io_time)

        cpu_burst_time = math.ceil(self.next_exp())
        if not io_bound:
            cpu_burst_time *= 4
        intervals.append(cpu_burst_time)

        return Process(initial_arrival_time, cpu_bursts, intervals, io_bound, pid)
