# 8D Report — Missing Source Links and Key Quotes (P5)

**Date**: 2026-04-17
**Team**: Kuang-Yu (problem owner) + Claude Code (analyst) + RC Audit Agent + Prevention Audit Agent
**Status**: Open — awaiting user review

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: Formatter layer strips URL fields and truncates content uniformly — no data contract between source modules and formatters ensures URL/quote propagation | Q2: Template-to-data alignment is aspirational — template demands `{shortened_teams_link}` and `{exact quote}` but no validation checks that formatters supply the required data before sending to Claude |
| **MRC** | Q3: No output fidelity specification — project has no defined standard for what constitutes "traceable" output; traceability was an implicit aspiration, never a measured requirement with acceptance criteria | Q4: No end-to-end output quality audit — pipeline outputs are consumed but never systematically compared against source data to detect information loss; the silent data loss pattern (wiki: `silent-staleness`) applies to field-level data, not just temporal freshness |

---

## D1: Team

| Role | Name | Expertise |
|------|------|-----------|
| Problem Owner | Kuang-Yu | Solo developer, pipeline architect |
| Root Cause Analyst | Claude Code (Orchestrator) | 8D methodology, four-quadrant analysis |
| RC Auditor | RC Audit Agent | Independent adversarial audit, exhaustion model |
| Prevention Auditor | Prevention Audit Agent (separate) | Independent prevention challenge, failure mode analysis |

## D2: Problem Definition (IS/IS NOT)

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | Briefing output contains paraphrased summaries without clickable links to original sources (Teams chat URLs, email IDs, meeting recordings, OneNote pages, JIRA tickets). Template demands `[點此查看]({shortened_teams_link})` and `「{exact quote}」` — output contains zero `[點此查看]` links. Quotes appear but may be reconstructed from 120-200 char truncated previews, not verbatim. | Not a data collection failure — raw source data already contains URLs (`join_url`, `body_html`, `attachments`, `onenote_urls`, JIRA `key`). Not inability to format — Claude produces well-structured Markdown with quotes and links when given the data. |
| **WHERE** | All 6 `_format_*` functions in `briefing.py` discard URL/metadata fields. `_format_calendar` omits `join_url`; `_format_emails` omits `sender_email` and Outlook EntryID; `_format_teams_chats` truncates `content[:200]` and omits message ID / chat ID; `_format_jira` includes `key` as text but not as clickable URL; `_format_onenote` omits page URL. | Does not affect source modules — `outlook_calendar.py` captures `join_url`, `teams_chats.py` captures `body_html` + `attachments` + `onenote_urls`, `jira_issues.py` captures `key` + `base_url` in config, `onenote.py` captures page content and URL. |
| **WHEN** | Since initial implementation. Formatters were written as plain-text summaries for token efficiency. Template later gained `{shortened_teams_link}` placeholders, but formatters were never updated. Verified in output from 2026-04-16 and 2026-04-17: zero `[點此查看]` links in either. | Not a regression — never worked. The template is aspirational, not descriptive of actual behavior. |
| **EXTENT** | Every source type affected: Calendar (0/N events with `join_url` passed through), Email (0/N with message ID or OWA link), Teams chat (0/N with deep link), JIRA (ticket keys shown as text, never as `{base_url}/browse/{key}` URL), OneNote (0/N with page URL). Content truncation uniform: emails at 120 chars, Teams at 200 chars, OneNote diff at 500 chars. | Not intermittent — 100% of items missing links. Not source-specific — affects all 6 source types identically. |

## D3: Containment (Immediate Actions)

| # | Action | Owner | Date | Status |
|---|--------|-------|------|--------|
| 1 | Draft 8D report written (`8D-005-missing-source-links-and-quotes.md`) identifying 4 quadrant root causes | Claude Code | 2026-04-16 | Done — INSUFFICIENT (Q3/Q4 at code level, not management level) |
| 2 | This full 8D report deepening to management-system level | Claude Code | 2026-04-17 | In progress |

**Note:** No code containment needed — the problem is information loss, not incorrect behavior. Output is still useful, just less traceable than it should be.

## D4: Root Cause Analysis (Four Quadrants)

### Q1: Technical x Occurrence (TRC-NC)

**Question: WHY do source URLs and verbatim content technically fail to reach the briefing output?**

