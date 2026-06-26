# QueueStorm Investigator — Production & Scoring Audit

Date: 2026-06-26 · Auditor lenses: API design · code review/quality · simplification · fuzzing · CI/CD
Method: read all source, ran the test suite, diffed every graded field vs. the official samples,
fuzzed the endpoint in-process, and probed the safety + classification layers adversarially.

---

## ✅ Resolution (all Tier 1–4 fixes applied 2026-06-26)

| Metric | Before | After |
|--------|--------|-------|
| Graded fields correct (10 samples) | 4/10 cases wrong | **10/10 correct** |
| pytest | 121 passed (gaps) | **160 passed** (now asserts severity + human_review + validator) |
| Safety validator false positives | 1/10 | **0/10** |
| Safety validator false negatives | 7/8 | **0/8** |
| Phishing over-breadth | 5/5 misclassified | **fixed** (co-occurrence) |
| Fuzz hard crashes | 0 | **0** (no regression) |
| Docker secret leak | `.env` baked in | **`.dockerignore` added** |

Changes: `rules.py` (human_review, severity, phishing), `investigator.py` (call site +
ambiguity), `safety.py` (allowlist inversion), `llm.py` (async + 8s timeout), `config.py`
(Pydantic v2, dead config removed), `models.py` (lenient optional enums), `.dockerignore`,
`.gitignore`, strengthened tests, `.github/workflows/ci.yml`. The findings below are retained
as the original audit record.

---

## Verdict

**Not yet competition-ready, but close.** The service is well-structured, reliable (0 crashes on
15 hostile inputs), schema-correct, and safe in keyless mode — but it was built from the *old*
`queuestorm_claude_code_prompt.md`, **not** the corrected `CLAUDE.md`, so it carries the exact
logic bugs that file warned about. **4 of 10 public sample cases produce a wrong graded field in
the 35-point Evidence Reasoning category**, and a classification over-breadth bug makes the
hidden-test risk larger than 4/10 suggests. All issues are small, localized fixes.

### Evidence snapshot (all reproduced empirically)

| Probe | Result |
|-------|--------|
| `pytest tests/` | **121 passed** ✅ (but the suite never asserts `severity` or `human_review_required`) |
| Diff all 6 graded fields vs. expected | **4/10 cases wrong**: SAMPLE-03, -06, -08, -09 ❌ |
| Fuzz 15 malformed/hostile payloads | **0 crashes** ✅ (all controlled 400/422/200) |
| Each expected sample reply vs. validator | **1/10 false-positive** (SAMPLE-10 reply discarded) ❌ |
| 8 realistic credential-request phrasings | **7/8 bypass** the validator (false negatives) ❌ |
| 5 non-phishing complaints mentioning pin/otp | **5/5 misclassified as phishing** ❌ |

The green test suite is the trap: it gives false confidence because it omits the two fields that
are actually wrong. The judge harness scores them (Rubric Layer 3: *"…case_type, department,
severity, and human_review_required"*).

---

## Findings by severity (ranked by scoring impact)

### TIER 1 — Evidence Reasoning (35 pts, the shortlisting filter). Fix first.

**1A. `human_review_required` keys off severity → 3 sample cases wrong.**
`app/rules.py: requires_human_review` starts with `if severity in (critical, high): return True`,
plus `amount >= 10000`. Result:
- SAMPLE-03 (payment_failed, high) → `True`, expected **False**.
- SAMPLE-09 (merchant settlement, 15000 ≥ 10000) → `True`, expected **False**.
- SAMPLE-08 (wrong_transfer, no txn identified) → `True` via case_type, expected **False**.

Fix (the corrected logic already in `CLAUDE.md §11.5`): drop severity; use disputes/suspicious/
ambiguous, gate the dispute set on `relevant_txn_id is not None`, threshold `>= 25000`.
Call site `app/investigator.py:457` must change signature to
`requires_human_review(case_type, evidence_verdict, relevant_txn_id, amount)`.

**1B. `determine_severity` default is `medium` → SAMPLE-06 wrong.**
`other` falls through to `return Severity.medium`; expected **low**. Add `if case_type == other: return low`.

**1C. `classify_case` phishing over-breadth → systematic hidden-test risk (NOT visible in the 10 samples).**
Phishing is top priority and matches the bare substrings `"pin"`, `"otp"`, `"password"`. So any
complaint mentioning a credential in a non-phishing context is misrouted to `fraud_risk`/`critical`:
- "I entered my PIN and the payment failed" → phishing (should be payment_failed)
- "I changed my password and want a refund" → phishing (should be refund_request)
- 5/5 such probes misclassified.

This corrupts case_type → department → severity → human_review together. Fix: require
**co-occurrence** of a credential noun with a social-engineering signal (`called`, `sms`, `asked
for`, `someone`, `link`, `click`, `verify your account`, `block`) or explicit scam words
(`scam`, `phishing`, `fraud call`, `impersonat`). Remove bare `pin`/`otp`/`password` from the
phishing keyword list.

### TIER 2 — Secret leak via Docker image (high IF a Docker image is submitted)

`.env` contains a **real, non-empty `GROQ_API_KEY`**. `.gitignore` correctly excludes it from the
**git repo** (no repo leak). But `Dockerfile` does `COPY . .` with **no `.dockerignore`**, so the
key is **baked into the Docker image** — a leak on submission path B (Docker image) and any pushed
image. `COPY . .` also bakes in the 35 MB `venv/` and the PDFs (image bloat, platform-specific venv).

Fix: add `.dockerignore` (`.env`, `venv/`, `.git`, `*.pdf`, `tests/`, `__pycache__/`,
`.pytest_cache/`, `*.md` except README if desired). Rotate the key after the event regardless.

### TIER 3 — Conditional on an LLM key being set

**3A. Blocking LLM call inside async handler.** `app/llm.py:103` calls the **synchronous** Groq
client (`client.chat.completions.create`) directly inside `async def`, with `timeout=20.0`. This
blocks the event loop: under the judge's concurrent load all requests serialize, p95 (full credit
≤5s) is forfeit, and a single slow call risks the 30s hard cutoff. Fix: `await asyncio.to_thread(...)`
or use `AsyncGroq`, and cut the timeout to ~6–8s. (Irrelevant in keyless mode — see deployment note.)

