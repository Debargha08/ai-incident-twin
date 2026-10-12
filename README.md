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

The system was evaluated on **8 baseline simulated incidents** covering service crashes, service degradation, and latency spikes across core infrastructure and application services.

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

Each incident is evaluated across the recovery workflow: **incident injection → root-cause investigation → recovery planning → safety evaluation → action selection → execution → verification → regression detection → recovery decision**.

### Observed Benchmark Results

The following results are from a recorded benchmark run over the 8 baseline scenarios.

| Metric | Observed Result |
|---|---:|
| Incidents evaluated | 8 |
| Root-cause accuracy | 100% (8/8) |
| Selected-action accuracy | 100% (8/8) |
| Candidate action coverage | 100% (8/8) |
| Safety approval rate | 100% (8/8) |
| Candidate safety block rate | 25.0% (4/16) |
| Safety candidates evaluated | 16 |
| Safety candidates blocked | 4 |
| Execution success rate | 100% (8/8) |
| Verification success rate | 100% (8/8) |
| Regression-free rate | 100% (8/8) |
| Overall recovery success | 100% (8/8) |
| Scenarios requesting retries | 0/8 |

**Interpreting the safety metrics:** the safety approval rate measures whether the final selected action passed the safety gate. The candidate safety block rate measures the fraction of all candidate evaluations that were blocked. These metrics describe different stages and are not contradictory.

The candidate block count varied between repeated runs (4 versus 5 blocked candidates in the runs observed). Therefore, candidate generation or safety-evaluation variability has not yet been ruled out. The 25.0% block rate above is the result of the recorded run, not a claim of deterministic behavior.

No scenario required a retry in this run. The retry mechanism is implemented, but the baseline run does not demonstrate successful recovery through a retry.

### Evaluation Limitations

This benchmark uses a simulated incident environment and a small, predefined set of failure scenarios. The observed results describe performance within this test setup; they do not establish production reliability or generalization to arbitrary incidents.

The baseline scenarios cover crashes, service degradation, and latency spikes. Broader validation would require additional failure combinations, cascading and dependency failures, repeated runs, and tests that deliberately exercise failed recovery and retry paths.

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

The current implementation and benchmark represent the completed portfolio scope of this project.


## License

This project is intended for educational, research, and portfolio purposes.
