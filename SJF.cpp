#include <math.h>

#include <cstdlib>
#include <iostream>
#include <queue>
#include <utility>
#include <vector>

#include "process.h"

// Shortest Job First Algorithm
struct SJF {
  bool operator()(const process& a, const process& b) {
    if (a.estimatedCPUTime == b.estimatedCPUTime) return a.id > b.id;
    return a.estimatedCPUTime > b.estimatedCPUTime;
  }
};

std::string SJFGetContents(
    std::priority_queue<process, std::vector<process>, SJF> q) {
  std::string contents = "[Q";
  if (q.size() == 0) return contents += "<empty>]";

  process t;
  while (q.size() != 0) {
    t = q.top();
    contents += t.id + " ";
    q.pop();
  }
  return contents += "]";
}

void shortestJobFirstFunc(int lambda, int alpha, processManager manager) {
  std::priority_queue<process, std::vector<process>, SJF> processes =
      manager.SJF;
  int time = 0;
  std::cout << "time " << time << "ms: Simulator started for SJF "
            << SJFGetContents(processes) << std::endl;

  // FINISH THE REST OF THIS ALGORITHM
  // NEED TO UPDATE TAU AFTER EVERY CPU BURST COMPLETES
}