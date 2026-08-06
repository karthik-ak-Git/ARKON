"""Tests for channel and topic managers."""

from app.events.channel import ChannelManager
from app.events.topic import TopicManager
from app.events.interfaces import ChannelType


class TestChannelManager:
    def test_create(self):
        mgr = ChannelManager()
        assert mgr.count() >= 10

    def test_get_default_channels(self):
        mgr = ChannelManager()
        channel = mgr.get_channel_by_type(ChannelType.SYSTEM)
        assert channel is not None
        assert channel.name == "system"

    def test_create_channel(self):
        mgr = ChannelManager()
        ch = mgr.create_channel(ChannelType.CUSTOM, name="custom_ch", description="test")
        assert ch.name == "custom_ch"
        assert mgr.count() >= 11

    def test_remove_channel(self):
        mgr = ChannelManager()
        ch = mgr.create_channel(ChannelType.CUSTOM, name="to_remove")
        assert mgr.remove_channel(ch.channel_id) is True

    def test_list_by_type(self):
        mgr = ChannelManager()
        system_channels = mgr.list_by_type(ChannelType.SYSTEM)
        assert len(system_channels) >= 1

    def test_to_dict(self):
        mgr = ChannelManager()
        d = mgr.to_dict()
        assert "total_channels" in d


class TestTopicManager:
    def test_create(self):
        mgr = TopicManager()
        assert mgr.count() >= 9

    def test_get_default_topics(self):
        mgr = TopicManager()
        topic = mgr.get_topic_by_name("tasks")
        assert topic is not None

    def test_create_topic(self):
        mgr = TopicManager()
        topic = mgr.create_topic("custom_topic", description="test")
        assert topic.name == "custom_topic"
        assert mgr.count() >= 10

    def test_create_duplicate(self):
        import pytest
        mgr = TopicManager()
        mgr.create_topic("dup")
        with pytest.raises(Exception):
            mgr.create_topic("dup")

    def test_remove_topic(self):
        mgr = TopicManager()
        topic = mgr.create_topic("to_remove")
        assert mgr.remove_topic(topic.topic_id) is True

    def test_list_by_channel(self):
        mgr = TopicManager()
        topics = mgr.list_by_channel(ChannelType.SCHEDULER)
        assert len(topics) >= 1

    def test_to_dict(self):
        mgr = TopicManager()
        d = mgr.to_dict()
        assert "total_topics" in d
