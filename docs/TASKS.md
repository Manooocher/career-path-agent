# TASKS.md

> Execution plan v2: 2 people × 5 days × ~8 h (D-03, D-04). Vertical slices; every evening ends with a checkpoint on the live URL.
> Owners: **A** = Agent & Data, **B** = Platform & Delivery (D-05). **HUMAN** = cannot be done by Claude Code.
> Size: **S** ≤ 2 h, **M** ≤ 4 h. A task that grows beyond M is split before continuing.
> Each task lists the ARCHITECTURE sections to read. Read only those, plus the AC rows referenced.
> Status markers: `[ ]` todo, `[~]` in progress, `[x]` done (ACs verified), `[!]` blocked (write the blocker under the task).

## Capacity check

| Item | Hours |
|---|---:|
| Available (2 × 8 h × 5 days) | 80 |
| Build tasks below | ~70 |
| Business plan, pitch, technical doc, video, package | ~10 |
| Buffer | **0** |

There is no buffer. If an evening checkpoint is missed, apply ARCHITECTURE "Cut list" that evening, or agree on overtime for the next day. Draft the business plan and pitch with an AI assistant before day 5 (HUMAN review only) to protect the 25 business/pitch points.

## Day map

| Day | A — Agent & Data | B — Platform & Delivery | Checkpoint |
|---|---|---|---|
| 1 | G1, G4, T-104, T-202a | G2, G3, T-101, T-102, T-105 | CP-1 |
| 2 | T-210, T-211 | T-103, T-201 | CP-2 |
| 3 | T-203, T-301, T-302 | T-305, T-204, T-303 | CP-3 |
| 4 | T-401, T-501, T-502 | T-212, T-402, T-503 | CP-4 |
| 5 | T-602, fixes, H-701, H-702 | T-603, T-604, T-605, H-703, H-705 | CP-5 (freeze 12:00), then H-704 |

## Slice 0 — Gates (day 1 morning)

### G1 Models and cost `[ ]`
- **Owner** A + HUMAN · **Size** S · **Depends** —
- **Do** Set the OpenRouter key credit limit to $5. Shortlist 2–3 candidates per tier; for each, run 5 structured-output calls with Persian input from the VPS; record JSON validity, Persian quality, latency, cost per call. Pick primary + fallback (different providers) per tier so that one golden flow costs ≤ $0.02.
- **Done when** O-01 resolved in `DECISIONS.md`; model lists in the VPS `.env`.

### G2 VPS and reachability `[ ]`
- **Owner** B + HUMAN · **Size** S · **Depends** —
- **Do** Inbound test (judges → our server). (1) SSH by key only, password and root login disabled. (2) Firewall allows only 22, 80, 443. (3) Automatic security updates on. (4) A host name (cheap domain preferred) resolves to the VPS IP. (5) Caddy serves a test page with a valid certificate. (6) The page opens from two Iranian networks (mobile + fixed-line) without VPN. (7) An external port check shows 5432 closed.
- **Done when** All seven checks pass; O-02 resolved.

### G3 Tooling `[x]`
- **Owner** A + B · **Size** S · **Depends** —
- **Do** Repo with these docs; branch rule `t-<id>-<slug>`; PRs reviewed by the other person.

### G4 Source site `[ ]`
- **Owner** A + HUMAN · **Size** S · **Depends** —
- **Do** Outbound test (our server → source), for the shortlist in DECISIONS O-07. A `200` on the home page is **not** enough. Per site, from the VPS: (1) a listing **detail** page returns 200; (2) its raw HTML (no JavaScript) contains the title, company, city and description, not a bot-challenge page; (3) 20 detail requests at 5 s spacing return no 403/429; (4) listing URLs are discoverable without disallowed URLs (sitemap or category pages); (5) fields needed by the jobs schema are present; (6) the site's terms page does not forbid automated collection; (7) at least 50 recent listings per path. Save 10 raw detail pages per finalist into `tests/fixtures/html/<site>/`.
- **Done when** One site passes all seven checks; O-07 resolved; ARCHITECTURE "Ingestion" → "Source profile" filled; sample pages committed.

## Slice 1 — Walking skeleton (day 1)

### T-101 Scaffold and configuration `[ ]`
- **Owner** B · **Size** M · **Depends** G3
- **Read** Stack decisions, Repo layout, Deployment
- **Paths** `pyproject.toml`, `app/main.py`, `app/config.py`, `Dockerfile`, `deploy/docker-compose.yml`, `deploy/Caddyfile`
- **Done when** App runs locally with containerized PostgreSQL; missing env var stops startup clearly; `/healthz` reports db status; commands written into `CLAUDE.md` "Commands".
- **AC** SR-08, SR-09

