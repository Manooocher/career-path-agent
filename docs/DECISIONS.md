# DECISIONS.md

<!-- CONTEXT INJECTION BLOCK — READ THIS FIRST
  Document Type : DECISION_LOG
  Generated     : 2026-10-04
  Domain(s)     : SW Arch | SWE | AI Agent Systems | IT
  Project       : CareerPath (job-search-agent), Quera BuildX Problem #2
  Status        : active
  Intended for  : Claude Code and the two team members
  RULES FOR AI:
  1. [stated] = said by the team. [decision] = chosen in planning. [assumption] = default pending confirmation. [open] = blocked on a human.
  2. Never act on an [open] item. Stop and ask.
  3. Never re-introduce an item from "Rejected" without a new decision row.
-->

## Status legend

| Tag | Meaning |
|---|---|
| [stated] | Fact given by the team |
| [decision] | Chosen during planning; change only with a new row |
| [assumption] | Default chosen to unblock work; confirm or replace at the named gate |
| [open] | Must be resolved by a human before the dependent task starts |
| [derived] | Computed from other rows |

## Decisions

Version 2 (2026-10-04): updated with the team's answers. Superseded values are noted in the Rationale column.

| ID | Topic | Decision | Tag | Rationale | Rejected alternative |
|---|---|---|---|---|---|
| D-01 | Problem | BuildX Problem #2 only | [stated] | Team choice | — |
| D-02 | Career paths | The product supports several tech career paths; **each profile targets exactly one path** at a time. Paths v1: frontend, backend, full-stack, mobile, DevOps/cloud, data & AI/ML. All seniority levels | [stated] + [decision] | Team: the frontend intern case was only an example. "One path per profile" keeps the problem's wording («برای یک مسیر شغلی») true for every user; confirm with organizer (Q-06). Supersedes v1 "junior frontend only" | One fixed path for everyone; many paths per profile |
| D-03 | Team and time | 2 people, ~8 h/day each, **5 days remaining** as of 2026-10-04 | [stated] | — | — |
| D-04 | Capacity | 80 person-hours: ~70 h build + ~10 h business plan, pitch, technical doc, video, package. **Zero buffer**: a missed checkpoint triggers the cut list or agreed overtime | [derived] | D-03 | — |
| D-05 | Roles | **A = Agent & Data** (graphs, prompts, scraping and enrichment, matching, evaluation, business plan, pitch). **B = Platform & Delivery** (VPS, backend, UI, auth, deploy, data QA, technical doc, video) | [decision] | Confirmed by the team | — |
| D-06 | LLM access | OpenRouter only, through the OpenAI-compatible adapter (`https://openrouter.ai/api/v1`). Failover = OpenRouter's ordered `models` fallback list (a second model from a different provider), not a second account. Request `require_parameters` so structured-output requests only route to providers that support them | [stated] + [decision] | Team bought OpenRouter credit; Frankfurt host has no regional block. Supersedes Iranian gateway default | Iranian gateway; direct provider APIs |
| D-07 | Hosting | Frankfurt VPS with Docker Compose: Caddy (automatic HTTPS) + app + PostgreSQL (internal network only). Host name: a cheap domain, or a wildcard-DNS host name pointing at the IP, so Caddy can obtain a certificate | [stated] + [decision] | Team rented the VPS. Supersedes Iranian PaaS default | Managed PaaS |
| D-08 | UI language | Persian, RTL | [decision] | Users are Persian speakers | English UI |
| D-09 | Resume language | Persian or English, chosen per draft; pasted resumes may be in either language | [stated] | Team answer 8. Supersedes v1 "toggle = Should" | Persian only |
| D-10 | Stack | Python 3.12, FastAPI, Jinja2 + HTMX (vendored), hand-written CSS tokens, Vazirmatn (self-hosted), PostgreSQL 16, SQLAlchemy 2 + Alembic, Pydantic v2, LangGraph + Postgres checkpointer, OpenAI Python SDK pointed at OpenRouter | [stated] | Confirmed by the team | Next.js split app |
| D-11 | Database | PostgreSQL in every environment | [decision] | — | SQLite locally |
| D-12 | Retrieval | No embeddings in the MVP; deterministic filters + weighted skill scoring over the snapshot | [decision] | $5 budget; a few hundred listings | pgvector |
| D-13 | Auth | Email + password, Argon2, server-side sessions, CSRF | [decision] | — | SMS OTP, JWT + Redis |
| D-14 | Listings data | **Real listings**, collected by a batch scraper from **one** primary Iranian job site chosen at gate G4 (robots.txt and terms checked), enriched once into structured fields by the FAST model, deduplicated by source URL, and **frozen as a snapshot by noon of day 4**. Every listing shows source, link and fetch date. Synthetic fixtures J01–J08 exist only in the test database | [stated] + [decision] | Team: real data scores better and is the priority. Batch + snapshot keeps the demo stable and costs predictable. Supersedes v1 synthetic dataset | Live scraping during user requests; several sources |
| D-15 | Agent decision points | DP-2 clarify, DP-3 evidence questions, DP-4 verification: Must. DP-1 relaxation: **Could** | [decision] | 5 days instead of 7 | All four as Must |
| D-16 | Feedback scope | Search session by default; explicit statements about the user change the profile | [decision] | — | — |
| D-17 | Hard vs soft | Hard: career path (H0), arrangement + city, salary floor when known, seniority two levels away, work type, user-hidden listings. Everything else is score-only. Unknown salary is neutral («توافقی» counts as unknown) | [decision] | Iranian listings often state salary as «توافقی» | — |
| D-18 | Output | Sanitized HTML resume with A4 print view + copy as text, in Persian (RTL) or English (LTR) | [decision] | — | Server-side PDF |
| D-19 | Budget | **$5 total** for build week + 10 judging days. OpenRouter key credit limit set to $5. Allocation: ingestion ≤ $0.75, development and tests ≤ $1.25, judging reserve ≥ $3.00 (`LLM_DAILY_BUDGET_USD` = 0.30 during judging). Model choice at G1 must keep one full golden flow ≤ $0.02 | [stated] + [decision] | Team answer 4; organizer provides no credits | Unlimited calls |
| D-20 | Submission language | Persian | [assumption] | — | — |
| D-21 | Profile entry | Pasted resume text (Persian or English) is extracted into draft evidence items the user confirms. Preferences are **always entered by the user**: target path, city, relocation, arrangement, work types, seniority, salary floor | [stated] | Team answer 10 | Fully automatic profile |
| D-22 | Scraping rules | Respect robots.txt and the site's terms; ≥ 3 s between requests; identify the client honestly; store only listing fields + a short excerpt + source URL; drop recruiter names, phone numbers and emails; never scrape during user requests; keep the raw snapshot out of any public repository | [decision] | Legal and reputational safety | Aggressive crawling |

