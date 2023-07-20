#include <math.h>

#include <cstdlib>
#include <iostream>
#include <utility>
#include <vector>

// Our process object.
struct process {
  // Default constructor because values are populated manually
  process() {}
  char id;
  int arrivalTime;
  std::vector<std::pair<int, int>*> burstTimes;
  bool isCPUBound;
};

// Returns a randomly generated double sized according to the project
// specifications
inline double next_exp(float lambda, int upperBound) {
  int num = upperBound;
  while (num > upperBound - 1) num = -log(drand48()) / lambda;
  return num + 1;
}

// Print function that formats according to the project specifications
int partOneOutput(std::vector<process*> processes, int numCPUProc) {
  // Print command line information
  std::cout << "<<< PROJECT PART I -- process set (n=" << processes.size()
            << ") with " << numCPUProc << " CPU-bound ";
  if (numCPUProc == 1)
    std::cout << "process >>>" << std::endl;
  else
    std::cout << "processes >>>" << std::endl;
  // Print data for each individual process
  for (unsigned int i = 0; i < processes.size(); ++i) {
    if (processes[i]->isCPUBound)
      std::cout << "CPU-bound process ";
    else
      std::cout << "I/O-bound process ";

    std::cout << processes[i]->id << ": arrival time "
              << processes[i]->arrivalTime << "ms; "
              << processes[i]->burstTimes.size();
    if (processes[i]->burstTimes.size() == 1) {
      std::cout << " CPU burst:" << std::endl;
    } else {
      std::cout << " CPU bursts:" << std::endl;
    }
    // Print information about each burst
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

  if (std::sscanf(argv[1], "%d", &numProc) != 1) {
    std::cerr << "Error: First argument should be of type int." << std::endl;
    return 1;
  }

  if (std::sscanf(argv[2], "%d", &numCPUProc) != 1) {
    std::cerr << "Error: Second argument should be of type int." << std::endl;
    return 1;
  }

  if (std::sscanf(argv[3], "%d", &seed) != 1) {
    std::cerr << "Error: Third argument should be of type int." << std::endl;
    return 1;
  }

  if (std::sscanf(argv[4], "%f", &lambda) != 1) {
    std::cerr << "Error: Fourth argument should be of type float." << std::endl;
    return 1;
  }

  if (std::sscanf(argv[5], "%d", &upperBound) != 1) {
    std::cerr << "Error: Fifth argument should be of type int." << std::endl;
    return 1;
  }
  // Additional error checking
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

  // Initialize and generate processes
  std::vector<process*> processes;

  for (int i = 0; i < numProc; ++i) {
    processes.push_back(new process());
    processes[i]->isCPUBound = (i >= numProc - numCPUProc);
    processes[i]->id = 65 + i;
    processes[i]->arrivalTime = floor(next_exp(lambda, upperBound)) - 1;
    int numCPUBursts = ceil(drand48() * 64);

    // Generate bursts for both CPU bound and IO Bound processes
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
  // Output data
  partOneOutput(processes, numCPUProc);
  return 0;
}
