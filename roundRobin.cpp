#include <cstdlib>
#include <iostream>
#include <queue>
#include <utility>
#include <vector>

#include "process.h"

std::string RRGetContents(
    std::priority_queue<process, std::vector<process>, roundRobin> q) {
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

struct roundRobin {
  bool operator()(const process& a, const process& b) {
    if (a.emplacedTime == b.emplacedTime) return a.id > b.id;
    return a.emplacedTime > b.emplacedTime;
  }
};

void roundRobinFunc(int maxTime, processManager manager) {
  std::priority_queue<process, std::vector<process>, roundRobin>* processes =
      &manager.RR;
  manager.burstTimeCounter = 0;

  process nextProcess = manager.incoming.top();
  while (processes->size() != 0) {
    process current = processes->top();
    int finder = 0;
    while (current.burstTimes[finder]->first == 0) ++finder;
    int burstTime = current.burstTimes[finder]->first;
    if (manager.burstTimeCounter + burstTime > nextProcess.arrivalTime) {
      // New process is arriving MAKE ITS OWN FUNCTION pass by reference
      process p = manager.incoming.top();
      manager.incoming.pop();
      p.emplacedTime = p.arrivalTime;
      processes->push(p);
    }
  }
}