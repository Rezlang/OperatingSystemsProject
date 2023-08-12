from process import Process
from heapq import *
import math

class CPU:
    def __init__(self, timeCS: int, lambda_: float, alpha: float):
        self.__tcs__: int = timeCS
        self.unarrived: list = []
        self.lambda_: float = lambda_
        self.alpha: float = alpha
        self.time: int = 0
        self.busyTime: int = 0
        self.status = {}
        # Stores ready time, entry time, and exit time for each process
        self.preemption:int = 0
        self.simout = open("simout.txt", "w")

    def roundStats(self, num, places):
        return math.ceil(num * 1000) / 1000

    def writeStats(self, algo):
        self.simout.write("Algorithm {}\n".format(algo))
        # CPU Utilization
        self.simout.write("-- CPU utilization: {:.3f}%\n".format(self.roundStats(100 * self.busyTime / self.time, 3)))
        # Average cpu burst time stats
        cpuBoundBurstTime = 0
        ioBoundBurstTime = 0
        numCPUBursts = 0
        numIOBursts = 0
        CPUBurstTime = 0
        numBursts = 0
        # Wait time stats
        cpuBoundWaitTime = 0
        ioBoundWaitTime = 0
        cpuBoundTurnaroundTime = 0
        ioBoundTurnaroundTime = 0
        numCPUProc = 0
        cpuBoundCS = 0
        ioBoundCS = 0
        cpuBoundPreemption = 0
        ioBoundPreemption = 0

        p: Process
        for p in self.status:
            for i in range(len(self.status[p])):
                if p.isIOBound:
                    ioBoundBurstTime += sum(self.status[p][i]["EXIT"]) - sum(self.status[p][i]["ENTRY"])
                    ioBoundWaitTime += sum(self.status[p][i]["ENTRY"]) - sum(self.status[p][i]["READY"]) - 2 * (
                        len(self.status[p][i]["ENTRY"]))
                    assert (len(self.status[p][i]["ENTRY"]) == len(self.status[p][i]["READY"]))
                    ioBoundCS += len(self.status[p][i]["EXIT"])
                    ioBoundTurnaroundTime += self.status[p][i]["EXIT"][-1] - self.status[p][i]["READY"][0] + 2
                    if i != len(self.status[p]) - 1:
                        ioBoundPreemption += len(self.status[p][i]["EXIT"]) - 1

                else:
                    cpuBoundBurstTime += sum(self.status[p][i]["EXIT"]) - sum(self.status[p][i]["ENTRY"])
                    cpuBoundWaitTime += sum(self.status[p][i]["ENTRY"]) - sum(self.status[p][i]["READY"]) - 2 * (
                        len(self.status[p][i]["ENTRY"]))
                    cpuBoundCS += len(self.status[p][i]["EXIT"])
                    cpuBoundTurnaroundTime += self.status[p][i]["EXIT"][-1] - self.status[p][i]["READY"][0] + 2
                    if i != len(self.status[p]) - 1:
                        cpuBoundPreemption += len(self.status[p][i]["EXIT"]) - 1
            # Turnaround time (first ready to last exit)
            if not p.isIOBound:
                numCPUProc += 1
                numCPUBursts += p.numCPUBursts
            else:
                numIOBursts += p.numCPUBursts

        CPUBurstTime = cpuBoundBurstTime + ioBoundBurstTime
        numBursts = numCPUBursts + numIOBursts
        waitTime = cpuBoundWaitTime + ioBoundWaitTime
        turnaroundTime = cpuBoundTurnaroundTime + ioBoundTurnaroundTime
        numContextSwitches = cpuBoundCS + ioBoundCS
        numPreemptions = cpuBoundPreemption + ioBoundPreemption
        self.simout.write("-- average CPU burst time: {:.3f} ms ({:.3f} ms/{:.3f} ms)\n".format(
            self.roundStats(CPUBurstTime / numBursts, 3),
            self.roundStats(cpuBoundBurstTime / numCPUBursts, 3),
            self.roundStats(ioBoundBurstTime / numIOBursts, 3)))
        self.simout.write("-- average wait time: {:.3f} ms ({:.3f} ms/{:.3f} ms)\n".format(
            self.roundStats(waitTime / numBursts, 3), self.roundStats(cpuBoundWaitTime / numCPUBursts, 3),
            self.roundStats(ioBoundWaitTime / numIOBursts, 3)))
        self.simout.write("-- average turnaround time: {:.3f} ms ({:.3f} ms/{:.3f} ms)\n".format(
            self.roundStats(turnaroundTime / numBursts, 3),
            self.roundStats(cpuBoundTurnaroundTime / numCPUBursts, 3),
            self.roundStats(ioBoundTurnaroundTime / numIOBursts, 3)))
        self.simout.write(
            "-- number of context switches: {} ({}/{})\n".format(numContextSwitches, cpuBoundCS,
                                                                 ioBoundCS))
        self.simout.write(
            "-- number of preemptions: {} ({}/{})\n".format(numPreemptions, cpuBoundPreemption, ioBoundPreemption))

    def printQueue(self, q: list):
        if len(q) == 0:
            return "[Q <empty>]"
        return "[Q " + " ".join([p[2].id for p in sorted(q, key=lambda x: (x[2].currentTau(), x[2].id))]) + "]"

    def printFCFS(self, q: list):
        if len(q) == 0:
            return "[Q <empty>]"
        return "[Q " + " ".join([p.id for p in q]) + "]"

    def roundRobin(self, processes: list, currEventTime: int):
        print("time {}ms: Simulator started for RR {}".format(0, self.printQueue([])))
        
        [p.calcTau(self.lambda_, self.alpha) for p in processes]
        p: Process
        for p in processes:
            self.status[p] = []
            for i in range(p.numCPUBursts):
                self.status[p].append({})
                self.status[p][i]["READY"] = []
                self.status[p][i]["ENTRY"] = []
                self.status[p][i]["EXIT"] = []
        unarrived = sorted(processes, key=lambda p: (p.arrivalTime, p.id), reverse=True)
        readyQueue = []
        activeProcess = None
        nextEventTime = 0
        while activeProcess or len(unarrived) != 0 or len(readyQueue) != 0:
            # Get next arrivals if at the next arrival time
            if len(unarrived) > 0 and self.time == unarrived[-1].arrivalTime:
                incomingProcesses = self.getIncomingProcesses(unarrived)
                self.time = incomingProcesses[0].arrivalTime
                # Add all to the ready queue and pre-empt curent process has been in for longer tha the quantum
                for p in incomingProcesses:
                    readyQueue.append(p)
                    if p.burstIndex == 0:
                        print("time {}ms: Process {} arrived; added to ready queue {}".format(p.arrivalTime, p.id,
                                                                                              self.printFCFS(
                                                                                                  readyQueue))) if self.time <= 9999 else None
                    else:
                        print(
                            "time {}ms: Process {} completed I/O; added to ready queue {}".format(p.arrivalTime, p.id,
                                                                                                  self.printFCFS(
                                                                                                      readyQueue))) if self.time <= 9999 else None
                    self.status[p][p.burstIndex]["READY"].append(self.time)
                    # Go to next arrival time if nothing is in the ready queue and there is no current process
            if len(readyQueue) == 0 and not activeProcess:
                incomingProcesses = self.getIncomingProcesses(unarrived)
                self.time = incomingProcesses[0].arrivalTime
                # Add all to the ready queue and pre-empt curent process has been in for longer tha the quantum
                for p in incomingProcesses:
                    readyQueue.append(p)
                    if p.burstIndex == 0:
                        print("time {}ms: Process {} arrived; added to ready queue {}".format(p.arrivalTime, p.id,
                                                                                              self.printFCFS(
                                                                                                  readyQueue))) if self.time <= 9999 else None
                    else:
                        print(
                            "time {}ms: Process {} completed I/O; added to ready queue {}".format(p.arrivalTime, p.id,
                                                                                                  self.printFCFS(
                                                                                                      readyQueue))) if self.time <= 9999 else None
                    self.status[p][p.burstIndex]["READY"].append(self.time)
                    # Context switch in next process
                self.time += self.__tcs__ // 2
                activeProcess = readyQueue.pop(0)
                if activeProcess.currentBurst() == activeProcess.currentOGBurst():
                    print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                 activeProcess.id,
                                                                                                 activeProcess.currentBurst(),
                                                                                                 self.printFCFS(
                                                                                                     readyQueue))) if self.time <= 9999 else None
                else:
                    print("time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst {}".format(
                        self.time, activeProcess.id, activeProcess.currentBurst(), activeProcess.currentOGBurst(),
                        self.printFCFS(readyQueue))) if self.time <= 9999 else None
                self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                nextEventTime = self.time + currEventTime
            elif not activeProcess:
                # Context switch in next process
                self.time += self.__tcs__ // 2
                activeProcess = readyQueue.pop(0)
                if activeProcess.currentBurst() == activeProcess.currentOGBurst():
                    print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                 activeProcess.id,
                                                                                                 activeProcess.currentBurst(),
                                                                                                 self.printFCFS(
                                                                                                     readyQueue))) if self.time <= 9999 else None
                else:
                    print("time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst {}".format(
                        self.time, activeProcess.id, activeProcess.currentBurst(), activeProcess.currentOGBurst(),
                        self.printFCFS(readyQueue))) if self.time <= 9999 else None
                self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                nextEventTime = self.time + currEventTime
            # Current process cannot be None at this point
            # run__ current process until next quantum or next arrival
            if len(unarrived) == 0 or nextEventTime <= unarrived[-1].arrivalTime:
                busyTime = nextEventTime - self.time
                self.time = min(nextEventTime, self.time + activeProcess.currentBurst())
                activeProcess.run__(busyTime)
                # Check if process will complete before end of next quantum
                if activeProcess.currentBurst() <= 0:
                    # Process finishes using the CPU and context switches with the next process
                    ioBoundWaitTime = activeProcess.currentIOBurst()
                    activeProcess.finishBurst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not activeProcess.finished():
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                        activeProcess.id,
                                                                                                        activeProcess.burstsRemaining(),
                                                                                                        "s" if activeProcess.burstsRemaining() > 1 else "",
                                                                                                        self.printFCFS(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBoundWaitTime,
                            self.printFCFS(readyQueue))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        activeProcess.arrivalTime = self.time + ioBoundWaitTime + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(unarrived) - 1
                        while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                                activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                                unarrived[i].id)):
                            i -= 1
                        unarrived.insert(i + 1, activeProcess)
                    else:
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                           self.printFCFS(readyQueue)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    activeProcess = None
                else:
                    if len(readyQueue) == 0:
                        print(
                            'time {}ms: Time slice expired; no preemption because ready queue is empty [Q <empty>]'.format(
                                self.time)) if self.time <= 9999 else None
                    else:
                        # Pre-empt and put in next process
                        print("time {}ms: Time slice expired; preempting process {} with {}ms remaining {}".format(
                            self.time, activeProcess.id, activeProcess.currentBurst(),
                            self.printFCFS(readyQueue))) if self.time <= 9999 else None
                        self.status[activeProcess][activeProcess.burstIndex]["EXIT"].append(self.time)
                        # Context switch out
                        self.time += self.__tcs__ // 2
                        readyQueue.append(activeProcess)
                        self.status[activeProcess][activeProcess.burstIndex]["READY"].append(self.time)
                        activeProcess = None
                        # Context switch in the new process
                        self.time += self.__tcs__ // 2
                        activeProcess = readyQueue.pop(0)
                        if activeProcess.currentBurst() == activeProcess.currentOGBurst():
                            print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                         activeProcess.id,
                                                                                                         activeProcess.currentBurst(),
                                                                                                         self.printFCFS(
                                                                                                             readyQueue))) if self.time <= 9999 else None
                        else:
                            print(
                                "time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst {}".format(
                                    self.time, activeProcess.id, activeProcess.currentBurst(),
                                    activeProcess.currentOGBurst(),
                                    self.printFCFS(readyQueue))) if self.time <= 9999 else None
                        self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                    nextEventTime = self.time + currEventTime
            else:
                busyTime = unarrived[-1].arrivalTime - self.time
                self.time = min(unarrived[-1].arrivalTime, self.time + activeProcess.currentBurst())
                activeProcess.run__(busyTime)
                # Check if process will complete before end of next quantum
                if activeProcess.currentBurst() <= 0:
                    # Process finishes using the CPU and context switches with the next process
                    ioBoundWaitTime = activeProcess.currentIOBurst()
                    activeProcess.finishBurst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not activeProcess.finished():
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                        activeProcess.id,
                                                                                                        activeProcess.burstsRemaining(),
                                                                                                        "s" if activeProcess.burstsRemaining() > 1 else "",
                                                                                                        self.printFCFS(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBoundWaitTime,
                            self.printFCFS(readyQueue))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        activeProcess.arrivalTime = self.time + ioBoundWaitTime + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(unarrived) - 1
                        while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                                activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                                unarrived[i].id)):
                            i -= 1
                        unarrived.insert(i + 1, activeProcess)
                    else:
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                           self.printFCFS(readyQueue)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    activeProcess = None
                else:
                    self.time = unarrived[-1].arrivalTime
        print("time {}ms: Simulator ended for RR [Q <empty>]".format(self.time))
        self.writeStats("RR")
        self.status = {}
        self.time = 0

    def firstComeFirstServed(self, processes: list):
        print("time {}ms: Simulator started for FCFS {}".format(0, self.printFCFS([])))
        [p.calcTau(self.lambda_, self.alpha) for p in processes]
        unarrived = sorted(processes, key=lambda p: (p.arrivalTime, p.id), reverse=True)
        for p in processes:
            self.status[p] = []
            for i in range(p.numCPUBursts):
                self.status[p].append({})
                self.status[p][i]["READY"] = []
                self.status[p][i]["ENTRY"] = []
                self.status[p][i]["EXIT"] = []
        readyQueue = []
        activeProcess = None
        nextBurstEnd = 2 ** 32
        while activeProcess or len(unarrived) != 0 or len(readyQueue) != 0:
            # Get all arrivals while before the next burst completion
            if len(unarrived) > 0:
                while len(unarrived) > 0 and unarrived[-1].arrivalTime <= nextBurstEnd:
                    # Get next set of arrivals
                    incomingProcesses = self.getIncomingProcesses(unarrived)
                    self.time = incomingProcesses[0].arrivalTime
                    # Add all arrivals to ready q
                    for p in incomingProcesses:
                        readyQueue.append(p)
                        if p.burstIndex == 0:
                            print("time {}ms: Process {} arrived; added to ready queue {}".format(p.arrivalTime, p.id,
                                                                                                  self.printFCFS(
                                                                                                      readyQueue))) if self.time <= 9999 else None
                        else:
                            print("time {}ms: Process {} completed I/O; added to ready queue {}".format(p.arrivalTime,
                                                                                                        p.id,
                                                                                                        self.printFCFS(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                        self.status[p][p.burstIndex]["READY"].append(self.time)
                    if not activeProcess:
                        # Context switch in as soon as the process arrives if nothing is in the CPU
                        self.time += self.__tcs__ // 2
                        activeProcess = readyQueue.pop(0)
                        self.busyTime += activeProcess.currentBurst()
                        nextBurstEnd = self.time + activeProcess.currentBurst()
                        print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                     activeProcess.id,
                                                                                                     activeProcess.currentBurst(),
                                                                                                     self.printFCFS(
                                                                                                         readyQueue))) if self.time <= 9999 else None
                        self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                        # Complete this burst if there is a current process
                if activeProcess:
                    # Process finishes using the CPU and context switches with the next process
                    self.time = nextBurstEnd
                    ioBoundWaitTime = activeProcess.currentIOBurst()
                    activeProcess.finishBurst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not activeProcess.finished():
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                        activeProcess.id,
                                                                                                        activeProcess.burstsRemaining(),
                                                                                                        "s" if activeProcess.burstsRemaining() > 1 else "",
                                                                                                        self.printFCFS(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBoundWaitTime,
                            self.printFCFS(readyQueue))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        activeProcess.arrivalTime = self.time + ioBoundWaitTime + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(unarrived) - 1
                        while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                                activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                                unarrived[i].id)):
                            i -= 1
                        unarrived.insert(i + 1, activeProcess)
                    else:
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                           self.printFCFS(readyQueue)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    activeProcess = None
            elif activeProcess:
                # Process finishes using the CPU and context switches with the next process
                self.time = nextBurstEnd
                ioBoundWaitTime = activeProcess.currentIOBurst()
                activeProcess.finishBurst()
                # If this process is not finished, put somewhere in the arrival q
                if not activeProcess.finished():
                    self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                    # Indicate that this process has completed its burst
                    print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                    activeProcess.id,
                                                                                                    activeProcess.burstsRemaining(),
                                                                                                    "s" if activeProcess.burstsRemaining() > 1 else "",
                                                                                                    self.printFCFS(
                                                                                                        readyQueue))) if self.time <= 9999 else None
                    # Context switch out of the cpu
                    print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                        self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBoundWaitTime,
                        self.printFCFS(readyQueue))) if self.time <= 9999 else None
                    # Set new arrival time for process
                    activeProcess.arrivalTime = self.time + ioBoundWaitTime + self.__tcs__ // 2
                    # Search for new chronological spot in arrival q from end
                    i = len(unarrived) - 1
                    while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                            activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                            unarrived[i].id)):
                        i -= 1
                    unarrived.insert(i + 1, activeProcess)
                else:
                    self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                    print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                       self.printFCFS(readyQueue)))
                # Context switch out of CPU
                self.time += self.__tcs__ // 2
                activeProcess = None

            # Place next process in CPU
            if len(readyQueue) > 0:
                self.time += self.__tcs__ // 2
                activeProcess = readyQueue.pop(0)
                nextBurstEnd = self.time + activeProcess.currentBurst()
                print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                             activeProcess.id,
                                                                                             activeProcess.currentBurst(),
                                                                                             self.printFCFS(
                                                                                                 readyQueue))) if self.time <= 9999 else None
                self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                self.busyTime += activeProcess.currentBurst()
            else:
                nextBurstEnd = 2 ** 32
        print("time {}ms: Simulator ended for FCFS [Q <empty>]".format(self.time))
        # Write stats to simout.txt
        self.writeStats("FCFS")
        self.status = {}
        self.time = 0

    def getIncomingProcesses(self, q):
        incomingProcesses = []
        nextProcessArrival = q[-1].arrivalTime
        while len(q) > 0 and q[-1].arrivalTime == nextProcessArrival:
            incomingProcesses.append(q.pop())
        return incomingProcesses

    def addReadyProcess(self, processes, q):
        for p in processes:
            heappush(q, (p.currentTau(), p.id, p))

    def shortestJobFirst(self, processes: list):
        print("time {}ms: Simulator started for SJF {}".format(0, self.printQueue([])))
        [p.calcTau(self.lambda_, self.alpha) for p in processes]
        for p in processes:
            self.status[p] = []
            for i in range(p.numCPUBursts):
                self.status[p].append({})
                self.status[p][i]["READY"] = []
                self.status[p][i]["ENTRY"] = []
                self.status[p][i]["EXIT"] = []
        unarrived = sorted(processes, key=lambda p: (p.arrivalTime, p.id), reverse=True)
        readyQueue = []
        activeProcess = None
        nextBurstEnd = 2 ** 32
        while activeProcess or len(unarrived) != 0 or len(readyQueue) != 0:
            # Get all arrivals while before the next burst completion
            if len(unarrived) > 0:
                while len(unarrived) > 0 and unarrived[-1].arrivalTime < nextBurstEnd:
                    # Get next set of arrivals
                    incomingProcesses = self.getIncomingProcesses(unarrived)
                    self.time = incomingProcesses[0].arrivalTime
                    # Add all arrivals to ready q
                    for p in incomingProcesses:
                        heappush(readyQueue, (p.currentTau(), p.id, p))
                        if p.burstIndex == 0:
                            print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue {}".format(
                                p.arrivalTime, p.id, p.currentTau(),
                                self.printQueue(readyQueue))) if self.time <= 9999 else None
                        else:
                            print("time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue {}".format(
                                p.arrivalTime, p.id, p.currentTau(),
                                self.printQueue(readyQueue))) if self.time <= 9999 else None
                    self.status[p][p.burstIndex]["READY"].append(self.time)
                    if not activeProcess:
                        # Context switch in as soon as the process arrives if nothing is in the CPU
                        self.time += self.__tcs__ // 2
                        _, _, activeProcess = heappop(readyQueue)
                        nextBurstEnd = self.time + activeProcess.currentBurst()
                        print(
                            "time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                              activeProcess.id,
                                                                                                              activeProcess.currentTau(),
                                                                                                              activeProcess.currentBurst(),
                                                                                                              self.printQueue(
                                                                                                                  readyQueue))) if self.time <= 9999 else None
                        self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                        # Complete this burst if there is a current process
                if activeProcess:
                    # Process finishes using the CPU and context switches with the next process
                    self.time = nextBurstEnd
                    oldTau = activeProcess.currentOGTau()
                    ioBurstWaitTime = activeProcess.currentIOBurst()
                    activeProcess.finishBurst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not activeProcess.finished():
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(
                            self.time, activeProcess.id, oldTau, activeProcess.burstsRemaining(),
                            "s" if activeProcess.burstsRemaining() > 1 else "",
                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                        # Compute a new tau value
                        print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                            self.time, activeProcess.id, oldTau, activeProcess.currentTau(),
                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBurstWaitTime,
                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        activeProcess.arrivalTime = self.time + ioBurstWaitTime + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(unarrived) - 1
                        while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                                activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                                unarrived[i].id)):
                            i -= 1
                        unarrived.insert(i + 1, activeProcess)
                        if len(unarrived) > 0 and unarrived[-1].arrivalTime == self.time:
                            # Get next set of arrivals
                            incomingProcesses = self.getIncomingProcesses(unarrived)
                            self.time = incomingProcesses[0].arrivalTime
                            # Add all arrivals to ready q
                            for p in incomingProcesses:
                                heappush(readyQueue, (p.currentTau(), p.id, p))
                                if p.burstIndex == 0:
                                    print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue {}".format(
                                        p.arrivalTime, p.id, p.currentTau(),
                                        self.printQueue(readyQueue))) if self.time <= 9999 else None
                                else:
                                    print(
                                        "time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue {}".format(
                                            p.arrivalTime, p.id, p.currentTau(),
                                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                                self.status[p][p.burstIndex]["READY"].append(self.time)

                    else:
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                           self.printQueue(readyQueue)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    activeProcess = None
            elif activeProcess:
                # Process finishes using the CPU and context switches with the next process
                self.time = nextBurstEnd
                oldTau = activeProcess.currentOGTau()
                ioBurstWaitTime = activeProcess.currentIOBurst()
                activeProcess.finishBurst()
                # If this process is not finished, put somewhere in the arrival q
                if not activeProcess.finished():
                    self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                    # Indicate that this process has completed its burst
                    print(
                        "time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                             activeProcess.id,
                                                                                                             oldTau,
                                                                                                             activeProcess.burstsRemaining(),
                                                                                                             "s" if activeProcess.burstsRemaining() > 1 else "",
                                                                                                             self.printQueue(
                                                                                                                 readyQueue))) if self.time <= 9999 else None
                    # Compute a new tau value
                    print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                        self.time, activeProcess.id, oldTau, activeProcess.currentTau(),
                        self.printQueue(readyQueue))) if self.time <= 9999 else None
                    # Context switch out of the cpu
                    print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                        self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBurstWaitTime,
                        self.printQueue(readyQueue))) if self.time <= 9999 else None
                    # Set new arrival time for process
                    activeProcess.arrivalTime = self.time + ioBurstWaitTime + self.__tcs__ // 2
                    # Search for new chronological spot in arrival q from end
                    i = len(unarrived) - 1
                    while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                            activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                            unarrived[i].id)):
                        i -= 1
                    unarrived.insert(i + 1, activeProcess)
                else:
                    self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                    print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                       self.printQueue(readyQueue)))
                # Context switch out of CPU
                self.time += self.__tcs__ // 2
                activeProcess = None

            # Place next process in CPU
            if len(readyQueue) > 0:
                self.time += self.__tcs__ // 2
                # Check for arrivals
                _, _, activeProcess = heappop(readyQueue)
                nextBurstEnd = self.time + activeProcess.currentBurst()
                print("time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                        activeProcess.id,
                                                                                                        activeProcess.currentTau(),
                                                                                                        activeProcess.currentBurst(),
                                                                                                        self.printQueue(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
            else:
                nextBurstEnd = 2 ** 32

        print("time {}ms: Simulator ended for SJF [Q <empty>]".format(self.time))
        self.writeStats("SJF")
        self.status = {}
        self.time = 0

    def shortestRemainingTime(self, process_list: list):
        print("time {}ms: Simulator started for SRT {}".format(0, self.printQueue([])))
        [p.calcTau(self.lambda_, self.alpha) for p in process_list]
        unarrived = sorted(process_list, key=lambda p: (p.arrivalTime, p.id), reverse=True)
        for p in process_list:
            self.status[p] = []
            for i in range(p.numCPUBursts):
                self.status[p].append({})
                self.status[p][i]["READY"] = []
                self.status[p][i]["ENTRY"] = []
                self.status[p][i]["EXIT"] = []
        readyQueue = []
        activeProcess = None
        nextBurstEnd = 2 ** 32
        while activeProcess or len(unarrived) != 0 or len(readyQueue) != 0:
            # Get all arrivals while before the next burst completion
            if len(unarrived) > 0:
                while len(unarrived) > 0 and unarrived[-1].arrivalTime <= nextBurstEnd:
                    # Get next set of arrivals
                    incomingProcesses = self.getIncomingProcesses(unarrived)
                    self.time = incomingProcesses[0].arrivalTime
                    if activeProcess:
                        activeProcess.run__(activeProcess.currentBurst() - (nextBurstEnd - self.time))
                    # Add all arrivals to ready q and consider pre-emption
                    preempted = False
                    for p in incomingProcesses:
                        heappush(readyQueue, (p.currentTau(), p.id, p))
                        if activeProcess and not preempted and (p.currentTau() < activeProcess.currentTau() or (
                                p.currentTau() == activeProcess.currentTau() and p.id < activeProcess.id)):
                            # Pre-empt the current process
                            preempted = True
                            if p.burstIndex == 0:
                                print(
                                    "time {}ms: Process {} (tau {}ms) arrived; preempting {} {}".format(p.arrivalTime,
                                                                                                        p.id,
                                                                                                        p.currentTau(),
                                                                                                        activeProcess.id,
                                                                                                        self.printQueue(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                            else:
                                print("time {}ms: Process {} (tau {}ms) completed I/O; preempting {} {}".format(
                                    p.arrivalTime, p.id, p.currentTau(), activeProcess.id,
                                    self.printQueue(readyQueue))) if self.time <= 9999 else None
                        else:
                            if p.burstIndex == 0:
                                print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue {}".format(
                                    p.arrivalTime, p.id, p.currentTau(),
                                    self.printQueue(readyQueue))) if self.time <= 9999 else None
                            else:
                                print("time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue {}".format(
                                    p.arrivalTime, p.id, p.currentTau(),
                                    self.printQueue(readyQueue))) if self.time <= 9999 else None
                        self.status[p][p.burstIndex]["READY"].append(self.time)
                    if preempted:
                        # Accunt for context switch from former process during preemption
                        self.status[activeProcess][activeProcess.burstIndex]["EXIT"].append(self.time)
                        heappush(readyQueue, (activeProcess.currentTau(), activeProcess.id, activeProcess))
                        self.status[activeProcess][activeProcess.burstIndex]["READY"].append(
                            self.time + self.__tcs__ // 2)
                        activeProcess = None
                        self.time += self.__tcs__ // 2
                    if not activeProcess:
                        # Context switch in as soon as the process arrives if nothing is in the CPU
                        self.time += self.__tcs__ // 2
                        _, _, activeProcess = heappop(readyQueue)
                        nextBurstEnd = self.time + activeProcess.currentBurst()
                        if activeProcess.currentBurst() == activeProcess.currentOGBurst():
                            print(
                                "time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                                activeProcess.id,
                                                                                                                activeProcess.currentTau(),
                                                                                                                activeProcess.currentBurst(),
                                                                                                                self.printQueue(
                                                                                                                    readyQueue))) if self.time <= 9999 else None
                        else:
                            print(
                                "time {}ms: Process {} (tau {}ms) started using the CPU for remaining {}ms of {}ms burst {}".format(self.time,
                                                                                                                activeProcess.id,
                                                                                                                activeProcess.currentTau(),
                                                                                                                activeProcess.currentBurst(),
                                                                                                                activeProcess.currentOGBurst(),
                                                                                                                self.printQueue(
                                                                                                                    readyQueue))) if self.time <= 9999 else None
                        self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
                        # Complete this burst if there is a current process
                if activeProcess:
                    # Process finishes using the CPU and context switches with the next process
                    self.time = nextBurstEnd
                    oldTau = activeProcess.currentOGTau()
                    ioBurstWaitTime = activeProcess.currentIOBurst()
                    activeProcess.finishBurst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not activeProcess.finished():
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(
                            self.time, activeProcess.id, oldTau, activeProcess.burstsRemaining(),
                            "s" if activeProcess.burstsRemaining() > 1 else "",
                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                        # Compute a new tau value
                        print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                            self.time, activeProcess.id, oldTau, activeProcess.currentTau(),
                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBurstWaitTime,
                            self.printQueue(readyQueue))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        activeProcess.arrivalTime = self.time + ioBurstWaitTime + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(unarrived) - 1
                        while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                                activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                                unarrived[i].id)):
                            i -= 1
                        unarrived.insert(i + 1, activeProcess)
                    else:
                        self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                           self.printQueue(readyQueue)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    activeProcess = None
            elif activeProcess:
                # Process finishes using the CPU and context switches with the next process
                self.time = nextBurstEnd
                oldTau = activeProcess.currentOGTau()
                ioBurstWaitTime = activeProcess.currentIOBurst()
                activeProcess.finishBurst()
                # If this process is not finished, put somewhere in the arrival q
                if not activeProcess.finished():
                    self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                    # Indicate that this process has completed its burst
                    print(
                        "time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                             activeProcess.id,
                                                                                                             oldTau,
                                                                                                             activeProcess.burstsRemaining(),
                                                                                                             "s" if activeProcess.burstsRemaining() > 1 else "",
                                                                                                             self.printQueue(
                                                                                                                 readyQueue))) if self.time <= 9999 else None
                    # Compute a new tau value
                    print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                        self.time, activeProcess.id, oldTau, activeProcess.currentTau(),
                        self.printQueue(readyQueue))) if self.time <= 9999 else None
                    # Context switch out of the cpu
                    print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                        self.time, activeProcess.id, self.time + self.__tcs__ // 2 + ioBurstWaitTime,
                        self.printQueue(readyQueue))) if self.time <= 9999 else None
                    # Set new arrival time for process
                    activeProcess.arrivalTime = self.time + ioBurstWaitTime + self.__tcs__ // 2
                    # Search for new chronological spot in arrival q from end
                    i = len(unarrived) - 1
                    while i >= 0 and (activeProcess.arrivalTime > unarrived[i].arrivalTime or (
                            activeProcess.arrivalTime == unarrived[i].arrivalTime and activeProcess.id >
                            unarrived[i].id)):
                        i -= 1
                    unarrived.insert(i + 1, activeProcess)
                else:
                    self.status[activeProcess][activeProcess.burstIndex - 1]["EXIT"].append(self.time)
                    print("time {}ms: Process {} terminated {}".format(self.time, activeProcess.id,
                                                                       self.printQueue(readyQueue)))
                # Context switch out of CPU
                self.time += self.__tcs__ // 2
                activeProcess = None

            # Place next process in CPU
            if len(readyQueue) > 0:
                self.time += self.__tcs__ // 2
                _, _, activeProcess = heappop(readyQueue)
                nextBurstEnd = self.time + activeProcess.currentBurst()
                if activeProcess.currentBurst() == activeProcess.currentOGBurst():
                    print(
                        "time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                        activeProcess.id,
                                                                                                        activeProcess.currentTau(),
                                                                                                        activeProcess.currentBurst(),
                                                                                                        self.printQueue(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                else:
                    print(
                        "time {}ms: Process {} (tau {}ms) started using the CPU for remaining {}ms of {}ms burst {}".format(self.time,
                                                                                                        activeProcess.id,
                                                                                                        activeProcess.currentTau(),
                                                                                                        activeProcess.currentBurst(),
                                                                                                        activeProcess.currentOGBurst(),
                                                                                                        self.printQueue(
                                                                                                            readyQueue))) if self.time <= 9999 else None
                self.status[activeProcess][activeProcess.burstIndex]["ENTRY"].append(self.time)
            else:
                nextBurstEnd = 2 ** 32
        print("time {}ms: Simulator ended for SRT [Q <empty>]".format(self.time))
        self.writeStats("SRT")
        self.status = {}
        self.time = 0