```
Why-1: Briefing output has zero clickable source links and quotes are reconstructed from truncated previews.
  → Claude API receives formatted context where URLs and full content have been stripped.

Why-2: Why are URLs and full content stripped from the formatted context?
  → _format_* functions in briefing.py cherry-pick fields using hardcoded access
    (e.g., e['subject'], e['sender_name'], m['content'][:200]) — URL fields like
    join_url, message ID, chat ID, page URL are never accessed.

Why-3: Why do formatters cherry-pick instead of passing through all metadata?
  → Formatters were designed as ad-hoc string builders minimizing token count.
    Each function independently decides which fields to include. No shared contract
    specifies required fields for downstream output.

Why-4: Why no shared contract?
  → Source modules return plain dicts with no schema. Formatters consume dicts
    with no type checking. Fields silently disappear when a formatter doesn't
    explicitly access them. Python dict access is permissive — missing fields
    cause no error, just absence.

Why-5: Why plain dicts without schema?
  → Pipeline was built incrementally: source first (get data), then formatter
    (summarize for Claude), then template (describe desired output). Each layer
    designed in isolation. Template demands links; formatter doesn't know this.

Why-6: Why designed in isolation?
  → No specification document defining the data flow contract between layers.
    Each layer's requirements were implicit in the developer's mind during
    implementation, not written down.

Why-7: Why no data flow specification?
  → Project treated the pipeline as a prototype/MVP — "get it working" rather
    than "get it right." Data flow was obvious when holding everything in
    working memory during initial development.

Why-8: Why prototype-quality data flow persisted?
  → No milestone or review that would have caught the contract gap. The template
    was added later (aspirational output format) without backpropagating its
    requirements to the formatter layer.

Why-9: Why no backpropagation of requirements?
  → Template was treated as a WISH LIST for Claude (prompt engineering), not as a
    SPECIFICATION constraining the data pipeline. The mental model: "tell Claude
    what we want and it will figure it out" — ignoring that Claude can't fabricate
    URLs it was never given.

Why-10: Why the wrong mental model?
  → Fundamental confusion between "prompt template as output spec" and "prompt
    template as data contract." The template looks like it's for Claude (it is),
    but it also implicitly specifies requirements on the data layer (it's not
    treated as such).

ROOT CAUSE: No data contract between source → formatter → template layers. Formatters
built as ad-hoc string reducers with no obligation to propagate URL/metadata fields.
Template treated as prompt engineering artifact, not as a requirements specification
that constrains the data pipeline.

First-Principles Test:
- Condition: ✅ Ongoing (contractless pipeline persists)
- On/Off: ✅ Adding typed contract with required URL fields forces propagation
- Class: ✅ Explains all missing fields across all 6 source types
- Controllability: ✅ Can define contract (TypedDict/dataclass)
```

### Q2: Technical x Non-Detection (TRC-ND)

**Question: WHY wasn't the template-to-data mismatch detected before reaching the user?**

```
Why-1: Template demands {shortened_teams_link} and {exact quote} but output has zero
       clickable links — and nobody noticed programmatically.
  → No validation checks whether formatted data can satisfy template placeholders.

Why-2: Why no validation?
  → The template is a TEXT STRING embedded in a prompt to Claude. It's not a
    structured format with machine-checkable slots. The {placeholders} are
    aspirational guidance for Claude, not Python f-string variables.

Why-3: Why aspirational rather than checkable?
  → Claude's flexibility creates an illusion of contract fulfillment. Claude
    CAN produce well-formatted output with quotes (it reconstructs from whatever
    data it has). The output LOOKS correct — quotes appear, formatting is right.
    Only upon inspection do you realize the quotes may be fabricated from 120-char
    truncated previews and links are silently omitted.

Why-4: Why does "looks correct" fool the detection system?
  → There IS no detection system. Output is generated → published → consumed.
    No post-generation check validates: (a) link count > 0 for sources that
    have URLs, (b) quotes match verbatim content from source data.

Why-5: Why no post-generation check?
  → Output quality was assessed informally by the user reading the Telegram brief
    and Notion page. The user evaluates CONTENT USEFULNESS, not DATA FIDELITY.
    A useful briefing without links is still useful — the degradation is below
    the user's complaint threshold.

Why-6: Why below complaint threshold?
  → User's primary need is "what happened yesterday and what do I need to do."
    Source links are a CONVENIENCE (click to verify). Absence of convenience
    doesn't trigger complaint — absence of content would.

Why-7: Why isn't convenience measured?
  → No quality dimensions defined for the output. No rubric saying "traceable
    output requires: (1) ≥1 source link per action item, (2) verbatim quotes
    ≥20 chars from source data." Quality is binary: "useful" vs "not useful."

Why-8: Why no quality rubric?
  → Pipeline's quality gate (Layer 3 in self-healing) scores AI response quality
    but on CONTENT dimensions (completeness, relevance), not DATA FIDELITY
    dimensions (link presence, quote accuracy, source traceability).

Why-9: Why content-only quality gate?
  → Quality gate was designed to catch Claude hallucination and topic coverage
    gaps — the most visible failure modes. Information LOSS (data present in
    source but absent in output) is a silent failure mode that doesn't trigger
    content-quality checks.

Why-10: Why is information loss silent?
  → This is the Silent Staleness Pattern (wiki: silent-staleness) applied to
    field-level data instead of temporal freshness. The pipeline runs, output
    looks normal, but metadata (URLs, full quotes) silently degraded. The user
    has no reason to doubt the output because the high-level content is correct.

ROOT CAUSE: No output fidelity validation. Quality gate checks content quality
(topic coverage, hallucination) but not data fidelity (are source URLs preserved?
are quotes verbatim?). The Silent Staleness Pattern applies: field-level information
loss is invisible because the output surface looks correct.

First-Principles Test:
- Condition: ✅ Ongoing (no fidelity check exists)
- On/Off: ✅ Adding post-generation link/quote validation catches the gap
- Class: ✅ Any field-level data loss escapes current quality gate
- Controllability: ✅ Can add fidelity dimensions to quality gate
```

### Q3: Managerial x Occurrence (MRC-NC)

**Question: WHY does the development process allow field-level data loss to exist uncorrected?**

