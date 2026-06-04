# MRC Identity Gate: Sanitize-Not-Raise (Broken-Run Fix)

Date: 2026-06-04
Status: DRAFT — design approved in brainstorming (diagram + change table + why)
Scope: skill-ai-escape-mrc only (the "broken" run-killer; the "garbage" proportionality fix is a separate spec)

<!-- WIKI-CONSULTED: function-replacement-convention (Read 2026-06-04) -->
<!-- WIKI-FINDING: replace the raise-path with sanitize in the SAME change; sweep all callers
     first; delete the raising path so it cannot coexist (Level-1 prevention). -->
<!-- WIKI-CONSULTED: gate-predicate-input-boundary -->
<!-- WIKI-FINDING: the false-fire drew truth from a denylist token (`skill-8d-mrc`) that names
     a LIVE sibling skill; fix the input boundary (drop the ambiguous token), not the threshold. -->

---

## 1. Problem & Context

The `sota-gate-orchestrator-miss` run finished Phases 0–8 (root cause + all 4 actions produced) and then **died at Phase 9** when `validate_phase9_plan()` found the legacy identity term `skill-8d-mrc` in the generated plan and raised `OutputIdentityContractError`. No email, all work discarded.

Two independent defects:

1. **Fatal-raise of a cosmetic check at the most expensive point.** A substring match — the cheapest possible problem, fixable by a string replace — is wired as a run-killing `raise` at the last phase, after every expensive phase succeeded. Fail-closed at the last stage discards all prior work; the correct posture for a cosmetic naming issue is sanitize-and-continue.
2. **`skill-8d-mrc` collides with a live sibling skill.** The denylist cannot distinguish this skill's deprecated former name from a legitimate reference to the currently-existing `skill-8d-mrc` workspace skill. Blind-rewriting would corrupt the reference; raising kills the run.

The same denylist is enforced at four sites with two policies today: `phase_4`/`phase_5` do *retry-once-then-raise*; `phase_7`/`phase_9` do *raise* directly.

## 2. Design

**Core policy — sanitize-then-proceed at every enforcement site. Never fatal-raise.**

- `phase_4_actions.py` / `phase_5_prevention_audit.py`: keep the existing retry-once-with-named-critique (it gives the LLM a chance to self-correct, cleaner than a mechanical rename), but the terminal fallback becomes **sanitize**, not **raise**.
- `phase_7_report.py` / `phase_9_write_plan.py`: today they raise directly. Change to **sanitize the validated text and continue**.

**Denylist split (the context-awareness):**

- Six unambiguous self-identity tokens — `run_8d`, `trigger_8d`, `eightd`, `8d-reports`, `pending-8d`, `CLAUDE_EIGHTD` — are this skill's own deprecated internals; no other skill uses them. **Auto-sanitized** via a canonical rename map.
- `skill-8d-mrc` is **removed** from the auto-acted denylist (it names a live sibling skill; any automatic action on it is wrong). Downgraded to a **non-blocking warn** in the log — visibility if the skill ever truly self-regresses, but never a raise and never a rewrite.

**Sanitization properties (research-grounded):**

- **Token-boundary safe:** rename matches on word boundaries (`\b`) so `eightd` renames `eightd-closed-loop` → `aem-closed-loop` but never corrupts an unrelated substring. Tokens are ASCII identifiers, so `\b` is well-defined (the CJK word-boundary caveat does not apply).
- **Idempotent:** the rename targets contain none of the sources, so `sanitize(sanitize(x)) == sanitize(x)`.
- **Order-stable:** prefixed tokens applied before bare ones (`eightd-` before bare `eightd`) to avoid partial rewrites.

## 3. Canonical rename map

