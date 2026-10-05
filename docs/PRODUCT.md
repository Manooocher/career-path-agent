# PRODUCT.md

> Scope authority: what the product does and does not do. Technical choices: `ARCHITECTURE.md`. Pass/fail criteria: `ACCEPTANCE.md`. Hard rules: `COMPETITION.md`. Decisions and open items: `DECISIONS.md`.
> Priority tags: **Must** = blocks submission. **Should** = expected; removed only through the cut list. **Could** = only if time remains.

## 1. Product definition

**CareerPath** (Persian UI name: «همراه شغلی») is a Persian-first web app for tech job seekers in Iran. Each user picks **one** target career path. An agent learns the user's real background and preferences, finds and explains fitting **real** listings for that path, revises the search and the resume from the user's feedback, and prepares an evidence-grounded resume (Persian or English) for one listing the user chooses.

Supported paths (one per profile): frontend, backend, full-stack, mobile, DevOps/cloud, data & AI/ML. All seniority levels from intern to senior.

## 2. Target user

| Item | Value |
|---|---|
| Who | Persian-speaking software job seekers, intern to senior, in one of the supported paths |
| Pain 1 | Listings that cannot work for them (wrong path, onsite in another city, salary below need, wrong level) waste time |
| Pain 2 | Nobody explains why they fit or do not fit |
| Pain 3 | One generic resume for every listing; general AI tools invent experience the person does not have |
| Not targeted | Recruiters, non-software roles |

Demo persona (video and E2E script): **Sara**, junior frontend developer in Shiraz (values in `ACCEPTANCE.md` → "Fixtures"). A second check persona on the deployed data: a junior **backend** developer, to prove the path filter.

## 3. Golden path

| # | Actor | Step | Priority |
|---|---|---|---|
| 1 | User | Opens the public URL, reads the Persian landing page, clicks «شروع» | Must |
| 2 | User | Signs up with email + password and is logged in immediately | Must |
| 3 | User | Chooses one target path and enters preferences (city, relocation, arrangement, work types, seniority, salary floor). Always manual | Must |
| 4 | Agent | Extracts draft skills, projects, education and experience from pasted resume text (Persian or English); the user confirms each item before it becomes evidence. Manual entry is always available | Must |
| 5 | User → Agent | Starts a search; the agent pane shows each step live | Must |
| 6 | Agent | Shows up to 5 real listings for the chosen path: score, label, matched skills, learnable gaps, considerations, explanation, source and fetch date; plus "excluded listings and why" | Must |
| 7 | User → Agent | Gives feedback: a quick reason on a card, or free text in Persian or English | Must |
| 8 | Agent | Interprets the feedback, asks when it is ambiguous (DP-2), applies it, reruns, and shows what changed | Must |
| 9 | Agent | When fewer than 3 listings remain, proposes one relaxation (DP-1) | Could |
| 10 | User | Selects a listing, sees its detail and explanation, clicks «آماده‌سازی درخواست», chooses resume language | Must |
| 11 | Agent | Asks up to 3 evidence questions about missing requirements (DP-3) | Must |
| 12 | Agent | Generates the tailored resume, verifies every claim (DP-4), shows the verification report | Must |
| 13 | User → Agent | Requests changes; the agent revises and re-verifies (max 2 revisions per draft) | Must |
| 14 | User | Copies the resume or prints it to PDF; opens the original listing through its link | Must |

## 4. Agent responsibilities and decision points

The agent combines deterministic tools (normalization, filtering, scoring, diffing, evidence lookup), LLM calls (extraction, interpretation, explanation, writing) and conditional control flow that pauses for the user. Without the agent, steps 4, 6 (explanations), 8, 11, 12 and 13 do not exist; what remains is a filter form over scraped listings.

| ID | Trigger | What the agent decides | What the user sees | Limit | Priority |
|---|---|---|---|---|---|
| DP-1 Relax | Fewer than 3 listings after hard filters | Which single constraint to relax to recover the most listings | A proposal with the gain and two buttons: accept / keep | 1 per run | Could |
| DP-2 Clarify | Feedback is ambiguous or lacks a value | Ask instead of guessing; what to ask; which options to offer | One question with suggested options | 2 rounds, then "no change applied" | Must |
| DP-3 Evidence | The chosen listing requires or prefers skills with no evidence in the profile | Which gaps to ask about (required first, max 3) and how | Questions with answer or skip | 3 per draft | Must |
| DP-4 Verify | After every generation or revision | Which claims lack evidence; remove and rewrite them | Verification report: claims checked, claims removed | 2 rewrite rounds | Must |

Offline, the agent also enriches each scraped listing once (path, seniority, arrangement, city, salary, required vs preferred skills) with a confidence value; low-confidence fields are shown as «نامشخص».

## 5. Honesty rule (Must)

