
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
    n_processes = 0
    n_cpu = 0
    rand48_seed = 0
    exp_lambda = 0.0
    exp_ubound = 0
    tcs = 0
    alpha = 0
    tslice = 0

    try:
        n_processes = int(sys.argv[1])
        if n_processes < 1 or n_processes > 26:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: n_processes should be an integer.")
        exit(1)
    try:
        n_cpu = int(sys.argv[2])
        if n_cpu < 0 or n_cpu > n_processes:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: n_cpu should be an integer.")
        exit(1)
    try:
        rand48_seed = int(sys.argv[3])
    except:
        print("ERROR: rand48_seed should be an integer.")
        exit(1)
    try:
        exp_lambda = float(sys.argv[4])
        if exp_lambda < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: exp_lambda should be a float/double.")
        exit(1)
    try:
        exp_ubound = int(sys.argv[5])
        if exp_ubound < 1:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: exp_ubound should be an integer.")
        exit(1)
    try:
        tcs = int(sys.argv[6])
        if tcs < 0 or tcs % 2 == 1:
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
        tslice = int(sys.argv[8])
        if tslice < 0:
            print("ERROR: n_processes should be >= 1 <= 26")
            exit(1)
    except:
        print("ERROR: tslice should be int")
        exit(1)

    if n_cpu > n_processes:
        print("ERROR: n_proc >= n_cpu")
        exit(1)

    # rand
    gen1 = Generator(exp_lambda, exp_ubound, rand48_seed)
    processes1 = []
    for i in range(n_processes):
        io_bound = i < n_processes - n_cpu
        p1 = gen1.next_process(io_bound, process_id_set[i])
        if p1:
            processes1.append(p1)
        else:
            i -= 1

    print("<<< PROJECT PART I -- process set (n={}) with {} CPU-bound {} >>>".format(n_processes, n_cpu,
                                                                                     "process" if n_cpu == 1 else "processes"))
    for i in range(len(processes1)):
        print(processes1[i])

    print("\n<<< PROJECT PART II -- t_cs={}ms; alpha={:.2f}; t_slice={}ms >>>".format(tcs, alpha, tslice))
    # built processes array

    cpu = CPU(tcs, exp_lambda, alpha)

    # run algorithms
    cpu.fcfs(deepcopy(processes1))
    print()
    cpu.shortest_job_first(deepcopy(processes1))
    print()
    cpu.shortest_time_remaining(deepcopy(processes1))
    print()
    cpu.round_robin(deepcopy(processes1), tslice)
