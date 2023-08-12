from rand import Rand48
import math
from process import Process

class Generator(object):
    def __init__(self, lambda_: int, upperBound: int, seed: int):
        # Initialize the generator with the given parameters
        self.lambda_ = lambda_
        self.randomizer = Rand48()
        self.randomizer.srand(seed)
        self.upperBound = upperBound

    def next_exp(self) -> float:
        """
        Generates the next value from an exponential distribution.
        If the generated value is greater than the upper bound, new values are generated until a valid one is found.
        """
        num = self.upperBound
        while num > self.upperBound - 1:
            num = int(-math.log(self.randomizer.drand()) / self.lambda_)
        return num + 1

    def next_process(self, isIOBound: bool, id: str):
        """
        Generates a new process with specified arrival time, number of CPU bursts, and intervals between bursts.
        """
        # Generate the arrival time based on an exponential distribution
        arrivalTime = math.ceil(self.next_exp()) - 1
        
        # Generate the number of CPU bursts
        numCPUBursts = math.ceil(64 * self.randomizer.drand())
        
        intervals = []
        for _ in range(numCPUBursts - 1):
            # Generate burst and I/O wait times based on exponential distributions
            burstTime = math.ceil(self.next_exp())
            ioBurstTime = math.ceil(self.next_exp()) * 10
            
            if not isIOBound:
                # Adjust burst and I/O times for CPU-bound processes
                burstTime *= 4
                ioBurstTime //= 8
                
            # Append burst and I/O times to the intervals list
            intervals.append(burstTime)
            intervals.append(ioBurstTime)

        burstTime = math.ceil(self.next_exp())
        if not isIOBound:
            burstTime *= 4
        intervals.append(burstTime)

        # Return a new Process object with generated attributes
        return Process(arrivalTime, numCPUBursts, intervals, isIOBound, id)
