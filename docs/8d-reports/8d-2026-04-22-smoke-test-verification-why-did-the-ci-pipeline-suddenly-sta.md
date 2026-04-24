# 8D Report: Smoke Test Verification — CI Pipeline Tuesday-Only Timeout

**Date**: 2026-04-22T07:24:15.079468
**Problem**: Smoke test verification: why did the CI pipeline suddenly start timing out on Tuesdays only
**Run ID**: run-1776812257-ee3f97f2
**Model**: Claude (8D MRC LangGraph pipeline, Phase 0 → Phase 8)
**Total Elapsed**: Full pipeline run covering Phases 0–7, including dual-tier research, three audit rounds in Phase 3, three audit rounds in Phase 5, and Phase 6 verification planning.

---

## Pipeline Timeline (Detailed Progress Log)

The 8D MRC skill executed as a LangGraph FSM with the following phase transitions:

- **Phase 0 — Dual-Tier Research (Meta + Analogous Domains)**
  - Identified three meta-categories of the problem class:
    1. Periodic temporal anomaly in a shared-resource system
    2. Hidden cyclical contention between independently scheduled jobs
    3. Calendar-correlated capacity degradation with no obvious causal link
  - Selected three analogous domains for cross-domain pattern transfer:
    1. Commercial aviation on-time performance (Tuesday maintenance-window cascades)
    2. Electrical grid load dispatch (weekly peak-demand brownouts)
    3. Hospital operating-room throughput (elective-surgery-day bottlenecks)
  - Purpose: seed the Why-chain generation with cross-domain prior that periodic shared-resource contention is the default hypothesis for day-of-week-periodic failure modes.

- **Phase 1 — IS / IS NOT Scoping**
  - Generated all four dimensions (what / where / when / extent) with IS, IS NOT, and distinction (what the distinction rules in or out).
  - Key diagnostic: `when` dimension — sudden-onset weekly periodicity → maps to scheduled external event.

- **Phase 2 — Why-Chain Generation (4 Quadrants)**
  - Drafted chains for q1 (TRC-NC), q2 (TRC-ND), q3 (MRC-NC), q4 (MRC-ND).
  - Q1 produced 11 whys with an explicit branch at Why #8 (sibling cause B: unbounded deadlines).
  - Q2 produced 11 whys bottoming at missing observability contract.
  - Q3 produced 12 whys bottoming at absence of a governance owner for operational-excellence policy.
  - Q4 produced 11 whys bottoming at the policy-scope defect in the management review mandate.

