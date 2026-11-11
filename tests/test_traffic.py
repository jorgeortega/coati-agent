"""The simulated week (Task 18): one eval question at a time to the served endpoint."""

import json

from coati_agent.traffic import ask, merge_lines, pick, record_for


class FakeError(Exception):
    def __init__(self, status):
        super().__init__(f"HTTP {status}")
        self.status_code = status


class FakeApi:
    """Answers with the scripted outcomes in order: an int is an HTTP error."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def do(self, method, path, body=None):
        self.calls.append((method, path, body))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, int):
            raise FakeError(outcome)
        return outcome


ANSWERED = {
    "output": [{"type": "message", "content": [{"type": "output_text", "text": "Pro is $150."}]}],
    "custom_outputs": {
        "status": "answered",
        "usage": {"input_tokens": 30000, "output_tokens": 400},
        "steps": [{"name": "chat"}, {"name": "get_plans"}, {"name": "chat"}],
    },
}

QUESTIONS = [{"id": f"q{i}", "question": f"Question {i}?"} for i in range(10)]


class Clock:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def test_pick_is_the_same_for_the_same_run_and_varies_between_runs():
    assert pick(QUESTIONS, "run-1") == pick(QUESTIONS, "run-1")
    assert len({pick(QUESTIONS, f"run-{n}")["id"] for n in range(30)}) > 3


def test_a_warm_endpoint_answers_on_the_first_try():
    api, clock = FakeApi(ANSWERED), Clock()
    result = ask(api, "coati-agent", "Question?", clock=clock, sleep=clock.sleep)

    assert api.calls == [
        (
            "POST",
            "/serving-endpoints/coati-agent/invocations",
            {"input": [{"role": "user", "content": "Question?"}]},
        )
    ]
    assert result["status"] == "answered"
    assert result["tries"] == 1
    assert result["input_tokens"] == 30000
    assert result["output_tokens"] == 400
    assert result["steps"] == ["chat", "get_plans", "chat"]


def test_a_cold_endpoint_is_asked_again_until_it_answers():
    api, clock = FakeApi(503, 504, ANSWERED), Clock()
    result = ask(api, "coati-agent", "Question?", clock=clock, sleep=clock.sleep, every_s=20)

    assert result["status"] == "answered"
    assert result["tries"] == 3
    assert clock.slept == [20, 20]


def test_it_gives_up_after_the_wait_and_says_why():
    api, clock = FakeApi(*[503] * 50), Clock()
    result = ask(
        api, "coati-agent", "Question?", clock=clock, sleep=clock.sleep, wait_s=60, every_s=20
    )

    assert result["status"] == "gave_up"
    assert result["error"] == "HTTP 503"
    assert result["input_tokens"] == 0


def test_another_error_is_not_retried():
    api, clock = FakeApi(403), Clock()
    result = ask(api, "coati-agent", "Question?", clock=clock, sleep=clock.sleep)

    assert result["status"] == "error"
    assert result["tries"] == 1


def test_the_record_holds_no_text():
    record = record_for({"id": "q3", "question": "What is my email?"}, {"status": "answered"}, "t")
    assert record == {"at": "t", "id": "q3", "status": "answered"}
    assert "question" not in json.dumps(record)


def test_merge_lines_appends_one_json_line():
    assert merge_lines("", {"id": "a"}) == '{"id": "a"}\n'
    assert merge_lines('{"id": "a"}\n', {"id": "b"}) == '{"id": "a"}\n{"id": "b"}\n'


def test_the_questions_are_the_eval_set():
    from coati_agent.traffic import QUESTIONS

    lines = [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()]
    assert len(lines) >= 40
    assert all({"id", "question"} <= set(line) for line in lines)
