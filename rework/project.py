import sys
from copy import deepcopy

from generator import Generator
from cpu import CPU
from string import ascii_uppercase as process_id_set

# Define the expected command-line arguments
__ERROR_PROMPT__ = "python3 project.py <n_proc: int> <n_cpu: int> <seed: int> <lambda: float> <ubound: int> <tcs: int> <alpha: float> <tslice: int>"

if __name__ == '__main__':
    # Validate and parse command-line arguments
    if not len(sys.argv) == 9:
        print("ERROR: USAGE:", __ERROR_PROMPT__)
        exit(1)

    # Initialize runtime variables with default values
    numProc = 0
    numCPUProc = 0
    seed = 0
    lambda_ = 0.0
    upperBound = 0
    timeContextSwitch = 0
    alpha = 0
    timeSlice = 0

    # Parse and validate the number of processes
    try:
        numProc = int(sys.argv[1])
        if numProc < 1 or numProc > 26:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: n_processes should be an integer.")
        exit(1)

    # Parse and validate the number of CPU processes
    try:
        numCPUProc = int(sys.argv[2])
        if numCPUProc < 0 or numCPUProc > numProc:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: n_cpu should be an integer.")
        exit(1)

    # Parse and validate the random seed
    try:
        seed = int(sys.argv[3])
    except:
        print("ERROR: rand48_seed should be an integer.")
        exit(1)

    # Parse and validate the lambda value
    try:
        lambda_ = float(sys.argv[4])
        if lambda_ < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: exp_lambda should be a float/double.")
        exit(1)

    # Parse and validate the upper bound value
    try:
        upperBound = int(sys.argv[5])
        if upperBound < 1:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: exp_ubound should be an integer.")
        exit(1)

    # Parse and validate the time context switch value
    try:
        timeContextSwitch = int(sys.argv[6])
        if timeContextSwitch < 0 or timeContextSwitch % 2 == 1:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: tcs should be an integer")
        exit(1)

    # Parse and validate the alpha value
    try:
        alpha = float(sys.argv[7])
        if alpha < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: alpha should be float")
        exit(1)

    # Parse and validate the time slice value
    try:
        timeSlice = int(sys.argv[8])
        if timeSlice < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: tslice should be int")
        exit(1)

    # Ensure that the number of CPU processes does not exceed the total number of processes
    if numCPUProc > numProc:
        print("ERROR: n_proc >= n_cpu")
        exit(1)

    # Initialize the random process generator
    gen = Generator(lambda_, upperBound, seed)
    
    # Generate and store processes
    processes = []
    for i in range(numProc):
        isIOBound = i < numProc - numCPUProc
        p = gen.next_process(isIOBound, process_id_set[i])
        if p:
            processes.append(p)
        else:
            i -= 1

    # Display generated CPU-bound and I/O-bound processes
    print("<<< PROJECT PART I -- process set (n={}) with {} CPU-bound {} >>>".format(numProc, numCPUProc,
                                                                                     "process" if numCPUProc == 1 else "processes"))
    for i in range(len(processes)):
        print(processes[i])

    # Display configuration for scheduling algorithms
    print("\n<<< PROJECT PART II -- t_cs={}ms; alpha={:.2f}; t_slice={}ms >>>".format(timeContextSwitch, alpha, timeSlice))
    
    # Initialize CPU scheduler
    cpu = CPU(timeContextSwitch, lambda_, alpha)
    
    # Run scheduling algorithms and display results
    cpu.firstComeFirstServed(deepcopy(processes))
    print()
    cpu.shortestJobFirst(deepcopy(processes))
    print()
    cpu.shortestRemainingTime(deepcopy(processes))
    print()
    cpu.roundRobin(deepcopy(processes), timeSlice)