1. The resume and every explanation may only state skills, projects, employers, institutions, degrees, dates and numbers present in **confirmed evidence**: profile items the user entered or explicitly confirmed.
2. A request to fabricate («بنویس سه سال سابقه دارم») is refused with a one-line reason; nothing is added.
3. Listing facts come only from the listing; missing or low-confidence facts are shown as «نامشخص».
4. Every listing shows its source site, a link to the original, and the fetch date, with the note «ممکن است این آگهی منقضی شده باشد».
5. When the LLM is unavailable or the budget is exhausted, deterministic output is labeled «حالت ساده» and is never presented as the agent's reasoning.
6. The product never claims to submit applications or to predict an employer's response.

## 6. Scope

| Feature | Priority |
|---|---|
| Email + password auth, server sessions | Must |
| Profile: one target path, preferences (manual), evidence items | Must |
| Resume-text extraction into confirmable draft items (fa/en) | Must |
| Batch scraper for one source + one-time LLM enrichment + dedupe + frozen snapshot (≥ 300 listings across the six paths) | Must |
| Hard filters (incl. path), deterministic scoring, three-tier explanation, excluded list with reasons | Must |
| Agent pane: live steps and decisions | Must |
| Feedback (quick + free text), DP-2, "what changed" panel | Must |
| DP-3 evidence questions, generation in fa/en, DP-4 verification, 2 revisions | Must |
| Copy + print-to-PDF | Must |
| «حالت ساده» fallback, per-user and global budget caps | Must |
| Privacy notice before profile data is sent to the LLM provider | Must |
| Usable layout at 375 px width | Should |
| DP-1 relaxation proposal | Could |
| Semantic relevance via embeddings | Could |
| "Delete my data" | Could |

Out of scope, with reasons:

| Item | Reason |
|---|---|
| Live scraping during user requests; more than one source | Fragile and slow; ban risk during judging; one parser fits 5 days |
| Forgot password, email verification, SMS OTP | Not required (C-09) |
| Sending applications, quotas, employer dashboard, response promises | No employer side; false claims |
| Code challenges, badges, karma, payments | Security risk or no MVP value |
| Non-software career paths | Skill taxonomy and data quality cannot be ensured in 5 days |

## 7. Success criteria

| Criterion | Target |
|---|---|
| Unassisted completion | An outsider completes the golden path on the live URL in ≤ 10 minutes |
| Visible adaptation | The golden feedback changes the results and the "what changed" panel names each change |
| Honesty | Zero unsupported claims across the evaluation set |
| Data | ≥ 300 real listings covering all six paths; enrichment accuracy targets in ACCEPTANCE met |
| Reliability | Golden scenario passes ≥ 9 of 10 consecutive runs on the deployed version |
| Cost | Total spend ≤ $5 including 10 judging days |

## 8. Golden demo scenario (≈ 2:45 of the 5-minute video)

Run on the frozen snapshot; the exact listings are chosen on day 4 by running the scenario and recorded in `tests/e2e_runs.md`.

1. Sign up as a new user on the live URL.
2. Paste Sara's resume text; confirm the extracted items; choose path «فرانت‌اند» and enter her preferences.
3. Start the search. The agent pane shows: normalize → filter → score → explain. Results show real listings with source and date; the excluded section lists other-city onsite and senior listings with reasons.
4. Type feedback «فقط دورکاری، حداقل حقوق ۲۵ میلیون». Two changes are applied; the "what changed" panel names them and the listings that left.
5. Select a listing that prefers a skill Sara lacks. The agent asks one evidence question; Sara answers «نه، فقط در حال یادگیری». No claim about that skill appears; it is shown as a learnable gap.
6. Choose English, read the resume and its verification report, ask «پروژه Bookshelf را اول بیاور», get version 2, print to PDF.

## 9. Assumptions and risks

| ID | Assumption or risk | Mitigation |
|---|---|---|
| A-1 | [assumption] "Several paths, one per profile" is within the problem's scope (Q-06) | Ask the organizer today; demo always shows one path |
| A-2 | [assumption] The chosen source site allows polite scraping and answers from Frankfurt (G4) | Fallback: run the scraper from a machine in Iran and upload the snapshot |
| A-3 | [assumption] Judges in Iran can reach the Frankfurt host reliably (Q-03, G2) | Test from two Iranian ISPs on day 1 |
| R-1 | $5 total budget across build and 10 judging days | Cheap models chosen at G1, OpenRouter key limit, per-user and daily caps, «حالت ساده» |
| R-2 | Listings expire after the snapshot | Fetch date + "may be expired" note + link to source |
| R-3 | Profile text is sent to a third-party provider | Privacy notice; send only what each step needs; no logging of prompt bodies |
| R-4 | Scope is larger than 68 build hours | Cut list in `ARCHITECTURE.md`; decide cuts at the evening checkpoint |
