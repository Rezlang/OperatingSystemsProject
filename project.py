import math
import random
import sys
from typing import List, Tuple
from enum import Enum

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

class Status(Enum):
    UNARRIVED = -1
    READY = 0
    SWITCHING_IN = 1
    RUNNING = 2
    WAITING = 3
    SWITCHING_OUT = 4

class Process:
    def __init__(self):
        self.id = ''
        self.arrivalTime = 0
        self.burstTimes: List[List[int]] = []
        self.isCPUBound = False
        self.status = Status.UNARRIVED
        self.switchingTimer = 0

class manager:
    def __init__(self, processes):
        self.generatedProcesses: List[Process] = processes
        self.readyQueue: List[Process] = []
        self.activeProcess: Process = self.generatedProcesses[0]

def FirstComeFirstServe(processes, contextSwitchTime):
    print("time 0ms: Simulator started for FCFS [Q <empty>]")
    PM = manager(processes)
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
                print("time ", time, "ms: Process "+PM.activeProcess.id + " started using the CPU for ",
                      PM.activeProcess.burstTimes[0][0], "ms burst ", end="", sep='')

                if len(PM.readyQueue) != 0:
                    print("[Q ", " ".join(x.id for x in PM.readyQueue), "]", sep='')
                else:
                    print("[Q <empty>]")
            else:
                PM.activeProcess.switchingTimer -= 1

        elif PM.activeProcess.status == Status.SWITCHING_OUT:
            if PM.activeProcess.switchingTimer == 0:
                PM.activeProcess.status = Status.WAITING
                PM.activeProcess = PM.readyQueue[0]
                PM.readyQueue.pop(0)
                PM.activeProcess.status = Status.SWITCHING_IN
                PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
            else:
                PM.activeProcess.switchingTimer -= 1

        if PM.activeProcess.status == Status.RUNNING:
            if PM.activeProcess.burstTimes[0][0] == 0:
                print("time ", time, "ms: Process "+PM.activeProcess.id + " completed a CPU burst; ",
                      len(PM.activeProcess.burstTimes)-1, " bursts to go ", end="", sep='')

                if len(PM.readyQueue) != 0:
                    print(
                        "[Q " + " ".join(x.id for x in PM.readyQueue) + "]", sep='')
                else:
                    print("[Q <empty>]")

                print("time ", time, "ms: Process " + PM.activeProcess.id + " switching out of CPU; blocking on I/O until time ",
                      (time + PM.activeProcess.burstTimes[0][1]), "ms ", end="", sep='')
                if len(PM.readyQueue) != 0:
                    print(
                        "[Q " + " ".join(x.id for x in PM.readyQueue) + "]", sep='')
                else:
                    print("[Q <empty>]")

                PM.activeProcess.switchingTimer = contextSwitchTime / 2 - 1
                PM.activeProcess.status = Status.SWITCHING_OUT
            else:
                PM.activeProcess.burstTimes[0][0] -= 1

        # check for IO burst completions
        for p in PM.generatedProcesses:
            if p.status == Status.WAITING:
                if p.burstTimes[0][1] == 0:
                    p.status = Status.READY
                    p.burstTimes.pop(0)
                    PM.readyQueue.append(p)
                    # time 3318ms: Process C completed I/O; added to ready queue [Q B C]
                    print("time ", time, "ms: Process " + p.id +
                          " completed I/O; added to ready queue ", end="", sep='')
                    if len(PM.readyQueue) != 0:
                        print(
                            "[Q ", " ".join(x.id for x in PM.readyQueue), "]", sep='')
                    else:
                        print("[Q <empty>]")
                else:
                    p.burstTimes[0][1] -= 1

        # Checks if new processes have arrived
        for p in PM.generatedProcesses:
            if p.arrivalTime <= time and p.status == Status.UNARRIVED:
                PM.readyQueue.append(p)
                print("time ", time, "ms: Process " + p.id +
                      " arrived; added to ready queue [Q ", " ".join(x.id for x in PM.readyQueue), "]", sep='')
                p.status = Status.READY
        done = True
        for p in PM.generatedProcesses:
            if len(p.burstTimes) != 0:
                done = False

        time += 1

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
            processes[i].arrivalTime) + 'ms; ' + str(len(processes[i].burstTimes)) + (' CPU burst:' if len(processes[i].burstTimes) == 1 else ' CPU bursts:'))
    #     the below output is only for part I
    #     for j in range(len(processes[i].burstTimes)):
    #         if j != len(processes[i].burstTimes) - 1:
    #             print('--> CPU burst ' + str(processes[i].burstTimes[j][0]) +
    #                   'ms --> I/O burst ' + str(processes[i].burstTimes[j][1]) + 'ms')
    #         else:
    #             print('--> CPU burst ' +
    #                   str(processes[i].burstTimes[j][0]) + 'ms')
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
        p.isCPUBound = i >= numProc - numCPUProc
        p.id = chr(65 + i)
        p.arrivalTime = math.floor(next_exp(lambda_, upperBound)) - 1
        numCPUBursts = math.ceil(randomizer.drand() * 64)
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
        processes.append(p)

    partOneOutput(processes, numCPUProc)

    # <<< PROJECT PART II -- t_cs=4ms; alpha=0.75; t_slice=256ms >>>
    print("<<< PROJECT PART II -- t_cs=", contextSwitchTime,
          "ms; alpha=", alpha, "; t_slice=", timeSlice, "ms >>>", sep="")

    fcfsProcesses = sorted(processes, key=lambda Process: Process.arrivalTime)
    FirstComeFirstServe(fcfsProcesses, contextSwitchTime)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
