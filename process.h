// Our process object.
struct process {
  char id;
  int arrivalTime;
  int emplacedTime;
  std::vector<std::pair<int, int>*> burstTimes;
  bool isCPUBound;
  int waitTime;
  int turnAroundtime;
  int tau;
  int estimatedCPUTime;
  // Default constructor because values are populated manually
  process() {}
  // Copy constructor to make insertion into queues easy
  process(process* p) {
    id = p->id;
    arrivalTime = p->arrivalTime;
    emplacedTime = p->emplacedTime;
    isCPUBound = p->isCPUBound;
    waitTime = p->waitTime;
    turnAroundtime = p->turnAroundtime;
    tau = p->tau;
    estimatedCPUTime = p->estimatedCPUTime;
    for (int i = 0; i < p->burstTimes.size(); i++) {
      burstTimes.push_back(new std::pair<int, int>(p->burstTimes[i]->first,
                                                   p->burstTimes[i]->second));
    }
  }
};

struct processManager {
  std::priority_queue<process, std::vector<process>, roundRobin> RR;
  std::priority_queue<process, std::vector<process>, FCFS> FIFO;
  std::priority_queue<process, std::vector<process>, SJF> SJF;
  std::priority_queue<process> SRT;
  std::priority_queue<process, std::vector<process>, incomingProcesses>
      incoming;

  int cpuUtilization;
  int burstTimeCounter;
};