### T-102 Database baseline `[ ]`
- **Owner** B · **Size** S · **Depends** T-101
- **Read** Schemas (users, sessions, login_attempts), Deployment
- **Paths** `app/db/`, `alembic/`
- **Done when** Migrations run on start; an integration test creates and reads a user.
- **AC** AC-DEPLOY-003

### T-104 LLM adapter `[ ]`
- **Owner** A · **Size** M · **Depends** G1, T-101
- **Read** LLM access, Schemas (llm_usage), Security
- **Paths** `app/llm/`, `app/prompts/smoke.md`, `tests/unit/test_llm_*`
- **Done when** OpenRouter calls with `models` lists and `require_parameters`; timeouts; one retry; Pydantic validation with one repair; usage rows with cost from the response; per-user and global caps; fault injection (refused in production). Mocked-transport tests for success, timeout, invalid JSON, cap reached.
- **AC** AC-REL-006, AC-SEC-005, SR-03, SR-09

### T-202a Test fixtures and taxonomy seed `[x]`
- **Owner** A · **Size** S · **Depends** —
- **Read** Schemas (jobs), Normalization; ACCEPTANCE "Fixtures"
- **Paths** `tests/fixtures/jobs_fixtures.json`, `data/taxonomy/skills.json`, `data/taxonomy/paths.json`
- **Done when** J01–J08 match ACCEPTANCE exactly; taxonomy covers the fixtures and the most common skills of the six paths with Persian and English aliases.
- **AC** AC-DATA-002

### T-105 First deploy `[ ]`
- **Owner** B · **Size** S · **Depends** G2, T-102
- **Read** Deployment, Topology
- **Paths** `deploy/`
- **Done when** Compose stack on the VPS; HTTPS host name serves `/healthz` with db ok; PostgreSQL not reachable from outside.
- **AC** AC-DEPLOY-001, AC-DEPLOY-003, AC-DEPLOY-007

**CP-1** Live HTTPS URL reachable from Iran; `/healthz` ok; a smoke LLM call from the VPS succeeds; source site decided.

## Slice 2 — Auth, profile, data (day 2)

### T-103 Auth and base layout `[ ]`
- **Owner** B · **Size** M · **Depends** T-102
- **Read** Routes, Security, UI system
- **Paths** `app/auth/`, `app/security/`, `app/web/templates/base.html`, `landing.html`, `signup.html`, `login.html`, `app/web/static/`
- **Done when** Sign-up logs the user in; login/logout; DB sessions; CSRF on every POST; login rate limit; RTL layout with tokens, Vazirmatn, vendored HTMX; labels, keyboard paths and contrast checked; Persian copy; integration tests per AC.
- **AC** AC-AUTH-001 … AC-AUTH-008, AC-SEC-001, AC-SEC-003, AC-UX-001, AC-UX-005, SR-06

### T-201 Profile and evidence `[ ]`
- **Owner** B · **Size** M · **Depends** T-103
- **Read** Schemas (profiles, evidence items), Normalization, Routes, UI system
- **Paths** `app/profile/`, `app/web/templates/profile*.html`
- **Done when** Target path + manual preferences; evidence items with add/remove and confirm; Persian validation; normalization on save; privacy notice; tests incl. Persian digits and aliases.
- **AC** AC-PROF-001, AC-PROF-002, AC-PROF-003, AC-PROF-005, AC-PROF-006

### T-210 Scraper: discover, fetch, parse, clean `[ ]`
- **Owner** A · **Size** M · **Depends** G4, T-102
- **Read** Ingestion, Schemas (jobs), Normalization
- **Paths** `app/ingest/sources/<site>`, `app/ingest/clean*`, `tests/unit/test_ingest_*` (saved sample HTML, no live calls)
- **Done when** Batch command collects ≥ 400 listing pages across the six paths with ≥ 3 s delay; PII stripped; salary and city parsed; tests on saved pages.
- **AC** AC-DATA-003, AC-DATA-006, SR-11, SR-12

### T-211 Enrichment, dedupe, snapshot `[ ]`
- **Owner** A · **Size** M · **Depends** T-210, T-104
- **Read** Ingestion, LLM access, Prompt rules
- **Paths** `app/ingest/enrich*`, `app/ingest/dedupe*`, `app/ingest/snapshot*`, `app/prompts/enrich_listing.md`
- **Done when** Batches of 5; schema-validated fields with confidence; cached by version; dedupe by URL; export/import; enrichment cost logged (≤ $0.75).
- **AC** AC-DATA-001, AC-DATA-005

**CP-2** Live: sign up, log in, save a profile, log out and back in. Locally: ≥ 300 enriched listings across the six paths.

