# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""GrantGuard: a consensus-powered grant evaluation market.

The contract freezes a grant rubric, evaluates public proposal evidence through
GenLayer consensus, opens a challenge window, and settles one native-GEN award.
"""

import datetime
import hashlib
import json
import typing

import genlayer as gl
from genlayer import Address, u256
from genlayer.storage import DynArray, TreeMap

allow_storage = gl.storage.allow

ROUND_OPEN = "OPEN"
ROUND_REVIEWING = "REVIEWING"
ROUND_CHALLENGE = "CHALLENGE"
ROUND_FINALIZED = "FINALIZED"
ROUND_CANCELLED = "CANCELLED"

PROPOSAL_SUBMITTED = "SUBMITTED"
PROPOSAL_REVIEWING = "REVIEWING"
PROPOSAL_QUALIFIED_PENDING = "QUALIFIED_PENDING"
PROPOSAL_REJECTED = "REJECTED"
PROPOSAL_INCONCLUSIVE = "INCONCLUSIVE"
PROPOSAL_FINAL = "QUALIFIED_FINAL"

CRITERIA = ("impact", "feasibility", "execution", "budget", "evidence")
MAX_TEXT = 2000
MAX_URL = 500
MAX_LIST = 8


def _fail(message: str) -> typing.NoReturn:
    raise gl.vm.UserError(message)


def _now() -> int:
    raw = str(gl.message.raw.get("datetime", ""))
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        value = datetime.datetime.fromisoformat(raw)
    except ValueError:
        _fail("transaction datetime is malformed")
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return int(value.timestamp())


def _canonical(value: typing.Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: typing.Any) -> str:
    return "0x" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _parse_obj(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except ValueError:
        _fail(label + " must be valid JSON")
    if not isinstance(value, dict):
        _fail(label + " must be an object")
    return value


def _parse_list(raw: str, label: str) -> list:
    try:
        value = json.loads(raw)
    except ValueError:
        _fail(label + " must be valid JSON")
    if not isinstance(value, list):
        _fail(label + " must be an array")
    if len(value) > MAX_LIST:
        _fail(label + " has too many items")
    return value


def _source(url: str) -> None:
    if not url.startswith("https://") or len(url) > MAX_URL:
        _fail("evidence sources must be absolute HTTPS URLs")
    host = url[8:].split("/", 1)[0].split(":", 1)[0].lower()
    if not host or host.startswith(("localhost", "127.", "10.", "172.", "192.168.", "0.")):
        _fail("evidence source must use a public host")


@allow_storage
class Round:
    round_id: str
    sponsor: Address
    title: str
    description: str
    rubric_json: str
    criteria_json: str
    evidence_policy: str
    deadline: u256
    challenge_window: u256
    funding: u256
    status: str
    finalized_proposal: str
    certificate_hash: str
    created_at: u256


@allow_storage
class Proposal:
    proposal_id: str
    round_id: str
    applicant: Address
    title: str
    summary: str
    repository_url: str
    budget: u256
    milestones_json: str
    evidence_json: str
    evidence_hash: str
    status: str
    scores_json: str
    review_json: str
    submitted_at: u256
    reviewed_at: u256
    challenge_deadline: u256
    challenged: bool
    award: u256
    withdrawn: bool


@allow_storage
class GrantGuard(gl.contract.Contract):
    rounds: TreeMap[str, Round]
    round_ids: DynArray[str]
    proposals: TreeMap[str, Proposal]
    proposal_ids: DynArray[str]
    seq: u256
    total_funding: u256
    total_awarded: u256

    def __init__(self) -> None:
        self.seq = 0
        self.total_funding = 0
        self.total_awarded = 0

    @gl.private
    def _id(self, prefix: str) -> str:
        self.seq = int(self.seq) + 1
        return prefix + "-" + str(int(self.seq)).zfill(4)

    @gl.private
    def _round(self, round_id: str) -> Round:
        value = self.rounds.get(round_id)
        if value is None:
            _fail("unknown grant round")
        return value

    @gl.private
    def _proposal(self, proposal_id: str) -> Proposal:
        value = self.proposals.get(proposal_id)
        if value is None:
            _fail("unknown proposal")
        return value

    @gl.public.write
    def create_round(
        self,
        title: str,
        description: str,
        rubric_json: str,
        evidence_policy: str,
        deadline: int,
        challenge_window: int,
    ) -> str:
        if not title.strip() or len(title) > MAX_TEXT:
            _fail("title is required and bounded")
        if len(description) > MAX_TEXT or len(evidence_policy) > MAX_TEXT:
            _fail("text field is too long")
        rubric = _parse_obj(rubric_json, "rubric_json")
        if sorted(rubric.keys()) != sorted(CRITERIA):
            _fail("rubric must contain every required criterion exactly once")
        now = _now()
        if int(deadline) <= now or int(challenge_window) <= 0:
            _fail("invalid deadline or challenge window")
        funding = int(gl.message.value)
        if funding <= 0:
            _fail("grant round must be funded")
        rid = self._id("round")
        record = Round(
            round_id=rid,
            sponsor=gl.message.sender_address,
            title=title,
            description=description,
            rubric_json=_canonical(rubric),
            criteria_json=_canonical(list(CRITERIA)),
            evidence_policy=evidence_policy,
            deadline=int(deadline),
            challenge_window=int(challenge_window),
            funding=funding,
            status=ROUND_OPEN,
            finalized_proposal="",
            certificate_hash="",
            created_at=now,
        )
        self.rounds[rid] = record
        self.round_ids.append(rid)
        self.total_funding = int(self.total_funding) + funding
        return rid

    @gl.public.write
    def submit_proposal(
        self,
        round_id: str,
        title: str,
        summary: str,
        repository_url: str,
        budget: int,
        milestones_json: str,
        evidence_json: str,
    ) -> str:
        grant = self._round(round_id)
        if grant.status != ROUND_OPEN or _now() >= int(grant.deadline):
            _fail("round is not accepting proposals")
        _source(repository_url)
        milestones = _parse_list(milestones_json, "milestones_json")
        evidence = _parse_list(evidence_json, "evidence_json")
        for item in evidence:
            if not isinstance(item, dict) or not str(item.get("url", "")).startswith("https://"):
                _fail("each evidence item needs a public HTTPS URL")
            _source(str(item["url"]))
        if not title.strip() or not summary.strip() or int(budget) <= 0:
            _fail("proposal fields are invalid")
        pid = self._id("proposal")
        record = Proposal(
            proposal_id=pid,
            round_id=round_id,
            applicant=gl.message.sender_address,
            title=title,
            summary=summary,
            repository_url=repository_url,
            budget=int(budget),
            milestones_json=_canonical(milestones),
            evidence_json=_canonical(evidence),
            evidence_hash=_digest({"round": round_id, "proposal": pid, "evidence": evidence}),
            status=PROPOSAL_SUBMITTED,
            scores_json="{}",
            review_json="{}",
            submitted_at=_now(),
            reviewed_at=0,
            challenge_deadline=0,
            challenged=False,
            award=0,
            withdrawn=False,
        )
        self.proposals[pid] = record
        self.proposal_ids.append(pid)
        return pid

    @gl.public.write
    def review_proposal(self, proposal_id: str) -> str:
        proposal = self._proposal(proposal_id)
        grant = self._round(proposal.round_id)
        if proposal.status not in (PROPOSAL_SUBMITTED, PROPOSAL_INCONCLUSIVE):
            _fail("proposal is not reviewable")
        proposal.status = PROPOSAL_REVIEWING
        rubric = _parse_obj(grant.rubric_json, "rubric_json")
        evidence = _parse_list(proposal.evidence_json, "evidence_json")
        prompt = _canonical({
            "task": "Evaluate a grant proposal against a frozen rubric.",
            "proposal": {"title": proposal.title, "summary": proposal.summary, "repository": proposal.repository_url, "budget": int(proposal.budget), "milestones": json.loads(proposal.milestones_json)},
            "rubric": rubric,
            "evidence": evidence,
            "output": {"scores": {key: "integer 0 through 5" for key in CRITERIA}, "decision": "QUALIFIED or REJECTED or INCONCLUSIVE", "reason": "short string", "evidence": "array of cited URLs"},
        })

        def leader() -> str:
            return gl.nondet.web.get(prompt)

        result = gl.eq_principle.prompt_comparative(
            leader,
            "Return a JSON object only. Use the exact criterion keys and fail closed when evidence is unavailable.",
        )
        raw = result.calldata if isinstance(result, gl.vm.Return) else result.get("calldata") if isinstance(result, dict) else result
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = None
        if not isinstance(raw, dict):
            proposal.status = PROPOSAL_INCONCLUSIVE
            proposal.review_json = _canonical({"decision": "INCONCLUSIVE", "reason": "consensus returned malformed data"})
            proposal.reviewed_at = _now()
            return proposal.status
        scores = raw.get("scores")
        decision = str(raw.get("decision", "INCONCLUSIVE"))
        if not isinstance(scores, dict) or any(key not in scores for key in CRITERIA):
            proposal.status = PROPOSAL_INCONCLUSIVE
            proposal.review_json = _canonical({"decision": "INCONCLUSIVE", "reason": "missing criterion"})
        elif any(not isinstance(scores[key], int) or scores[key] < 0 or scores[key] > 5 for key in CRITERIA):
            proposal.status = PROPOSAL_INCONCLUSIVE
            proposal.review_json = _canonical({"decision": "INCONCLUSIVE", "reason": "invalid score"})
        elif decision == "QUALIFIED":
            proposal.status = PROPOSAL_QUALIFIED_PENDING
            proposal.challenge_deadline = _now() + int(grant.challenge_window)
        elif decision == "REJECTED":
            proposal.status = PROPOSAL_REJECTED
        else:
            proposal.status = PROPOSAL_INCONCLUSIVE
        proposal.scores_json = _canonical(scores if isinstance(scores, dict) else {})
        proposal.review_json = _canonical(raw)
        proposal.reviewed_at = _now()
        return proposal.status

    @gl.public.write
    def challenge_proposal(self, proposal_id: str, reason: str, evidence_url: str) -> str:
        proposal = self._proposal(proposal_id)
        if proposal.status != PROPOSAL_QUALIFIED_PENDING or _now() > int(proposal.challenge_deadline):
            _fail("challenge window is closed")
        if not reason.strip() or len(reason) > MAX_TEXT:
            _fail("challenge reason is invalid")
        _source(evidence_url)
        proposal.challenged = True
        proposal.status = PROPOSAL_INCONCLUSIVE
        proposal.review_json = _canonical({"decision": "INCONCLUSIVE", "challenge": reason, "evidence_url": evidence_url})
        return proposal.status

    @gl.public.write
    def finalize_round(self, round_id: str, proposal_id: str) -> str:
        grant = self._round(round_id)
        proposal = self._proposal(proposal_id)
        if proposal.round_id != round_id or proposal.status != PROPOSAL_QUALIFIED_PENDING:
            _fail("proposal is not finalizable")
        if proposal.challenged or _now() < int(proposal.challenge_deadline):
            _fail("challenge window is still open")
        if grant.status == ROUND_FINALIZED:
            _fail("round already finalized")
        grant.status = ROUND_FINALIZED
        proposal.status = PROPOSAL_FINAL
        proposal.award = int(grant.funding)
        grant.finalized_proposal = proposal_id
        grant.certificate_hash = _digest({"round": round_id, "proposal": proposal_id, "evidence": proposal.evidence_hash, "scores": proposal.scores_json})
        self.total_awarded = int(self.total_awarded) + int(grant.funding)
        return grant.certificate_hash

    @gl.public.write
    def withdraw_award(self, proposal_id: str) -> int:
        proposal = self._proposal(proposal_id)
        if proposal.status != PROPOSAL_FINAL or proposal.withdrawn:
            _fail("award is not withdrawable")
        if gl.message.sender_address != proposal.applicant:
            _fail("only the winning applicant may withdraw")
        amount = int(proposal.award)
        proposal.award = 0
        proposal.withdrawn = True
        proposal.applicant.transfer_native(amount)
        return amount

    @gl.public.view
    def get_round(self, round_id: str) -> str:
        return _canonical(self._round(round_id).__dict__)

    @gl.public.view
    def get_proposal(self, proposal_id: str) -> str:
        return _canonical(self._proposal(proposal_id).__dict__)

    @gl.public.view
    def get_certificate(self, round_id: str) -> str:
        return self._round(round_id).certificate_hash

    @gl.public.view
    def list_rounds(self) -> str:
        return _canonical([self.rounds[rid].__dict__ for rid in self.round_ids])

    @gl.public.view
    def list_proposals(self, round_id: str) -> str:
        return _canonical([self.proposals[pid].__dict__ for pid in self.proposal_ids if self.proposals[pid].round_id == round_id])

    @gl.public.view
    def accounting_invariant(self) -> bool:
        return int(self.total_awarded) <= int(self.total_funding)
