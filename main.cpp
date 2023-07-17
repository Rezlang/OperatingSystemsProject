#include <math.h>

#include <cstdlib>
#include <iostream>
#include <utility>
#include <vector>

struct process {
  process() {}
  char id;
  int arrivalTime;
  std::vector<std::pair<int, int>*> burstTimes;
  bool isCPUBound;
};

inline double next_exp(float lambda, int upperBound) {
  int num = upperBound;
  while (num > upperBound - 1) num = -log(drand48()) / lambda;
  return num + 1;
}

/* <<< PROJECT PART I -- process set (n=3) with 1 CPU-bound process >>>
I/O-bound process A: arrival time 136ms; 17 CPU bursts:
--> CPU burst 1330ms --> I/O burst 5740ms
--> CPU burst 735ms --> I/O burst 660ms
--> CPU burst 24ms --> I/O burst 450ms
--> CPU burst 683ms --> I/O burst 1850ms
--> CPU burst 1100ms --> I/O burst 14220ms
--> CPU burst 1000ms --> I/O burst 6950ms
--> CPU burst 1166ms --> I/O burst 5290ms
--> CPU burst 1561ms --> I/O burst 2820ms
--> CPU burst 149ms --> I/O burst 720ms
--> CPU burst 388ms --> I/O burst 7370ms
--> CPU burst 34ms --> I/O burst 9540ms
--> CPU burst 954ms --> I/O burst 9960ms
--> CPU burst 236ms --> I/O burst 17010ms
--> CPU burst 734ms --> I/O burst 5850ms
--> CPU burst 1124ms --> I/O burst 19640ms
--> CPU burst 62ms --> I/O burst 2350ms
--> CPU burst 647ms
I/O-bound process B: arrival time 929ms; 12 CPU bursts:
--> CPU burst 2438ms --> I/O burst 880ms
--> CPU burst 1173ms --> I/O burst 540ms
...
--> CPU burst 2245ms --> I/O burst 27510ms
--> CPU burst 615ms
CPU-bound process C: arrival time 26ms; 60 CPU bursts:
--> CPU burst 2920ms --> I/O burst 368ms
--> CPU burst 2328ms --> I/O burst 3112ms
...
--> CPU burst 1784ms --> I/O burst 626ms
--> CPU burst 1704ms*/

int partOneOutput(std::vector<process*> processes, int numCPUProc) {
  std::cout << "<<< PROJECT PART I -- process set (n=" << processes.size()
            << ") with " << numCPUProc << " CPU-bound ";
  if (numCPUProc > 1)
    std::cout << "processes >>>" << std::endl;
  else
    std::cout << "process >>>" << std::endl;

  for (unsigned int i = 0; i < processes.size(); ++i) {
    if (processes[i]->isCPUBound)
      std::cout << "CPU-bound process ";
    else
      std::cout << "I/O-bound process ";

    std::cout << processes[i]->id << ": arrival time "
              << processes[i]->arrivalTime << "ms; "
              << processes[i]->burstTimes.size() << " CPU bursts:" << std::endl;
    for (unsigned int j = 0; j < processes[i]->burstTimes.size(); ++j) {
      if (j != processes[i]->burstTimes.size() - 1)
        std::cout << "--> CPU burst " << processes[i]->burstTimes[j]->first
                  << "ms --> I/O burst " << processes[i]->burstTimes[j]->second
                  << "ms" << std::endl;
      else
        std::cout << "--> CPU burst " << processes[i]->burstTimes[j]->first
                  << "ms" << std::endl;
    }
  }
  return 0;
}

int main(int argc, char* argv[]) {
  // Check the number of command line arguments
  if (argc != 6) {
    std::cerr << "Error: Invalid number of command line arguments. Expected 5 "
                 "arguments."
              << std::endl;
    return 1;  // Returning non-zero value to indicate error
  }

  // Parse and store the command line arguments
  int numProc, numCPUProc, seed, upperBound;
  float lambda;

  // Parse and store the first argument as int
  if (std::sscanf(argv[1], "%d", &numProc) != 1) {
    std::cerr << "Error: First argument should be of type int." << std::endl;
    return 1;
  }

  // Parse and store the second argument as int
  if (std::sscanf(argv[2], "%d", &numCPUProc) != 1) {
    std::cerr << "Error: Second argument should be of type int." << std::endl;
    return 1;
  }

  // Parse and store the third argument as int
  if (std::sscanf(argv[3], "%d", &seed) != 1) {
    std::cerr << "Error: Third argument should be of type int." << std::endl;
    return 1;
  }

  // Parse and store the fourth argument as float
  if (std::sscanf(argv[4], "%f", &lambda) != 1) {
    std::cerr << "Error: Fourth argument should be of type float." << std::endl;
    return 1;
  }

  // Parse and store the fifth argument as int
  if (std::sscanf(argv[5], "%d", &upperBound) != 1) {
    std::cerr << "Error: Fifth argument should be of type int." << std::endl;
    return 1;
  }

  if (numProc < numCPUProc) {
    return 2;
  }
  if (numProc < 1 || numProc > 26) {
    return 2;
  }
  if (lambda <= 0) {
    return 2;
  }

  srand48(seed);

  std::vector<process*> processes;

  for (int i = 0; i < numProc; ++i) {
    processes.push_back(new process());
    processes[i]->isCPUBound = (i >= numProc - numCPUProc);
    processes[i]->id = 65 + i;
    processes[i]->arrivalTime = floor(next_exp(lambda, upperBound)) - 1;
    int numCPUBursts = ceil(drand48() * 64);

    if (processes[i]->isCPUBound) {
      for (int j = 0; j < numCPUBursts - 1; ++j) {
        processes[i]->burstTimes.push_back(new std::pair<int, int>(
            ceil(next_exp(lambda, upperBound)) * 4,
            ceil(next_exp(lambda, upperBound)) * 10 / 8));
      }
      processes[i]->burstTimes.push_back(
          new std::pair<int, int>(ceil(next_exp(lambda, upperBound) * 4), 0));
    } else {
      for (int j = 0; j < numCPUBursts - 1; ++j) {
        processes[i]->burstTimes.push_back(
            new std::pair<int, int>(ceil(next_exp(lambda, upperBound)),
                                    ceil(next_exp(lambda, upperBound)) * 10));
      }
      processes[i]->burstTimes.push_back(
          new std::pair<int, int>(ceil(next_exp(lambda, upperBound)), 0));
    }
  }

  partOneOutput(processes, numCPUProc);
  return 0;
}
