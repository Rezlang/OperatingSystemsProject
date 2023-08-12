from process import Process
from heapq import *


class CPU:
    def __init__(self, context_switch_time: int, lamda: float, alpha: float):
        self.__tcs__ = context_switch_time
        self.__arrivalqueue__ = []
        self.lamda = lamda
        self.alpha = alpha
        self.time = 0
        self.time_in_cpu = 0
        self.state = {}
        # Stores ready time, entry time, and exit time for each process
        self.preemption = 0
        self.simout = open("simout.txt", "w")

    def dec_ceil(self, num, places):
        s = str(num)
        rounded_s = str(round(num, places))
        # If the last digit of rounded_s is the same, then we did not round up
        if s[len(rounded_s) - 1] == rounded_s[-1]:
            return round(num, places) + 1 / (10 ** places)
        else:
            return round(num, places)

    def __savestats__(self, algo):
        self.simout.write("Algorithm {}\n".format(algo))
        # CPU Utilization
        self.simout.write("-- CPU Utilization: {:.3f}%\n".format(self.dec_ceil(100 * self.time_in_cpu / self.time, 3)))
        # Average cpu burst time stats
        total_cpu_bound_burst_time = 0
        total_io_bound_burst_time = 0
        total_bursts_cpu = 0
        total_bursts_io = 0
        total_cpu_burst_time = 0
        total_bursts = 0
        # Wait time stats
        wait_time_cpu_bound = 0
        wait_time_io_bound = 0
        turnaround_time_cpu = 0
        turnaround_time_io = 0
        cpu_bound_processes = 0
        context_switches_cpu = 0
        context_switches_io = 0
        preemptions_cpu = 0
        preemptions_io = 0
        for p in self.state:
            for i in range(len(self.state[p])):
                if p.io_bound:
                    total_io_bound_burst_time += sum(self.state[p][i]["EXIT"]) - sum(self.state[p][i]["ENTRY"])
                    wait_time_io_bound += sum(self.state[p][i]["ENTRY"]) - sum(self.state[p][i]["READY"]) - 2 * (
                        len(self.state[p][i]["ENTRY"]))
                    assert (len(self.state[p][i]["ENTRY"]) == len(self.state[p][i]["READY"]))
                    context_switches_io += len(self.state[p][i]["EXIT"])
                    turnaround_time_io += self.state[p][i]["EXIT"][-1] - self.state[p][i]["READY"][0] + 2
                    if i != len(self.state[p]) - 1:
                        preemptions_io += len(self.state[p][i]["EXIT"]) - 1

                else:
                    total_cpu_bound_burst_time += sum(self.state[p][i]["EXIT"]) - sum(self.state[p][i]["ENTRY"])
                    wait_time_cpu_bound += sum(self.state[p][i]["ENTRY"]) - sum(self.state[p][i]["READY"]) - 2 * (
                        len(self.state[p][i]["ENTRY"]))
                    context_switches_cpu += len(self.state[p][i]["EXIT"])
                    turnaround_time_cpu += self.state[p][i]["EXIT"][-1] - self.state[p][i]["READY"][0] + 2
                    if i != len(self.state[p]) - 1:
                        preemptions_cpu += len(self.state[p][i]["EXIT"]) - 1
            # Turnaround time (first ready to last exit)
            if not p.io_bound:
                cpu_bound_processes += 1
                total_bursts_cpu += p.cpu_bursts
            else:
                total_bursts_io += p.cpu_bursts

        total_cpu_burst_time = total_cpu_bound_burst_time + total_io_bound_burst_time
        total_bursts = total_bursts_cpu + total_bursts_io
        total_wait_time = wait_time_cpu_bound + wait_time_io_bound
        total_turnaround_time = turnaround_time_cpu + turnaround_time_io
        total_context_switches = context_switches_cpu + context_switches_io
        total_preemptions = preemptions_cpu + preemptions_io
        self.simout.write("-- average CPU burst time: {:.3f} ms ({:.3f}ms/{:.3f}ms)\n".format(
            self.dec_ceil(total_cpu_burst_time / total_bursts, 3),
            self.dec_ceil(total_cpu_bound_burst_time / total_bursts_cpu, 3),
            self.dec_ceil(total_io_bound_burst_time / total_bursts_io, 3)))
        self.simout.write("-- average wait time: {:.3f} ms ({:.3f}ms/{:.3f}ms)\n".format(
            self.dec_ceil(total_wait_time / total_bursts, 3), self.dec_ceil(wait_time_cpu_bound / total_bursts_cpu, 3),
            self.dec_ceil(wait_time_io_bound / total_bursts_io, 3)))
        self.simout.write("-- average turnaround time: {:.3f} ms ({:.3f}ms/{:.3f}ms)\n".format(
            self.dec_ceil(total_turnaround_time / total_bursts, 3),
            self.dec_ceil(turnaround_time_cpu / total_bursts_cpu, 3),
            self.dec_ceil(turnaround_time_io / total_bursts_io, 3)))
        self.simout.write(
            "-- number of context switches: {} ({},{})\n".format(total_context_switches, context_switches_cpu,
                                                                 context_switches_io))
        self.simout.write(
            "-- number of preemptions: {} ({},{})\n".format(total_preemptions, preemptions_cpu, preemptions_io))

    def __printreadyqueue__(self, rdyq: list):
        if len(rdyq) == 0:
            return "[Q <empty>]"
        return "[Q " + " ".join([p[2].pid for p in sorted(rdyq, key=lambda x: (x[2].this_tau(), x[2].pid))]) + "]"

    def __printreadyqueueFCFS__(self, rdyq: list):
        if len(rdyq) == 0:
            return "[Q <empty>]"
        return "[Q " + " ".join([p.pid for p in rdyq]) + "]"

    def round_robin(self, process_list: list, quantum: int):
        print("time {}ms: Simulator started for RR {}".format(0, self.__printreadyqueue__([])))
        [p.compute_predicted(self.lamda, self.alpha) for p in process_list]
        for p in process_list:
            self.state[p] = []
            for i in range(p.cpu_bursts):
                self.state[p].append({})
                self.state[p][i]["READY"] = []
                self.state[p][i]["ENTRY"] = []
                self.state[p][i]["EXIT"] = []
        arrival_q = sorted(process_list, key=lambda p: (p.arrival_time, p.pid), reverse=True)
        ready_q = []
        current_process = None
        next_quantum = 0
        while current_process or len(arrival_q) != 0 or len(ready_q) != 0:
            # Get next arrivals if at the next arrival time
            if len(arrival_q) > 0 and self.time == arrival_q[-1].arrival_time:
                next_arrivals = self.get_next_arrivals(arrival_q)
                self.time = next_arrivals[0].arrival_time
                # Add all to the ready queue and pre-empt curent process has been in for longer tha the quantum
                for p in next_arrivals:
                    ready_q.append(p)
                    if p.burst_index == 0:
                        print("time {}ms: Process {} arrived; added to ready queue {}".format(p.arrival_time, p.pid,
                                                                                              self.__printreadyqueueFCFS__(
                                                                                                  ready_q))) if self.time <= 9999 else None
                    else:
                        print(
                            "time {}ms: Process {} completed I/O; added to ready queue {}".format(p.arrival_time, p.pid,
                                                                                                  self.__printreadyqueueFCFS__(
                                                                                                      ready_q))) if self.time <= 9999 else None
                    self.state[p][p.burst_index]["READY"].append(self.time)
                    # Go to next arrival time if nothing is in the ready queue and there is no current process
            if len(ready_q) == 0 and not current_process:
                next_arrivals = self.get_next_arrivals(arrival_q)
                self.time = next_arrivals[0].arrival_time
                # Add all to the ready queue and pre-empt curent process has been in for longer tha the quantum
                for p in next_arrivals:
                    ready_q.append(p)
                    if p.burst_index == 0:
                        print("time {}ms: Process {} arrived; added to ready queue {}".format(p.arrival_time, p.pid,
                                                                                              self.__printreadyqueueFCFS__(
                                                                                                  ready_q))) if self.time <= 9999 else None
                    else:
                        print(
                            "time {}ms: Process {} completed I/O; added to ready queue {}".format(p.arrival_time, p.pid,
                                                                                                  self.__printreadyqueueFCFS__(
                                                                                                      ready_q))) if self.time <= 9999 else None
                    self.state[p][p.burst_index]["READY"].append(self.time)
                    # Context switch in next process
                self.time += self.__tcs__ // 2
                current_process = ready_q.pop(0)
                if current_process.this_burst() == current_process.this_og_burst():
                    print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                 current_process.pid,
                                                                                                 current_process.this_burst(),
                                                                                                 self.__printreadyqueueFCFS__(
                                                                                                     ready_q))) if self.time <= 9999 else None
                else:
                    print("time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst {}".format(
                        self.time, current_process.pid, current_process.this_burst(), current_process.this_og_burst(),
                        self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                next_quantum = self.time + quantum
            elif not current_process:
                # Context switch in next process
                self.time += self.__tcs__ // 2
                current_process = ready_q.pop(0)
                if current_process.this_burst() == current_process.this_og_burst():
                    print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                 current_process.pid,
                                                                                                 current_process.this_burst(),
                                                                                                 self.__printreadyqueueFCFS__(
                                                                                                     ready_q))) if self.time <= 9999 else None
                else:
                    print("time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst {}".format(
                        self.time, current_process.pid, current_process.this_burst(), current_process.this_og_burst(),
                        self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                next_quantum = self.time + quantum
            # Current process cannot be None at this point
            # Run current process until next quantum or next arrival
            if len(arrival_q) == 0 or next_quantum <= arrival_q[-1].arrival_time:
                run_time = next_quantum - self.time
                self.time = min(next_quantum, self.time + current_process.this_burst())
                current_process.run(run_time)
                # Check if process will complete before end of next quantum
                if current_process.this_burst() <= 0:
                    # Process finishes using the CPU and context switches with the next process
                    io_wait_time = current_process.this_io()
                    current_process.complete_this_burst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not current_process.done():
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                        current_process.pid,
                                                                                                        current_process.remaining_bursts(),
                                                                                                        "s" if current_process.remaining_bursts() > 1 else "",
                                                                                                        self.__printreadyqueueFCFS__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                            self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(arrival_q) - 1
                        while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                                current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                                arrival_q[i].pid)):
                            i -= 1
                        arrival_q.insert(i + 1, current_process)
                    else:
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                           self.__printreadyqueueFCFS__(ready_q)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    current_process = None
                else:
                    if len(ready_q) == 0:
                        print(
                            'time {}ms: Time slice expired; no preemption because ready queue is empty [Q <empty>]'.format(
                                self.time)) if self.time <= 9999 else None
                    else:
                        # Pre-empt and put in next process
                        print("time {}ms: Time slice expired; preempting process {} with {}ms remaining {}".format(
                            self.time, current_process.pid, current_process.this_burst(),
                            self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                        self.state[current_process][current_process.burst_index]["EXIT"].append(self.time)
                        # Context switch out
                        self.time += self.__tcs__ // 2
                        ready_q.append(current_process)
                        self.state[current_process][current_process.burst_index]["READY"].append(self.time)
                        current_process = None
                        # Context switch in the new process
                        self.time += self.__tcs__ // 2
                        current_process = ready_q.pop(0)
                        if current_process.this_burst() == current_process.this_og_burst():
                            print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                         current_process.pid,
                                                                                                         current_process.this_burst(),
                                                                                                         self.__printreadyqueueFCFS__(
                                                                                                             ready_q))) if self.time <= 9999 else None
                        else:
                            print(
                                "time {}ms: Process {} started using the CPU for remaining {}ms of {}ms burst {}".format(
                                    self.time, current_process.pid, current_process.this_burst(),
                                    current_process.this_og_burst(),
                                    self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                        self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                    next_quantum = self.time + quantum
            else:
                run_time = arrival_q[-1].arrival_time - self.time
                self.time = min(arrival_q[-1].arrival_time, self.time + current_process.this_burst())
                current_process.run(run_time)
                # Check if process will complete before end of next quantum
                if current_process.this_burst() <= 0:
                    # Process finishes using the CPU and context switches with the next process
                    io_wait_time = current_process.this_io()
                    current_process.complete_this_burst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not current_process.done():
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                        current_process.pid,
                                                                                                        current_process.remaining_bursts(),
                                                                                                        "s" if current_process.remaining_bursts() > 1 else "",
                                                                                                        self.__printreadyqueueFCFS__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                            self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(arrival_q) - 1
                        while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                                current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                                arrival_q[i].pid)):
                            i -= 1
                        arrival_q.insert(i + 1, current_process)
                    else:
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                           self.__printreadyqueueFCFS__(ready_q)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    current_process = None
                else:
                    self.time = arrival_q[-1].arrival_time
        print("time {}ms: Simulator ended for RR [Q <empty>]".format(self.time))
        self.__savestats__("RR")
        self.state = {}
        self.time = 0

    def fcfs(self, process_list: list):
        print("time {}ms: Simulator started for FCFS {}".format(0, self.__printreadyqueueFCFS__([])))
        [p.compute_predicted(self.lamda, self.alpha) for p in process_list]
        arrival_q = sorted(process_list, key=lambda p: (p.arrival_time, p.pid), reverse=True)
        for p in process_list:
            self.state[p] = []
            for i in range(p.cpu_bursts):
                self.state[p].append({})
                self.state[p][i]["READY"] = []
                self.state[p][i]["ENTRY"] = []
                self.state[p][i]["EXIT"] = []
        ready_q = []
        current_process = None
        next_burst_completion = 2 ** 32
        while current_process or len(arrival_q) != 0 or len(ready_q) != 0:
            # Get all arrivals while before the next burst completion
            if len(arrival_q) > 0:
                while len(arrival_q) > 0 and arrival_q[-1].arrival_time <= next_burst_completion:
                    # Get next set of arrivals
                    next_arrivals = self.get_next_arrivals(arrival_q)
                    self.time = next_arrivals[0].arrival_time
                    # Add all arrivals to ready q
                    for p in next_arrivals:
                        ready_q.append(p)
                        if p.burst_index == 0:
                            print("time {}ms: Process {} arrived; added to ready queue {}".format(p.arrival_time, p.pid,
                                                                                                  self.__printreadyqueueFCFS__(
                                                                                                      ready_q))) if self.time <= 9999 else None
                        else:
                            print("time {}ms: Process {} completed I/O; added to ready queue {}".format(p.arrival_time,
                                                                                                        p.pid,
                                                                                                        self.__printreadyqueueFCFS__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                        self.state[p][p.burst_index]["READY"].append(self.time)
                    if not current_process:
                        # Context switch in as soon as the process arrives if nothing is in the CPU
                        self.time += self.__tcs__ // 2
                        current_process = ready_q.pop(0)
                        self.time_in_cpu += current_process.this_burst()
                        next_burst_completion = self.time + current_process.this_burst()
                        print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                                     current_process.pid,
                                                                                                     current_process.this_burst(),
                                                                                                     self.__printreadyqueueFCFS__(
                                                                                                         ready_q))) if self.time <= 9999 else None
                        self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                        # Complete this burst if there is a current process
                if current_process:
                    # Process finishes using the CPU and context switches with the next process
                    self.time = next_burst_completion
                    old_tau = current_process.this_og_tau()
                    io_wait_time = current_process.this_io()
                    current_process.complete_this_burst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not current_process.done():
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                        current_process.pid,
                                                                                                        current_process.remaining_bursts(),
                                                                                                        "s" if current_process.remaining_bursts() > 1 else "",
                                                                                                        self.__printreadyqueueFCFS__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                            self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(arrival_q) - 1
                        while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                                current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                                arrival_q[i].pid)):
                            i -= 1
                        arrival_q.insert(i + 1, current_process)
                    else:
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                           self.__printreadyqueueFCFS__(ready_q)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    current_process = None
            elif current_process:
                # Process finishes using the CPU and context switches with the next process
                self.time = next_burst_completion
                old_tau = current_process.this_og_tau()
                io_wait_time = current_process.this_io()
                current_process.complete_this_burst()
                # If this process is not finished, put somewhere in the arrival q
                if not current_process.done():
                    self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                    # Indicate that this process has completed its burst
                    print("time {}ms: Process {} completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                    current_process.pid,
                                                                                                    current_process.remaining_bursts(),
                                                                                                    "s" if current_process.remaining_bursts() > 1 else "",
                                                                                                    self.__printreadyqueueFCFS__(
                                                                                                        ready_q))) if self.time <= 9999 else None
                    # Context switch out of the cpu
                    print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                        self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                        self.__printreadyqueueFCFS__(ready_q))) if self.time <= 9999 else None
                    # Set new arrival time for process
                    current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                    # Search for new chronological spot in arrival q from end
                    i = len(arrival_q) - 1
                    while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                            current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                            arrival_q[i].pid)):
                        i -= 1
                    arrival_q.insert(i + 1, current_process)
                else:
                    self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                    print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                       self.__printreadyqueueFCFS__(ready_q)))
                # Context switch out of CPU
                self.time += self.__tcs__ // 2
                current_process = None

            # Place next process in CPU
            if len(ready_q) > 0:
                self.time += self.__tcs__ // 2
                current_process = ready_q.pop(0)
                next_burst_completion = self.time + current_process.this_burst()
                print("time {}ms: Process {} started using the CPU for {}ms burst {}".format(self.time,
                                                                                             current_process.pid,
                                                                                             current_process.this_burst(),
                                                                                             self.__printreadyqueueFCFS__(
                                                                                                 ready_q))) if self.time <= 9999 else None
                self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                self.time_in_cpu += current_process.this_burst()
            else:
                next_burst_completion = 2 ** 32
        print("time {}ms: Simulator ended for FCFS [Q <empty>]".format(self.time))
        # Write stats to simout.txt
        self.__savestats__("FCFS")
        self.state = {}
        self.time = 0

    def get_next_arrivals(self, arrival_q):
        next_arrivals = []
        next_arrival_time = arrival_q[-1].arrival_time
        while len(arrival_q) > 0 and arrival_q[-1].arrival_time == next_arrival_time:
            next_arrivals.append(arrival_q.pop())
        return next_arrivals

    def add_to_ready_q(self, processes, ready_q):
        for p in processes:
            heappush(ready_q, (p.this_tau(), p.pid, p))

    def shortest_job_first(self, process_list: list):
        print("time {}ms: Simulator started for SJF {}".format(0, self.__printreadyqueue__([])))
        [p.compute_predicted(self.lamda, self.alpha) for p in process_list]
        for p in process_list:
            self.state[p] = []
            for i in range(p.cpu_bursts):
                self.state[p].append({})
                self.state[p][i]["READY"] = []
                self.state[p][i]["ENTRY"] = []
                self.state[p][i]["EXIT"] = []
        arrival_q = sorted(process_list, key=lambda p: (p.arrival_time, p.pid), reverse=True)
        ready_q = []
        current_process = None
        next_burst_completion = 2 ** 32
        while current_process or len(arrival_q) != 0 or len(ready_q) != 0:
            # Get all arrivals while before the next burst completion
            if len(arrival_q) > 0:
                while len(arrival_q) > 0 and arrival_q[-1].arrival_time < next_burst_completion:
                    # Get next set of arrivals
                    next_arrivals = self.get_next_arrivals(arrival_q)
                    self.time = next_arrivals[0].arrival_time
                    # Add all arrivals to ready q
                    for p in next_arrivals:
                        heappush(ready_q, (p.this_tau(), p.pid, p))
                        if p.burst_index == 0:
                            print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue {}".format(
                                p.arrival_time, p.pid, p.this_tau(),
                                self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        else:
                            print("time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue {}".format(
                                p.arrival_time, p.pid, p.this_tau(),
                                self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                    self.state[p][p.burst_index]["READY"].append(self.time)
                    if not current_process:
                        # Context switch in as soon as the process arrives if nothing is in the CPU
                        self.time += self.__tcs__ // 2
                        _, _, current_process = heappop(ready_q)
                        next_burst_completion = self.time + current_process.this_burst()
                        print(
                            "time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                              current_process.pid,
                                                                                                              current_process.this_tau(),
                                                                                                              current_process.this_burst(),
                                                                                                              self.__printreadyqueue__(
                                                                                                                  ready_q))) if self.time <= 9999 else None
                        self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                        # Complete this burst if there is a current process
                if current_process:
                    # Process finishes using the CPU and context switches with the next process
                    self.time = next_burst_completion
                    old_tau = current_process.this_og_tau()
                    io_wait_time = current_process.this_io()
                    current_process.complete_this_burst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not current_process.done():
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(
                            self.time, current_process.pid, old_tau, current_process.remaining_bursts(),
                            "s" if current_process.remaining_bursts() > 1 else "",
                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        # Compute a new tau value
                        print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                            self.time, current_process.pid, old_tau, current_process.this_tau(),
                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(arrival_q) - 1
                        while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                                current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                                arrival_q[i].pid)):
                            i -= 1
                        arrival_q.insert(i + 1, current_process)
                        if len(arrival_q) > 0 and arrival_q[-1].arrival_time == self.time:
                            # Get next set of arrivals
                            next_arrivals = self.get_next_arrivals(arrival_q)
                            self.time = next_arrivals[0].arrival_time
                            # Add all arrivals to ready q
                            for p in next_arrivals:
                                heappush(ready_q, (p.this_tau(), p.pid, p))
                                if p.burst_index == 0:
                                    print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue {}".format(
                                        p.arrival_time, p.pid, p.this_tau(),
                                        self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                                else:
                                    print(
                                        "time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue {}".format(
                                            p.arrival_time, p.pid, p.this_tau(),
                                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                                self.state[p][p.burst_index]["READY"].append(self.time)

                    else:
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                           self.__printreadyqueue__(ready_q)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    current_process = None
            elif current_process:
                # Process finishes using the CPU and context switches with the next process
                self.time = next_burst_completion
                old_tau = current_process.this_og_tau()
                io_wait_time = current_process.this_io()
                current_process.complete_this_burst()
                # If this process is not finished, put somewhere in the arrival q
                if not current_process.done():
                    self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                    # Indicate that this process has completed its burst
                    print(
                        "time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                             current_process.pid,
                                                                                                             old_tau,
                                                                                                             current_process.remaining_bursts(),
                                                                                                             "s" if current_process.remaining_bursts() > 1 else "",
                                                                                                             self.__printreadyqueue__(
                                                                                                                 ready_q))) if self.time <= 9999 else None
                    # Compute a new tau value
                    print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                        self.time, current_process.pid, old_tau, current_process.this_tau(),
                        self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                    # Context switch out of the cpu
                    print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                        self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                        self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                    # Set new arrival time for process
                    current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                    # Search for new chronological spot in arrival q from end
                    i = len(arrival_q) - 1
                    while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                            current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                            arrival_q[i].pid)):
                        i -= 1
                    arrival_q.insert(i + 1, current_process)
                else:
                    self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                    print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                       self.__printreadyqueue__(ready_q)))
                # Context switch out of CPU
                self.time += self.__tcs__ // 2
                current_process = None

            # Place next process in CPU
            if len(ready_q) > 0:
                self.time += self.__tcs__ // 2
                # Check for arrivals
                _, _, current_process = heappop(ready_q)
                next_burst_completion = self.time + current_process.this_burst()
                print("time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                        current_process.pid,
                                                                                                        current_process.this_tau(),
                                                                                                        current_process.this_burst(),
                                                                                                        self.__printreadyqueue__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
            else:
                next_burst_completion = 2 ** 32

        print("time {}ms: Simulator ended for SJF [Q <empty>]".format(self.time))
        self.__savestats__("SJF")
        self.state = {}
        self.time = 0

    def shortest_time_remaining(self, process_list: list):
        print("time {}ms: Simulator started for SRT {}".format(0, self.__printreadyqueue__([])))
        [p.compute_predicted(self.lamda, self.alpha) for p in process_list]
        arrival_q = sorted(process_list, key=lambda p: (p.arrival_time, p.pid), reverse=True)
        for p in process_list:
            self.state[p] = []
            for i in range(p.cpu_bursts):
                self.state[p].append({})
                self.state[p][i]["READY"] = []
                self.state[p][i]["ENTRY"] = []
                self.state[p][i]["EXIT"] = []
        ready_q = []
        current_process = None
        next_burst_completion = 2 ** 32
        while current_process or len(arrival_q) != 0 or len(ready_q) != 0:
            # Get all arrivals while before the next burst completion
            if len(arrival_q) > 0:
                while len(arrival_q) > 0 and arrival_q[-1].arrival_time <= next_burst_completion:
                    # Get next set of arrivals
                    next_arrivals = self.get_next_arrivals(arrival_q)
                    self.time = next_arrivals[0].arrival_time
                    if current_process:
                        current_process.run(current_process.this_burst() - (next_burst_completion - self.time))
                    # Add all arrivals to ready q and consider pre-emption
                    preempted = False
                    for p in next_arrivals:
                        heappush(ready_q, (p.this_tau(), p.pid, p))
                        if current_process and not preempted and (p.this_tau() < current_process.this_tau() or (
                                p.this_tau() == current_process.this_tau() and p.pid < current_process.pid)):
                            # Pre-empt the current process
                            preempted = True
                            if p.burst_index == 0:
                                print(
                                    "time {}ms: Process {} (tau {}ms) arrived; preempting {} {}".format(p.arrival_time,
                                                                                                        p.pid,
                                                                                                        p.this_tau(),
                                                                                                        current_process.pid,
                                                                                                        self.__printreadyqueue__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                            else:
                                print("time {}ms: Process {} (tau {}ms) completed I/O; preempting {} {}".format(
                                    p.arrival_time, p.pid, p.this_tau(), current_process.pid,
                                    self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        else:
                            if p.burst_index == 0:
                                print("time {}ms: Process {} (tau {}ms) arrived; added to ready queue {}".format(
                                    p.arrival_time, p.pid, p.this_tau(),
                                    self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                            else:
                                print("time {}ms: Process {} (tau {}ms) completed I/O; added to ready queue {}".format(
                                    p.arrival_time, p.pid, p.this_tau(),
                                    self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        self.state[p][p.burst_index]["READY"].append(self.time)
                    if preempted:
                        # Accunt for context switch from former process during preemption
                        self.state[current_process][current_process.burst_index]["EXIT"].append(self.time)
                        heappush(ready_q, (current_process.this_tau(), current_process.pid, current_process))
                        self.state[current_process][current_process.burst_index]["READY"].append(
                            self.time + self.__tcs__ // 2)
                        current_process = None
                        self.time += self.__tcs__ // 2
                    if not current_process:
                        # Context switch in as soon as the process arrives if nothing is in the CPU
                        self.time += self.__tcs__ // 2
                        _, _, current_process = heappop(ready_q)
                        next_burst_completion = self.time + current_process.this_burst()
                        print(
                            "time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                              current_process.pid,
                                                                                                              current_process.this_tau(),
                                                                                                              current_process.this_burst(),
                                                                                                              self.__printreadyqueue__(
                                                                                                                  ready_q))) if self.time <= 9999 else None
                        self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
                        # Complete this burst if there is a current process
                if current_process:
                    # Process finishes using the CPU and context switches with the next process
                    self.time = next_burst_completion
                    old_tau = current_process.this_og_tau()
                    io_wait_time = current_process.this_io()
                    current_process.complete_this_burst()
                    # If this process is not finished, put somewhere in the arrival q
                    if not current_process.done():
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        # Indicate that this process has completed its burst
                        print("time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(
                            self.time, current_process.pid, old_tau, current_process.remaining_bursts(),
                            "s" if current_process.remaining_bursts() > 1 else "",
                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        # Compute a new tau value
                        print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                            self.time, current_process.pid, old_tau, current_process.this_tau(),
                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        # Context switch out of the cpu
                        print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                            self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                            self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                        # Set new arrival time for process
                        current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                        # Search for new chronological spot in arrival q from end
                        i = len(arrival_q) - 1
                        while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                                current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                                arrival_q[i].pid)):
                            i -= 1
                        arrival_q.insert(i + 1, current_process)
                    else:
                        self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                        print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                           self.__printreadyqueue__(ready_q)))
                    # Context switch out of CPU
                    self.time += self.__tcs__ // 2
                    current_process = None
            elif current_process:
                # Process finishes using the CPU and context switches with the next process
                self.time = next_burst_completion
                old_tau = current_process.this_og_tau()
                io_wait_time = current_process.this_io()
                current_process.complete_this_burst()
                # If this process is not finished, put somewhere in the arrival q
                if not current_process.done():
                    self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                    # Indicate that this process has completed its burst
                    print(
                        "time {}ms: Process {} (tau {}ms) completed a CPU burst; {} burst{} to go {}".format(self.time,
                                                                                                             current_process.pid,
                                                                                                             old_tau,
                                                                                                             current_process.remaining_bursts(),
                                                                                                             "s" if current_process.remaining_bursts() > 1 else "",
                                                                                                             self.__printreadyqueue__(
                                                                                                                 ready_q))) if self.time <= 9999 else None
                    # Compute a new tau value
                    print("time {}ms: Recalculating tau for process {}: old tau {}ms ==> new tau {}ms {}".format(
                        self.time, current_process.pid, old_tau, current_process.this_tau(),
                        self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                    # Context switch out of the cpu
                    print("time {}ms: Process {} switching out of CPU; blocking on I/O until time {}ms {}".format(
                        self.time, current_process.pid, self.time + self.__tcs__ // 2 + io_wait_time,
                        self.__printreadyqueue__(ready_q))) if self.time <= 9999 else None
                    # Set new arrival time for process
                    current_process.arrival_time = self.time + io_wait_time + self.__tcs__ // 2
                    # Search for new chronological spot in arrival q from end
                    i = len(arrival_q) - 1
                    while i >= 0 and (current_process.arrival_time > arrival_q[i].arrival_time or (
                            current_process.arrival_time == arrival_q[i].arrival_time and current_process.pid >
                            arrival_q[i].pid)):
                        i -= 1
                    arrival_q.insert(i + 1, current_process)
                else:
                    self.state[current_process][current_process.burst_index - 1]["EXIT"].append(self.time)
                    print("time {}ms: Process {} terminated {}".format(self.time, current_process.pid,
                                                                       self.__printreadyqueue__(ready_q)))
                # Context switch out of CPU
                self.time += self.__tcs__ // 2
                current_process = None

            # Place next process in CPU
            if len(ready_q) > 0:
                self.time += self.__tcs__ // 2
                _, _, current_process = heappop(ready_q)
                next_burst_completion = self.time + current_process.this_burst()
                print("time {}ms: Process {} (tau {}ms) started using the CPU for {}ms burst {}".format(self.time,
                                                                                                        current_process.pid,
                                                                                                        current_process.this_tau(),
                                                                                                        current_process.this_burst(),
                                                                                                        self.__printreadyqueue__(
                                                                                                            ready_q))) if self.time <= 9999 else None
                self.state[current_process][current_process.burst_index]["ENTRY"].append(self.time)
            else:
                next_burst_completion = 2 ** 32
        print("time {}ms: Simulator ended for SRT [Q <empty>]".format(self.time))
        self.__savestats__("SRT")
        self.state = {}
        self.time = 0
