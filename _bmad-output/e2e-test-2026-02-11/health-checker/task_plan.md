# Service Health Monitoring - Task Plan

## Objective
Continuously monitor all 4 services required for E2E testing and alert the team lead immediately if any service goes down.

## Services Monitored
| Service | Endpoint | Method | Expected |
|---------|----------|--------|----------|
| SurrealDB | http://localhost:8000/health | HTTP GET (status code) | 200 |
| API | http://localhost:5055/health | HTTP GET (status code) | 200 |
| Frontend | http://localhost:8502 | HTTP GET (status code) | 200 |
| Worker | Process list | `ps aux \| grep run_worker` | Process running |

## Schedule
- Check interval: 30 seconds
- Duration: 15 minutes (30 checks total)
- Start time: Recorded in progress.md

## Alert Protocol
- If any service returns non-200 or worker process not found: Immediately SendMessage to team-lead
- Log all results (pass/fail) to progress.md with timestamps

## Outputs
- `task_plan.md` - This file
- `progress.md` - Timestamped check results
- `findings.md` - Final summary after 15 minutes
