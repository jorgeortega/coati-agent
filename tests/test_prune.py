"""prune_traces: the served agent's traces go after 30 days (the privacy policy)."""

import datetime

import pytest

from coati_agent.prune import KEEP_DAYS, cutoff_ms, prune

NOW = datetime.datetime(2026, 12, 11, 3, 0, tzinfo=datetime.UTC)


class FakeClient:
    """Deletes up to `batch` traces a call from `remaining`, like MLflow."""

    def __init__(self, remaining, batch=100):
        self.remaining = remaining
        self.batch = batch
        self.calls = []

    def delete_traces(self, experiment_id, max_timestamp_millis=None, max_traces=None):
        self.calls.append((experiment_id, max_timestamp_millis, max_traces))
        deleted = min(self.remaining, max_traces or self.remaining, self.batch)
        self.remaining -= deleted
        return deleted


def test_the_policy_says_thirty_days():
    assert KEEP_DAYS == 30


def test_the_cutoff_is_thirty_days_before_now_in_milliseconds():
    expected = datetime.datetime(2026, 11, 11, 3, 0, tzinfo=datetime.UTC)
    assert cutoff_ms(NOW) == int(expected.timestamp() * 1000)


def test_deletes_in_batches_until_nothing_older_is_left():
    client = FakeClient(remaining=250, batch=100)
    deleted = prune(client, "123", NOW)

    assert deleted == 250
    assert client.remaining == 0
    assert all(call[0] == "123" and call[1] == cutoff_ms(NOW) for call in client.calls)
    assert client.calls[-1] is not None


def test_nothing_to_delete_is_one_call():
    client = FakeClient(remaining=0)
    assert prune(client, "123", NOW) == 0
    assert len(client.calls) == 1


def test_refuses_a_shorter_window_than_a_day():
    with pytest.raises(ValueError):
        cutoff_ms(NOW, days=0)


def test_stops_if_the_store_keeps_returning_traces():
    class Stuck(FakeClient):
        def delete_traces(self, experiment_id, max_timestamp_millis=None, max_traces=None):
            self.calls.append((experiment_id, max_timestamp_millis, max_traces))
            return max_traces

    client = Stuck(remaining=0)
    with pytest.raises(RuntimeError):
        prune(client, "123", NOW, max_rounds=5)
    assert len(client.calls) == 5
