
import sys
from copy import deepcopy

from generator import Generator
from cpu import CPU
from string import ascii_uppercase as process_id_set

__ERROR_PROMPT__ = "python3 project.py <n_proc: int> <n_cpu: int> <seed: int> <lambda: float> <ubound: int> <tcs: int> <alpha: float> <tslice: int>"

if __name__ == '__main__':
    # exec arg validation
    if not len(sys.argv) == 9:
        print("ERROR: USAGE:", __ERROR_PROMPT__)
        exit(1)

    # Runtime vars
    numProc = 0
    numCPUProc = 0
    seed = 0
    lambda_ = 0.0
    upperBound = 0
    timeContextSwitch = 0
    alpha = 0
    timeSlice = 0

    try:
        numProc = int(sys.argv[1])
        if numProc < 1 or numProc > 26:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: n_processes should be an integer.")
        exit(1)
    try:
        numCPUProc = int(sys.argv[2])
        if numCPUProc < 0 or numCPUProc > numProc:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: n_cpu should be an integer.")
        exit(1)
    try:
        seed = int(sys.argv[3])
    except:
        print("ERROR: rand48_seed should be an integer.")
        exit(1)
    try:
        lambda_ = float(sys.argv[4])
        if lambda_ < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: exp_lambda should be a float/double.")
        exit(1)
    try:
        upperBound = int(sys.argv[5])
        if upperBound < 1:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: exp_ubound should be an integer.")
        exit(1)
    try:
        timeContextSwitch = int(sys.argv[6])
        if timeContextSwitch < 0 or timeContextSwitch % 2 == 1:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: tcs should be an integer")
        exit(1)

    try:
        alpha = float(sys.argv[7])
        if alpha < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: alpha should be float")
        exit(1)

    try:
        timeSlice = int(sys.argv[8])
        if timeSlice < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: tslice should be int")
        exit(1)

    if numCPUProc > numProc:
        print("ERROR: n_proc >= n_cpu")
        exit(1)

    # rand
    gen = Generator(lambda_, upperBound, seed)
    processes = []
    for i in range(numProc):
        isIOBound = i < numProc - numCPUProc
        p = gen.next_process(isIOBound, process_id_set[i])
        if p:
            processes.append(p)
        else:
            i -= 1

    print("<<< PROJECT PART I -- process set (n={}) with {} CPU-bound {} >>>".format(numProc, numCPUProc,
                                                                                     "process" if numCPUProc == 1 else "processes"))
    for i in range(len(processes)):
        print(processes[i])

    print("\n<<< PROJECT PART II -- t_cs={}ms; alpha={:.2f}; t_slice={}ms >>>".format(timeContextSwitch, alpha, timeSlice))
    # built processes array

    cpu = CPU(timeContextSwitch, lambda_, alpha)

    # run algorithms
    cpu.firstComeFirstServed(deepcopy(processes))
    print()
    cpu.shortestJobFirst(deepcopy(processes))
    print()
    cpu.shortestRemainingTime(deepcopy(processes))
    print()
    cpu.roundRobin(deepcopy(processes), timeSlice)