## Rejected from the AI Studio master spec

| ID | Rejected item | Reason |
|---|---|---|
| R-01 | 60-second code micro-challenges and "verified" badges | Requires executing user code (security risk); the reference code faked verification by returning a fixed skill list |
| R-02 | Karma economy, power levels, cryptographically signed badges | No user value in a one-week MVP; pitch vision at most |
| R-03 | Applicant quota (max 15), "dispatch", "status within 48 hours" | No employer side exists; these would be false claims |
| R-04 | Redis (cache, sessions, rate limit) | Postgres covers it at this scale |
| R-05 | pgvector, HNSW, 1536-d embeddings | See D-12 |
| R-06 | Next.js split frontend | See D-10 |
| R-07 | SMS OTP, Shaparak / BNPL payments | Not required (C-09); extra failure points during judging |
| R-08 | GEO / JSON-LD / SEO work | Does not affect any scoring axis of the MVP |
| R-09 | Hardcoded resume content (sample projects, sample experience, placeholder name) | Violates the honesty rule |
| R-10 | Auto-approval after two feedback rounds; auto-selecting the top listing | Fakes human-in-the-loop; the user must choose |
| R-11 | Min-heap / Hoare-logic / "O(log N)" claims | Unmeasured or untrue for the shipped code; sorting 40 items is trivial |
| R-12 | Unsourced market numbers (TAM 45k, 90B Toman, "<2% conversion", "150 resumes") and "100% guaranteed availability" | Unverifiable claims in front of judges |
| R-13 | Compose file with default passwords, public DB/Redis ports, `NEXT_PUBLIC_API_URL=http://backend:8000` | Security flaws; the browser cannot resolve an internal container hostname |
| R-14 | Positioning Quera Jobs as an incumbent that "cannot copy us" | Quera runs this event; frame Quera's community as a channel/partner instead |
| R-15 | Live scraping inside the user flow | Slow, fragile, and can get the server blocked during judging |
| R-16 | Several scrape sources in the MVP | Each source is a separate parser; one source fits 5 days |

