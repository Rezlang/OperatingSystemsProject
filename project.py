import math
import random
import sys
from copy import deepcopy
from typing import List, Tuple
from enum import Enum
import heapq


class Rand48:
    # class to handle rand48 style of random number generation
    # source: Dietrich Epp on stackoverflow
    def __init__(self):
        self.n = 0

    def srand(self, seed):
        self.n = (seed << 16) + 0x330e

    def next(self):
        self.n = (25214903917 * self.n + 11) & (2**48 - 1)
        return self.n

    def drand(self):
        return self.next() / 2**48


randomizer = Rand48()


def round(num):
    return math.ceil(num * 1000) / 1000


class Status(Enum):
    UNARRIVED = -1
    READY = 0
    SWITCHING_IN = 1
    RUNNING = 2
    WAITING = 3
    SWITCHING_OUT = 4
    TERMINATED = 5


class Process:
    def __init__(self):
        self.id = ''
        self.arrivalTime = 0
        self.burstTimes: List[List[int]] = []
        self.isCPUBound = False
        self.status = Status.UNARRIVED
        self.switchingTimer = 0
        self.numContextSwitches = 0
        self.numBursts = 0
        self.waitTime = 0
        self.turnaroundTime: List[int] = []
        self.reachedCPU: List[bool] = []
        self.turnaroundIndex = 0
        self.numPreemptions = 0
        self.tau = 0
        self.timeRunning = 0
        self.OGBurstTimes: List[List[int]] = []

    def __lt__(self, other):
        return self.id < other.id

    def recalcTau(self, alpha):
        self.tau = math.ceil(
            alpha * self.OGBurstTimes[self.turnaroundIndex][0] + (1-alpha) * self.tau)
        return self.tau


class manager:
    def __init__(self, processes, numCPUProc):
        self.generatedProcesses: List[Process] = processes
        self.readyQueue: List[Tuple[int, Process]] = []
        self.activeProcess: Process = self.generatedProcesses[0]
        self.busyTime = 0
        self.numCPU = numCPUProc

        self.avgCPUBurst = sum(sum(q[0] for q in p.burstTimes) for p in self.generatedProcesses) / sum(
            len(p.burstTimes) for p in self.generatedProcesses)
        self.avgCPUProcBurst = sum(sum(q[0] for q in p.burstTimes) if p.isCPUBound else 0 for p in self.generatedProcesses) / sum(
            len(p.burstTimes) if p.isCPUBound else 0 for p in self.generatedProcesses)
        self.avgIOProcBurst = sum(sum(q[0] for q in p.burstTimes) if not p.isCPUBound else 0 for p in self.generatedProcesses) / sum(
            len(p.burstTimes) if not p.isCPUBound else 0 for p in self.generatedProcesses)

    def calculateTurnarounds(self):
        CPUBound = 0
        IOBound = 0
        for p in self.generatedProcesses:
            for i in range(len(p.turnaroundTime)-1):

                if p.isCPUBound:
                    CPUBound += p.turnaroundTime[i+1] - p.turnaroundTime[i]
                else:
                    IOBound += p.turnaroundTime[i+1] - p.turnaroundTime[i]
                i += 1
        return ((CPUBound + IOBound) / sum(p.numBursts for p in self.generatedProcesses),
                CPUBound /
                sum(p.numBursts if p.isCPUBound else 0 for p in self.generatedProcesses),
                IOBound / sum(p.numBursts if not p.isCPUBound else 0 for p in self.generatedProcesses))

    def printQueue(self):
        if len(self.readyQueue) != 0:
            print("[Q " + " ".join(x[1].id for x in self.readyQueue) + "]", sep='')
        else:
            print("[Q <empty>]")


# sum(sum(p.turnaroundTime) for p in PM.generatedProcesses) / sum(p.numBursts for p in PM.generatedProcesses),
# sum(sum(p.turnaroundTime) if p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(p.numBursts if p.isCPUBound else 0 for p in PM.generatedProcesses),
# sum(sum(p.turnaroundTime) if not p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(p.numBursts if not p.isCPUBound else 0  for p in PM.generatedProcesses)