## Slice 3 — Matching and agent core (day 3)

### T-203 Matching core `[x]`
- **Owner** A · **Size** M · **Depends** T-202a
- **Read** Normalization, Matching, Enums and mappings
- **Paths** `app/matching/`, `tests/unit/test_matching_*`
- **Done when** H0–H5, score, labels, tiers, tie-break, reasons, path counts, diff (relaxation search only if DP-1 is kept); fixture tests reproduce "Expected outcomes" exactly; property tests.
- **AC** AC-MATCH-001, AC-MATCH-004, AC-MATCH-005, AC-MATCH-006, SR-10

### T-301 Runner and checkpointer `[ ]`
- **Owner** A · **Size** S · **Depends** T-104
- **Read** Execution model, Agent design (first paragraph), Schemas (runs, agent_questions)
- **Paths** `app/agent/runner*`, `app/agent/state*`
- **Done when** Background runs; one active run per user; interrupt → `awaiting_user` → answer resumes the same thread; startup recovery; tests.
- **AC** AC-AGENT-003, AC-REL-004, AC-REL-008

### T-302 Match graph `[ ]`
- **Owner** A · **Size** M · **Depends** T-301, T-203
- **Read** Agent design (Match graph, Prompt rules), Fallback mode, LLM access
- **Paths** `app/agent/graphs/match*`, `app/prompts/explain.md`, `tests/agent/`
- **Done when** M1–M9; one batched explanation call; ground check with template fallback; «حالت ساده» under fault injection or budget cap; decisions trace; mocked tests.
- **AC** AC-MATCH-003, AC-AGENT-004, AC-AGENT-005, AC-REL-009, SR-04, SR-05

### T-305 Resume-text extraction `[ ]`
- **Owner** B · **Size** S · **Depends** T-201, T-301
- **Read** Agent design (Extract graph), Routes
- **Paths** `app/agent/graphs/extract*`, `app/prompts/extract_resume.md`, profile templates
- **Done when** Persian and English text → draft items; confirm converts to evidence; preferences untouched.
- **AC** AC-PROF-004

### T-204 Results view `[ ]`
- **Owner** B · **Size** S · **Depends** T-201, T-203
- **Read** UI system, Routes, Schemas (match_results)
- **Paths** `app/web/templates/results*.html`
- **Done when** Cards with every AC-MATCH-002 field incl. source and date; excluded section; other-path count; empty state.
- **AC** AC-MATCH-002, AC-DATA-005, AC-UX-002

### T-303 Run page and agent pane `[ ]`
- **Owner** B · **Size** M · **Depends** T-204, T-301
- **Read** UI system, Routes, Execution model
- **Paths** `app/web/templates/run*.html`, `agent_pane*.html`, `question_form.html`
- **Done when** Polling partial with steps; decisions trace; generic question form (options, free answer, skip); «حالت ساده» badge; limit messages; error with retry; stacks below main pane at ≤ 768 px.
- **AC** AC-AGENT-001, AC-REL-006, AC-UX-002, AC-UX-004

**CP-3** Live, with the snapshot imported: Sara's search shows steps and grounded explanations within 30 s; extraction works on her resume text.

## Slice 4 — Feedback and resume (day 4)

### T-212 Data QA and snapshot freeze `[ ]`
- **Owner** B + HUMAN · **Size** S · **Depends** T-211
- **Read** ACCEPTANCE AC-DATA rows
- **Do** Label 30 random listings by hand; compare with enrichment; record in `tests/data_qa.md`; freeze and import the final snapshot by noon.
- **AC** AC-DATA-004

### T-401 Feedback graph `[ ]`
- **Owner** A · **Size** M · **Depends** T-302
- **Read** Agent design (Feedback graph, Prompt rules), Schemas (search_sessions, feedback), Normalization
- **Paths** `app/agent/graphs/feedback*`, `app/prompts/feedback_parse.md`, `app/prompts/clarify.md`
- **Done when** F1–F5; allowlist; DP-2 with 2-round cap; search vs profile scope; child run with parent; fixture test reproduces "After golden feedback"; injection inputs produce no effect.
- **AC** AC-FBK-002, AC-FBK-004, AC-FBK-005, AC-FBK-006, AC-FBK-007

### T-402 Feedback UI and "what changed" `[ ]`
- **Owner** B · **Size** S · **Depends** T-303, T-401
- **Read** UI system, Matching (Diff), Routes
- **Done when** Quick reasons per card; free text box; clarification in the agent pane; "what changed" panel; "hidden by you" list.
- **AC** AC-FBK-001, AC-FBK-003