```
Why-1: Formatters strip URL fields and the template-to-data gap persists.
  → No one has prioritized fixing it despite awareness (draft 8D-005 from 4/16).

Why-2: Why not prioritized?
  → The output is USEFUL without links. User gets actionable briefing. Links are
    a quality improvement, not a bug fix. Quality improvements compete against
    new features and actual bugs for development bandwidth.

Why-3: Why does quality compete with features?
  → No defined output quality standard specifying minimum acceptable output
    characteristics. Without a standard, "missing links" is an improvement
    suggestion, not a non-conformance.

Why-4: Why no output quality standard?
  → Project defines quality operationally ("does the pipeline run and produce
    output?") not functionally ("does the output meet traceability requirements?").
    Pipeline health (self-healing, staleness detection) is well-developed.
    Output content quality is ad-hoc.

Why-5: Why operational quality only?
  → Development prioritized RELIABILITY (it must run daily without human
    intervention) over FIDELITY (output must preserve source metadata).
    Reliability is existential — if the pipeline doesn't run, there's no output.
    Fidelity is incremental — output without links is still output.

Why-6: Why was this prioritization not revisited?
  → No periodic output quality review. Pipeline health is monitored (self-healing
    logs, staleness counters). Output quality is assessed only when the user
    reads it and notices something wrong.

Why-7: Why no output quality review?
  → No OUTPUT SPECIFICATION to review against. You can't audit compliance with
    a standard that doesn't exist. The template (daily_sum.md) is the closest
    thing to a spec, but it's treated as prompt guidance, not as an acceptance
    criteria document.

Why-8: Why no output specification?
  → Project evolved from "can we automate a daily brief?" (feasibility) to
    "automate a daily brief" (production). The transition from prototype to
    production happened WITHOUT defining what "production quality" means for
    the output. Infrastructure got production treatment (self-healing, error
    handling, monitoring). Output did not.

Why-9: Why infrastructure but not output?
  → Infrastructure failures are VISIBLE (pipeline crashes, stale data banners,
    Telegram notifications missing). Output quality degradation is INVISIBLE
    (useful briefing, just without links). Visible problems get fixed.
    Invisible problems persist.

Why-10: Why are invisible problems not systematically discovered?
  → No output quality management process. In mature systems (IATF 16949,
    ASPICE SYS.2), output requirements are defined BEFORE implementation and
    verified AFTER. This project has neither: no pre-defined output acceptance
    criteria, no post-delivery fidelity audit. The quality management gap
    from P1 (deferred fixes) extends to output: just as behavioral rules
    need gates, output quality needs measurable acceptance criteria.

ROOT CAUSE: No output fidelity specification or acceptance criteria. Project
transitioned from prototype to production without defining what "production
quality" means for the OUTPUT (as opposed to the INFRASTRUCTURE). Without a
specification, field-level data loss is an improvement suggestion, not a
non-conformance — it can never be "detected" because there's nothing to
detect it against.

MRC Level Check: ✅ MANAGEMENT SYSTEM — quality specification, acceptance criteria,
prototype-to-production transition process.

First-Principles Test:
- Condition: ✅ Ongoing (no output spec exists)
- On/Off: ✅ Defining output spec with link/quote requirements makes gap a NC
- Class: ✅ Any output quality dimension without a spec is invisible
- Controllability: ✅ Can define output spec
```

### Q4: Managerial x Non-Detection (MRC-ND)

**Question: WHY does the process allow field-level information loss to go UNDETECTED across the full pipeline?**

```
Why-1: Data flows source → formatter → Claude prompt → Claude output → publish
       with no checkpoint verifying field preservation at any stage.
  → No stage-gate checks for data fidelity in the pipeline.

Why-2: Why no stage-gate checks?
  → Pipeline monitoring is OPERATIONAL: "did each stage succeed?" (try/except
    with [WARN] logging). Not DATA-AWARE: "did each stage preserve required
    fields?" Success = function returned without error.

Why-3: Why operational-only monitoring?
  → Pipeline stages communicate via RETURN VALUES (dicts, strings). Monitoring
    checks function-level success/failure, not content-level completeness.
    A formatter that returns a string with zero URLs is a "success."

Why-4: Why is zero-URL output a "success"?
  → No DEFINITION of what constitutes a complete/correct formatted output.
    Success is defined by absence of exceptions, not by presence of required
    data. The function signature says "return str" — any string is valid.

Why-5: Why no definition of correct output?
  → Same root as Q3: no output specification. But here the gap is specifically
    in INTER-STAGE validation. Even without a full output spec, a simple
    assertion ("formatted output for N items with URLs should contain ≥1 URL")
    would catch the gap. No such assertion exists.

Why-6: Why no inter-stage assertion?
  → Testing strategy is END-TO-END (run pipeline, check final output) not
    STAGE-WISE (check each transformation preserves required fields). E2E
    testing catches "pipeline produces output" but not "output preserves
    source metadata."

Why-7: Why E2E-only testing?
  → No test infrastructure for stage-wise validation. Unit tests exist for
    some components but not for formatter fidelity. The formatter functions
    are treated as PRESENTATION logic (how to display), not as DATA
    TRANSFORMATION logic (what to preserve).

Why-8: Why presentation vs transformation distinction matters?
  → Presentation logic is tested by reading the output. Transformation logic
    is tested by comparing input and output. The formatters ARE transformations
    (dict → string with specific fields), but they're treated as presentation
    (make it look nice for Claude). This misclassification means they don't
    get transformation-appropriate testing (field preservation checks).

Why-9: Why are formatters misclassified?
  → Mental model: "formatter prepares human-readable context for Claude" vs
    correct model: "formatter is an ETL step that must preserve metadata while
    reducing token count." The ETL model demands field preservation guarantees;
    the presentation model does not.

Why-10: Why the wrong mental model for formatters?
  → No architecture review classified pipeline components by their data
    responsibilities. Components grew organically — each function does what
    it needs to do, nobody mapped the full data flow to identify where
    information loss could occur. This is the Silent Staleness Pattern
    (wiki: silent-staleness) at the architecture level: the system looks
    healthy (runs daily, produces output) while silently losing data at
    transformation boundaries.

ROOT CAUSE: No data flow architecture review classifying pipeline stages as
transformations with field-preservation obligations. Formatters misclassified
as presentation logic (no fidelity testing needed) instead of ETL stages
(field preservation must be verified). Silent Staleness Pattern applied to
architecture: system looks healthy while silently losing data at each
transformation boundary.

MRC Level Check: ✅ MANAGEMENT SYSTEM — architecture review, pipeline stage
classification, monitoring scope definition.

First-Principles Test:
- Condition: ✅ Ongoing (no architecture review or stage classification)
- On/Off: ✅ Architecture review + stage-wise validation catches field loss
- Class: ✅ Any untested transformation boundary can silently lose fields
- Controllability: ✅ Can review and classify pipeline stages
```

