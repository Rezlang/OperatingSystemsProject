from copy import deepcopy
from math import ceil


class Process(object):

    def __init__(self, arrival_time: int, cpu_bursts: int, intervals: list, io_bound: bool, pid: str):
        # arrival time in ms
        # number is intervals is cpu bursts * 2 - 1, since every cpu burst is interrupted by an io burst
        # -> processing goes cpu, io, cpu, io, ...., io, cpu

        self.arrival_time = arrival_time
        self.cpu_bursts = cpu_bursts
        self.intervals = deepcopy(intervals)
        self.og_intervals = deepcopy(intervals)
        self.predicted_bursts = list()
        self.intervals_completed = 0
        self.io_bound = io_bound
        self.pid = pid
        self.burst_index = 0
        self.og_predicted_bursts = list()

    def compute_predicted(self, lamda: float, alpha: float):
        for i in range(0, len(self.intervals), 2):
            if i == 0:
                self.predicted_bursts.append(ceil(1 / lamda))
            else:
                self.predicted_bursts.append(
                    ceil(alpha * self.intervals[i - 2] + (1 - alpha) * self.predicted_bursts[-1]))
        self.og_predicted_bursts = deepcopy(self.predicted_bursts)

    def this_og_burst(self):
        if self.burst_index > len(self.predicted_bursts) - 1:
            raise IndexError("Process has completed bursts.")
        return self.og_intervals[2 * self.burst_index]

    def this_burst(self):
        if self.burst_index > len(self.predicted_bursts) - 1:
            raise IndexError("Process has completed bursts.")
        return self.intervals[2 * self.burst_index]

    def this_tau(self):
        if self.burst_index > len(self.predicted_bursts) - 1:
            raise IndexError("Process has completed bursts.")
        return self.predicted_bursts[self.burst_index]

    def this_og_tau(self):
        if self.burst_index > len(self.predicted_bursts) - 1:
            raise IndexError("Process has completed bursts.")
        return self.og_predicted_bursts[self.burst_index]

    def this_io(self):
        if self.burst_index > len(self.predicted_bursts) - 1:
            raise IndexError("Process has completed bursts.")
        elif self.burst_index == len(self.predicted_bursts) - 1:
            return 0
        return self.intervals[2 * self.burst_index + 1]

    def complete_this_burst(self):
        self.burst_index += 1

    def remaining_bursts(self):
        return self.cpu_bursts - self.burst_index

    def done(self):
        return self.burst_index > len(self.predicted_bursts) - 1

    def run(self, t):
        if self.burst_index > len(self.predicted_bursts) - 1:
            raise IndexError("Process has completed bursts.")
        self.intervals[2 * self.burst_index] -= t
        self.predicted_bursts[self.burst_index] = max(0, self.predicted_bursts[self.burst_index] - t)

    def print(self):
        print(
            "{}-bound process {}: arrival time {}ms; {} CPU bursts:".format("I/O" if self.io_bound else "CPU", self.pid,
                                                                            self.arrival_time, self.cpu_bursts))
        for i in range(0, len(self.intervals) - 1):
            if i % 2 == 0:
                print("--> CPU burst {}ms".format(self.intervals[i]), end=" ")

            else:
                print("--> I/O burst {}ms".format(self.intervals[i]))
        print("--> CPU burst {}ms".format(self.intervals[-1]))

    def __str__(self):
        return "{}-bound process {}: arrival time {}ms; {} CPU bursts".format("I/O" if self.io_bound else "CPU", self.pid, self.arrival_time, self.cpu_bursts)
