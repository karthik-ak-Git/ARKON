# Scheduler

Priority-based task scheduling with fairness and preemption.

## Strategies

| Strategy | Description |
|----------|-------------|
| **Priority** | Higher priority tasks execute first |
| **Fairness** | Round-robin across agent types |
| **Preemption** | Higher priority tasks can interrupt lower ones |
| **Backpressure** | Slow down producers when queue is full |

## Configuration

```json
{
  "max_concurrent": 10,
  "strategy": "priority",
  "preemption_enabled": true,
  "fairness_window": 100
}
```

## Queue Management

- Tasks are queued with priority levels (0-9)
- Dead-letter queue for failed tasks
- Retry with exponential backoff
- Queue depth monitoring and alerting
