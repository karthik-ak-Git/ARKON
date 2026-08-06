"""Tests for replay."""

import time
from app.events.replay import EventReplayManager, ReplayCheckpoint
from app.events.interfaces import Event, EventType, ReplayStrategy


class TestEventReplayManager:
    def test_create_manager(self):
        mgr = EventReplayManager()
        d = mgr.to_dict()
        assert d["replay_count"] == 0
        assert d["checkpoints"] == 0

    def test_replay_all(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK) for _ in range(5)]
        result = mgr.replay(events, strategy=ReplayStrategy.ALL)
        assert len(result) == 5

    def test_replay_since_timestamp(self):
        mgr = EventReplayManager()
        now = time.time()
        events = [
            Event(event_type=EventType.TASK, timestamp=now - 100),
            Event(event_type=EventType.TASK, timestamp=now),
        ]
        result = mgr.replay(events, strategy=ReplayStrategy.SINCE_TIMESTAMP, since_timestamp=now - 10)
        assert len(result) == 1

    def test_replay_since_timestamp_no_param(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK)]
        try:
            mgr.replay(events, strategy=ReplayStrategy.SINCE_TIMESTAMP)
            assert False, "Should have raised"
        except Exception:
            pass

    def test_replay_since_event_id(self):
        mgr = EventReplayManager()
        e1 = Event(event_type=EventType.TASK)
        e2 = Event(event_type=EventType.TASK)
        result = mgr.replay([e1, e2], strategy=ReplayStrategy.SINCE_EVENT_ID, since_event_id=e1.event_id)
        assert len(result) == 1
        assert result[0].event_id == e2.event_id

    def test_replay_since_event_id_no_param(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK)]
        try:
            mgr.replay(events, strategy=ReplayStrategy.SINCE_EVENT_ID)
            assert False, "Should have raised"
        except Exception:
            pass

    def test_replay_from_last_checkpoint(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK) for _ in range(3)]
        result = mgr.replay(events, strategy=ReplayStrategy.FROM_LAST_CHECKPOINT)
        assert len(result) == 3

    def test_replay_with_callback(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK)]
        processed = []
        mgr.replay(events, callback=lambda e: processed.append(e))
        assert len(processed) == 1

    def test_replay_callback_error(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK)]
        try:
            mgr.replay(events, callback=lambda e: (_ for _ in ()).throw(RuntimeError("fail")))
            assert False, "Should have raised"
        except Exception:
            pass

    def test_replay_history(self):
        mgr = EventReplayManager()
        events = [Event(event_type=EventType.TASK)]
        mgr.replay(events)
        history = mgr.get_replay_history()
        assert len(history) == 1
        assert history[0]["events_replayed"] == 1

    def test_replay_empty(self):
        mgr = EventReplayManager()
        result = mgr.replay([])
        assert len(result) == 0

    def test_save_checkpoint(self):
        mgr = EventReplayManager()
        cp = ReplayCheckpoint(checkpoint_id="cp1", last_event_id="e1")
        mgr.save_checkpoint(cp)
        assert mgr.get_checkpoint("cp1") is not None

    def test_list_checkpoints(self):
        mgr = EventReplayManager()
        mgr.save_checkpoint(ReplayCheckpoint(checkpoint_id="cp1"))
        mgr.save_checkpoint(ReplayCheckpoint(checkpoint_id="cp2"))
        assert len(mgr.list_checkpoints()) == 2

    def test_delete_checkpoint(self):
        mgr = EventReplayManager()
        mgr.save_checkpoint(ReplayCheckpoint(checkpoint_id="cp1"))
        assert mgr.delete_checkpoint("cp1") is True
        assert mgr.get_checkpoint("cp1") is None

    def test_delete_checkpoint_not_found(self):
        mgr = EventReplayManager()
        assert mgr.delete_checkpoint("nonexistent") is False

    def test_to_dict(self):
        mgr = EventReplayManager()
        mgr.save_checkpoint(ReplayCheckpoint(checkpoint_id="cp1"))
        mgr.replay([Event(event_type=EventType.TASK)])
        d = mgr.to_dict()
        assert d["checkpoints"] == 1
        assert d["replay_count"] == 1


class TestReplayCheckpoint:
    def test_create(self):
        cp = ReplayCheckpoint()
        d = cp.to_dict()
        assert d["checkpoint_id"] == ""
        assert d["last_event_id"] == ""
        assert d["events_replayed"] == 0

    def test_create_with_values(self):
        cp = ReplayCheckpoint(
            checkpoint_id="cp1",
            last_event_id="e1",
            last_timestamp=123.0,
            events_replayed=10,
        )
        d = cp.to_dict()
        assert d["checkpoint_id"] == "cp1"
        assert d["last_event_id"] == "e1"
        assert d["last_timestamp"] == 123.0
        assert d["events_replayed"] == 10

    def test_to_dict_has_created_at(self):
        cp = ReplayCheckpoint()
        d = cp.to_dict()
        assert "created_at" in d
        assert d["created_at"] > 0