def FirstComeFirstServe(processes, contextSwitchTime, numCPUProc):
    print("time 0ms: Simulator started for FCFS [Q <empty>]")
    PM = manager(processes, numCPUProc)
    PM.activeProcess.numContextSwitches += 1

    PM.activeProcess.turnaroundTime.append(PM.activeProcess.arrivalTime)

    PM.activeProcess.reachedCPU[0] = True
    PM.activeProcess.status = Status.SWITCHING_IN
    PM.activeProcess.switchingTimer = contextSwitchTime / 2
    time = PM.activeProcess.arrivalTime
    print("time ", time, "ms: Process " + PM.activeProcess.id +
          " arrived; added to ready queue [Q "+PM.activeProcess.id+"]", sep='')
    done = False
    while (not done):

        # Updated running process
        if PM.activeProcess.status == Status.SWITCHING_IN:
            if PM.activeProcess.switchingTimer == 0:
                PM.activeProcess.status = Status.RUNNING
                # time 28ms: Process C started using the CPU for 2920ms burst [Q <empty>]
                if time < 10000000:
                    print("time ", time, "ms: Process "+PM.activeProcess.id + " started using the CPU for ",
                          PM.activeProcess.burstTimes[0][0], "ms burst ", end="", sep='')

                    PM.printQueue()
            else:
                PM.activeProcess.switchingTimer -= 1

        elif PM.activeProcess.status == Status.SWITCHING_OUT:
            if PM.activeProcess.switchingTimer == 0:

                if (PM.activeProcess.burstTimes[0][1] == 0):
                    PM.activeProcess.status = Status.TERMINATED
                else:
                    PM.activeProcess.status = Status.WAITING
                    if len(PM.readyQueue) != 0:
                        PM.activeProcess = PM.readyQueue[0][1]
                        PM.readyQueue.pop(0)
                        PM.activeProcess.turnaroundTime.append(time)

                        PM.activeProcess.numContextSwitches += 1
                        if not PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex]:
                            PM.activeProcess.turnaroundTime.append(time)
                        PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
                        PM.activeProcess.status = Status.SWITCHING_IN
                        PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
            else:
                PM.activeProcess.switchingTimer -= 1

        if (PM.activeProcess.status == Status.WAITING or PM.activeProcess.status == Status.READY or PM.activeProcess.status == Status.TERMINATED) and len(PM.readyQueue) != 0:
            PM.activeProcess = PM.readyQueue[0][1]
            PM.readyQueue.pop(0)
            if not PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex]:
                PM.activeProcess.turnaroundTime.append(time)

            PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
            PM.activeProcess.numContextSwitches += 1
            PM.activeProcess.status = Status.SWITCHING_IN
            PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1

        if PM.activeProcess.status == Status.RUNNING:
            if PM.activeProcess.burstTimes[0][0] == 0:

                if len(PM.activeProcess.burstTimes) == 1:
                    print("time ", time, "ms: Process ",
                          PM.activeProcess.id, " terminated ", sep="", end="")
                    PM.printQueue()
                elif time < 10000000:
                    if len(PM.activeProcess.burstTimes)-1 != 1:
                        print("time ", time, "ms: Process "+PM.activeProcess.id + " completed a CPU burst; ",
                              len(PM.activeProcess.burstTimes)-1, " bursts to go ", end="", sep='')
                    else:
                        print("time ", time, "ms: Process "+PM.activeProcess.id + " completed a CPU burst; ",
                              len(PM.activeProcess.burstTimes)-1, " burst to go ", end="", sep='')

                    PM.printQueue()
                    print("time ", time, "ms: Process " + PM.activeProcess.id + " switching out of CPU; blocking on I/O until time ",
                          (time + PM.activeProcess.burstTimes[0][1] + contextSwitchTime // 2), "ms ", end="", sep='')
                    PM.printQueue()

                if len(PM.activeProcess.burstTimes) != 1:
                    PM.activeProcess.turnaroundIndex += 1

                PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
                PM.activeProcess.status = Status.SWITCHING_OUT
            else:
                PM.activeProcess.burstTimes[0][0] -= 1

        # check for IO burst completions
        for p in PM.generatedProcesses:
            if p.status == Status.WAITING:
                if p.burstTimes[0][1] == 0:
                    p.burstTimes.pop(0)
                    if len(PM.readyQueue) == 0 and PM.activeProcess.status != Status.RUNNING:
                        PM.activeProcess = p
                        PM.activeProcess.numContextSwitches += 1
                        if not PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex]:
                            PM.activeProcess.turnaroundTime.append(time)
                        PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
                        p.status = Status.SWITCHING_IN
                        p.switchingTimer = contextSwitchTime / 2 - 1
                        print("time ", time, "ms: Process " + p.id +
                              " completed I/O; added to ready queue ", end="", sep='')
                        print("[Q " + p.id + "]", sep='')
                    else:
                        p.status = Status.READY
                        heapq.heappush(PM.readyQueue, (time, p))
                        # time 3318ms: Process C completed I/O; added to ready queue [Q B C]
                        if time < 10000000:
                            print("time ", time, "ms: Process " + p.id +
                                  " completed I/O; added to ready queue ", end="", sep='')
                            PM.printQueue()
                else:
                    p.burstTimes[0][1] -= 1

        # Checks if new processes have arrived
        for p in PM.generatedProcesses:
            if p.status == Status.RUNNING:
                PM.busyTime += 1
            if p.status == Status.READY:
                p.waitTime += 1
            if p.status == Status.SWITCHING_IN or p.status == Status.SWITCHING_OUT or p.status == Status.RUNNING or p.status == Status.WAITING:
                p.turnaroundTime[p.turnaroundIndex] += 1

        for p in PM.generatedProcesses:
            if p.arrivalTime <= time and p.status == Status.UNARRIVED:
                heapq.heappush(PM.readyQueue, (time, p))
                if time < 10000000:
                    print("time ", time, "ms: Process " + p.id +
                          " arrived; added to ready queue ", end="", sep='')
                    PM.printQueue()
                p.status = Status.READY
        done = True
        for p in PM.generatedProcesses:
            if p.status != Status.TERMINATED:
                done = False

        time += 1 if not done else 0
    # time 324063ms: Simulator ended for FCFS [Q <empty>]
    print("time ", time, "ms: Simulator ended for FCFS [Q <empty>]", sep="")
    fn = "simout.txt"
    fp = open(fn, "w")
#     Algorithm FCFS
# -- CPU utilization: 84.253%
# -- average CPU burst time: 3067.776 ms (4071.000 ms/992.138 ms)
# -- average wait time: 779.663 ms (217.284 ms/1943.207 ms)
# -- average turnaround time: 3851.439 ms (4292.284 ms/2939.345 ms)
# -- number of context switches: 89 (60/29)
# -- number of preemptions: 0 (0/0)
# TODO: First number in parenthesis is for CPU-bound processes, the second is for IO-bound processes

    print("Algorithm FCFS", file=fp)
    print(
        "-- CPU utilization: {:.3f}%".format(PM.busyTime / time * 100), file=fp)
    print("-- average CPU burst time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(round(
        PM.avgCPUBurst), round(PM.avgCPUProcBurst), round(PM.avgIOProcBurst)), file=fp)

    print("-- average wait time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(sum(p.waitTime for p in PM.generatedProcesses) / sum((p.numBursts+1)/2 for p in PM.generatedProcesses),
                                                                         sum(p.waitTime if p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(
        (p.numBursts+1)/2 if p.isCPUBound else 0 for p in PM.generatedProcesses),
        sum(p.waitTime if not p.isCPUBound else 0 for p in PM.generatedProcesses) / sum((p.numBursts+1)/2 if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    turnarounds = PM.calculateTurnarounds()
    print("-- average turnaround time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(
        turnarounds[0], turnarounds[1], turnarounds[2]), file=fp)
    print("-- number of context switches: {:d} ({:d}/{:d})".format(sum(p.numContextSwitches for p in PM.generatedProcesses),
                                                                   sum(
                                                                       p.numContextSwitches if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                                   sum(p.numContextSwitches if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    print("-- number of preemptions: {:d} ({}/{})".format(sum(p.numPreemptions for p in PM.generatedProcesses),
                                                          sum(
                                                              p.numPreemptions if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                          sum(p.numPreemptions if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    print("", file=fp)
    fp.close()


def ShortestJobFirst(processes, contextSwitchTime, numCPUProc, alpha):
    print("time 0ms: Simulator started for SJF [Q <empty>]")
    PM = manager(processes, numCPUProc)
    PM.activeProcess.numContextSwitches += 1
    PM.activeProcess.reachedCPU[0] = True
    PM.activeProcess.status = Status.SWITCHING_IN
    PM.activeProcess.switchingTimer = contextSwitchTime / 2

    time = PM.activeProcess.arrivalTime
    print("time ", time, "ms: Process " + PM.activeProcess.id +
          " (tau ", PM.activeProcess.tau, "ms) arrived; added to ready queue [Q "+PM.activeProcess.id+"]", sep='')
    done = False
    while (not done):

        # Updated running process
        if PM.activeProcess.status == Status.SWITCHING_IN:
            if PM.activeProcess.switchingTimer == 0:
                PM.activeProcess.status = Status.RUNNING
                # time 28ms: Process C started using the CPU for 2920ms burst [Q <empty>]
                if time < 10000000:
                    print("time ", time, "ms: Process "+PM.activeProcess.id + " (tau ", PM.activeProcess.tau, "ms) started using the CPU for ",
                          PM.activeProcess.burstTimes[0][0], "ms burst ", end="", sep='')

                    PM.printQueue()
            else:
                PM.activeProcess.switchingTimer -= 1

        elif PM.activeProcess.status == Status.SWITCHING_OUT:
            if PM.activeProcess.switchingTimer == 0:

                if (PM.activeProcess.burstTimes[0][1] == 0):
                    PM.activeProcess.status = Status.TERMINATED
                else:
                    PM.activeProcess.status = Status.WAITING

                    if len(PM.readyQueue) != 0:
                        PM.activeProcess = PM.readyQueue[0][1]
                        PM.readyQueue.pop(0)

                        PM.activeProcess.numContextSwitches += 1
                        PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
                        PM.activeProcess.status = Status.SWITCHING_IN
                        PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
            else:
                PM.activeProcess.switchingTimer -= 1

        if (PM.activeProcess.status == Status.WAITING or PM.activeProcess.status == Status.READY or PM.activeProcess.status == Status.TERMINATED) and len(PM.readyQueue) != 0:
            PM.activeProcess = PM.readyQueue[0][1]
            PM.readyQueue.pop(0)
            PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
            PM.activeProcess.numContextSwitches += 1
            PM.activeProcess.status = Status.SWITCHING_IN
            PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1

        if PM.activeProcess.status == Status.RUNNING:
            if PM.activeProcess.burstTimes[0][0] == 0:

                if len(PM.activeProcess.burstTimes) == 1:
                    print("time ", time, "ms: Process ",
                          PM.activeProcess.id, " terminated ", sep="", end="")
                    PM.printQueue()
                elif time < 10000000:
                    print("time ", time, "ms: Process "+PM.activeProcess.id + " (tau ", PM.activeProcess.tau, "ms) completed a CPU burst; ",
                          len(PM.activeProcess.burstTimes)-1, " burst", 's' if len(PM.activeProcess.burstTimes)-1 != 1 else '', " to go ", end="", sep='')
                    PM.printQueue()

                oldTau = PM.activeProcess.tau
                PM.activeProcess.recalcTau(alpha)

                if time < 10000000 and len(PM.activeProcess.burstTimes) != 1:
                    # time 9056ms: Recalculating tau for process C: old tau 2440ms ==> new tau 2356ms [Q B]
                    print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms ".format(
                        time, PM.activeProcess.id, oldTau, PM.activeProcess.tau), end="")

                    PM.printQueue()
                    print("time ", time, "ms: Process " + PM.activeProcess.id + " switching out of CPU; blocking on I/O until time ",
                          (time + PM.activeProcess.burstTimes[0][1] + contextSwitchTime // 2), "ms ", end="", sep='')
                    PM.printQueue()

                if len(PM.activeProcess.burstTimes) != 1:
                    PM.activeProcess.turnaroundIndex += 1

                PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
                PM.activeProcess.status = Status.SWITCHING_OUT
            else:
                PM.activeProcess.burstTimes[0][0] -= 1

        # check for IO burst completions
        for p in PM.generatedProcesses:
            if p.status == Status.WAITING:
                if p.burstTimes[0][1] == 0:
                    p.burstTimes.pop(0)
                    if len(PM.readyQueue) == 0 and PM.activeProcess.status != Status.RUNNING:
                        PM.activeProcess = p
                        PM.activeProcess.numContextSwitches += 1
                        PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
                        p.status = Status.SWITCHING_IN
                        p.switchingTimer = contextSwitchTime / 2 - 1
                        print("time ", time, "ms: Process ", p.id, " (tau ", p.tau, "ms)",
                              " completed I/O; added to ready queue ", end="", sep='')
                        print("[Q " + p.id + "]", sep='')
                    else:
                        p.status = Status.READY
                        pTuple = (p.tau, p)
                        heapq.heappush(PM.readyQueue, pTuple)
                        # time 3318ms: Process C completed I/O; added to ready queue [Q B C]
                        if time < 10000000:
                            print("time ", time, "ms: Process " + p.id +
                                  " (tau ", p.tau, "ms) completed I/O; added to ready queue ", end="", sep='')
                            PM.printQueue()
                else:
                    p.burstTimes[0][1] -= 1

        # Checks if new processes have arrived
        for p in PM.generatedProcesses:
            if p.status == Status.RUNNING:
                PM.busyTime += 1
            if p.status == Status.READY:
                p.waitTime += 1
            if p.status == Status.SWITCHING_IN or p.status == Status.SWITCHING_OUT or p.status == Status.RUNNING or p.status == Status.WAITING:
                p.turnaroundTime[p.turnaroundIndex] += 1

        for p in PM.generatedProcesses:
            if p.arrivalTime <= time and p.status == Status.UNARRIVED:
                pTuple = (p.tau, p)
                heapq.heappush(PM.readyQueue, pTuple)
                if time < 10000000:
                    print("time ", time, "ms: Process " + p.id +
                          " (tau ", p.tau, "ms) arrived; added to ready queue [Q ", " ".join(x[1].id for x in PM.readyQueue), "]", sep='')
                p.status = Status.READY
        done = True
        for p in PM.generatedProcesses:
            if p.status != Status.TERMINATED:
                done = False

        time += 1 if not done else 0
    # time 324063ms: Simulator ended for FCFS [Q <empty>]
    print("time ", time, "ms: Simulator ended for SJF [Q <empty>]\n", sep="")
    fn = "simout.txt"
    fp = open(fn, "a")
#     Algorithm FCFS
# -- CPU utilization: 84.253%
# -- average CPU burst time: 3067.776 ms (4071.000 ms/992.138 ms)
# -- average wait time: 779.663 ms (217.284 ms/1943.207 ms)
# -- average turnaround time: 3851.439 ms (4292.284 ms/2939.345 ms)
# -- number of context switches: 89 (60/29)
# -- number of preemptions: 0 (0/0)
# TODO: First number in parenthesis is for CPU-bound processes, the second is for IO-bound processes

    print("Algorithm SJF", file=fp)
    print(
        "-- CPU utilization: {:.3f}%".format(round(PM.busyTime / time * 100)), file=fp)
    print("-- average CPU burst time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(
        round(PM.avgCPUBurst), round(PM.avgCPUProcBurst), round(PM.avgIOProcBurst)), file=fp)

    print("-- average wait time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(round(sum(p.waitTime for p in PM.generatedProcesses) / sum((p.numBursts+1)/2 for p in PM.generatedProcesses)),
                                                                         round(sum(p.waitTime if p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(
                                                                              (p.numBursts+1)/2 if p.isCPUBound else 0 for p in PM.generatedProcesses)),
                                                                         round(sum(p.waitTime if not p.isCPUBound else 0 for p in PM.generatedProcesses) / sum((p.numBursts+1)/2 if not p.isCPUBound else 0 for p in PM.generatedProcesses))), file=fp)
    print("-- average turnaround time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(sum(sum(p.turnaroundTime) for p in PM.generatedProcesses) / sum(p.numBursts for p in PM.generatedProcesses),
                                                                               sum(sum(p.turnaroundTime) if p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(
                                                                                   p.numBursts if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                                               sum(sum(p.turnaroundTime) if not p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(p.numBursts if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    print("-- number of context switches: {:d} ({:d}/{:d})".format(sum(p.numContextSwitches for p in PM.generatedProcesses),
                                                                   sum(
                                                                       p.numContextSwitches if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                                   sum(p.numContextSwitches if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    print("-- number of preemptions: {:d} ({}/{})".format(sum(p.numPreemptions for p in PM.generatedProcesses),
                                                          sum(
                                                              p.numPreemptions if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                          sum(p.numPreemptions if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    print("", file=fp)
    fp.close()


def RoundRobin(processes, contextSwitchTime, numCPUProc, timeLimit):
    print("time 0ms: Simulator started for RR [Q <empty>]")
    PM = manager(processes, numCPUProc)
    PM.activeProcess.numContextSwitches += 1

    PM.activeProcess.turnaroundTime.append(PM.activeProcess.arrivalTime)

    PM.activeProcess.reachedCPU[0] = True
    PM.activeProcess.status = Status.SWITCHING_IN
    PM.activeProcess.switchingTimer = contextSwitchTime / 2
    time = PM.activeProcess.arrivalTime
    print("time ", time, "ms: Process " + PM.activeProcess.id +
          " arrived; added to ready queue [Q "+PM.activeProcess.id+"]", sep='')
    done = False
    while (not done):

        # Updated running process
        if PM.activeProcess.status == Status.SWITCHING_IN:
            PM.activeProcess.timeRunning = 0
            if PM.activeProcess.switchingTimer == 0:
                PM.activeProcess.status = Status.RUNNING

                # time 28ms: Process C started using the CPU for 2920ms burst [Q <empty>]
                if time < 10000000:
                    if (PM.activeProcess.burstTimes[0][0] == PM.activeProcess.OGBurstTimes[0][0]):
                        print("time ", time, "ms: Process "+PM.activeProcess.id + " started using the CPU for ",
                              PM.activeProcess.burstTimes[0][0], "ms burst ", end="", sep='')
                    else:
                        print("time ", time, "ms: Process "+PM.activeProcess.id + " started using the CPU for remaining ", PM.activeProcess.burstTimes[0][0], "ms of ",
                              PM.activeProcess.OGBurstTimes[0][0], "ms burst ", end="", sep='')
                    PM.printQueue()
            else:
                PM.activeProcess.switchingTimer -= 1

        elif PM.activeProcess.status == Status.SWITCHING_OUT:
            if PM.activeProcess.switchingTimer == 0:
                if (PM.activeProcess.burstTimes[0][1] == 0 and PM.activeProcess.burstTimes[0][0] == 0):
                    PM.activeProcess.status = Status.TERMINATED
                else:
                    if PM.activeProcess.burstTimes[0][0] == 0:
                        PM.activeProcess.status = Status.WAITING
                    else:
                        # process was preempted
                        PM.activeProcess.status = Status.READY
                        heapq.heappush(PM.readyQueue, (time, PM.activeProcess))
                    if len(PM.readyQueue) != 0:
                        PM.activeProcess = PM.readyQueue[0][1]
                        PM.readyQueue.pop(0)
                        PM.activeProcess.turnaroundTime.append(time)

                        PM.activeProcess.numContextSwitches += 1
                        if not PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex]:
                            PM.activeProcess.turnaroundTime.append(time)

                        PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
                        PM.activeProcess.status = Status.SWITCHING_IN
                        PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
            else:
                PM.activeProcess.switchingTimer -= 1

        if (PM.activeProcess.status == Status.WAITING or PM.activeProcess.status == Status.READY or PM.activeProcess.status == Status.TERMINATED) and len(PM.readyQueue) != 0:
            PM.activeProcess = PM.readyQueue[0][1]
            PM.readyQueue.pop(0)
            if not PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex]:
                PM.activeProcess.turnaroundTime.append(time)

            PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
            PM.activeProcess.numContextSwitches += 1
            PM.activeProcess.status = Status.SWITCHING_IN
            PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1

        if PM.activeProcess.status == Status.RUNNING:
            PM.activeProcess.timeRunning += 1
            if PM.activeProcess.timeRunning > timeLimit:
                if len(PM.readyQueue) != 0:
                    # preempt
                    if time < 10000000:
                        print("time ", time, "ms: Time slice expired; preempting process ", PM.activeProcess.id,
                              " with ", PM.activeProcess.burstTimes[0][0], "ms remaining ", sep="", end="")
                        PM.printQueue()
                    PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
                    PM.activeProcess.status = Status.SWITCHING_OUT
                    PM.activeProcess.numPreemptions += 1
                else:
                    if time < 10000000:
                        print(
                            "time ", time, "ms: Time slice expired; no preemption because ready queue is empty [Q <empty>]", sep="")
                    PM.activeProcess.timeRunning = 1
                    PM.activeProcess.burstTimes[0][0] -= 1
            elif PM.activeProcess.burstTimes[0][0] == 0:

                if len(PM.activeProcess.burstTimes) == 1:
                    print("time ", time, "ms: Process ",
                          PM.activeProcess.id, " terminated ", sep="", end="")
                    PM.printQueue()
                elif time < 10000000:
                    if len(PM.activeProcess.burstTimes)-1 != 1:
                        print("time ", time, "ms: Process "+PM.activeProcess.id + " completed a CPU burst; ",
                              len(PM.activeProcess.burstTimes)-1, " bursts to go ", end="", sep='')
                    else:
                        print("time ", time, "ms: Process "+PM.activeProcess.id + " completed a CPU burst; ",
                              len(PM.activeProcess.burstTimes)-1, " burst to go ", end="", sep='')

                    PM.printQueue()
                    print("time ", time, "ms: Process " + PM.activeProcess.id + " switching out of CPU; blocking on I/O until time ",
                          (time + PM.activeProcess.burstTimes[0][1] + contextSwitchTime // 2), "ms ", end="", sep='')
                    PM.printQueue()

                if len(PM.activeProcess.burstTimes) != 1:
                    PM.activeProcess.turnaroundIndex += 1

                PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
                PM.activeProcess.status = Status.SWITCHING_OUT
            else:
                PM.activeProcess.burstTimes[0][0] -= 1

        # check for IO burst completions
        for p in PM.generatedProcesses:
            if p.status == Status.WAITING:
                if p.burstTimes[0][1] == 0:
                    p.burstTimes.pop(0)
                    p.OGBurstTimes.pop(0)
                    if len(PM.readyQueue) == 0 and PM.activeProcess.status != Status.RUNNING:
                        PM.activeProcess = p
                        PM.activeProcess.numContextSwitches += 1
                        if not PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex]:
                            PM.activeProcess.turnaroundTime.append(time)
                        PM.activeProcess.reachedCPU[PM.activeProcess.turnaroundIndex] = True
                        p.status = Status.SWITCHING_IN
                        p.switchingTimer = contextSwitchTime / 2 - 1
                        if time < 10000000:
                            print("time ", time, "ms: Process " + p.id +
                                  " completed I/O; added to ready queue ", end="", sep='')
                            print("[Q " + p.id + "]", sep='')
                    else:
                        p.status = Status.READY
                        heapq.heappush(PM.readyQueue, (time, p))
                    # time 3318ms: Process C completed I/O; added to ready queue [Q B C]
                        if time < 10000000:
                            print("time ", time, "ms: Process " + p.id +
                                  " completed I/O; added to ready queue ", end="", sep='')
                            PM.printQueue()
                else:
                    p.burstTimes[0][1] -= 1

        # Checks if new processes have arrived
        for p in PM.generatedProcesses:
            if p.status == Status.RUNNING:
                PM.busyTime += 1
            if p.status == Status.READY:
                p.waitTime += 1
            if p.status == Status.SWITCHING_IN or p.status == Status.SWITCHING_OUT or p.status == Status.RUNNING or p.status == Status.WAITING:
                p.turnaroundTime[p.turnaroundIndex] += 1

        for p in PM.generatedProcesses:
            if p.arrivalTime <= time and p.status == Status.UNARRIVED:
                heapq.heappush(PM.readyQueue, (time, p))
                if time < 10000000:
                    print("time ", time, "ms: Process " + p.id +
                          " arrived; added to ready queue ", end="", sep='')
                    PM.printQueue()
                p.status = Status.READY
        done = True
        for p in PM.generatedProcesses:
            if p.status != Status.TERMINATED:
                done = False

        time += 1 if not done else 0
    # time 324063ms: Simulator ended for FCFS [Q <empty>]
    print("time ", time, "ms: Simulator ended for RR [Q <empty>]", sep="")
    fn = "simout.txt"
    fp = open(fn, "a")
#     Algorithm FCFS
# -- CPU utilization: 84.253%
# -- average CPU burst time: 3067.776 ms (4071.000 ms/992.138 ms)
# -- average wait time: 779.663 ms (217.284 ms/1943.207 ms)
# -- average turnaround time: 3851.439 ms (4292.284 ms/2939.345 ms)
# -- number of context switches: 89 (60/29)
# -- number of preemptions: 0 (0/0)
# TODO: First number in parenthesis is for CPU-bound processes, the second is for IO-bound processes

    print("Algorithm RR", file=fp)
    print(
        "-- CPU utilization: {:.3f}%".format(round(PM.busyTime / time * 100)), file=fp)
    print("-- average CPU burst time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(
        round(PM.avgCPUBurst), round(PM.avgCPUProcBurst), round(PM.avgIOProcBurst)), file=fp)

    print("-- average wait time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(sum(p.waitTime for p in PM.generatedProcesses) / sum((p.numBursts+1)/2 for p in PM.generatedProcesses),
                                                                         sum(p.waitTime if p.isCPUBound else 0 for p in PM.generatedProcesses) / sum(
        (p.numBursts+1)/2 if p.isCPUBound else 0 for p in PM.generatedProcesses),
        sum(p.waitTime if not p.isCPUBound else 0 for p in PM.generatedProcesses) / sum((p.numBursts+1)/2 if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    turnarounds = PM.calculateTurnarounds()
    print("-- average turnaround time: {:.3f} ms ({:.3f} ms/{:.3f} ms)".format(
        turnarounds[0], turnarounds[1], turnarounds[2]), file=fp)
    print("-- number of context switches: {:d} ({:d}/{:d})".format(sum(p.numContextSwitches for p in PM.generatedProcesses),
                                                                   sum(
                                                                       p.numContextSwitches if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                                   sum(p.numContextSwitches if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    print("-- number of preemptions: {:d} ({}/{})".format(sum(p.numPreemptions for p in PM.generatedProcesses),
                                                          sum(
                                                              p.numPreemptions if p.isCPUBound else 0 for p in PM.generatedProcesses),
                                                          sum(p.numPreemptions if not p.isCPUBound else 0 for p in PM.generatedProcesses)), file=fp)
    fp.close()


def next_exp(lambda_: float, upperBound: int) -> int:
    num = upperBound
    while num > upperBound - 1:
        num = int(-math.log(randomizer.drand()) / lambda_)
    return num + 1


def partOneOutput(processes: List[Process], numCPUProc: int) -> int:
    print('<<< PROJECT PART I -- process set (n=' + str(len(processes)) + ') with ' +
          str(numCPUProc) + ' CPU-bound ' + ("process >>>" if numCPUProc == 1 else "processes >>>"))
    for i in range(len(processes)):
        print(('CPU-bound process ' if processes[i].isCPUBound else 'I/O-bound process ') + str(processes[i].id) + ': arrival time ' + str(
            processes[i].arrivalTime) + 'ms; ' + str(len(processes[i].burstTimes)) + (' CPU burst' if len(processes[i].burstTimes) == 1 else ' CPU bursts'))

    print()
    return 0


def main(argv):
    if len(argv) != 9:
        print('Error: Invalid number of command line arguments. Expected 8 arguments.')
        return 1
    numProc = int(argv[1])
    numCPUProc = int(argv[2])
    seed = int(argv[3])
    lambda_ = float(argv[4])
    upperBound = int(argv[5])
    contextSwitchTime = int(argv[6])
    alpha = float(argv[7])
    timeSlice = int(argv[8])

    if numProc < numCPUProc:
        return 2
    if numProc < 1 or numProc > 26:
        return 2
    if lambda_ <= 0:
        return 2

    randomizer.srand(seed)

    processes = []
    for i in range(numProc):
        p = Process()
        p.tau = math.ceil(1 / lambda_)
        p.isCPUBound = i >= numProc - numCPUProc
        p.id = chr(65 + i)
        p.arrivalTime = math.floor(next_exp(lambda_, upperBound)) - 1
        numCPUBursts = math.ceil(randomizer.drand() * 64)
        p.turnaroundTime = [0] * numCPUBursts
        p.reachedCPU = [False] * numCPUBursts
        p.numBursts = (numCPUBursts * 2) - 1
        if p.isCPUBound:
            for j in range(numCPUBursts - 1):
                p.burstTimes.append([math.ceil(next_exp(lambda_, upperBound)) * 4,
                                    math.ceil(next_exp(lambda_, upperBound)) * 10 // 8])

            p.burstTimes.append(
                [math.ceil(next_exp(lambda_, upperBound) * 4), 0])
        else:
            for j in range(numCPUBursts - 1):
                p.burstTimes.append([math.ceil(next_exp(lambda_, upperBound)),
                                    math.ceil(next_exp(lambda_, upperBound)) * 10])
            p.burstTimes.append([math.ceil(next_exp(lambda_, upperBound)), 0])
        p.OGBurstTimes = deepcopy(p.burstTimes)
        processes.append(p)

    partOneOutput(processes, numCPUProc)

    # <<< PROJECT PART II -- t_cs=4ms; alpha=0.75; t_slice=256ms >>>
    print("<<< PROJECT PART II -- t_cs=", contextSwitchTime,
          "ms; alpha=", alpha, "; t_slice=", timeSlice, "ms >>>", sep="")
    processes.sort(key=lambda Process: Process.arrivalTime)
    FirstComeFirstServe(deepcopy(processes), contextSwitchTime, numCPUProc)
    ShortestJobFirst(deepcopy(processes), contextSwitchTime, numCPUProc, alpha)
    RoundRobin(deepcopy(processes), contextSwitchTime, numCPUProc, timeSlice)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