### RC Audit Result

**Audit Process:** 3 challenge rounds + 1 exhaustion assessment. Independent adversarial audit testing each quadrant for depth, accuracy, and distinction.

#### Round 1: Initial Challenge

| # | Weakness | Quadrant | Fix |
|---|----------|----------|-----|
| 1 | Q1 Why-9: "wish list vs specification" is restatement of Why-6 — circular | Q1 | Refined: Why-9 specifies the MENTAL MODEL confusion (prompt guidance vs data contract). Why-6 is about review absence. Different aspects. |
| 2 | Q2: "Silent Staleness Pattern" analogy is a stretch — staleness is about TIME, this is about FIELDS | Q2 | Retained with qualification: "applied to field-level data instead of temporal freshness." The mechanism is identical (system looks healthy, data silently degraded, no trigger for investigation). The wiki concept generalizes. |
| 3 | Q3 Why-8: "prototype to production transition" — was there an explicit transition? | Q3 | Revised: transition was IMPLICIT (pipeline started running on Task Scheduler daily, accumulating users/dependents). No ceremony or checklist. The absence of explicit transition IS the gap. |
| 4 | Q4: "ETL model" jargon may obscure the actual insight | Q4 | Simplified explanation: formatters must be tested for what they PRESERVE, not just what they PRODUCE. Kept ETL terminology as accurate descriptor. |

#### Round 2: Depth Challenge

| # | Weakness | Quadrant | Fix |
|---|----------|----------|-----|
| 5 | Q1: Why-10 repeats Q2 findings — both say "template as wish list" | Q1/Q2 | Sharpened distinction: Q1 is about why the GAP EXISTS (no contract). Q2 is about why the gap goes UNDETECTED (no validation). Root causes are different mechanisms even though they share a common ancestor. |
| 6 | Q3: "No output quality standard" — is this really management-level? Could be just a missing document. | Q3 | Deepened: the missing document is a SYMPTOM. The management-level root cause is the implicit prototype-to-production transition without defining "production quality." A document is a TRC fix; the process that should have REQUIRED the document is the MRC. |
| 7 | Q3/Q4 overlap: both cite "no output specification" | Q3/Q4 | Differentiated: Q3 is about OCCURRENCE (why the gap persists — no spec to define it as a problem). Q4 is about DETECTION (why it's not caught — no stage-wise validation because formatters misclassified). Different prevention actions. |
| 8 | Q2 Why-5: "below complaint threshold" — is this speculation about user behavior? | Q2 | Grounded: verified in actual output (2026-04-16, 2026-04-17) — user received briefings with quotes but zero links, continued using the system. 2 days of zero links = below complaint threshold. Not speculation. |

#### Round 3: Completeness Challenge

| # | Weakness | Quadrant | Fix |
|---|----------|----------|-----|
| 9 | IS/IS NOT: "quotes may be fabricated" — verify with evidence | D2 | Verified: output/daily_sum_2026-04-17.md line 209 shows quote "這個目標是追蹤 safety 完整性..." attributed to Soar Hung. _format_teams_chats truncates at [:200]. Quote is 70+ chars so fits within truncation. This specific quote is likely real (from email preview). But quotes attributed to Teams messages with [:200] truncation may be reconstructed. Refined language to "may be reconstructed from truncated content." |
| 10 | D2 EXTENT: "100% of items missing links" — is JIRA really missing links? The formatter shows ticket key. | D2 | Clarified: JIRA key appears as TEXT (e.g., "RL6767-5641") not as clickable URL (e.g., `[RL6767-5641](https://devops.realtek.com/jira/browse/RL6767-5641)`). Key is present but not actionable as a link. |
| 11 | Missing: what about Copilot raw passthrough? _format_teams_chats passes copilot_raw directly. | Q1 | Added to analysis: copilot_raw passthrough is an exception — it passes Claude's own summary text, which by nature has no source URLs. This is a different failure mode (Copilot doesn't provide URLs) vs formatters stripping URLs. Both contribute. |

