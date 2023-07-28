#include <math.h>

#include <cstdlib>
#include <iostream>
#include <queue>
#include <utility>
#include <vector>

#include "process.h"
// https://submitty.cs.rpi.edu/courses/u23/csci4210/course_material/lectures/06-22/06-22-notes.txt

struct roundRobin;
struct SJF;
void roundRobinFunc(int maxTime, processManager manager);
std::string RRGetContents(
    std::priority_queue<process, std::vector<process>, roundRobin> q);

struct incomingProcesses {
  bool operator()(const process& a, const process& b) {
    if (a.arrivalTime == b.arrivalTime) return a.id > b.id;
    return a.arrivalTime > b.arrivalTime;
  }
};

// First Come First Serve Algorithm
struct FCFS {
  bool operator()(const process& a, const process& b) {
    if (a.emplacedTime == b.emplacedTime) return a.id > b.id;
    return a.emplacedTime > b.emplacedTime;
  }
};

void firstComeFirstServedFunc(processManager manager);
void shortestTimeRemainingFunc(processManager manager);

/*FUNCTION TO GET CONTENTS OF QUEUE AS STRING

  q = orginalqueue;
  std::string contents = "[Q";
  if (q.size() == 0) return contents += "<empty>]";

  process t;
  while(q.size() != 0) {
    t = q.top();
    contents += t.id + " ";
    q.pop();
  }
  return contents += "]";
*/

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
    // for (unsigned int j = 0; j < processes[i]->burstTimes.size(); ++j) {
    //   if (j != processes[i]->burstTimes.size() - 1)
    //     std::cout << "--> CPU burst " << processes[i]->burstTimes[j]->first
    //               << "ms --> I/O burst " <<
    //               processes[i]->burstTimes[j]->second
    //               << "ms" << std::endl;
    //   else
    //     std::cout << "--> CPU burst " << processes[i]->burstTimes[j]->first
    //               << "ms" << std::endl;
    // }
  }
  return 0;
}

int main(int argc, char* argv[]) {
  // Check the number of command line arguments
  if (argc != 9) {
    std::cerr << "Error: Invalid number of command line arguments. Expected 8 "
                 "arguments."
              << std::endl;
    return 1;  // Returning non-zero value to indicate error
  }

  // Parse and store the command line arguments
  int numProc, numCPUProc, seed, upperBound, tCS, tSlice;
  float lambda, alpha;

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

  if (std::sscanf(argv[6], "%d", &tCS) != 1) {
    std::cerr << "Error: Sixth argument should be of type int." << std::endl;
    return 1;
  }

  if (std::sscanf(argv[7], "%f", &alpha) != 1) {
    std::cerr << "Error: Seventh argument shold be of type float." << std::endl;
    return 1;
  }

  if (std::sscanf(argv[8], "%d", &tSlice) != 1) {
    std::cerr << "Error: Eighth argument should be of type int." << std::endl;
    return 1;
  }

  // Additional error checking
  if (numProc < numCPUProc) {
    return 2;
  }
  if (numProc < 1 || numProc > 26) {
    return 2;
  }
  if (lambda <= 0.) {
    return 2;
  }
  if (tCS < 0 || tCS % 2 == 1) {
    return 2;
  }
  if (alpha < 0. || alpha > 1.) {
    return 2;
  }
  if (tSlice < 0) {
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
    processes[i]->emplacedTime = processes[i]->arrivalTime;
    processes[i]->tau = ceil(1 / lambda);
    processes[i]->waitTime = processes[i]->estimatedCPUTime =
        processes[i]->turnAroundtime = 0;
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

  partOneOutput(processes, numCPUProc);

  // Initialize processManager...
  processManager manager;

  return 0;
}
