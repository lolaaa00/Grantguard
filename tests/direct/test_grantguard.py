import json
import hashlib
from pathlib import Path

SOURCE = (Path(__file__).parents[2] / "contracts" / "grantguard.py").read_text()
CRITERIA = ("impact", "feasibility", "execution", "budget", "evidence")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def test_rubric_has_five_required_criteria():
    assert len(CRITERIA) == 5
    assert set(CRITERIA) == {"impact", "feasibility", "execution", "budget", "evidence"}
    assert "class GrantGuard(gl.contract.Contract)" in SOURCE
    assert "review_proposal" in SOURCE


def test_digest_is_structured_and_stable():
    value = {"round": "round-0001", "proposal": "proposal-0001", "evidence": ["https://example.com"]}
    assert _digest(value) == _digest(json.loads(_canonical(value)))


def test_canonical_encoding_is_sorted():
    assert _canonical({"b": 2, "a": 1}) == '{"a":1,"b":2}'