### T-501 Resume graph R1–R4 `[ ]`
- **Owner** A · **Size** S · **Depends** T-301, T-201
- **Read** Agent design (Resume graph), Schemas (agent_questions, evidence items)
- **Paths** `app/agent/graphs/resume*`, `app/prompts/evidence_questions.md`, `app/prompts/absorb_answers.md`
- **Done when** Gaps required-first, max 3; interrupt; answers become evidence or nothing; fixture tests for J01 (1 question) and J04 (2 questions).
- **AC** AC-APP-001, AC-APP-002

### T-502 Generation and verification R5–R8 `[ ]`
- **Owner** A · **Size** M · **Depends** T-501
- **Read** Agent design (Resume graph, Verification rules), Schemas (resume_drafts, resume_claims), Security
- **Paths** `app/agent/graphs/resume*`, `app/agent/verify*`, `app/prompts/resume_generate.md`
- **Done when** fa/en sections with evidence refs; V1–V3; rewrite loop ≤ 2; fabrication refusal; revise kind re-enters at R5, max 3 versions; tests with planted unsupported claims.
- **AC** AC-APP-003, AC-APP-004, AC-APP-005, AC-APP-006, AC-APP-008, AC-REL-003

### T-503 Listing detail, resume page, print `[ ]`
- **Owner** B · **Size** M · **Depends** T-303, T-502
- **Read** UI system, Routes, Security
- **Paths** `app/web/templates/job_detail.html`, `draft*.html`, `print.html`, `app/security/sanitize*`
- **Done when** Detail page with source link; language choice; resume page (RTL for fa, LTR for en) with verification report, versions and revision box; copy as text; A4 print; sanitizer tests.
- **AC** AC-APP-007, AC-SEC-004

**CP-4** Full golden E2E script passes once on the live URL with the frozen snapshot; the chosen demo listing is recorded in `tests/e2e_runs.md`.

## Slice 5 — Release and submission (day 5)

### T-602 Evaluation and adversarial tests `[ ]`
- **Owner** A · **Size** S · **Depends** T-401, T-502
- **Read** ACCEPTANCE "Agent evaluation set", Security
- **Done when** 10 cases pass with the mock; one live run recorded (≥ 9/10, 0 fabricated claims); IDOR tests for runs, drafts, profile.
- **AC** AC-FBK-007, AC-APP-005, AC-SEC-002, AC-SEC-005

### T-603 Operations `[ ]`
- **Owner** B · **Size** S · **Depends** T-105
- **Read** Deployment, Failure modes
- **Done when** Nightly off-VPS backup with one restore; uptime monitor with alert; cold-start check; 5-user concurrency test.
- **AC** AC-DEPLOY-002, AC-DEPLOY-004, AC-DEPLOY-005, AC-REL-005

### T-604 Unassisted usability test `[ ]`
- **Owner** A + B + HUMAN · **Size** S · **Depends** CP-4
- **Do** Two outsiders run the golden path on the live URL with no help (day 4 evening or day 5 morning); fix the top 3 issues.
- **AC** AC-UX-003

### T-605 Ten-run release check `[ ]`
- **Owner** B (A fixes) · **Size** S · **Depends** CP-4
- **Do** Run the golden E2E script 10 times on the live URL; record durations, failures and cost in `tests/e2e_runs.md`; sign off the "Static review checklist" (SR-01 … SR-12).
- **AC** AC-REL-001, AC-REL-002, AC-REL-007, AC-DEPLOY-006, SR-01, SR-02, SR-07

### H-701 Business plan (Persian) `[ ]` — Owner A + HUMAN · Draft before day 5, final day 5 morning · `SUBMISSION.md`
### H-702 Pitch (Persian) `[ ]` — Owner A + HUMAN · Day 5 morning
### H-703 Technical documentation (Persian) `[ ]` — Owner B + HUMAN · Day 5; from ARCHITECTURE + real costs from `llm_usage`
### H-704 Video `[ ]` — Owner A + B + HUMAN · Day 5 after freeze; recorded on the live URL
### H-705 Package `[ ]` — Owner B + HUMAN · Day 5; zip with link, `.txt` with video link, docs, source without `data/snapshot/`; secret scan

## Could (only if a checkpoint finishes early)

| ID | Item | Owner | AC |
|---|---|---|---|
| T-403 | DP-1 relaxation proposal | A | AC-AGENT-002 |
| T-801 | H6 military-clearance filter | A | — |
| T-802 | Embedding-based relevance | A | — |
| T-803 | Delete-my-data | B | — |

## Cut list

Use the order in ARCHITECTURE "Cut list". Decide cuts at the evening checkpoint, never mid-task. Record each cut as a new row in `DECISIONS.md`.
