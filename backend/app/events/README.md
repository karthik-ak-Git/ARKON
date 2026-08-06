# Event Bus

Communication backbone for the ARKON system. Infrastructure only — contains no business logic, no video editing, no AI, no workflows — only communication.

## Architecture

```
Event Bus
├── Bus (orchestrator)
├── Broker (message queues)
├── Publisher (event creation)
├── Subscriber (event reception)
├── Router (rule-based routing)
├── Dispatcher (delivery)
├── Channel (communication channels)
├── Topic (event topics)
├── Subscription (subscription management)
├── Middleware (logging, metrics, auth, etc.)
├── Filter (event filtering)
├── Persistence (event storage)
├── Replay (event replay)
├── Dead Letter (failed events)
├── Stream (live streaming)
└── Metrics (collection)
```

## Key Files

| File | Purpose |
|------|---------|
| `bus.py` | Main EventBus orchestrator |
| `broker.py` | Message broker with queues |
| `publisher.py` | Event publishing |
| `subscriber.py` | Event subscription |
| `router.py` | Rule-based event routing |
| `dispatcher.py` | Event delivery |
| `channel.py` | Communication channel management |
| `topic.py` | Event topic management |
| `subscription.py` | Subscription lifecycle management |
| `middleware.py` | Middleware pipeline |
| `filter.py` | Event filtering (11 types) |
| `persistence.py` | Event persistence layer |
| `replay.py` | Event replay strategies |
| `dead_letter.py` | Dead letter queue |
| `stream.py` | Live event streaming |
| `metrics.py` | Metrics collection |
| `serializer.py` | Event serialization |
| `interfaces.py` | Core types and protocols |
| `exceptions.py` | Exception hierarchy |

## Quick Start

```python
from app.events import EventBus, EventBusConfig, ChannelType, EventPriority

bus = EventBus(EventBusConfig())
bus.start()

# Publish
event = bus.publish(
    event_type="task.created",
    source="scheduler",
    channel=ChannelType.SCHEDULER,
    topic="tasks",
    payload={"task_id": "t-123"},
)

# Subscribe
sub = bus.subscribe("tasks", callback=handle_task_event)

bus.stop()
```

## Design Principles

1. **Infrastructure Only** — No business logic, no workflows, no AI
2. **Fire and Forget** — Default delivery mode, no guarantees
3. **At Least Once** — Reliable delivery with retry
4. **Exactly Once** — Best effort, not guaranteed
5. **Loose Coupling** — Subsystems never depend on each other directly
6. **Kernel Owned** — EventBus is created and managed by the Kernel