#### Residual Risks

| # | Risk | Why Residual | Mitigation |
|---|------|-------------|------------|
| R1 | Quote accuracy cannot be fully verified without comparing against source data at output time | Would require storing source data alongside output — storage/complexity tradeoff | Post-generation validation can check quote length and presence, not accuracy |
| R2 | Some source types genuinely lack URLs (Outlook COM doesn't expose a stable web-accessible URL for emails) | Platform limitation — not all data sources provide web-linkable references | Fall back to Outlook protocol links (`outlook://`) or OWA URLs where possible; mark others as "no link available" |
| R3 | Token budget pressure may resurface if all URLs and full quotes are added | Real constraint — context window is finite | Importance-weighted budget (key items get full content + URL; others get summary) |
| R4 | Copilot raw passthrough inherently lacks source URLs | Copilot returns prose summaries, not structured data with links | When Copilot is the source, note "source: M365 Copilot" without pretending a deep link exists |

**Verdict: EXHAUSTED** — no further weaknesses found that change root cause conclusions or prevention direction.

---

## D5: Corrective Actions (Q1, Q2)

| # | Quadrant | Action | Owner | Date | Evidence |
|---|----------|--------|-------|------|----------|
| CA1 | Q1 TRC-NC | Define `FormattedItem` TypedDict with required fields: `source_url: str | None`, `raw_content: str` (pre-truncation for key items), `source_type: str`. All `_format_*` functions must produce items conforming to this contract. Add URL construction helpers per source type (Teams deep link, JIRA browse URL, Calendar join_url passthrough, OneNote webUrl, Email OWA link). | Claude Code | TBD | TypedDict definition + formatter refactor + unit tests asserting URL propagation |
| CA2 | Q2 TRC-ND | Add post-generation fidelity check: after Claude produces output, scan for (a) action items without `[點此查看]` links — warn if source data had URLs, (b) quotes shorter than 20 chars — flag as potentially truncated. Add "data fidelity" dimension to quality gate scoring alongside existing content quality dimensions. | Claude Code | TBD | Fidelity check function + quality gate enhancement + test |
| CA3 | Q1 TRC-NC | Replace uniform truncation (`[:200]`, `[:120]`) with importance-weighted content budget: `is_mention=True` or `importance=High` or action-keyword match → 800 chars; others → 150 chars. Ensures key quotes survive intact. | Claude Code | TBD | Budget logic in formatters + test with sample data |

## D6: Prevention Actions (Q3, Q4)

### Prevention Q3 (MRC-NC): Output Fidelity Specification + Production Quality Gate

**What the draft got wrong:** Draft 8D-005 proposed "URL construction helpers" and "typed data contract" — both are TRC (code-level fixes). The MRC root cause is: no output quality specification exists, so the gap cannot be classified as a non-conformance. Fixing the code without fixing the process means the NEXT aspirational template feature will have the same gap.

**Action:** Define an Output Fidelity Specification as a project artifact (`docs/output-spec.md`) with measurable acceptance criteria:

1. **Specification document** defining output quality dimensions:
   - **Traceability**: Every action item MUST include a source link (URL or "unavailable" with reason). Metric: % of action items with source links. Target: 100%.
   - **Quote fidelity**: Every action item MUST include a verbatim quote ≥20 chars from source data. Metric: % of action items with quotes. Target: 100%.
   - **Source coverage**: Every source type with data MUST appear in output. Metric: source types in output / source types with data. Target: 100%.
   - **Field preservation**: URL fields from source data MUST survive to formatted context. Metric: URLs in formatted context / URLs in source data. Target: ≥80% (some sources genuinely lack URLs).

2. **Template-as-spec process**: When adding new placeholders to templates, BACKPROPAGATE requirements to the data layer. Checklist: (a) can the formatter supply this data? (b) does the source module capture it? (c) is there a test? Template changes without passing this checklist are blocked.

3. **Production readiness gate**: Before any pipeline component transitions from "working" to "scheduled/production," verify output against the fidelity spec. This applies retroactively to the current pipeline (it's already in production without having passed this gate).

**10-Why Prevention Chain:**

```
Spec defined (Why-10 fix)
  → Production quality criteria exist for output, not just infrastructure (Why-9)
  → Output quality becomes visible and auditable (Why-8)
  → Prototype-to-production transition has a quality checkpoint (Why-7)
  → Template additions require data layer verification (Why-6)
  → Missing links classified as non-conformance, not improvement (Why-5)
  → Quality improvement vs bug fix distinction resolved by spec (Why-4)
  → Output fidelity has defined standard (Why-3)
  → Fixing the gap is prioritized as NC, not feature request (Why-2)
  → Source URLs and quotes reach the output (Why-1)
```

**Gate Test:**

| Test | Result | Evidence |
|------|--------|---------|
| Scope | PASS | Prevents CLASS: any future template-to-data gap becomes detectable against the spec. Not specific to URLs. |
| Persistence | PASS | Specification document in repo + template change checklist + production readiness gate. Lives beyond any single session. |
| Measurability | PASS | 4 defined metrics with numeric targets. Can be measured automatically (link count, quote length, source coverage). |
| Prevention vs TRC | PASS | TRC = add URL helpers. MRC = define the spec that REQUIRES URL helpers and catches future gaps. |

**Prevention Hierarchy Level:** 3 (Detect against specification before delivery) — aspiring to Level 2 via automated fidelity check in pipeline.

**Deployment Scope:** PROJECT-LEVEL — output fidelity spec is specific to this pipeline. The principle (define acceptance criteria before production) is generalizable but the artifact is project-specific.

### Prevention Q4 (MRC-ND): Pipeline Stage Classification + Data Flow Audit

**What the draft got wrong:** Draft 8D-005 proposed "template-input alignment test" — a TRC detection mechanism. The MRC root cause is: formatters are misclassified as presentation logic and therefore don't get transformation-appropriate testing. No architecture review maps data flow and field preservation obligations.

**Action:** Conduct a data flow architecture review and establish ongoing pipeline stage classification:

1. **Data flow map** (`docs/data-flow-map.md`): Document each pipeline stage with:
   - Input fields (from source module)
   - Output fields (to next stage)
   - Fields that MUST be preserved (based on output fidelity spec from Q3)
   - Fields that may be reduced/summarized (with stated budget)
   - Classification: **ETL** (field preservation required) or **Presentation** (formatting only)

2. **Stage-wise validation**: For each stage classified as ETL, add a validation assertion:
   - Formatter receives N items with URLs → formatted output contains ≥N URL strings
   - Formatter receives M items with content → formatted output preserves content for items matching importance criteria
   - These assertions run as part of the pipeline (not just unit tests) — catch regressions at runtime.

3. **Periodic data flow audit** (quarterly): Compare actual field flow against the data flow map. Check for new fields added to source modules that aren't propagated to formatters. This catches the "new field silently dropped" pattern before it becomes a user-visible problem.

4. **Silent data loss detection**: Extend the Silent Staleness Pattern defense (wiki: `silent-staleness`) from temporal freshness to field-level freshness. Just as the pipeline detects stale DATES (Layer 1 in wiki), it should detect stale/missing FIELDS (URLs present in source but absent in output).

**10-Why Prevention Chain:**

```
Architecture review + stage classification (Why-10 fix)
  → Data flow responsibilities are explicit per stage (Why-9)
  → Formatters classified as ETL, get preservation testing (Why-8)
  → Stage-wise validation checks field preservation (Why-7)
  → Inter-stage assertions catch missing fields (Why-6)
  → Zero-URL formatted output flagged as assertion failure (Why-5)
  → Pipeline monitoring becomes DATA-AWARE, not just operational (Why-4)
  → Missing URLs detected before output reaches user (Why-3)
  → Quality gate covers data fidelity, not just content (Why-2)
  → Field-level information loss is detected and prevented (Why-1)
```

**Gate Test:**

| Test | Result | Evidence |
|------|--------|---------|
| Scope | PASS | Prevents CLASS: any field-level data loss at any pipeline stage. Not specific to URLs. |
| Persistence | PASS | Data flow map in repo + stage-wise assertions in code + quarterly audit schedule. |
| Measurability | PASS | Fields preserved / fields expected, per stage. Assertion pass/fail counts. Quarterly audit report. |
| Prevention vs TRC | PASS | TRC = add URL validation. MRC = classify stages and establish the process that requires validation at transformation boundaries. |

**Prevention Hierarchy Level:** 2 (Error-proofing via runtime assertions at transformation boundaries) — highest feasible level for data flow validation.

**Deployment Scope:** PROJECT-LEVEL for the data flow map; GENERALIZABLE PRINCIPLE (classify pipeline stages, validate transformations) applicable to any ETL-style pipeline.

### Prevention Audit Result

**Audit Process:** 3 challenge rounds + exhaustion assessment by independent prevention auditor.

#### Round 1: Initial Prevention Challenge

| # | Weakness | Fix |
|---|----------|-----|
| 1 | Q3: "Output spec" is a document — documents get ignored (same as text instructions). Where's the gate? | Added: template change checklist + production readiness gate. Document + gate combination. Automated fidelity check in pipeline enforces at runtime. |
| 2 | Q3: "Backpropagate requirements" to data layer — who enforces this? | Checklist tied to template file changes: pre-commit hook detects changes to `templates/*.md` and requires corresponding test update. |
| 3 | Q4: "Quarterly audit" — proven to slip without enforcement. | Audit tracked in `governance/` with git-based evidence. Missing quarterly report visible in git log. Calendar reminder as backup. |
| 4 | Q4: Stage-wise assertions can be bypassed (remove assertion, commit passes). | Assertions in a dedicated `validators/` module imported by pipeline. Pre-commit hook checks that validators are called. Removing import = hook failure. |

#### Round 2: Depth Challenge

| # | Weakness | Fix |
|---|----------|-----|
| 5 | Q3: "100% target" for action items with source links — some sources genuinely have no linkable URL (e.g., Outlook COM emails). Unrealistic target = ignored target. | Revised: 100% must have EITHER a link OR "link unavailable: {reason}". The requirement is traceability (user knows where data came from), not that every item is clickable. |
| 6 | Q3: Production readiness gate applied retroactively — does that mean current pipeline is "non-production" until passing? | Clarified: current pipeline is in production de facto. Gate applies to the OUTPUT SPEC compliance, not the pipeline status. Result: identify and track gaps as open NCs. |
| 7 | Q4: Data flow map maintenance cost — who updates it when source modules change? | Added: source module change triggers map review (pre-commit hook detects changes to `sources/*.py` and prints reminder). Not a blocking gate (too noisy), but a visible reminder. |
| 8 | Q4: "Extend Silent Staleness Pattern to field level" — is this a real extension or metaphor-stretching? | Validated: the mechanism is identical. Temporal staleness: pipeline runs → stale dates → user trusts output. Field staleness: pipeline runs → missing URLs → user trusts output. Same detection principle (compare expected vs actual), same defense layers. Legitimate extension. |

#### Round 3: Exhaustion Challenge

| # | Weakness | Fix |
|---|----------|-----|
| 9 | Both Q3 and Q4 create maintenance burden (spec, map, quarterly audit) — solo developer may deprioritize | Acknowledged. Mitigated: automated assertions do the heavy lifting. Spec and map are one-time creation + low-frequency maintenance. The quarterly audit is the highest-cost item but also the most valuable for catching drift. |
| 10 | "Template change checklist" — is there evidence this pattern works in practice? | Evidence from this project: pre-commit hooks for wiki markers and detection artifacts DO work (verified in git history). Same enforcement mechanism, new trigger (template file change). |

#### Residual Risks

| # | Risk | Why Residual | Mitigation |
|---|------|-------------|------------|
| W1 | Output spec becomes stale if output evolves without spec updates | Can't fully prevent spec drift without automated spec-to-output comparison | Quarterly audit catches drift; spec in same repo as code |
| W2 | Stage-wise assertions add runtime overhead | Assertions are string checks (O(n) on formatted output), negligible vs Claude API call | Monitor pipeline latency; disable assertions only if >10% overhead |
| W3 | Data flow map is a snapshot, not a living system | Full automation (type system enforcing field flow) is beyond current project scope | Map + quarterly review is practical minimum for solo project |
| W4 | Template change hook may generate false positives (cosmetic template edits) | Hook checks for placeholder changes, not all edits | Exemption tag `# TEMPLATE-COSMETIC` for non-functional changes |

**Verdict: EXHAUSTED** — prevention actions are appropriately scoped for the project scale with clear enforcement mechanisms.

---

## D7: Verification Plan

| # | Prevention | Metric | Data Source | Timeframe | Success Criteria | Failure Action |
|---|-----------|--------|-------------|-----------|------------------|----------------|
| 1 | Q3: Output Fidelity Spec | Action items with source links or "unavailable" annotation | Post-generation fidelity check log | 30 days after implementation | 100% of action items have link or annotation | Investigate: is the spec incomplete, or is the formatter not propagating? |
| 2 | Q3: Template change checklist | Template changes with corresponding formatter + test updates | Pre-commit hook enforcement log | 6 months | 100% of template placeholder additions have data layer verification | Strengthen hook to blocking gate |
| 3 | Q4: Stage-wise validation | Assertion pass rate across pipeline runs | Pipeline run logs | 30 days after implementation | ≥95% assertion pass rate (some runs may have sources unavailable) | Investigate failed assertions — are they bugs or spec issues? |
| 4 | Q4: Quarterly data flow audit | Fields in source modules vs fields in formatted output | Audit report in `governance/` | 6 months (2 quarterly cycles) | ≥2 audits completed; new fields captured within 1 quarter | Automate field inventory comparison |
| 5 | Overall | Zero-link action items in output | grep output files for action items without links | Ongoing | 0 link-less action items (excluding annotated "unavailable") | Re-open D4: root cause not fully addressed |

---

## D8: Lessons Learned & Horizontal Deployment

### Lessons Learned

1. **Templates are specifications, not wish lists.** When a template says `{shortened_teams_link}`, that's a DATA REQUIREMENT on the upstream pipeline, not just prompt guidance for Claude. Treating templates as aspirational creates silent gaps between what the output promises and what the data pipeline delivers.

2. **Silent Staleness applies to fields, not just time.** The wiki's Silent Staleness Pattern (data goes stale without visible indicators) applies equally to field-level information loss. A pipeline can deliver fresh, useful output while silently dropping metadata (URLs, full quotes, attachment references) at every transformation boundary. The detection principle is the same: compare expected fields against actual fields.

3. **Formatters are ETL, not presentation.** String-building functions that transform structured data (dicts with URLs, content, metadata) into prompt context are data transformations with preservation obligations. Testing them only for "does the output look right" misses "does the output contain what the source provided." The ETL classification demands field preservation testing.

4. **Prototype-to-production needs an output checkpoint.** This project developed strong infrastructure quality (self-healing, error handling, monitoring) but never defined output quality. The implicit prototype-to-production transition (started running on Task Scheduler) should have included: "what must the output contain to be considered production quality?" Infrastructure quality ≠ output quality.

5. **Quality gates measure what they're designed for — nothing more.** The existing quality gate scores Claude's response on content dimensions (completeness, relevance). It works perfectly for that purpose. But adding a quality gate for content doesn't mean data fidelity is covered. Each quality dimension needs explicit definition and measurement.

### Horizontal Deployment

| Similar problem/process | Action | Status |
|------------------------|--------|--------|
| P3: Configured-but-disconnected features | Same class: template promises feature, data layer doesn't deliver. Q3 output spec addresses this systematically. | Covered by Q3 prevention |
| Action item extraction (`extract_action_items`) | Extracts items from Claude output — if Claude omits links (because formatters don't provide URL data), extracted items also lack links. | Downstream effect of this problem; fixed by CA1 |
| Future source modules (e.g., SharePoint, new API integrations) | New sources must conform to `FormattedItem` TypedDict contract. Data flow map must be updated. | Covered by Q4 prevention (stage classification + quarterly audit) |
| Notion publisher (`notion_summary.py`) | Receives action items — if items lack source links, Notion tasks lack context. | Downstream effect; covered by CA1 propagating URLs through pipeline |
| Any pipeline project in `D:/D-claude/` | Principle: define output spec before production; classify transformations; validate field preservation. | Generalizable pattern; candidate for wiki ingest |

### Documents Updated

- [ ] `docs/output-spec.md` — Output fidelity specification (to be created as part of CA implementation)
- [ ] `docs/data-flow-map.md` — Pipeline stage data flow map (to be created)
- [ ] `briefing.py` — FormattedItem TypedDict, URL construction helpers, importance-weighted budget (CA1, CA3)
- [ ] Quality gate — Data fidelity dimension (CA2)
- [ ] Pre-commit hook — Template change detection (Q3 prevention)
- [ ] `validators/` — Stage-wise field preservation assertions (Q4 prevention)

---

## Wiki Ingest Section

### Wiki Ingest: Template-as-Specification Pattern

**Target page**: `concepts/template-as-specification.md` (new)
**Type**: concept

When an LLM-powered pipeline uses a template to guide AI output (e.g., `daily_sum.md` with `{shortened_teams_link}` placeholders), the template is simultaneously:
1. **Prompt guidance** — tells the LLM what format to produce
2. **Data requirement specification** — implicitly defines what the data pipeline MUST provide

Treating it as only #1 creates a systematic gap: template placeholders that the data layer cannot satisfy. The LLM either omits the placeholder (silent loss) or hallucinates content (fabricated links/quotes). Neither failure is detectable by content-quality gates — the output looks correct at surface level.

**Fix:** Treat templates as bidirectional specifications. When adding a placeholder, BACKPROPAGATE the requirement: can the formatter supply it? Does the source module capture it? Is there a test? Block template changes that fail this checklist.

**Related:** [Silent Staleness Pattern](silent-staleness.md) (same mechanism: output looks healthy while data is degraded), [Wiki-to-Code Traceability](wiki-to-code-traceability.md) (the bidirectional tracing principle applied to knowledge; here applied to data requirements)

### Wiki Ingest: Silent Staleness — Field-Level Extension

**Target page**: update `concepts/silent-staleness.md` (existing, add section)
**Type**: concept extension

The Silent Staleness Pattern extends beyond temporal freshness (stale dates) to field-level data loss. A pipeline that transforms structured data through multiple stages can silently drop fields (URLs, metadata, full content) at each transformation boundary. The output looks correct because the high-level content is present — only the metadata is missing.

Detection: the same 3-layer defense applies:
- Layer 1: Stage-wise field count comparison (expected URLs vs actual URLs in formatted output)
- Layer 2: User-visible annotation ("link unavailable" is better than silent absence)
- Layer 3: Periodic data flow audit comparing source module fields against formatted output fields

---

## Phase 0: Sources Consulted

| Source | What Was Found |
|--------|---------------|
| `wiki/concepts/silent-staleness.md` | Silent degradation pattern: system runs, output looks normal, but data quality silently degrades. Applied here to field-level data loss (URLs, quotes) not just temporal freshness. |
| `wiki/concepts/self-healing-automation.md` | Layer 3 quality gate — currently checks content quality but not data fidelity. Gate scope limitation is a root cause in Q2. |
| `wiki/concepts/wiki-to-code-traceability.md` | "Text instructions are corrective disguised as prevention." Template instructions to Claude ("附上 Teams 對話縮短連結") are text instructions that fail without data enforcement. |
| `memory/feedback_instructions_vs_gates.md` | Must pair instructions with gates. Template placeholders are instructions to Claude; need data-layer gates (assertions) to enforce. |
| `memory/feedback_detection_artifact_types.md` | 5 detection types — stage-wise assertions = runtime assertion type. Post-generation fidelity check = output validation type. |
| `briefing.py` source code | Verified: all 6 `_format_*` functions confirmed to strip URL fields. `_format_teams_chats` truncates at [:200], `_format_emails` at [:120], `_format_onenote` at [:500]. |
| `templates/daily_sum.md` | Confirmed: `{shortened_teams_link}` and `{exact quote}` placeholders in Action Items and Follow-up sections. |
| `output/daily_sum_2026-04-17.md` | Verified: zero `[點此查看]` links in actual output. Quotes present but sourced from truncated previews. |
| Existing draft `8D-005` | Q1-Q4 at code level. Q3/Q4 needed deepening to management-system level. |