## Kept from the AI Studio master spec

| ID | Kept item | Where |
|---|---|---|
| K-01 | Cyclic LangGraph with human-in-the-loop and a Postgres checkpointer | ARCHITECTURE "Agent design" |
| K-02 | Three-tier explanation: matched skills, learnable gaps, dealbreakers (as exclusion reasons) | ARCHITECTURE "Matching" |
| K-03 | Required vs optional skills with guarded ratios (no division by zero) | ARCHITECTURE "Matching" |
| K-04 | Persian text normalization (Arabic ي/ك, ZWNJ, digits) | ARCHITECTURE "Normalization" |
| K-05 | Split workspace: main pane + agent pane | ARCHITECTURE "UI system" |
| K-06 | Dual-provider failover | ARCHITECTURE "LLM access" |
| K-07 | Sanitized Markdown/HTML output against stored XSS | ARCHITECTURE "Security" |
| K-08 | Self-hosted static assets (no CDN dependency inside Iran) | ARCHITECTURE "UI system" |
| K-09 | Remote/onsite city dealbreaker (e.g., Tehran onsite for a Shiraz candidate) | ARCHITECTURE "Matching" |

## Open items

| ID | Item | Owner | Gate | Blocks |
|---|---|---|---|---|
| O-01 | `FAST` and `SMART` model IDs on OpenRouter (Persian quality, JSON-schema support, cost per golden flow ≤ $0.02). Shortlist (prices from third-party trackers, early October 2026; confirm on each openrouter.ai model page): DeepSeek V4 Flash, DeepSeek V4.1 Flash, Gemini 3.1 Flash Lite as cross-provider fallback. Rejected on cost: Gemini 3.x Flash (~$0.75/$3.75 per M ≈ $0.045 per flow). Reasoning tokens off or minimal for every call | A | G1 | T-104 and every LLM task |
| O-02 | Host name + HTTPS on the VPS; reachability from two Iranian ISPs | B | G2 | T-105 |
| O-07 | Source site. robots.txt reviewed 2026-10-04: **Jobinja** allows all (first candidate); **JobVision** blocks every URL with `?`, so discovery via its sitemap only (second candidate; check whether pages are server-rendered); **IranTalent** blocks search and query URLs, detail pages via sitemap (many English listings); **Karboom** allows job pages, has a sitemap; **e-estekhdam** allows job pages but sets crawl-delay 5 for named bots, broad non-tech market; **IranEstekhdam** allows all but is mostly government/newspaper ads (rejected). robots.txt is not permission: terms must be read too. Final choice by the seven G4 checks | A | G4 | T-210 |
| O-05 | Organizer: exact deadline (Q-05), multi-path reading (Q-06), UI language (Q-02), judges' network (Q-03) | B | Day 1 | D-02, D-07 |