**3B. Safety validator: false positives AND false negatives.**
- False positive: greedy `verify.*(?:pin|otp|password)` / `confirm.*…` match across a whole
  sentence, so SAMPLE-10's own canonical reply ("…will **verify** with the biller… do not share
  your **PIN**") is flagged and replaced with the generic fallback (Response-Quality loss).
- False negative: patterns require exact `"<verb> your <cred>"` adjacency, so 7/8 realistic
  requests bypass — "send me your OTP", "tell me your PIN", "type your PIN here", "reply with your
  one-time password", "forward the OTP", etc.

Best fix (allowlist inversion): flag **any** PIN/OTP/password/card-number mention by default, and
allow it **only** in a warning context (`do not share`, `don't share`, `never share`, `never ask
for`, Bangla `শেয়ার করবেন না` / `চাই না`). In this domain every legitimate mention is a warning,
so this removes both false-pos and false-neg at once. Must still pass all 10 expected replies and
flag all 8 probe requests.

### TIER 4 — Polish / quality (manual review + tie-breakers)

- `venv/` (35 MB) is **not** in `.gitignore` → would bloat the repo. Add it.
- Ambiguity detection only triggers on an **exact** score tie (`scored[0][0] == scored[1][0]`),
  not the spec's "within 15 points" — latent for near-tie hidden cases (`investigator.py:233-238`).
- Input enums are **strict** (`language:"invalid"` → 400). Defensible (400 is a controlled error),
  but `CLAUDE.md` recommends leniency on optional fields to maximize the reliability score.
- Dead config: `settings.request_timeout` is defined but never used.
- Pydantic v2 deprecation: replace inner `class Config` with `model_config = SettingsConfigDict(...)`.
- Null transaction-history element (`[None]`) → 400 (Pydantic rejects before the investigator's
  null-filter runs). The defensive filter in `investigator.py:436` is effectively dead code.

---

## CI/CD lens (`/ci-cd-and-automation`)

No pipeline exists (`.github/` absent). For a production-grade claim, add a minimal GitHub Actions
workflow that runs `pytest` on push/PR with `GROQ_API_KEY=""` (deterministic, no network). This
also continuously guards the Tier-1 regressions once the sample-case tests assert all 6 fields.
Suggested: `.github/workflows/ci.yml` — checkout → setup-python 3.11 → `pip install -r
requirements.txt` → `pytest -q`.

---

## Test-suite gap (root cause of the false confidence)

`tests/test_sample_cases.py` asserts ticket_id, relevant_transaction_id, evidence_verdict,
case_type, department — but **not severity or human_review_required**, the two fields that are
wrong. Add both assertions, plus the mandatory safety regression test from `CLAUDE.md §9.3`
("every `expected_output.customer_reply` passes the validator"), which would have caught SAMPLE-10.

---

## What's already good (keep it)

- Clean rules-first architecture; structured fields are deterministic (correct design for the 35 pts).
- Reliable: 0 crashes on 15 hostile payloads; graceful 400/422; no stack-trace leakage.
- Keyless operation works and is fast (~0.00s/req in tests) → full p95 latency credit.
- Schema is exact: correct enums, `relevant_transaction_id` is real JSON `null`, all required fields.
- Bilingual templates (EN + BN), prompt-injection sanitizer, dual-layer safety intent.
- Sensible deploy assets: Dockerfile, docker-compose healthcheck, railway.json, README w/ MODELS,
  RUNBOOK, sample_output.json.

---

## Recommended deployment mode

**Run keyless (no `GROQ_API_KEY`).** No LLM credits are provided; keyless gives full Evidence/Schema
credit, sub-second latency, and—because templates never request credentials—makes the validator's
false-pos/neg (3B) moot except the SAMPLE-10 quality nit. If a key is used, fix 3A and 3B first.

---

## Fix order (all small, all localized)

1. `rules.py` — `requires_human_review` (1A) + `determine_severity` other→low (1B) + phishing
   keywords (1C); update call site in `investigator.py`.
2. Add `.dockerignore` (2); add `venv/` to `.gitignore` (4).
3. `tests/test_sample_cases.py` — assert severity + human_review; add validator regression test.
4. (If using a key) `llm.py` async + timeout (3A); `safety.py` allowlist inversion (3B).
5. `.github/workflows/ci.yml` (CI); Pydantic ConfigDict + remove dead config (4).

Expected result after step 1: **10/10 graded fields correct** on the public samples and the
systematic phishing misclassification removed for hidden tests.