| Legacy token | Rewrites to |
|---|---|
| `run_8d` | `run_ai_escape_mrc` |
| `trigger_8d` | `trigger_ai_escape_mrc` |
| `eightd-<x>` (CLI prefix) | `aem-<x>` |
| `eightd` (bare) | `aem` |
| `8d-reports` | `ai-escape-mrc-reports` |
| `pending-8d` | `pending-ai-escape-mrc` |
| `CLAUDE_EIGHTD` | `CLAUDE_AI_ESCAPE_MRC` |

(`skill-8d-mrc` is intentionally absent — not auto-acted.)

## 4. Files & changes

Per function-replacement-convention: **sweep all callers first** (`grep -rn` for `validate_no_legacy_identity_terms` and `validate_action_payload`), switch every pipeline caller to the sanitize path, and **delete the raise-path in the same change** so raise+sanitize cannot coexist.

| # | File : symbol | Now | After |
|---|---|---|---|
| 1 | `validators.py` : `FORBIDDEN_LEGACY_IDENTITY_TERMS` | 7 tokens incl. `skill-8d-mrc` | 6 tokens (drop `skill-8d-mrc`); add `LEGACY_IDENTITY_RENAME_MAP` |
| 2 | `validators.py` : new `sanitize_legacy_identity(text) -> str` | — | token-boundary, idempotent rename of the 6 tokens; returns cleaned text; logs a non-blocking warn if `skill-8d-mrc` is present |
| 3 | `validators.py` : `validate_no_legacy_identity_terms` / `validate_action_payload` (the raising path) | raise on any hit | **deleted** (or repurposed to non-raising detection only) once the caller sweep confirms no pipeline site needs the raise |
| 4 | `phase_4_actions.py` : `_call_with_legacy_term_retry` | retry → RAISE | retry → `sanitize_legacy_identity` → proceed |
| 5 | `phase_5_prevention_audit.py` : audit retry loop | retry → RAISE | retry → sanitize → proceed |
| 6 | `phase_7_report.py` : identity check | RAISE | sanitize → proceed |
| 7 | `phase_9_write_plan.py` : `validate_phase9_plan` | RAISE (predicate 3) | sanitize the plan text → proceed (size/marker predicates unchanged) |

## 5. Error handling

After this change, none of the four phase sites can raise `OutputIdentityContractError`. Sanitization is total (always returns clean text). The run-terminating identity path is eliminated — a finished run can no longer be destroyed by a naming check.

## 6. Testing

1. **Run-completes-after-sanitize:** a Phase 9 plan containing `run_8d` → output sanitized to `run_ai_escape_mrc` AND `validate_phase9_plan` returns normally (no exception) — a re-creation of the sota-gate death now yields a clean, deliverable plan.
2. **Live-sibling reference preserved:** a plan/report containing `skill-8d-mrc` → passes through unchanged (no raise, no rewrite); a warn is logged.
3. **Token-boundary:** `eightd-closed-loop` → `aem-closed-loop`; a contrived word containing the substring (e.g. `weightday`) is untouched.
4. **Idempotence:** `sanitize_legacy_identity(sanitize_legacy_identity(x)) == sanitize_legacy_identity(x)`.
5. **No raise from phase sites:** `phase_4/5/7/9` identity handling never raises `OutputIdentityContractError` on dirty input.
6. **Caller sweep clean:** no remaining call to a raising identity validator from any phase.

## 7. Research citations

- Sanitize vs reject (sanitize alters meaning — so only the 6 unambiguous tokens are rewritten, not `skill-8d-mrc`): securityinnovation, arc42 quality model.
- Fail-open/closed at expensive last stage (don't discard completed work on a cheap check): authzed.com "Failed Open / Fail Closed".
- Word-boundary `\b` to avoid substring false-positives/corruption: regular-expressions.info, MDN word-boundary assertion, Microsoft .NET regex best practices.
- Idempotent canonicalization (`f(f(x))=f(x)`): rusoblanco purity/determinism/idempotency, Unicode UAX#15.
- CAPA/8D right-sizing (informs the separate garbage-fix spec): thefdagroup "Problem with 8D for CAPA", qualityinspection.org.