- **Phase 3 — RC Audit Loop (3 rounds)**
  - Round 1 verdict: CONTINUE (truncated q2, missing q3/q4, Why #7 restates Why #6, Why #11 is synthesis).
  - Round 2 verdict: CONTINUE (Why #8 parallel cause not labeled, Why #10 unverified, counterfactual not tested).
  - Round 3 verdict: CONTINUE (Why #7 still a restatement, Why #11 truncated, chain stops short of NC/MRC crossover).
  - Loop-back: Phase 2 was revisited to incorporate audit_notes, but residual weaknesses remain RESIDUAL (documented, not silently dropped).

- **Phase 4 — Corrective and Prevention Actions per Quadrant**
  - Corrective actions scoped to Q1 (TRC-NC) and Q2 (TRC-ND).
  - Prevention actions scoped to Q3 (MRC-NC) and Q4 (MRC-ND), each with hierarchy-of-controls classification, failure-mode-of-prevention analysis, and deployment scope.

- **Phase 5 — Prevention Audit Loop (3 rounds)**
  - Round 1 verdict: CONTINUE (Q3 hierarchy level inflated, shared-infra detection blind spot, emergency-change bypass under-controlled, Q4 truncated).
  - Round 2 verdict: CONTINUE (CAB-bypass surface unaddressed, threshold self-declared/gameable, annual cadence too slow, fail-open surface uncounted).
  - Round 3 verdict: EXHAUSTED (remaining weaknesses documented as RESIDUAL; ADDRESSABLE fixes accepted or escalated).

- **Phase 6 — Verification Plan + Proof of Action**
  - Fallback skeleton populated for all four quadrants (metric/target/data_source/baseline/measurement_schedule/failure_response fields marked TBD pending PoA evidence attachment).
  - Overall timeframe: 6 months minimum.
  - Phase 8 trigger: next recurrence of the same problem class.

- **Phase 7 — Closure Audit**
  - Verified: all four quadrants have Why-chains, roots, corrective/prevention actions, and gate tests where required.
  - Flagged: Q4 prevention action truncated in audit payload (Round 2/3 could not fully audit), Phase 6 verification metrics marked TBD.

---

## Section A: Root Cause Matrix

|       | Non-Conformance (NC)                                                                                                                                                                   | Non-Detection (ND)                                                                                                                                                                  |
|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: Smoke stage has neither data-tier isolation from non-CI workloads nor bounded per-operation deadlines in the test harness — removing either one alone prevents the Tuesday timeout. | Q2: CI/test plane has no observability contract — no duration SLIs, no per-dependency spans, no seasonality-aware detectors, no change-calendar correlation.                        |
| MRC   | Q3: No governance owner maintains the operational-excellence / service-tiering policy to include internal developer platforms (CI), so uncoordinated cross-tenant workloads are allowed. | Q4: Governance policy mandates review content around customer-facing OKRs only — no reporting mandate for internal-platform reliability, producing a self-reinforcing blind spot.  |

---

## Section B: Corrective Actions Matrix

|       | Non-Conformance (NC)                                                                                                                                                | Non-Detection (ND)                                                                                                                                                 |
|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: Apply `statement_timeout=15s` to smoke-test DB role + per-test client-side deadlines + one-shot Tuesday scheduled-job reschedule for 2 Tuesdays.                | Q2: Instrument smoke stage as observable probe — duration metric, per-dependency spans, seasonality-aware alert at 60% of hard timeout, Tuesday-event overlay.     |
| MRC   | Q3: (See Prevention — systemic)                                                                                                                                      | Q4: (See Prevention — systemic)                                                                                                                                     |

---

## Section B2: Prevention Actions Matrix

|       | Non-Conformance (NC)                                                                                                                                                                             | Non-Detection (ND)                                                                                                                                                                       |
|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: (See Corrective — instance-scoped)                                                                                                                                                           | Q2: (See Corrective — instance-scoped)                                                                                                                                                   |
| MRC   | Q3: Charter Director-level Operational Governance Owner (OGO); service-catalog entry mandatory for any shared infra; CAB auto-rejects without catalog DRI; annual attestation + provisioning gate. | Q4: CI Observability Contract as monitoring-as-code — per-stage duration SLIs, declared soft-SLO, seasonality-aware anomaly rules, pre-merge lint gate, scheduled-workload registry. |

**Q3 gate_test evidence:**
- **Scope (PASS)**: Prevents the class, not the instance. CAB tooling's catalog-lookup rule blocks ANY uncoordinated recurring workload on ANY shared internal infrastructure (CI, artifact store, shared DBs, test clusters). Annual policy-scope attestation covers platforms that do not yet exist.
- **Persistence (PASS)**: Three reinforcing artifacts — chartered role with board-reported KPI (survives turnover), CAB tool config-as-code (mechanical enforcement), version-controlled policy repo with annual-review CI check.
- **Measurability (PASS)**: Third-party auditor at 6-month mark verifies — (1) OGO charter exists with KPI, (2) service-catalog entries cross-checked against VPC/namespace telemetry, (3) CAB rejection rule present in config-as-code with test case, (4) signed/dated annual attestation, (5) KPI dashboard trend.

**Q4 gate_test evidence:**
- **Scope (PASS)**: Prevents the entire class of slow-burn CI degradation invisible until hard timeout. Contract applies uniformly to every stage and every scheduled job, current and future.
- **Persistence (PASS)**: Required pre-merge status check backed by lint rule in version control. Dashboards, alert rules, and scheduled-workload registry generated from checked-in config via monitoring-as-code.
- **Measurability (PASS)**: Third-party auditor in 6 months verifies — (1) `.ci-observability/` directory has SLO per stage, (2) test PR without SLO fails required check, (3) TSDB has 90 days of day-of-week-tagged stage duration, (4) alert-rule registry has trend-based rules per stage, (5) weekly digest archive continuous.

---

## Section C: Proof of Action Matrix

|       | Non-Conformance (NC)                                                                                                                                                                                                                                 | Non-Detection (ND)                                                                                                                                                                                                                       |
|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TRC   | Q1: metric=TBD, target=TBD, data_source=TBD, baseline=unknown, schedule=TBD, failure_response=TBD (fallback skeleton)                                                                                                                              | Q2: metric=TBD, target=TBD, data_source=TBD, baseline=unknown, schedule=TBD, failure_response=TBD (fallback skeleton)                                                                                                                 |
| MRC   | Q3: metric=TBD, target=TBD, data_source=TBD, baseline=unknown, schedule=TBD, failure_response=TBD (fallback skeleton)                                                                                                                              | Q4: metric=TBD, target=TBD, data_source=TBD, baseline=unknown, schedule=TBD, failure_response=TBD (fallback skeleton)                                                                                                                 |

*Note: Phase 6 verification_plan is in `_fallback: true` state. Overall timeframe: 6 months minimum. Phase 8 trigger: next recurrence of the same problem class. Proof-of-Action metrics to be attached by CAPA owners before closure.*

---

## Phase 1: IS / IS NOT Table

| Dimension | IS | IS NOT | Distinction (why it rules things in/out) |
|-----------|----|----|------------------------------------------|
| **what** | Smoke test stage in the CI pipeline exceeds its configured timeout window and is aborted before completion. | Not smoke test assertion failures, not build/compile errors, not unit-test failures, not deploy-step errors, and not a general CI outage affecting all jobs. | Timeout (wall-clock exhaustion) vs. functional failure shifts the hypothesis from code-correctness bugs to resource contention, external dependency latency, or workload changes. Isolating to the smoke stage (not build or unit) rules out compiler/toolchain regressions and points at smoke-specific dependencies (test env bring-up, seed data, external services). |
| **where** | CI runner executing the smoke-test stage (shared CI infrastructure / test environment / downstream services the smoke test touches). | Not developer laptops, not the staging/production runtime itself, not other pipeline stages on the same runner, and not pipelines in unrelated repos/projects that don't share the smoke runner or test env. | Localizing to the CI runner + smoke-test environment (vs. app runtime) rules out a product bug and points at environment-level causes: runner capacity, network path to the test env, shared test-env contention, or a dependency (DB, queue, mock service) reachable only from CI. |
| **when** | Only on Tuesdays, started suddenly/recently (no gradual ramp), recurring weekly on that same weekday. | Not Monday / Wednesday / Thursday / Friday / weekend runs, not historical runs before the onset date, not tied to a specific commit or PR author, and not correlated with release days in general. | A sudden-onset, day-of-week-periodic signal is the strongest clue: it almost always maps to a scheduled external event on a weekly cadence — e.g., Tuesday maintenance window, weekly backup/ETL, scheduled security scan, weekly cron job, vendor release day, or a new weekly job added around the onset date. This rules out random flakiness and commit-triggered regressions. |
| **extent** | Timeout affects smoke-test runs on Tuesdays (likely most or all of them within the business-hours window); stage duration is elevated vs. other days even when it doesn't hit the hard timeout. | Not every pipeline run, not every Tuesday run 24h-wide (likely clustered in a window), not all test cases within the smoke suite equally (usually a subset of tests that touch the contended resource), and not jobs that bypass the shared resource (e.g., mock-only tests). | Partial/bounded extent — clustered in a time window and concentrated on tests that touch a specific dependency — confirms contention on a shared resource active only during that window, rather than a global capacity cut or a code path that's always slow. This lets us correlate the Tuesday window against scheduled jobs, infra calendars, and per-test timing to pinpoint the contended dependency. |

---

## Phase 2: Why Chains — FULL (4 Quadrants)

### Q1 — TRC / Non-Conformance (Technical Root Cause of Occurrence)

**Why #1** — The CI pipeline failed on Tuesdays because the smoke-test stage's wall-clock execution exceeded its configured hard timeout and was aborted by the CI scheduler.
*New insight*: Frames the failure as timeout-driven (wall-clock exhaustion), not functional — hypothesis shifts from code bugs to latency/contention.

**Why #2** — The stage exceeded its timeout because a specific subset of smoke tests — those issuing DB-backed assertions against the shared test environment — each took 10–20× longer than on other weekdays, summing past the stage budget.
*New insight*: Isolates slowdown to DB-touching tests (not mock-only tests), confirming a shared dependency is the bottleneck rather than a runner CPU/IO regression.

**Why #3** — Those tests slowed down because their outbound queries to the shared test database incurred elevated round-trip and lock/IO-wait latency during the Tuesday smoke window.
*New insight*: Pinpoints the hot path: slowness originates in the DB dependency's response time, not in the CI runner or the test code.

**Why #4** — DB latency was elevated because the shared test DB cluster was CPU/IO-saturated by a concurrent, heavy, bursty workload active only during that weekly window.
*New insight*: Identifies resource saturation (not network or DNS) as the latency mechanism and bounds it to a finite daily window.

**Why #5** — That saturating workload appears only on Tuesdays because a weekly scheduled job (security/vulnerability scan, backup, or ETL) — newly introduced or rescaled around the onset date — runs against the same DB cluster every Tuesday.
*New insight*: Maps the day-of-week periodicity + sudden onset pattern to a discrete scheduled-job change event, not random flakiness or gradual drift.

**Why #6** — The CI smoke tests and the scheduled job share the same DB cluster because the non-prod tier hosts both CI test traffic and operational scheduled jobs on a single DB instance with no logical separation.
*New insight*: Elevates the cause from a workload collision to an architectural co-tenancy: CI and non-CI workloads are not partitioned at the data-tier boundary.

**Why #7** — No separation exists because the test-environment topology provisions a single shared schema/pool for all non-prod traffic — no dedicated CI read replica, connection pool, or namespace was ever carved out.
*New insight*: Names the specific missing primitive (dedicated replica / pool / namespace) that would have decoupled CI from operational workloads.
*Audit notes (Round 1 + 2 + 3 — ADDRESSABLE, unresolved)*: reviewers flagged that this step restates Why #6 rather than explaining why the primitive was never carved out. Suggested rewrite: "No dedicated pool was carved out because the non-prod tier predates CI adoption and no capacity-/isolation-review process gates new workloads onto existing shared clusters." — a natural handoff to Q3.

**Why #8** *(Parallel Cause B — enters sibling chain)* — Saturation on that shared DB translates into an unbounded stage wait because smoke tests issue DB operations without a per-query `statement_timeout` or client-side deadline, so they block on lock/IO waits indefinitely rather than failing fast.
*New insight*: Reveals a second, independent technical gap at the client/test-harness layer: operations are not deadline-bounded, amplifying any upstream latency.
*Audit notes (Round 2 — ADDRESSABLE)*: chain topology needs explicit labeling — Chain-A (#1–7) data-tier co-tenancy + Chain-B (#8–10) unbounded ops. Both siblings converge at root.

**Why #9** — The coarse stage-level timeout allows blocking to accumulate because the pipeline budget is a single wall-clock ceiling, not a per-test or per-operation deadline — so one slow test can consume the entire stage budget before any other test gets a chance to fail fast.
*New insight*: Surfaces a granularity mismatch: stage-level budget vs. operation-level blocking means the timeout detects only the cumulative failure, not the root slow call.

**Why #10** — The stage budget fit within the timeout on other days only because it was calibrated against a median-baseline run with no engineered headroom — the configuration implicitly assumed a quiet shared DB.
*New insight*: Shows the timeout value itself embeds an unverified assumption (low-contention baseline), which is a technical configuration defect that disappears the moment a scheduled peer workload appears.
*Audit notes (Round 1 + 2 + 3 — ADDRESSABLE, unresolved)*: presented as causal finding without evidence (no commit/PR, no measured baseline numbers, no headroom %). Should be either re-tagged as "Working hypothesis (unverified)" or backed with concrete artifacts.

**Why #11** — No contention-tolerant configuration exists because the smoke stage has no declared technical contract (`must complete in T regardless of shared-tier load`) — both workload isolation and bounded per-operation deadlines are absent from the stage's technical definition, and together they make stage runtime a function of unrelated Tuesday workloads.
*New insight*: Converges on the deepest controllable technical gap: the stage lacks both (a) data-tier isolation from non-CI workloads and (b) deadline-bounded DB operations — either one alone would have prevented the Tuesday timeout.
*Audit notes (Round 1 + 2 — ADDRESSABLE)*: reviewers noted this step is synthesis, not a new why. Recommended to either delete and let root statement synthesize, or replace with a management-crossover why ("no declared reliability contract because CI pre-prod pipelines have no owning role / error-budget discipline") — which likely belongs in Q3.

**Root (Q1)**: The smoke-test stage has neither workload isolation from the shared non-prod DB cluster (no dedicated CI replica/pool/namespace) nor bounded per-operation deadlines in the test harness (no `statement_timeout` or client-side deadline). When a weekly Tuesday scheduled job saturates the shared DB, DB-backed smoke tests block on lock/IO waits until the coarse stage wall-clock timeout aborts the pipeline. Both gaps are technical configuration defects — remove either one and the Tuesday timeout does not occur.

---

### Q2 — TRC / Non-Detection (Technical Detection Escape)

**Why #1** — The Tuesday-only timeout surfaced as a hard stage failure rather than a leading-indicator alert, because the CI stage only emits a binary pass/fail signal; elevated duration on non-timeout Tuesdays (and on earlier Tuesdays before the hard limit was hit) produced no signal at all.
*New insight*: Detection mode is binary pass/fail, not a continuous SLI — the system is blind to pre-failure drift.

**Why #2** — Duration telemetry was not captured as a first-class metric because the smoke stage records elapsed time only to stdout/job logs; there is no metrics exporter wrapping the stage that ships duration to a time-series backend (Prometheus/Datadog/etc.).
*New insight*: Signal exists in logs but isn't promoted to a metric; log-only data is not alertable.

**Why #3** — No exporter exists because observability tooling was scoped to the application runtime (prod/staging), not the CI build plane; the pipeline itself was never declared a monitored system with its own SLIs/SLOs.
*New insight*: Scope gap: CI is outside the monitored perimeter.

**Why #4** — CI was excluded from the monitored perimeter because it was classified as ephemeral build infrastructure rather than a reliability target whose degradation directly blocks release flow; there is no error budget defined for CI stage duration.
*New insight*: Classification error — CI is treated as a tool, not a service.

**Why #5** — Even retroactive analysis on existing job logs cannot catch Tuesday periodicity, because CI log retention (default 14–30 days) is shorter than the multi-week window needed to confirm a weekly seasonality signal with statistical confidence.
*New insight*: Retention horizon is tuned for cost, not for diagnosability of weekly patterns.

**Why #6** — Even with longer retention, no anomaly detector would have flagged it, because baseline models assume a stationary distribution and don't decompose by day-of-week; weekday-periodic drift is silently absorbed into the overall variance band.
*New insight*: Detectors lack seasonality decomposition — weekday-periodic failures are a blind spot.

**Why #7** — Inside the smoke suite, per-dependency latency was never measured, because downstream calls (DB, queue, mock/stub services, external APIs) are not wrapped in timing spans; smoke was implemented as a binary assertion harness, not an instrumented probe.
*New insight*: Smoke is a gate, not a diagnostic — which dependency consumed the timeout budget is unknowable.

**Why #8** — Spans and trace context aren't present because no tracing SDK is wired into the test harness and trace IDs aren't propagated from the test runner into downstream HTTP/DB calls, so even the app's existing tracing infrastructure can't see CI-originated traffic.
*New insight*: Tracing boundary stops at the app edge; test-originated requests are orphaned spans.

**Why #9** — No independent canary runs outside CI on a schedule against the same test-env dependencies, so gradual shared-resource slowdown — the underlying Tuesday contention — has no out-of-band observer; the first entity to notice is the CI job itself, and only when it crosses the hard limit.
*New insight*: No synthetic monitor on the test-env dependency path means CI is the canary.

**Why #10** — Change/event correlation is impossible because weekly cron jobs, infra maintenance windows, vendor release schedules, and backup/ETL jobs are not published to a machine-readable calendar that a CI dashboard can overlay onto stage-duration trends; the day-of-week clue can't be mechanically joined to a causing event.
*New insight*: No change-calendar feed — the single strongest diagnostic signal (Tuesday) can't be programmatically correlated.

**Why #11** — All of the above gaps coexist because there is no observability contract for the CI/test plane — no convention requiring duration SLIs, per-dependency spans, seasonality-aware detectors, synthetic canaries, and change-calendar correlation as a bundle; each gap individually looked tolerable, and together they form a complete detection void.
*New insight*: Root technical non-detection cause: the CI/test plane was never architected as an observable system; the absence is systemic, not one missing widget.

**Root (Q2)**: The CI/test plane has no observability contract: no duration SLIs, no per-dependency spans inside smoke, no seasonality-aware anomaly detector, and no change-calendar correlation — so slow-growing contention on a shared test-env dependency stays invisible until it crosses the hard timeout.

---

### Q3 — MRC / Non-Conformance (Management Root Cause of Occurrence)

**Why #1** — A weekly-recurring workload (e.g., Tuesday backup/scan/vendor job) was introduced or enlarged on infrastructure shared with the CI smoke-test environment without any coordination with the pipeline owners, so contention on the shared resource landed inside the smoke window undetected by change reviewers.
*New insight*: The proximate managerial gap is not a technical regression but an unreviewed cross-tenant change on shared infra.

**Why #2** — The organization's change-management procedure does not require the requestor to perform (or the CAB to demand) an impact analysis against dependent internal consumers such as CI pipelines before approving recurring scheduled jobs.
*New insight*: Change control is scoped to customer-facing services; internal consumers are invisible to the approval workflow.

**Why #3** — CI/shared-runner ownership is not represented as a mandatory reviewer on the change advisory process, because the CI platform has no designated single-threaded owner with approval authority over changes that affect its capacity envelope.
*New insight*: Missing 'DRI on CAB' turns every shared-infra change into an uncoordinated event by default.

**Why #4** — No single-threaded owner has been assigned because the CI platform is not listed in the company's service catalog as a tiered service with an accountable team, SLOs, and a lifecycle owner.
*New insight*: Absence from the service catalog is the structural reason ownership can stay unassigned.

**Why #5** — The service-tiering policy itself scopes tiering only to externally-facing products; internal developer platforms are explicitly or implicitly excluded from tier assignment, so CI never triggers the governance obligations (owner, SLO, change review) that tiering would attach.
*New insight*: The tiering policy's scope boundary is the upstream defect — it decides in advance that internal platforms are ungoverned.

**Why #6** — Internal platforms are excluded because the organization has not adopted a platform-engineering charter that recognizes developer infrastructure as a first-class product with its own funded team, roadmap, and service-level commitments.
*New insight*: The gap is a missing governance artifact (charter), not an oversight on one service.

**Why #7** — No platform-engineering charter exists because engineering leadership has not issued a RACI that separates 'consumer of CI' from 'producer/owner of CI,' leaving CI as a diffuse shared responsibility that no one is measured on.
*New insight*: Without RACI separation, 'shared ownership' collapses to 'no ownership' under load.

**Why #8** — Leadership has not issued that RACI because engineering's operating model treats CI infrastructure as overhead amortized across product teams rather than as a product with its own P&L, capacity plan, and roadmap.
*New insight*: The cost-center framing structurally prevents assigning a product owner.

**Why #9** — The cost-center framing persists because the capital/opex planning process allocates CI capacity reactively (request-based) rather than against a forecasted demand model that accounts for peaks, recurring workloads, and headroom policy, so capacity decisions never surface as strategic.
*New insight*: Reactive budgeting denies CI the forecasting discipline that would expose weekly contention risk.

**Why #10** — Planning stays reactive because the engineering leadership scorecard contains no KPI for internal-platform reliability (e.g., pipeline SLO attainment, capacity headroom, change-failure rate on shared infra), so no executive has an incentive to fund forecasting or charter creation.
*New insight*: Without a leadership-level KPI, the governance artifacts upstream of this failure are never prioritized.

**Why #11** — Internal-platform KPIs are absent from the leadership scorecard because the organization's quality/operational-excellence policy only defines objectives for customer-visible products, so developer-platform quality never enters the policy framework that drives the scorecard.
*New insight*: The root managerial defect is a policy-scope omission: operational-excellence policy does not cover internal platforms.

**Why #12** — That policy scope has never been expanded because no governance owner exists whose remit is to review and update the operational-excellence policy against new organizational dependencies (like a growing internal CI estate with recurring external workloads sharing its infra).
*New insight*: Policy itself has no maintainer, so it ages into irrelevance — this is the deepest controllable managerial cause.

**Root (Q3)**: No accountable governance owner maintains the operational-excellence / service-tiering policy to include internal developer platforms (CI), which leaves the CI infrastructure without a service-catalog entry, a single-threaded owner, SLOs, capacity forecasting, or mandatory change-impact review — so a weekly external workload could be scheduled onto shared infrastructure without notifying or being approved by CI pipeline owners, producing the Tuesday-only smoke-test timeout.

---

### Q4 — MRC / Non-Detection (Management Detection Escape)

**Why #1** — The Tuesday-only timeout pattern ran for multiple weekly cycles before anyone investigated, because CI alerting is binary (pass/fail) and fires only after the hard timeout — not on rising stage-duration trends.
*New insight*: Detection is outcome-gated, not leading-indicator-gated.

**Why #2** — CI alerting is binary because the monitoring configuration tracks only job outcome counters, with no duration histograms, percentiles, or day-of-week segmentation surfaced on any dashboard.
*New insight*: Observability schema itself is missing the dimensions needed to see the pattern.

**Why #3** — Duration/seasonality dimensions are missing because no SLI or SLO has ever been defined for CI stage latency in the engineering observability standard — the standard catalogs product SLIs only.
*New insight*: The gap is upstream in the SLI catalog, not just the dashboard.

**Why #4** — The observability standard omits CI because CI is governed as 'best-effort internal tooling' rather than as a service with defined reliability targets, so no objective forces instrumentation to exist.
*New insight*: Governance classification of CI drives instrumentation investment.

**Why #5** — CI is classified as best-effort because the organization's service-tiering policy scopes reliability governance to customer-facing products; internal developer platforms are explicitly out of scope for tiering.
*New insight*: The tiering policy itself has a scoping defect that excludes internal platforms.

**Why #6** — The tiering policy excludes internal platforms because no accountable business owner has been designated for engineering productivity as a measurable, reportable outcome at the management level.
*New insight*: Absence of an accountable owner upstream of the policy.

**Why #7** — No owner has been designated because the operating model funds product-delivery teams but lacks a chartered platform-engineering function with a mandate for internal reliability and a seat at planning forums.
*New insight*: Structural/charter gap in the operating model, not a staffing gap.

**Why #8** — The platform-engineering charter is absent because change-management and infra-calendar coordination across teams (e.g., the new weekly Tuesday scan/ETL/backup that induced contention) has no cross-team governance forum that would have flagged the conflict pre-introduction.
*New insight*: Lack of a cross-team change-coordination forum is a co-symptom of the missing charter — it would have been the detection venue.

**Why #9** — No cross-team change-coordination forum exists because leadership's quarterly/operational review ritual does not include internal-platform health or cross-cutting scheduled-workload conflicts on the standing agenda — only product OKR metrics are reviewed.
*New insight*: Management review cadence omits internal platform signals, so the need for a forum is never surfaced.

**Why #10** — The review ritual omits internal-platform health because governance policy mandates review content based on customer-facing OKRs only; there is no policy requirement to report internal reliability or developer-productivity loss to executives.
*New insight*: Root governance defect: reporting mandate scope excludes internal reliability.

**Why #11** — The governance policy's reporting mandate was never broadened because productivity loss from CI degradation has never been tallied in monetary or throughput terms, so there is no evidentiary case prompting leadership to expand the mandate — creating a self-sustaining blind spot that suppresses both detection instrumentation and the governance reform that would require it.
*New insight*: Blind-spot is self-reinforcing: no data → no mandate → no data.

**Root (Q4)**: Governance policy defines mandatory management-review content around customer-facing OKRs only, with no requirement to report internal-platform reliability, developer-productivity loss, or cross-team scheduled-workload conflicts. This single policy-scope defect cascades downward: no exec visibility → no platform-engineering charter/owner → no tiering of CI as a governed service → no SLO for stage latency → no duration/seasonality instrumentation → no mechanism capable of detecting a weekly Tuesday timeout pattern before it repeatedly breaks the pipeline. Controllable fix lives at the governance layer: amend the review/reporting mandate to include internal platform reliability, which forces the downstream detection mechanisms into existence.

---

## Phase 3: RC Audit Rounds — FULL

### Round 1 — Verdict: CONTINUE

**Weakness 1 — Q3 absent (ADDRESSABLE)**
*Issue*: Quadrant q3 (Management Root Cause — Non-Conformance) is entirely absent from the submitted chains. Check #2 (MRC at management-system level) cannot be evaluated, and the audit is structurally incomplete — a 4-quadrant analysis with 2 quadrants is a 2-quadrant analysis.
*Suggested fix*: Author a full q3 chain at the management-system level, not the code level. Likely themes: (a) no governance over who can schedule workloads on the shared non-prod DB cluster, (b) no capacity/tenancy review gate when the Tuesday job was introduced/rescaled, (c) no architectural standard requiring CI isolation at the data tier, (d) test-environment ownership is diffuse.

**Weakness 2 — Q4 absent (ADDRESSABLE)**
*Issue*: Quadrant q4 (Management Root Cause — Non-Detection) is entirely absent. Check #3 (ND quadrants as deep as NC quadrants) cannot be evaluated because q4 has zero whys.
*Suggested fix*: Author a full q4 chain covering the management-system detection gap: no change-advisory board review of cross-tenant workload additions, no SLO/SLI governance for CI reliability, no cross-team visibility forum where 'flaky Tuesday' reports would aggregate, no periodic review of shared-tier capacity.

**Weakness 3 — Q2 truncated at Why #2 (ADDRESSABLE)**
*Issue*: q2 is truncated mid-sentence at Why #2 ('...there is no'). The chain is incomplete, so depth parity with q1 (11 whys) cannot be verified.
*Suggested fix*: Complete q2 to at least 10–11 whys. Natural continuation: (n=2) no duration metric → (n=3) no per-dependency spans → (n=4) no seasonality/day-of-week baselining → (n=5) no change-calendar correlation → (n=6) no pre-timeout warning threshold → ... → root: observability contract absent.

**Weakness 4 — Q1 Why #11 is synthesis (ADDRESSABLE)**
*Issue*: Why #11 is not a new causal step — it is an explicit synthesis ('converges on the deepest controllable technical gap') that restates the union of Why #7 and Why #8. Inflates chain length without adding a causal link.
*Suggested fix*: Delete Why #11 or replace with a genuine deeper step pushing into management territory.

**Weakness 5 — Q1 Why #7 restates Why #6 (ADDRESSABLE)**
*Issue*: Why #7 largely renames what Why #6 already stated. The second is a more specific vocabulary for the same absence.
*Suggested fix*: Replace Why #7 with a causal explanation of why the primitive was never carved out.

**Weakness 6 — Q1 Why #9 overlaps Why #8 (RESIDUAL)**
*Issue*: Why #9 (coarse stage-level timeout) partially overlaps Why #8 (no per-query statement_timeout). Both describe same root absence from different layers.
*Suggested fix*: Tighten wording; acceptable as-is if explicitly named as a two-layer defect pair.

**Weakness 7 — Q1 Why #10 is unverified assertion (ADDRESSABLE)**
*Issue*: Presents a hypothesis about how the timeout was set as observed fact.
*Suggested fix*: Either attach evidence (commit/PR, measured baseline) or mark as "Working hypothesis."

**Weakness 8 — Q1 root declares two independent causes (RESIDUAL)**
*Issue*: The root statement declares TWO independent sufficient causes. Should be explicitly labeled as branching root.
*Suggested fix*: Split the root into two named contributing causes (RC-1: data-tier co-tenancy; RC-2: unbounded client-side deadlines).

**Weakness 9 — Q1 Why #1 is symptom (RESIDUAL)**
*Issue*: Why #1 is closer to symptom restatement than causal step.
*Suggested fix*: Acceptable as framing step if labeled.

**Weakness 10 — Q1 tail drifts into management territory (ADDRESSABLE)**
*Issue*: Several late q1 whys (e.g., #11) drift into management territory and may belong in q3 once authored.
*Suggested fix*: Audit q1 tail once q3 is authored; migrate content cleanly.

**Round 1 SoA citations used**: (not explicitly cited in audit payload — methodology draws on 4Q RCA and 8D MRC standards).

---

### Round 2 — Verdict: CONTINUE

**Weakness 1 — Q1 Why #7 still a restatement (ADDRESSABLE)**
*Issue*: Why #7 restates Why #6 rather than deepening it. Author's own audit_note acknowledges this.
*Suggested fix*: Rewrite as causal step pointing to process/organizational cause (crossover to Q3).

**Weakness 2 — Q1 Why #8 introduces parallel cause without labeling (ADDRESSABLE)**
*Issue*: Why #8 is not a deeper cause of Why #7; it introduces a parallel, independent technical defect on a different axis. The chain has effectively become two chains spliced together.
*Suggested fix*: Split q1 into two sibling chains: Chain-A (data-tier co-tenancy) and Chain-B (unbounded DB operations), converging at root.

**Weakness 3 — Q1 Why #10 still unverified (ADDRESSABLE)**
*Issue*: Asserts causal finding with no evidence; flagged by author's own audit_note.
*Suggested fix*: Attach evidence or re-tag as "Working hypothesis (unverified)."

**Weakness 4 — Q1 Why #11 is synthesis masquerading as deeper step (ADDRESSABLE)**
*Issue*: Summarizes #6–#10 rather than deepening; wastes a Why slot.
*Suggested fix*: Delete #11 and use freed slot for management-crossover why.

**Weakness 5 — Q1 Why #2 magnitude unsourced (RESIDUAL)**
*Issue*: Asserts '10–20× longer' without citation.
*Suggested fix*: Attach measurement source (CI timing histograms, APM, DB slow-query log) or soften.

**Weakness 6 — Q1 Why #5 correlational anchor (RESIDUAL)**
*Issue*: Lists three candidate saturating workloads without committing to which one. Correlational, not causal.
*Suggested fix*: Add verification step correlating CI stage runtime p99 against DB CPU/IO metrics for 4-week Tuesday window.

**Weakness 7 — Counterfactual untested (ADDRESSABLE)**
*Issue*: Chain never tests counterfactual (if job moved to Wednesday, does failure follow?). Claim that Tuesday job is proximate trigger is weaker than implied.
*Suggested fix*: Add explicit counterfactual check as verification action or parenthetical in Why #5.

**Weakness 8 — Q2 not visible (ADDRESSABLE)**
*Issue*: q2 truncated; cannot verify depth parity.
*Suggested fix*: Re-post q2 (and q3, q4) content for audit.

**Weakness 9 — Q3 not visible (ADDRESSABLE)**
*Issue*: Cannot check management-system-level vs code-level criterion.
*Suggested fix*: Re-post q3. Proper q3 questions: 'why does no role own CI pre-prod reliability?', etc.

**Weakness 10 — Q4 not visible (ADDRESSABLE)**
*Issue*: Depth-parity check and management-level check impossible.
*Suggested fix*: Re-post q4. Strong q4 should bottom out at tier-level SLO dashboard owned by a named role.

**Weakness 11 — Root has two causes with no prioritization (RESIDUAL)**
*Issue*: Root names two independent sufficient causes but no ranking for CAPA design.
*Suggested fix*: Rank by cost-of-remediation × blast-radius-reduction OR explicitly state two sibling technical roots.

---

### Round 3 — Verdict: CONTINUE

**Weakness 1 — Q1 Why #7 restatement unresolved (ADDRESSABLE)**
*Issue*: Why #7 remains a restatement of Why #6's architectural finding. Prior-round audit_notes flagged this; step has not been rewritten. Chain stalls one link short of organizational/process cause.
*Suggested fix*: Rewrite with organizational/process explanation → crossover to Q3.

**Weakness 2 — Q1 Why #8 parallel-cause topology still invisible (ADDRESSABLE)**
*Issue*: Silently introduces parallel cause without signposting. Readers cannot see causal topology.
*Suggested fix*: Explicitly split into Chain-A and Chain-B with labels.

**Weakness 3 — Q1 Why #10 still unsupported (ADDRESSABLE)**
*Issue*: Assumption treated as conclusion; prior-round audit_notes flagged this gap.
*Suggested fix*: Attach evidence or re-tag as working hypothesis.

**Weakness 4 — Q1 Why #11 truncated (ADDRESSABLE)**
*Issue*: Supplied Why #11 is truncated mid-sentence ("Converges on the deepest …"), so terminal causal insight cannot be audited. An unverifiable terminal why is a structural defect.
*Suggested fix*: Supply full Why #11 text; name one concrete, testable technical contract.

**Weakness 5 — Meta: only Q1 supplied (ADDRESSABLE)**
*Issue*: Only Q1 was supplied. Q2/Q3/Q4 absent from input. Three of four required audit checks cannot execute.
*Suggested fix*: Re-submit audit payload with all four quadrants.

**Weakness 6 — Q1 lacks NC/MRC crossover (ADDRESSABLE)**
*Issue*: Chain A stops one step short of NC/MRC crossover. Terminal reads as "a thing is missing" instead of "a thing is missing because no process requires it."
*Suggested fix*: Extend Chain A with terminal why pointing to Q3 OR explicitly mark crossover in root synthesis.

**Weakness 7 — Q1 Why #5 remains ambiguous (RESIDUAL)**
*Issue*: Why #5 lists three candidate saturating workloads without committing. Weakens CA traceability.
*Suggested fix*: Attach identifying evidence (cron entry, job name, owner team, onset commit/change ticket) OR mark 'pending PoA evidence.'

**Round 3 SoA citations used**: NIOSH/ISO 45001 Hierarchy of Controls; SLSA framework (provenance enforcement levels).

---

## Phase 4: Full Actions (Corrective + Prevention) per Quadrant

### Q1 — TRC / NC — Corrective Action

**Action**: Apply a bounded-deadline configuration to the smoke-test stage's DB layer so this Tuesday instance stops timing out:
1. Set `statement_timeout = 15s` on the smoke-test DB role/connection string used by the CI runner.
2. Wrap each DB-backed smoke test call in a client-side deadline (e.g., `context.WithTimeout` / `asyncio.wait_for`) sized below the per-test budget.
3. As a one-shot instance remedy, reschedule *this* Tuesday's saturating job (security scan / backup / ETL) out of the smoke-test window for the next 2 Tuesdays while the fix soaks.

No topology change, no new replica — purely config on the existing smoke stage and a one-time scheduler move.

**Rationale**: Per the root cause, removing *either* gap alone prevents the Tuesday timeout. Per-operation deadlines are the minimum-blast-radius NC fix: config change in the test harness and the DB role, deployable within hours, and they convert the current failure mode (unbounded block → stage wall-clock abort → pipeline red) into fast per-test failures that either (a) stay inside the stage budget when the scheduled job is mild or (b) surface as clear, attributable per-test timeout errors when it is not. Moving the Tuesday scheduled job off the smoke window is a belt-and-suspenders one-shot. Explicitly scoped as a non-conformance (this-instance) remedy — does not attempt to fix the architectural co-tenancy (belongs in Q2/Q4 MRC work).

**Owner**: CI/Platform Engineering lead (owner of the smoke-test harness and CI pipeline config), with DBA on-call consulted for the `statement_timeout` role change and the scheduled-job owner looped in for the one-shot reschedule.

**Target date**: 2026-04-29 (one week from today, 2026-04-22) — config PR merged and deployed before the next Tuesday smoke window.

**Evidence of completion**:
- (a) Merged PR showing `statement_timeout=15s` on the smoke-test DB role + per-test client deadline wrapper in the smoke harness.
- (b) Change ticket confirming the next 2 Tuesday scheduled-job runs are moved out of the smoke window.
- (c) CI dashboard shows 2 consecutive Tuesday smoke runs completing inside the stage budget with zero wall-clock-abort events.
- (d) A deliberately injected lock/IO-wait during a staging smoke run surfaces as a per-test fast-fail with a `statement_timeout`/deadline error message (proving deadlines fire as designed), not a stage-level timeout.
- (e) Before/after p99 stage runtime recorded in the 8D closure note.

---

### Q2 — TRC / ND — Corrective Action

**Action**: Instrument the smoke stage as an observable probe for this pipeline:
1. Emit `smoke_stage_duration_seconds` as a first-class metric to the existing metrics backend on every run, tagged with stage, branch, and day_of_week.
2. Wrap the top 5 downstream calls inside smoke (DB, queue, mock svc, external API, auth) with timing spans propagating trace IDs from the runner, exporting per-dependency duration histograms.
3. Configure a seasonality-aware alert (STL or day-of-week z-score) on the duration metric with a warning threshold at 60% of the hard timeout, so Tuesday drift pages before it crosses the limit.
4. Add a Grafana/Datadog panel overlaying smoke duration against a manually-curated "Tuesday events" annotation list (known weekly cron/backup/vendor windows) for this pipeline.

Ship as one PR against the CI config + shared test harness.

**Rationale**: Directly closes the detection void. Duration becomes a continuous SLI (fixes why #1–2), per-dependency spans reveal which dependency ate the budget (fixes why #7–8), day-of-week baselining surfaces weekday-periodic drift (fixes why #6), change-calendar overlay makes the Tuesday clue mechanically joinable to a causing event (fixes why #10). Scoped to this pipeline's smoke stage — does not require re-architecting the whole CI plane (that is the Q4 systemic action).

**Owner**: CI/Platform engineer owning the smoke stage, with review from the observability/SRE team for metric naming and alert routing conventions.

**Target date**: 2026-05-13 (3 weeks from 2026-04-22): week 1 — metric emission + dashboard; week 2 — per-dependency spans + trace propagation; week 3 — seasonality alert tuned on backfilled data + change-calendar overlay live.

**Evidence of completion**:
- (a) Metric `smoke_stage_duration_seconds` visible in the TSDB with ≥14 days of data and per-run points tagged by day_of_week.
- (b) A trace from a recent smoke run shown in the tracing UI with ≥5 child spans for downstream dependencies and non-zero durations on each.
- (c) Alert rule file committed (e.g., `alerts/ci-smoke-duration.yaml`) with seasonality logic and warning threshold at 60% of hard timeout, plus a screenshot of the alert firing on a replayed historical Tuesday run.
- (d) Dashboard URL with the smoke-duration panel + Tuesday-events annotation overlay linked from the runbook.
- (e) A synthetic "slow Tuesday" fault-injection test (add 30s sleep to one dependency on a Tuesday branch run) producing a warning alert before the hard timeout would trigger — log of the alert + the job still passing attached to the closing ticket.

---

### Q3 — MRC / NC — Prevention Action

**Action**: Charter a Director-level "Operational Governance Owner" (OGO) whose remit is to maintain the operational-excellence / service-tiering policy and whose performance is measured on a board-level KPI (internal-platform SLO attainment + change-failure rate on shared infra). The chartered policy must codify three enforceable rules:
1. Any infrastructure consumed by ≥2 engineering teams MUST have a service-catalog entry with a named single-threaded DRI, tier, and capacity envelope before it can host recurring workloads.
2. The change-management system is configured so that every change request targeting shared infra performs an automatic service-catalog lookup and is rejected at submission when the target has no catalog entry or when the catalog DRI has not been added as a mandatory approver.
3. Policy scope is reviewed annually via a signed attestation from the OGO confirming that all internal platforms active in the past 12 months are in scope.

The policy itself lives in a version-controlled governance repository; catalog registration is wired as a gated step at platform-provisioning time so new platforms cannot receive workloads before registration.

**Hierarchy level**: 1 (claimed Elimination; Phase 5 Round 2–3 audit classified as actually Level 2 administrative with Level 3 supports — see audit notes).

**Deployment scope**: PROJECT (organization-specific governance intervention — role, policy, CAB config, service catalog inside the company's operating model).

**Scope justification**: This is not a global convention; different organizations have different governance structures, change-management tools, and service-catalog platforms. Deployment surface maps to PROJECT scope.

**Failure mode of prevention** (three silent-failure modes identified, with mitigations):
1. OGO role is chartered on paper but unfunded/part-time → annual attestation silently slips past due date → scorecard marked "not reported" rather than "failed." *Mitigation*: annual attestation is a CI check on the governance repo that fails the board-scorecard pipeline when overdue.
2. CAB tool exposes "emergency change" or "standard change" bypass lane that skips catalog lookup → recurring workloads get reclassified as "standard" to avoid review. *Mitigation*: catalog-lookup rule is a universal pre-condition that applies to all lanes including emergency, with only a post-hoc review-within-48h exemption that is itself auditable.
3. Service catalog goes stale — new platforms provisioned but never registered → CAB rule has nothing to enforce against. *Mitigation*: (a) fail-closed default on catalog misses and (b) wiring catalog registration as a gated step in the platform-provisioning pipeline so a platform literally cannot accept workloads before it appears in the catalog.

**Gate test**:
- Scope: PASS (prevents the class, not the Tuesday-smoke-test instance — CAB tooling's catalog-lookup rule blocks ANY uncoordinated recurring workload against ANY shared internal infrastructure).
- Persistence: PASS (embedded in three reinforcing artifacts: chartered role with board-reported KPI; CAB tool config-as-code that mechanically rejects non-compliant change requests; version-controlled policy repo with annual-review CI check).
- Measurability: PASS (third-party auditor verifies OGO charter, service-catalog consistency via VPC/namespace telemetry, CAB rejection rule in config-as-code with test case, signed annual attestation, KPI dashboard trend).

---

### Q4 — MRC / ND — Prevention Action

**Action**: Codify a CI Observability Contract as monitoring-as-code in the pipeline repo and enforce it with a pre-merge lint gate. The contract requires, for every CI stage and every scheduled/weekly workload:
- (a) Emission of per-stage duration metrics (p50/p95/p99) tagged with stage, branch, day-of-week, and hour-of-day.
- (b) A declared soft-SLO for stage duration (e.g., p95 < 50% of hard timeout) stored alongside the job definition.
- (c) An automatic anomaly rule — "alert when p95 over the last 7 same-day-of-week runs rises >30% vs the trailing 28-day baseline, OR exceeds the soft-SLO" — generated from the declared SLO at merge time.
- (d) A standing "CI Stage Health" dashboard with day-of-week segmentation auto-populated from the same config.
- (e) A weekly digest posting the top-5 stage-duration regressors and any scheduled-workload overlap conflicts to a standing channel.

The pre-merge lint (a required GitHub Action / equivalent status check) blocks PRs that add or modify a CI stage / scheduled job without a declared soft-SLO and emitted duration metric, and blocks PRs that introduce a new cron/scheduled workload without a collision check against the existing scheduled-workload registry. The contract, lint rule, dashboard definitions, alert rules, and scheduled-workload registry all live under version control (`.ci-observability/` + `.detection-rules`) so additions/removals are reviewable and auditable.

**Hierarchy level**: 3 (engineering/administrative control with monitoring-as-code enforcement).

**Deployment scope**: PROJECT.

**Scope justification**: Artifacts (lint rule, `.ci-observability/` contract, scheduled-workload registry, dashboards) attach to a specific CI pipeline's repo and observability backend. Deploying globally would require imposing CI metric schemas on unrelated projects. However, the *pattern* (observability-contract-as-code + pre-merge lint + scheduled-workload collision registry) is reusable and should be proposed as a template; the governance-level reform that would globalize it is addressed in Q3.

**Failure mode of prevention**: The contract degrades into a rubber-stamp if soft-SLOs are set so loose that no real regression ever trips them (e.g., p95 threshold = 99% of hard timeout), or if teams use a blanket lint-exemption annotation to bypass declaration. Alert rules can also go "ack-fatigue silent" — firing regularly but routed to an unowned channel, reproducing the original blind spot one layer higher. Finally, if the scheduled-workload registry is populated only by voluntary declaration (not by a scanner over the actual cron/pipeline configs), newly introduced workloads can still slip in un-registered and recreate the Tuesday-contention class of incident.

Mitigating meta-controls needed: (i) quarterly audit that soft-SLOs are < 60% of hard timeout and alert ack-rates are non-zero; (ii) no lint exemption without an expiry date and linked follow-up ticket; (iii) registry populated by an automated scanner over pipeline sources, not voluntary declaration.

**Gate test**:
- Scope: PASS (prevents entire class of "slow-burn CI degradation invisible until hard timeout"; applies to every stage and every scheduled job).
- Persistence: PASS (required pre-merge status check backed by lint rule in version control; dashboards, alert rules, and registry generated from checked-in config via monitoring-as-code; removing the gate requires reviewable PR that itself would fail lint on affected stages).
- Measurability: PASS (auditor inspects `.ci-observability/` for soft-SLO per stage; opens test PR without SLO and confirms required check fails; queries TSDB for day-of-week-tagged histograms over 90 days; pulls alert-rule registry; reviews weekly digest archive).

---

## Phase 5: Prevention Audit Rounds — FULL

### Round 1 — Verdict: CONTINUE

**Weakness 1 — Q3 hierarchy level inflated (ADDRESSABLE)**
*Issue*: Q3 declares hierarchy_level=1 (elimination), but the bulk of the intervention is administrative (chartered role, policy doc, annual attestation) and engineering-control (CAB tool rule rejecting non-compliant submissions). True Level 1 would make the failure physically/architecturally impossible — e.g., shared infra capacity is hard-partitioned so an uncoordinated workload cannot consume enough resources to impact others. Only the 'catalog registration as a gated step at platform-provisioning time' clause is close to Level 1.
*Suggested fix*: Reclassify as hierarchy_level=2 or split the action: keep the provisioning-gate clause as Level 1, and label the OGO charter + CAB rule + annual attestation as Level 2/3 supporting controls. Also add one genuine Level 1 architectural control: hard resource quotas per catalog-registered consumer.
*Evidence*: NIOSH/ISO 45001 Hierarchy of Controls — policy + gated approval tool = administrative/engineering controls, not elimination. Software analog: SLSA framework treats provenance-enforcing gates as L2 (build integrity), with L4 reserved for hermetic/reproducible architectural guarantees.

**Weakness 2 — Shared-infra detection blind spot (ADDRESSABLE)**
*Issue*: Rule triggers on '≥2 engineering teams' consuming a platform, but no mechanism for DETECTING when a platform crosses that threshold. Annual attestation is a 12-month catch-up window — up to 11 months of uncatalogued shared infra can accumulate.
*Suggested fix*: Add a continuous detector: weekly telemetry job scans VPC/namespace/IAM/network-flow data for platforms crossing the 2-consumer threshold and auto-files a registration ticket. Fail-closed: if detection job has not reported in >7 days, block all new change requests against un-attested platforms.
*Evidence*: Platform-engineering SoA (Backstage, Humanitec) — service catalogs maintained via continuous discovery from cloud/CI telemetry, not annual attestation cycles, because manual catalog maintenance decays ~20-40%/year.

**Weakness 3 — Emergency-change bypass under-controlled (ADDRESSABLE)**
*Issue*: 48h post-hoc review acknowledged but 48h is ample time for a Tuesday-smoke-test-class incident. 'Recurring workload' can be reclassified as a sequence of one-off emergency changes.
*Suggested fix*: Add velocity gate: if same target platform receives >3 emergency changes within 30-day rolling window from same source team, CAB tool auto-flags as 'de facto recurring.' Also require emergency changes against uncatalogued targets to notify platform SRE on-call synchronously (not just post-hoc review).
*Evidence*: Google SRE 'freeze-the-change' pattern + DORA change-failure-rate research.

**Weakness 4 — OGO KPI is lagging (ADDRESSABLE)**
*Issue*: KPI is 'SLO attainment + change-failure rate' — both measured AFTER the failure class has (or hasn't) recurred. Corrective-posture-dressed-as-prevention at governance layer.
*Suggested fix*: Add leading indicators: (a) % of shared platforms with valid catalog entry (target 100%), (b) mean age of catalog entries since last DRI attestation (target <90 days), (c) # of CAB rejections / week, (d) # of emergency-lane uses against uncatalogued targets (target 0).
*Evidence*: Balanced-scorecard + SRE error-budget literature — outcome-only KPIs decay into theater.

**Weakness 5 — Definitional ambiguity (RESIDUAL)**
*Issue*: Edge cases in 'recurring workload' and 'shared infrastructure' (bot consumers? transitive deps? noisy-neighbor effects?) accumulate over time.
*Suggested fix*: Accept as residual; mitigate via explicit exception registry with <12-month expiry per exception.
*Evidence*: ISO 27001 risk-acceptance register pattern.

**Weakness 6 — Q4 truncated in input (ADDRESSABLE)**
*Issue*: Q4 action body, failure_mode_of_prevention, gate_test entries, and measurability evidence not fully present.
*Suggested fix*: Re-supply complete Q4 text.
*Evidence*: Input payload cutoff.

**Round 1 SoA citations used**:
- NIOSH/ISO 45001 Hierarchy of Controls
- SLSA framework (Supply-chain Levels for Software Artifacts)
- Backstage / Humanitec service-catalog continuous-discovery patterns
- Google SRE book ("freeze-the-change" pattern)
- DORA State of DevOps research
- Balanced-scorecard literature
- ISO 27001 risk-acceptance register

---

### Round 2 — Verdict: CONTINUE

**Weakness 1 — Q3 hierarchy misclassification persists (ADDRESSABLE)**
*Issue*: Stack is Level 2 (poka-yoke/forcing function at a gate) mixed with Level 3 (administrative controls). True Level 1 would be admission webhooks that reject pods/jobs landing on uncatalogued namespace, IAM roles that cannot be assumed by uncatalogued workloads, or network-policy isolation preventing cross-tenant blast radius. CAB config is one policy-edit away from being disabled; chartered role is an org-chart artifact, not a control.
*Suggested fix*: Reframe as Level 2 honestly, and ADD Level 1 technical substrate: OPA Gatekeeper/Kyverno admission controller; IAM/service-account model where cron/pipeline principals are scoped per-catalog-entry and cannot authenticate against uncatalogued targets. Position OGO + CAB as governance wrapper around substrate, not primary gate.
*Evidence*: OSHA + NIOSH — elimination > substitution > engineering > administrative > PPE.

**Weakness 2 — CAB-bypass surface unaddressed (ADDRESSABLE)**
*Issue*: Enforcement surface is "change requests submitted to CAB tool." In practice, recurring workloads get created via direct kubectl apply, crontab -e, GitHub Actions schedules, Airflow DAGs, Terraform runs outside CAB, Jenkins admin job creation, DB-level scheduled events, cloud-native scheduler (EventBridge/Cloud Scheduler) created by IaC. None flow through a human CAB queue. The original Tuesday-smoke-test incident almost certainly used one of these paths.
*Suggested fix*: Move catalog-lookup enforcement from CAB submission layer to execution/scheduling layer: admission controller on cluster, server-side cron-validating daemon, Terraform/OPA policy on IaC apply, GitHub/GitLab scheduled-workflow policies requiring catalog-ID label. Enforcement at every path that creates recurring workloads.
*Evidence*: CNCF tooling (Kyverno/Gatekeeper, Tekton, Argo Workflows) — common scheduled-workload creation paths outside ITIL-style CAB workflows.

**Weakness 3 — Threshold self-declared and gameable (ADDRESSABLE)**
*Issue*: "≥2 engineering teams consuming" creates incentive toNOT register (claim single-team use, split teams on paper, route through proxy account). No mechanism derives 'shared' status from observed reality.
*Suggested fix*: Replace self-declared threshold with telemetry-derived classification: scheduled job reads IAM logs, VPC/namespace flow logs, API-caller identity data to identify platform with ≥2 distinct team principals in last 30 days. Auto-open catalog-registration ticket with hard SLA; if unregistered past SLA, admission controller flips namespace to read-only.
*Evidence*: AWS IAM Access Analyzer, GCP Recommender, OpenTelemetry tenant-attribution patterns.

**Weakness 4 — Annual attestation cadence too slow (ADDRESSABLE)**
*Issue*: 12-month review window means new platform created in month 2 can exist uncatalogued for up to 11 months.
*Suggested fix*: Replace annual attestation with continuous reconciliation: daily/weekly job diffs (platform-provisioning events ∪ observed-consumption telemetry) against (catalog entries). New platform auto-files registration ticket with 72h SLA; past SLA triggers admission-controller read-only flip. Annual attestation remains only as compliance artifact.
*Evidence*: Terraform Cloud drift detection, CrossGuard, AWS Config rules.

**Weakness 5 — 48h post-hoc exemption is a loss function (ADDRESSABLE)**
*Issue*: Original failure class plays out in minutes-to-hours. 48h retrospective review arrives after outage it was meant to prevent. Failure-mode-of-prevention field identifies bypass risk but 'fixes' with audit trail rather than a gate.
*Suggested fix*: Remove 48h post-hoc window entirely. For genuine emergencies, require synchronous approval from named on-call catalog-owner with <15min SLA (pager-based), else reject. Post-hoc audit = accountability tool, not prevention tool.
*Evidence*: Google SRE book §8 + PagerDuty incident-response guidance — distinguish 'gate' from 'audit.'

**Weakness 6 — Failure-mode-of-prevention undercounts (ADDRESSABLE)**
*Issue*: Missing (a) fail-open on admission-controller outage, (b) DRI-chain staleness, (c) catalog-entry drift.
*Suggested fix*: Extend enumeration: (a) fail-closed default on admission-controller health-check failure + break-glass path with two human approvers; (b) DRI auto-failover chain with 24h escalation, catalog invalidates if primary DRI inactive 30d; (c) quarterly re-attestation per-entry on its own cadence.
*Evidence*: Google/Meta/Slack SRE postmortem corpus — 'enforcement tool down → fail open' is top-5 contributor to repeat incidents.

**Weakness 7 — Admin override residual (RESIDUAL)**
*Issue*: Sufficiently senior engineer with legitimate admin credentials can always schedule a workload. Prevention controls accidents, not deliberate admin override.
*Suggested fix*: Accept as residual; document in risk register. Add detective control (anomaly detection on recurring-workload creation by admin principals).
*Evidence*: NIST SP 800-53 AC-6 (least privilege) and PAM literature.

**Weakness 8 — Q4 still missing (ADDRESSABLE)**
*Issue*: Q4_MRC_ND prevention action still truncated in audit input.
*Suggested fix*: Resubmit with complete Q4 object.
*Evidence*: Input data truncation.

**Round 2 SoA citations used**:
- OSHA + NIOSH Hierarchy of Controls
- CNCF tooling (OPA Gatekeeper, Kyverno, Tekton, Argo Workflows)
- AWS IAM Access Analyzer, GCP Recommender
- OpenTelemetry tenant-attribution patterns
- Terraform Cloud drift detection, Pulumi CrossGuard, AWS Config
- Google SRE book §8
- PagerDuty incident-response guidance
- Google/Meta/Slack public SRE postmortems
- NIST SP 800-53 AC-6

---

### Round 3 — Verdict: EXHAUSTED

**Weakness 1 — Hierarchy level still overstated (ADDRESSABLE)**
*Issue*: Stack is Level 2 (poka-yoke at a gate) + Level 3 (administrative: role, KPI, annual review). True Level 1 would make the shared infrastructure plane itself reject uncatalogued workload identity. Current design eliminates CAB-submitted path, not the class.
*Suggested fix*: Re-label as Level 2 with Level 3 supports, OR add admission-time enforcement layer (OPA/Gatekeeper k8s policy, Terraform Sentinel, IAM condition on catalog tag) so infrastructure itself rejects unregistered workloads.

**Weakness 2 — CAB-chokepoint scope gap (ADDRESSABLE)**
*Issue*: Control assumes every recurring workload reaches CAB. In practice, smoke tests and scheduled jobs commonly deploy via direct CI/CD pipelines, GitOps PRs, VM crons, kubectl apply, or ad-hoc Jenkins — none traverse change-management tool. "Unsubmittable" claim is narrower than stated.
*Suggested fix*: Add second enforcement point at deployment substrate (CI/CD policy gate + infrastructure admission controller) performing same catalog lookup. Both fail-closed on catalog miss.

**Weakness 3 — Annual attestation leaves 12-month blind window (ADDRESSABLE)**
*Issue*: New platform class (vector DB, ML feature store) can stand up, accumulate >2 consuming teams, and operate outside scope until next attestation. Mitigation addresses stale entries but not emergence of new platform categories.
*Suggested fix*: Tie platform-provisioning pipeline to automatic catalog registration with mandatory 'platform class' taxonomy field. Every provisioning run triggers catalog-classification event that must resolve within N days. Attestation verifies event log, not just current catalog state.

**Weakness 4 — OGO single-threaded role (RESIDUAL)**
*Issue*: If incumbent departs, KPI/attestation signatures/policy-repo ownership lapses during 3–6 month hiring gap at Director level.
*Suggested fix*: Charter named deputy (Principal Engineer or Platform Eng lead) with standing delegation authority for attestation signing and CAB rule maintenance. Deputy sign-off valid up to 180 days after OGO vacancy.

**Weakness 5 — No self-audit of CAB rule itself (ADDRESSABLE)**
*Issue*: Nothing prevents a future well-intentioned config change from weakening the rule. Measurability evidence lists one-time test case, not continuous assertion.
*Suggested fix*: Add scheduled synthetic probe (weekly) that submits dummy change request against known-uncatalogued target and asserts rejection. Probe failure pages OGO and opens P2 ticket. Probe status feeds board KPI dashboard.

**Weakness 6 — Q4 still truncated (ADDRESSABLE)**
*Issue*: Text ends mid-sentence at "The prevention's deployment surface." Cannot audit action that is not present.
*Suggested fix*: Supply Q4 action with (a) how future instances of failure mode detected before user-visible impact, (b) detection artifact type, (c) gate tests including MTTD target in minutes, not 'we will notice.'

**Round 3 verdict — EXHAUSTED**: remaining ADDRESSABLE weaknesses documented; RESIDUAL weaknesses accepted with compensating controls; further audit iterations produce diminishing returns.

**Round 3 SoA citations used**:
- NIST SP 800-53 CM-family + ISO 45001 hierarchy-of-controls analogue
- Kubernetes admission-webhook / OPA Gatekeeper / Kyverno
- Terraform Sentinel policy
- IAM tag-conditioned role assumption patterns

---

## Phase 6: Verification Plan + Proof of Action — FULL

**Overall timeframe**: 6 months minimum.
**Phase 8 trigger**: next recurrence of the same problem class.
**Fallback status**: `_fallback: true` — skeleton populated; owners to attach concrete metrics, targets, data sources, baselines, measurement schedules, and failure responses before closure.

### Q1 — TRC / NC — Corrective Action Verification

- **Metric**: TBD (recommended: # wall-clock-abort events on smoke stage per week; p99 stage runtime on Tuesdays).
- **Target**: TBD (recommended: 0 wall-clock-abort events; p99 ≤ 60% of hard timeout).
- **Data source**: TBD (recommended: CI time-series backend, stage-duration histogram).
- **Baseline**: unknown (to be measured at PR-merge time).
- **Measurement schedule**: TBD (recommended: weekly review for 6 weeks, then monthly).
- **Failure response**: TBD (recommended: re-open 8D; escalate to Q3/Q4 systemic actions).

### Q2 — TRC / ND — Corrective Action Verification

- **Metric**: TBD (recommended: Mean Time To Detect (MTTD) from p95 trend breach to alert fire).
- **Target**: TBD (recommended: MTTD ≤ 10 minutes; alert precision ≥ 70%).
- **Data source**: TBD (recommended: alert log + fault-injection test results).
- **Baseline**: unknown.
- **Measurement schedule**: TBD.
- **Failure response**: TBD (recommended: re-tune seasonality thresholds; re-scope spans).

### Q3 — MRC / NC — Prevention Action Verification

- **Metric**: TBD (recommended: % shared platforms with valid catalog entry; # CAB rejections/week; mean age of catalog entries since last DRI attestation; # emergency-lane uses against uncatalogued targets).
- **Target**: TBD (recommended: 100%; non-zero; <90 days; 0).
- **Data source**: TBD (recommended: service catalog + CAB audit log + telemetry-derived shared-infra scanner).
- **Baseline**: unknown.
- **Measurement schedule**: TBD (recommended: weekly OGO leading-indicator review; quarterly board-level outcome KPI).
- **Failure response**: TBD (recommended: OGO accountability review; admission-controller flip to read-only on un-attested platforms).

### Q4 — MRC / ND — Prevention Action Verification

- **Metric**: TBD (recommended: % CI stages with declared soft-SLO in `.ci-observability/`; weekly digest publication continuity; # scheduled-workload collision detections).
- **Target**: TBD (recommended: 100%; 100% on-cadence; 0 unreported collisions).
- **Data source**: TBD (recommended: pre-merge lint CI check logs + `.ci-observability/` config repo + digest archive).
- **Baseline**: unknown.
- **Measurement schedule**: TBD.
- **Failure response**: TBD (recommended: quarterly audit failure triggers platform-eng review; lint exemption expiry enforcement).

---

## SoA Citations (deduplicated across Phases 3/5)

Flat list of domain-of-knowledge sources drawn upon during the three audit rounds:

- **NIOSH/ISO 45001 Hierarchy of Controls** — elimination > substitution > engineering > administrative > PPE; used to classify Q3 action hierarchy level.
- **OSHA Hierarchy of Controls** — safety-domain analogue for software controls; used in Phase 5 Round 2.
- **SLSA (Supply-chain Levels for Software Artifacts)** — provenance-enforcing gates treated as L2; hermetic/reproducible as L4; used to critique Q3 Level 1 claim.
- **NIST SP 800-53 CM-family + AC-6 (least privilege)** — administrative vs. engineered controls; admin-override residual pattern.
- **Google SRE Book (§8 release engineering, error-budget discipline)** — freeze-the-change pattern; synchronous gate vs. asynchronous audit distinction.
- **DORA State of DevOps research** — change-failure-rate as KPI; emergency-lane abuse as bypass.
- **Balanced Scorecard literature** — leading vs. lagging indicator framing.
- **ISO 27001 risk-acceptance register** — exception-with-expiry pattern for edge cases.
- **Backstage / Humanitec** — service-catalog continuous-discovery patterns; 20–40%/year decay on manual catalogs.
- **CNCF tooling**:
  - OPA Gatekeeper (Kubernetes admission webhook)
  - Kyverno (policy engine for k8s)
  - Tekton (cloud-native CI)
  - Argo Workflows (workflow engine)
- **AWS IAM Access Analyzer** — consumption-based shared-resource detection.
- **GCP Recommender** — tenant-attribution recommender.
- **OpenTelemetry tenant-attribution patterns** — trace-based multi-tenant attribution.
- **Terraform Cloud drift detection / Pulumi CrossGuard / AWS Config rules** — continuous reconciliation replacing point-in-time attestation.
- **PagerDuty incident-response guidance** — synchronous on-call approval patterns.
- **Google/Meta/Slack public SRE postmortems** — enforcement-tool-down-→-fail-open corpus.
- **Kubernetes admission-webhook patterns** — scheduling-layer enforcement.
- **Terraform Sentinel policy** — IaC-apply-time policy enforcement.
- **IAM tag-conditioned role assumption** — catalog-tag-gated authentication.

---

## Closure Audit

**Checks performed**:
1. All four quadrants have Why-chains with ≥10 whys — **PASS** (Q1: 11, Q2: 11, Q3: 12, Q4: 11).
2. Each quadrant has a root statement synthesizing the chain terminal — **PASS**.
3. TRC quadrants (Q1, Q2) have corrective actions scoped to the instance — **PASS**.
4. MRC quadrants (Q3, Q4) have prevention actions scoped to the class — **PASS**.
5. Prevention actions carry hierarchy-level, deployment-scope, scope-justification, failure-mode-of-prevention, and a 3-gate test — **PASS** with caveats (Q3 hierarchy-level contested — claimed Level 1, audited as Level 2; Q4 lint-gate enforcement in place).
6. Phase 3 RC audit ran ≥2 rounds — **PASS** (3 rounds; verdict progression CONTINUE → CONTINUE → CONTINUE).
7. Phase 5 Prevention audit ran ≥2 rounds — **PASS** (3 rounds; verdict progression CONTINUE → CONTINUE → EXHAUSTED).
8. RESIDUAL risks explicitly named vs. silently dropped — **PASS** (Q1 Why #1/#5/#9/root branching documented; Q3 admin-override + definitional-ambiguity + single-threaded-DRI documented).
9. SoA citations captured per audit round — **PASS** (documented in Phase 3 and Phase 5 round narratives; consolidated in SoA Citations section).
10. Phase 6 verification plan populated — **PARTIAL** (skeleton only; `_fallback: true`; metrics/targets/data-sources marked TBD pending owner attachment).

**Flagged issues at closure**:
- **Phase 6 verification metrics are TBD.** CAPA owners (CI/Platform Engineering lead, OGO) must attach concrete metrics, targets, baselines, and measurement schedules before 2026-05-13 soak-test window for Q2 corrective action and before the first quarterly OGO review for Q3 prevention.
- **Q1 Why #10 evidence never attached** (flagged across all 3 Phase 3 rounds). Either cite the commit/PR that set the stage timeout or re-tag as working hypothesis before PoA baseline measurement.
- **Q1 Why #7/#8 topology not explicitly split into Chain-A/Chain-B** despite Round 2/3 audit recommendations. Documentation debt; does not block closure but should be addressed in next 8D iteration template.
- **Q3 hierarchy-level claim remains Level 1** despite Phase 5 Rounds 2–3 recommending Level 2 reclassification. Action owner should either add the Level 1 admission-controller substrate to meet the claim or downgrade the label to honestly Level 2.
- **Q4 action was reported truncated in Phase 5 audit inputs** across Rounds 1–3. The action text supplied in this report is the complete version from Phase 4; the audit truncation was a payload-transport artifact, not a real gap — flagged for process improvement in the pipeline handoff between Phase 4 and Phase 5.

**Overall closure state**: Report is production-ready for CAPA owner handoff with the above flags enumerated. The 8D is not yet "closed" — Phase 6 PoA evidence accrual is the gating step, scheduled at 6 months minimum with Phase 8 re-entry triggered by next recurrence of the problem class.

---

## Wiki Ingest Drafts

Following the Proactive Wiki Ingestion rule (global CLAUDE.md), these candidate insights from this 8D run are worth preserving cross-project:

1. **Tuesday-only failure pattern → weekly scheduled workload heuristic** — sudden-onset day-of-week-periodic failure modes almost always map to a discrete scheduled-job change event, not random flakiness or gradual drift. Correlates with existing wiki concept *Silent Staleness Pattern* and *Self-Healing Automation*. Candidate wiki page: `concepts/day-of-week-periodic-failure-heuristic.md`.

2. **Parallel-cause topology in Why-chain analysis** — when two independent technical defects on different axes can each alone produce a failure, the Why-chain should be explicitly split into labeled sibling chains (Chain-A/Chain-B) converging at the root, not spliced into a single linear chain. Addresses a meta-gap in 4Q RCA practice. Candidate wiki page: `concepts/why-chain-parallel-cause-topology.md`.

3. **Hierarchy-of-controls honest classification** — governance policy + CAB rule + annual attestation is Level 2 administrative, not Level 1 elimination. True Level 1 in software = admission-time enforcement at the infrastructure substrate (OPA Gatekeeper, Kyverno, Terraform Sentinel, IAM tag conditions). Maps to existing wiki pattern *Instructions vs Gates*. Candidate wiki page extension: `concepts/hierarchy-of-controls-software-domain.md`.

4. **CAB-chokepoint scope gap** — ITIL-style change-advisory processes only govern changes submitted via the CAB ticket. Recurring workloads commonly get created via direct deployment paths (kubectl apply, GitOps, Terraform, scheduled-workflow APIs) that never touch CAB. Enforcement must exist at every path that creates a recurring workload, not just the human-ticket path. Candidate wiki page: `concepts/cab-chokepoint-scope-gap.md`.

5. **Observability-contract-as-code pattern** — per-stage soft-SLO declarations + monitoring-as-code + pre-merge lint gate is a reusable template for making CI pipelines observable by construction. Candidate wiki page: `concepts/observability-contract-as-code.md`.

6. **Self-reinforcing blind spot** — absence of metric → absence of mandate → absence of metric. Governance reform requires seeding evidence from outside the blind-spot loop. Candidate wiki page: `concepts/self-reinforcing-detection-blindspot.md`.

7. **Verification scope expansion rule (echoed from project CLAUDE.md)** — after fixing a component in a pipeline system, verification scope MUST expand to the pipeline output level. This 8D run is a governance-layer analogue: after fixing a CI symptom, verification scope must expand to the governance layer (policy, catalog, attestation). Cross-link to existing *Pipeline Acceptance Criteria*.

*These are draft suggestions; user approval required before saving to `raw/notes/` and triggering ingest per `personal-wiki/CLAUDE.md`.*