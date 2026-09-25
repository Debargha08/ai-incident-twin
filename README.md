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
