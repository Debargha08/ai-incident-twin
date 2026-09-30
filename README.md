# AI Incident Twin & Autonomous Recovery Platform

An AI-powered production incident response system that simulates a distributed production environment, detects failures, investigates root causes, plans safe recovery actions, executes approved remediation, and verifies that the system has actually recovered.

The project is designed around a closed-loop autonomous reliability workflow rather than one-shot incident analysis.

## Overview

The system simulates a small production environment containing services, dependencies, telemetry, failures, and recovery operations.



## Core Workflow

Production Simulation
        |
        v
Failure Injection
        |
        v
Telemetry Collection
        |
        v
Incident Detection
        |
        v
AI Investigation
        |
        v
Recovery Planning
        |
        v
Safety Evaluation
        |
        v
Recovery Execution
        |
        v
Recovery Verification
        |
        v
Regression Detection
        |
        v
Reflection / Retry

## Key Capabilities

- Simulated distributed production environment with service dependencies
- Failure injection for crashes, degradation, and latency failures
- Metrics, logs, and request traces for incident investigation
- Automated anomaly detection and evidence correlation
- LLM-based root-cause investigation using local inference
- Structured recovery action generation
- Safety gates and precondition validation before execution
- Risk-aware recovery action selection
- Autonomous recovery execution
- Post-recovery verification and regression detection


## Autonomous Recovery Loop

The system does not simply generate a remediation suggestion.

A recovery action must pass through the following stages:

Detect
  |
  v
Investigate
  |
  v
Plan
  |
  v
Safety Evaluation
  |
  v
Execute
  |
  v
Verify
  |
  +----> Regression detected ----> Reflect / Retry
  |
  v
Recovered

## Safety Architecture

Autonomous recovery is constrained by a dedicated safety layer.

Before an action can execute, the system evaluates:

- Target service validity
- Action validity
- Preconditions
- Expected outcomes
- Dependency validity
- Risk level
- Dangerous-action policies
- Manual approval requirements

High-risk operations can be blocked or require manual approval rather than being executed automatically.

## AI Investigation

The investigation agent uses local LLM inference through Ollama.

The investigator receives observable incident evidence including:

- Metrics
- Logs
- Traces
- Anomaly signals
- Failure timeline
- Service relationships

The system prevents dependency topology from being treated as root-cause evidence unless the dependency itself has observable failure evidence.


## Recovery Verification

A recovery is not considered successful simply because an action executes without an exception.

After execution, the system verifies:

- Service health
- Error rate
- Latency
- Recovery state
- Dependent service health

Regression detection checks affected services and their dependents for newly introduced or unresolved failures.

## Benchmark

The current benchmark contains three production failure scenarios:

| Scenario | Expected Root Cause | Expected Recovery |
|---|---|---|
| Redis crash | Redis | Restart service |
| Order service degradation | Order service | Restore / restart service |
| Payment service crash | Payment service | Restart service |

### Current Results

Across the three benchmark scenarios:

- Root-cause accuracy: **100% (3/3)**
- Recovery-action coverage: **100% (3/3)**
- Recovery verification: **100% (3/3)**
- Regression-free recovery: **100% (3/3)**
- Overall recovery success: **100% (3/3)**

These results are from the current three-scenario benchmark and should not be interpreted as production-scale reliability.

## Tech Stack

- **Language:** Python
- **LLM:** Qwen 2.5 7B
- **Inference:** Ollama
- **Agent orchestration:** LangGraph
- **LLM framework:** LangChain
- **API:** FastAPI
- **Testing:** Pytest
- **Observability:** Simulated metrics, logs, and traces
- **Version control:** Git


## Architecture

```text
                         +----------------------+
                         |     FastAPI / API     |
                         +----------+-----------+
                                    |
                                    v
                    +---------------+----------------+
                    |      Incident Twin Engine      |
                    +---------------+----------------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
              v                     v                     v
        Simulation             Telemetry            Intelligence
        Environment            Pipeline             Layer
              |                     |                     |
              |                     |             +-------+-------+
              |                     |             | Investigation |
              |                     |             | Anomaly       |
              |                     |             | Evidence      |
              |                     |             | RCA           |
              |                     |             +-------+-------+
              |                     |                     |
              v                     v                     v
        Failure Injection       Logs/Traces        Recovery Planner
                                                          |
                                                          v
                                                   Safety Gate
                                                          |
                                                          v
                                                Recovery Executor
                                                          |
                                                          v
                                             Verification / Regression
                                                          |
                                                          v
                                                     Reflection



                                                     Reflection

```


