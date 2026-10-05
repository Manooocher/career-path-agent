# COMPETITION.md

> Hard rules of the Quera BuildX product event. Source: the organizer's printed pages "توضیحات مسابقه" and "۲ - همراه کاریابی برای یک مسیر شغلی" (quera.org, printed 2026-10-03).
> This file overrides every other document in the repository. If an organizer update changes a rule, update this file first.

## Selected problem (verbatim, Persian)

> **۲ - همراه کاریابی برای یک مسیر شغلی**
> کارجو میان آگهی‌های نامرتبط، نسخه‌های مختلف رزومه و درخواست‌های بی‌پاسخ سردرگم می‌شود. محصولی بسازید که فرصت مناسب استخدام شدن را پیدا کند و کارجو را تا آماده‌شدن یک درخواست همراهی کند (مثل ساخت رزومه کارجو). ایجنت باید ترجیحات و سوابق واقعی فرد را بشناسد، علت تناسب یا عدم تناسب را توضیح دهد و با بازخورد او جست‌وجو و رزومه را اصلاح کند.
>
> نمونه‌های مجاز: همراه کاریابی کارآموز فرانت‌اند که آگهی‌ها را غربال کند و آگهی‌های مناسب را پیشنهاد دهد؛ همراه ساخت رزومه که از کارجو سؤال بپرسد و رزومهٔ او را مطابق استانداردها آماده کند.

The problem statement has five testable obligations. Every one must be visible in the live product:

| ID | Obligation | Where it lives |
|---|---|---|
| P-1 | Find suitable opportunities for **one** career path (the path chosen in each profile) | PRODUCT §1, ARCHITECTURE "Matching" (H0) |
| P-2 | Know the person's **real** preferences and background | PRODUCT §3, §5 (honesty rule) |
| P-3 | Explain fit **and** non-fit | ARCHITECTURE "Matching" (three tiers + excluded list) |
| P-4 | Use feedback to revise **the search** | ARCHITECTURE "Agent design" → feedback graph |
| P-5 | Use feedback to revise **the resume**, through to a ready application | ARCHITECTURE "Agent design" → resume graph |

## Constraints

| ID | Constraint | Consequence if violated |
|---|---|---|
| C-01 | Exactly one problem from the list (we chose #2). | Disqualification |
| C-02 | The product must have an agentic core; an agent as a side feature is not accepted. | Disqualification |
| C-03 | No site builders, agent builders, or automation tools such as n8n. | Disqualification |
| C-04 | Libraries and frameworks such as LangGraph and Pydantic are allowed. | — |
| C-05 | No local execution of LLMs; access must go through a service provider. | Disqualification |
| C-06 | Embedding models are allowed (e.g., for RAG). | — |
| C-07 | A web UI is required. CLI-only, images, mockups, or screens without real functionality are not accepted. | Disqualification |
| C-08 | A user must sign up, log in, give input, and receive the result on the deployed version without help from the team. | Functional test failure |
| C-09 | Heavy infrastructure and secondary features (e.g., forgot password) are not required. | — |
| C-10 | The product must stay available for judging for 10 days after the event ends. | Functional test failure |

## Scoring

| Axis | Points |
|---|---:|
| Technical | 25 |
| UI/UX | 25 |
| Business plan / pitch | 25 |
| Functional test of the product | 25 |

## Deliverables (one zip)

| ID | Deliverable | Required content |
|---|---|---|
| S-1 | Product link | Deployed URL that allows sign-up, login and use through the last step |
| S-2 | 5-minute video (link inside a .txt file) | Idea → execution; problem, target user, agent's role; the real sign-up, login and use through the result **on the live version** |
| S-3 | Technical & infrastructure docs | Architecture, agent execution flow, models and tools, data sources, setup and deployment, costs, technical limitations |
| S-4 | Business plan docs | Problem and target market, value proposition, competitors and differentiation, revenue model, main costs, user-acquisition plan |
| S-5 | Pitch docs | Problem and market opportunity, solution and product demo, competitive advantage, business model, team, growth path |
| S-6 | Full source code | — |

Not required: a custom domain or a separate marketing site.

## Open questions for the organizer

| ID | Question | Status |
|---|---|---|
| Q-01 | Is a synthetic dataset acceptable? | Moot: the team uses real scraped listings (D-14) |
| Q-02 | Must the product UI be Persian? | Open; we build Persian |
| Q-03 | From which network do judges open the link? | Open; the host is in Frankfurt (D-07) |
| Q-04 | Are API credits provided? | Answered: no |
| Q-05 | Exact submission deadline (date and time)? | Open; team estimate: 5 days from 2026-10-04 |
| Q-06 | The problem says «برای یک مسیر شغلی». Is a product that supports several paths, with exactly one path per user profile, within scope? | **Open, ask today**: D-02 depends on it |