## Project Structure

app/
├── evaluation/
├── intelligence/
├── recovery/
├── simulation/
├── telemetry/
├── main.py
└── recovery_action.py



## Running Locally

1. Create a virtual environment:
   `python3 -m venv .venv`
   `source .venv/bin/activate`

2. Install dependencies:
   `pip install -r requirements.txt`

3. Install the local LLM:
   `ollama pull qwen2.5:7b`

4. Run the application:
   `python3 -m app.main`


## Design Principles

1. **Evidence before inference**  
   Root-cause hypotheses must be supported by observable evidence.

2. **Plan before execution**  
   Recovery actions are generated and evaluated before execution.

3. **Safety before autonomy**  
   Autonomous remediation is constrained by explicit safety policies.

4. **Execution is not recovery**  
   A recovery action is successful only after verification.

5. **Recovery can regress**  
   Dependent services are checked after remediation.

6. **Evaluation is separate from execution**  
   Benchmark ground truth is used only to measure system performance, not to select recovery actions.

## Evaluation & Benchmark

The system was evaluated using a benchmark of **8 simulated production incidents** covering service crashes, service degradation, and latency spikes across core infrastructure and application services.

### Benchmark Scenarios

| Scenario | Failure Type | Target |
|---|---|---|
| Redis Crash | Service crash | Redis |
| Order Service Degradation | Service degradation | Order Service |
| Payment Service Crash | Service crash | Payment Service |
| PostgreSQL Crash | Service crash | PostgreSQL |
| User Service Crash | Service crash | User Service |
| Order Service Latency Spike | Latency degradation | Order Service |
| User Service Latency Spike | Latency degradation | User Service |
| Redis Latency Spike | Latency degradation | Redis |

### Evaluation Dimensions

Each incident is evaluated across the complete recovery workflow: **incident injection → root-cause investigation → recovery planning → safety evaluation → safe action selection → execution → verification → regression detection → recovery decision**.

The benchmark measures root-cause accuracy, recovery-action accuracy, safety approval, execution success, verification success, regression-free recovery, overall recovery success, unsafe candidate blocking, and retry requests.

### Final Benchmark Results

| Metric | Result |
|---|---:|
| Incidents Evaluated | **8** |
| Root-Cause Accuracy | **100%** |
| Recovery-Action Accuracy | **100%** |
| Safety Approval Rate | **100%** |
| Execution Success Rate | **100%** |
| Verification Success Rate | **100%** |
| Regression-Free Rate | **100%** |
| Overall Recovery Success | **100%** |
| Unsafe Candidates Blocked | **4** |
| Retry Requests | **0 / 8** |

The safety evaluation demonstrated that unsafe recovery candidates can be identified and blocked before execution. During the final benchmark run, **4 unsafe candidates were blocked**, while all selected recovery actions passed the safety gate.

No benchmark scenario required a retry or re-investigation during the final run. The retry mechanism is instrumented as part of the workflow, but its retry path was not exercised by these 8 scenarios.

### Evaluation Limitations

This benchmark uses a simulated incident environment and evaluates a defined set of failure modes. The results demonstrate system behavior within the implemented simulation rather than guaranteeing equivalent performance on arbitrary real-world production incidents.

The benchmark currently covers service crashes, service degradation, and latency spikes. Additional failure classes and larger scenario sets would be required for broader evaluation.

## Current Status

**Core autonomous incident-response system: complete.**

Implemented:

- Production environment simulation
- Failure injection
- Telemetry generation
- Incident detection
- AI investigation
- Recovery planning
- Recovery safety evaluation
- Autonomous recovery execution
- Recovery verification
- Regression detection
- Benchmark evaluation

Production-facing documentation and additional benchmark scenarios can be added in future iterations.


## License

This project is intended for educational, research, and portfolio purposes.
