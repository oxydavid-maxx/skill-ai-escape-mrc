# 8D Report -- Configured but Disconnected Features (P2)

**Date**: 2026-04-17
**Team**: 光佑 (Kuang-Yu) + Claude Code
**Status**: Open -- awaiting user review

---

## Summary Table

| | Non-Conformance (NC) | Non-Detection (ND) |
|---|---|---|
| **TRC** | Q1: Config artifacts (`lookups/recordings.yaml`, `onenote.yaml`, `search_strategy.md`) 被當作 planning output 而非 executable spec — 沒有 import contract 強制 consumer code 必須存在。 | Q2: Pipeline 的 zero-result success 與 unconfigured-source success 完全不可區分 — 沒有 coverage metric 揭示 "configured 但 not scanned" 的缺口。 |
| **MRC** | Q3: 開發流程允許 config-only commits 被視為 "done" — 沒有 artifact-pair gate 要求 config + consumer 必須在同一 lifecycle 內成對出現。 | Q4: 審查流程缺乏 config-to-code completeness 的 structural audit — 信任感來自 config 存在而非 runtime 覆蓋。 |

---

## D1: Team

| Role | Member | Responsibility |
|------|--------|---------------|
| Developer | Claude Code (LLM agent) | Created `lookups/` config files and `recording_discovery.py` in separate sessions |
| User / Reviewer | 光佑 (Kuang-Yu) | Approved commits, discovered the 10-day gap on Apr 16 |
| Analyst | Claude Code (8D orchestrator) | This report |

---

## D2: Problem Definition (IS / IS NOT)

| Dimension | IS | IS NOT | DISTINCTION |
|-----------|-----|--------|-------------|
| **WHAT** | `lookups/recordings.yaml` (3 SharePoint paths) + `lookups/onenote.yaml` (1 OneNote section) + `lookups/search_strategy.md` (8-step plan) 存在但沒有 consumer code 讀取。Strategy doc 描述 7-step scan，code 僅實作 steps 1-4。 | NOT a code bug — Chains 1-4 功能正確。NOT a missing config — YAML 完整且語法正確。NOT a partial implementation — 每個 artifact 獨立看都是 correct。 | 缺口在兩個各自正確的 artifacts 之間 — 它們從未被 wired together。這是 integration gap，不是 functional bug。 |
| **WHERE** | `recording_discovery.py` Chains 1-4 (Apr 9) vs Chain 5-7 (described in `search_strategy.md`, Chain 5 實作 Apr 17)。`onenote.yaml` 至今（Apr 17）仍無 consumer。同樣 pattern 出現在 `copilot_fetch.py`：`_check_cdp_available` 與 `_ensure_cdp_has_copilot` 共存 7 天。 | NOT in data fetching logic（Chains 1-4 work）。NOT in YAML syntax。NOT in Graph API auth。NOT in Copilot CDP connection。 | 問題域是 config-to-code interface 而非任何單一 module 的功能。每個 module boundary 都是潛在斷點。 |
| **WHEN** | 10-day gap: `recordings.yaml` committed Apr 7 (8860bc2), `recording_discovery.py` created Apr 9 (f0b7ca2) without reading it, Chain 5 added Apr 17 (1bffbf7) only after user noticed。CDP pattern: 7-day gap (bc93a4f Apr 9 → 9bf62c9 Apr 16) between `_ensure` creation and `_check` deletion。 | NOT a regression — connection never existed。NOT intermittent — deterministically absent。NOT time-dependent — gap would persist indefinitely without human intervention。 | 區別於 "broke something that worked"。This *never* worked。The gap is *stable* — no natural force would close it。 |
| **WHO** | Claude Code (developer agent) created both sides in different sessions with different mental contexts。Apr 7 session focused on lookup structure design; Apr 9 session focused on recording discovery implementation。 | NOT user error — user approved each commit on its own merit。NOT a misunderstanding of requirements — both artifacts correctly reflect the intent。 | The gap is between sessions, not between intent and implementation. Each session correctly executed its own scope but failed to verify cross-session integration. |
| **EXTENT** | 3 SharePoint folders configured but never scanned for 10 days。`onenote.yaml` with 1 OneNote section still unread (10+ days)。Strategy doc steps 5-7 described but unimplemented for 10 days。1 CDP function (`_check_cdp_available`) incorrectly used for 7 days → 4 days silent data loss。 | NOT limited to `lookups/` — same pattern can recur anywhere config and code are created in separate sessions。NOT limited to Claude Code — any developer (human or LLM) working in session-bounded contexts faces this。 | The scale of *invisible* damage is the real concern. Zero-result success masked the gap for 10 days of daily pipeline runs. |

---

## D3: Containment Actions

| # | Action | Owner | Date | Status |
|---|--------|-------|------|--------|
| 1 | Implement Chain 5: SharePoint folder scan reading `recordings.yaml` | Claude Code | 2026-04-17 | Done (1bffbf7) |
| 2 | Delete `_check_cdp_available` — NameError enforces `_ensure_cdp_has_copilot` | Claude Code | 2026-04-16 | Done (9bf62c9) |
| 3 | Add structural guard test: `_check_cdp_available` must not exist | Claude Code | 2026-04-16 | Done (test_regression.py) |
| 4 | Add `.detection-rules` entry blocking `_check_cdp_available` resurrection | Claude Code | 2026-04-16 | Done |
| 5 | `onenote.yaml` consumer code: NOT YET IMPLEMENTED | -- | -- | Open |

**Note**: Containment addresses *this instance* but not the systemic pattern. Steps 6-7 of `search_strategy.md` and `onenote.yaml` consumption remain partially open.

---

## D4: Root Cause Analysis (Four Quadrants, 10+ Whys Each)

### Q1: Technical Root Cause -- Non-Conformance

**Question: Why did `recording_discovery.py` not read `recordings.yaml` for 10 days?**

```
Why-1:  recording_discovery.py (f0b7ca2, Apr 9) was created with Chains 1-3 only,
        treating Teams chat messages as the sole data source.

Why-2:  The Apr 9 session's scope was "discover recordings from chat data" — it
        never checked what existed in lookups/ because lookups/ was created in a
        different session (Apr 7).

Why-3:  lookups/recordings.yaml is a passive YAML file — it cannot signal that it
        exists, cannot error when unread, cannot assert it has a consumer.

Why-4:  No import contract or registration mechanism exists between config files
        and consumer modules. YAML files are "fire and forget."

Why-5:  The commit message for 8860bc2 says "lookups/recordings.yaml — user-maintained
        SharePoint/local recording paths" — this frames it as a reference artifact,
        not as an executable data source requiring a code consumer.

Why-6:  search_strategy.md documents Steps 1-8 but is itself a passive Markdown file.
        No mechanism verifies that the code implements all described steps.

Why-7:  When recording_discovery.py was created, it imported yaml but only used it
        for config.yaml. The module's header docstring mentions only 3 chains,
        not the lookups/ directory — the developer's mental model was complete
        within its own scope.

Why-8:  Each session builds from "what do I need to accomplish now?" not from
        "what exists that I should integrate with?" The default direction is
        forward-looking (new code), not inventory-checking (existing config).

Why-9:  There is no "pending consumers" list. When 8860bc2 created lookups/,
        no TODO, issue, or follow-up item was created saying "wire these into
        recording_discovery.py."

Why-10: The same pattern repeats with onenote.yaml — committed in the same 8860bc2,
        still has no consumer 10 days later. This proves it's not an oversight on
        one file; it's a systemic pattern of config-without-consumer.

Why-11: In the CDP case, _ensure_cdp_has_copilot was added (bc93a4f, Apr 9) but
        _check_cdp_available was left alive. The new function was wired to
        summarize_meetings_via_copilot only — fetch_all_via_copilot still used the
        old function. Same pattern: new capability exists, old call site not updated.
```

**First-Principles Test**: 這個 root cause 能否從第一性原理推導？Passive data files 本質上不具備 asserting consumers 的能力。YAML/Markdown 是 data formats, 不是 executable contracts。任何基於 passive file + no import contract 的架構，都必然產生 config-without-consumer 缺口。這是 architectural invariant, 不是偶然疏忽。

**Root Cause**: Passive config files have no mechanism to assert they are consumed. The development process treats config creation as a standalone deliverable, not as half of a config-consumer pair that requires completion.

---

### Q2: Technical Root Cause -- Non-Detection

**Question: Why was the 10-day gap not detected by any automated or manual check?**

```
Why-1:  The pipeline ran successfully every day during the 10-day gap — no errors,
        no warnings, no test failures. Exit code 0 every run.

Why-2:  Zero recordings from SharePoint is a valid result (some days have no
        meetings), so the output looked completely normal.

Why-3:  The pipeline's output reports only WHAT was found, not WHAT was searched.
        "0 recordings" appears the same whether 3 SharePoint folders were scanned
        or 0 were scanned.

Why-4:  No "source coverage" metric exists. The pipeline doesn't report "Discovery
        chains executed: 4/7" or "SharePoint folders scanned: 0/3."

Why-5:  No integration test asserts "if recordings.yaml has N entries, discover_recordings
        must attempt to access N folders." Tests only check functional correctness
        of existing chains.

Why-6:  search_strategy.md documents Steps 1-8 but nothing verifies the code
        implements all 8. The document is aspirational, not contractual.

Why-7:  The pre-commit hook checks for WIKI-CONSULTED markers and detection artifacts,
        but has NO check for "new config files in lookups/ must have a consumer."
        The hook addresses knowledge consultation, not integration completeness.

Why-8:  The user trusted the config was being used because (a) the config file
        existed, (b) the strategy doc described the flow, and (c) the pipeline
        produced output. This is the "false confidence from config existence" pattern.

Why-9:  Daily briefing output showed "0 recordings" or "N recordings from chat" —
        the user had no reason to check whether SharePoint scanning was occurring
        since the chat-based discovery already produced some results on meeting days.

Why-10: No periodic audit compares search_strategy.md steps against actual code.
        The strategy doc was never re-read after initial creation. It functioned
        as a one-time design artifact, not as a living contract.

Why-11: The Silent Staleness Pattern (wiki concept) describes this exactly: the
        system appears healthy, delivers output, shows no errors — but underlying
        data sources are not being accessed. The wiki page existed but was not
        consulted during recording_discovery.py development.

Why-12: Even after the CDP dual-function 8D was completed on Apr 16, the
        recordings.yaml gap was not found by analogy. The auditor fixed the
        specific instance (_check vs _ensure) without searching for the same
        pattern class (config-exists-but-not-consumed) elsewhere in the codebase.
```

**First-Principles Test**: Zero-result success 在 source discovery 系統中本質上不可區分。任何 pipeline 如果只報告 found items 而不報告 searched sources，都會有這個 detection gap。這是 observability architecture 的缺陷，不是 test coverage 的缺陷 — 即使 test coverage 達到 100%，若 tests 只驗證 existing chains 的正確性，仍然無法發現 missing chains。

**Root Cause**: Zero-result success is indistinguishable from unconfigured-source success. No coverage metric reveals which configured capabilities are actually wired, and no structural test maps config files to consumer code.

---

### Q3: Management Root Cause -- Non-Conformance

**Question: Why does the development process produce disconnected artifacts as a recurring pattern?**

```
Why-1:  Config files and strategy docs are created as "planning/design outputs"
        that feel complete when committed. The commit for 8860bc2 creates 3 files,
        has a well-written commit message, and looks like a thorough deliverable.

Why-2:  Development sessions are context-bounded. The Apr 7 session created lookups/;
        the Apr 9 session created recording_discovery.py. Neither session checked
        what the other produced because there's no cross-session integration protocol.

Why-3:  The project has no "artifact pair" rule. In contrast, the wiki-to-code
        traceability convention (WIKI-CONSULTED markers) was successfully enforced
        because it has a pre-commit hook. Config-to-consumer pairing has no such gate.

Why-4:  The pre-commit hook enforces wiki consultation and detection artifacts, but
        does NOT enforce integration completeness. It checks "did you consult the wiki?"
        not "did you wire all configs to consumers?"

Why-5:  "Config-first" development feels productive — creating lookups/ establishes
        the data model, the folder structure, the documentation. But this productivity
        is illusory when the config is never consumed. It's planning mistaken for doing.

Why-6:  The project lacks a definition of "done" that includes integration verification.
        "Done" is implicitly "code works in isolation" not "code is wired into the pipeline
        and exercises all configured sources."

Why-7:  The LLM developer (Claude Code) optimizes for session-level completeness.
        Each session produces a coherent deliverable. But the inter-session handoff
        has no mechanism to surface "work left incomplete by the previous session."

Why-8:  No "orphan config" detection exists at any level — not in CI, not in pre-commit,
        not in periodic audits. An orphan config file can exist indefinitely without
        triggering any alarm.

Why-9:  The wiki documents self-healing, silent staleness, function replacement, and
        wiki-to-code traceability — but has NO entry for "config-to-code integration
        verification." The knowledge gap in the wiki reflects a knowledge gap in the
        development process.

Why-10: The "Instructions vs Gates" insight (from memory feedback_instructions_vs_gates.md)
        was already learned: text instructions fail without hard gates. Yet config-to-code
        completeness is still governed by text instruction (the strategy doc) not a hard
        gate (pre-commit check).

Why-11: The commit message convention (CONSUMER: <module>) proposed in the previous
        draft was never implemented. Proposals that exist only in 8D reports and not
        in hooks are themselves examples of "configured but disconnected."
```

**First-Principles Test**: 任何 session-bounded development process (human or LLM) 如果沒有 cross-session artifact tracking，都會產生 orphan configs。這不是 Claude Code 特有的問題 — 人類開發者在不同 branch/sprint 中也會產生同樣的 gap。差別在於人類有 stand-up meetings 和 code reviews 作為 cross-session bridge，而 LLM agent 目前沒有等效機制。

**Root Cause**: The development process has no artifact-pair gate. Config creation is treated as a standalone deliverable with no enforcement that a consumer must follow within a bounded timeframe. The existing gate infrastructure (pre-commit hooks) enforces wiki consultation and detection artifacts but not config-to-code completeness.

---

### Q4: Management Root Cause -- Non-Detection

**Question: Why did no process catch the false confidence for 10 days?**

```
Why-1:  Daily briefing output showed "N recordings found" or "0 recordings" — both
        are valid outputs. The user consumed the output daily without questioning
        whether all configured sources were being scanned.

Why-2:  The user's confidence came from config existence: "we have recordings.yaml
        with 3 folders, so those folders are being scanned." Config existence was
        treated as evidence of capability — a cognitive shortcut.

Why-3:  No "source coverage report" is generated as part of pipeline output. The
        output is purely results-oriented. It reports "what we found" not "where
        we looked."

Why-4:  The pre-commit hook runs tests, checks wiki markers, checks detection
        artifacts, and runs structural grep rules. But it has NO structural test
        for config-to-code completeness. The hook is comprehensive for code quality
        but blind to integration completeness.

Why-5:  The existing regression tests (test_regression.py) only guard against known
        past bugs (e.g., _check_cdp_available resurrection). There is no test class
        that verifies "all files in lookups/ are read by at least one source module."

Why-6:  search_strategy.md describes 8 steps but no automated check compares the
        step count in the doc against the chain count in the code. The doc is
        never re-read by any automated process.

Why-7:  The 8D process that investigated the CDP dual-function bug (Apr 16) found
        and fixed that specific instance. But the audit did NOT generalize to
        "search for other config-exists-but-not-consumed patterns." Instance-level
        fix, not pattern-level sweep.

Why-8:  The project has no scheduled "integration health check" that periodically
        verifies all config files have consumers, all strategy doc steps are
        implemented, and all lookup files are being read.

Why-9:  Telegram daily brief shows a condensed summary. The user reads it on mobile.
        There is no "diagnostic section" reporting pipeline health metrics like
        source coverage. Even if the user suspected something, the output format
        wouldn't reveal the gap.

Why-10: The "Silent Staleness" wiki page describes exactly this failure mode —
        system appears healthy while data sources are not being accessed. But the
        wiki page's defense recommendations (staleness banner, coverage reporting)
        were not applied to recording_discovery.py because the wiki was not
        consulted during that module's creation (pre-dates the traceability hook).

Why-11: No alert triggers on "configured sources > executed sources." The pipeline
        doesn't even track this metric, let alone alert on it. The concept of
        "source coverage" doesn't exist in the system's observability model.

Why-12: The "false confidence from documentation" pattern compounds over time.
        The more complete the lookups/ directory and search_strategy.md look,
        the MORE confident the user becomes that everything is working — even
        though the documentation quality is inversely correlated with actual
        code integration (well-documented but unimplemented > poorly-documented
        but implemented).
```

**First-Principles Test**: 任何 results-only observability model（只報告 found items, 不報告 searched sources）都會產生 false confidence。這是 observability 架構的 fundamental gap。即使增加 100 個 tests，如果 tests 只驗證 "existing chains work correctly"，仍然無法偵測 "missing chains"。需要的是 meta-level coverage check: 不是 "does Chain 5 work?" 而是 "does Chain 5 exist?"

**Root Cause**: The audit and observability infrastructure does not include config-to-code completeness checking. Confidence is derived from config existence (a passive artifact) rather than runtime coverage (an active measurement). No scheduled or triggered audit sweeps for orphan configs.

---

## RC Audit (3 Rounds, Explicit Role Switching)

### Round 1

**[AUDITOR]**

我以獨立 auditor 身份挑戰以上分析：

1. **Q1 深度不足**: Why-chain 停在 "passive YAML files" — 但這只是 format choice。真正的問題是為什麼 developer 在 Apr 9 session 沒有 grep `lookups/` 目錄？在 f0b7ca2 commit 中，recording_discovery.py imports `yaml` 但只讀 `config.yaml`，這暗示 developer 知道 YAML 是 data source。為什麼不搜尋所有 YAML？

2. **Q3 太 abstract**: "session-bounded development" 是對的，但 8860bc2 的 commit message 明確寫了 "lookups/recordings.yaml — user-maintained SharePoint/local recording paths"。如果 Claude Code *寫了*這個 message，它知道這些 paths 需要被 consumed。Q3 應該解釋為什麼 knowing the intent 沒有轉化為 action。

3. **Q2/Q4 overlap**: Q2 Why-11 ("Silent Staleness wiki page existed but not consulted") 和 Q4 Why-10 幾乎相同。Non-detection 的 technical vs management root cause 需要更明確區分。

4. **Missing counterfactual**: 如果 recordings.yaml 改用 Python dict 而非 YAML（embedded in code），問題會消失嗎？如果是，那 root cause 不是 "passive file" 而是 "separate file" — 即 physical separation of config and code。

**[ANALYST]**

回應 auditor 挑戰：

1. **On Why-chain depth (Q1)**: 接受挑戰。Developer 在 Apr 9 使用 `yaml` import 但只讀 `config.yaml`，確實暗示 YAML-as-data-source 的 mental model 存在。真正的 gap 是：developer 沒有執行 `grep -r "\.yaml" lookups/` 或類似的 discovery scan。這指向 **search scope blindness** — 開發者的搜尋範圍限於 "我正在建造的東西需要什麼"（forward-looking），而非 "倉庫裡有什麼等著被整合"（inventory-checking）。已在 Q1 Why-8 中部分涵蓋，但 auditor 說得對，需要更 specific。

2. **On Q3 intent-to-action gap**: 接受。8860bc2 的 commit message 是 Claude Code 自己寫的，意味著在 Apr 7 session 中，agent 完全知道這些 paths 需要 consumers。但 Apr 9 session 是不同的 context window — Claude Code 沒有 persistent memory across sessions。`CLAUDE.md` 中沒有記載 "lookups/ 有 pending consumers"。Root cause 更精確地說是：**intra-agent memory loss between sessions + no CLAUDE.md convention for tracking pending integrations**。

3. **On Q2/Q4 overlap**: 接受。修正區分：Q2（technical ND）聚焦於 pipeline observability 的 architectural gap（no coverage metric, zero-result ambiguity）。Q4（management ND）聚焦於 audit process 的 structural gap（no orphan-config scan in pre-commit, no periodic integration health check, no sweep after related 8D）。Wiki consultation failure 移到 Q4 only（它是 process gap, 不是 technical gap）。

4. **On counterfactual**: Excellent point。如果 config 是 embedded Python dict（e.g., `SHAREPOINT_FOLDERS = [...]` in `recording_discovery.py`），問題確實消失 — config 和 consumer 在同一個 file。但這犧牲了 user-editability（non-coder 不能編輯 Python）。真正的 root cause 不是 "separate file" 而是 "separate file WITHOUT a binding contract"。YAML + registry pattern（import-time assertion）保留 separation 的好處同時消除 disconnect risk。

### Round 2

**[AUDITOR]**

Round 1 改善了分析。繼續挑戰：

1. **Q3 prevention gap**: Analyst 提到 "intra-agent memory loss between sessions"。但 CLAUDE.md 已經被用作 persistent cross-session memory（它包含 wiki consultation rules, detection artifact rules）。為什麼不在 CLAUDE.md 中記載 "lookups/onenote.yaml has no consumer" 作為 known debt？這是 CLAUDE.md 的用途 gap 還是 agent behavior gap？

2. **Q4 "sweep after related 8D"**: 在 Apr 16 完成 CDP 8D 時，auditor 發現了 `_check` vs `_ensure` 的 disconnection。但沒有 generalize 到 "search all config-without-consumer"。這是因為 8D template 沒有要求 "horizontal search for same pattern class" 嗎？或是 auditor 沒有想到？

3. **Residual blind spot**: `onenote.yaml` 至今仍無 consumer。Report 在 D3 containment 中標記為 "Open" 但沒有 deadline。如果 prevention actions 需要 weeks 才能部署，onenote.yaml 會繼續 orphan — 這是否應該有 separate containment action？

4. **Scale question**: 除了 `lookups/` 目錄之外，codebase 中是否還有其他 config-without-consumer patterns？`copilot_prompts.yaml` 是否被完整消費？`config.yaml` 的所有 sections 都有 consumers 嗎？Report 應該量化 current exposure。

**[ANALYST]**

回應 Round 2：

1. **CLAUDE.md as cross-session memory**: 精確的觀察。CLAUDE.md *確實*被用作 persistent instruction — wiki rules, detection rules 都在裡面。但它被用於 *process rules*（"how to work"），不是 *state tracking*（"what's pending"）。Known debt tracking 使用的是 project memory (`MEMORY.md`) 或 issues。但目前 `MEMORY.md` 也沒有 "pending consumer" 項目。Root cause refinement: **the persistent memory instruments (CLAUDE.md, MEMORY.md) are scoped to process rules and context, not to artifact-level integration state tracking。** Adding a "pending consumers" section to CLAUDE.md or MEMORY.md 是 process fix，但仍然是 text instruction — 需要 gate enforcement。

2. **8D horizontal search**: 8D template 在 D8 (Lessons Learned) 有 "Horizontal Deployment" 但在 D4 (RC Analysis) 沒有要求 "search for same pattern class across codebase"。Apr 16 8D 確實有 D8 residual risks mentioning "pattern repeats in non-lookup contexts" 但沒有 actionable sweep。**Root cause: 8D process itself lacks a mandatory "pattern sweep" step between D5 (corrective) and D6 (prevention)**。Added to D8 of this report.

3. **onenote.yaml containment**: 接受。Adding explicit containment action with deadline。但 more importantly, this validates the need for an orphan-config detection gate — if the gate existed, onenote.yaml would have been flagged automatically at commit time.

4. **Current exposure**: Let me quantify.
   - `lookups/recordings.yaml` → consumer: `recording_discovery.py` Chain 5 (added Apr 17) -- NOW connected
   - `lookups/onenote.yaml` → consumer: NONE -- ORPHAN
   - `lookups/search_strategy.md` → consumer: NONE (no code reads it) -- ORPHAN (design doc)
   - `copilot_prompts.yaml` → consumer: `copilot_fetch.py` loads and uses all defined prompts -- CONNECTED
   - `config.yaml` → consumer: multiple modules via `load_config()` -- CONNECTED (but unchecked for unused sections)

   Current exposure: **2 orphan config files** (`onenote.yaml`, `search_strategy.md` as living spec), 1 recently connected (`recordings.yaml`). Risk: config.yaml may also have unused sections but is harder to audit (secrets file).

### Round 3

**[AUDITOR]**

Final round. Focus on prevention robustness:

1. **Prevention vs containment confusion**: The previous draft (Apr 16) proposed "Session handoff checklist" (P3) and "Source coverage logging" (P4). These are good ideas but both are text-based instructions. Given the "instructions vs gates" lesson already in memory, shouldn't ALL prevention actions include a hard gate? A checklist in CLAUDE.md will be forgotten just like the strategy doc was.

2. **Orphan-config gate design**: If we add a pre-commit check "every YAML in lookups/ must have a consumer in sources/*.py," how do we handle legitimate config files that are consumed by scripts outside sources/ (e.g., a future CLI tool)? False positives in pre-commit gates erode trust and lead to `--no-verify`.

3. **Completeness of pattern coverage**: The config-without-consumer pattern has at least 3 variants:
   - Config file without consumer code (recordings.yaml)
   - Strategy doc without implementing code (search_strategy.md Steps 5-7)
   - New function without full caller migration (_ensure vs _check)

   Does the proposed prevention address ALL three variants? Or only variant 1?

4. **Meta-prevention**: This is the second 8D in 2 days that identifies "instructions fail without gates." At what point does the 8D process itself need a meta-gate ensuring prevention actions ARE gates, not instructions?

**[ANALYST]**

Final responses:

1. **All prevention must include gates**: Fully agree. Revising prevention actions to include hard gates for every item. "Source coverage logging" is observability (detection aid), not prevention — it should be in Q2 (ND) domain. "Session handoff checklist" must become a pre-commit check, not a CLAUDE.md instruction. Updated in D6.

2. **Orphan-config gate design (false positive risk)**: Valid concern. Design:
   - Gate checks `lookups/*.yaml` and `lookups/*.md` (not all YAML in repo — `config.yaml`, `copilot_prompts.yaml` are in root and already consumed).
   - Gate requires either (a) a `grep -r "filename" sources/ publishers/ auth/ main.py` match, OR (b) a `# CONSUMER-EXEMPT: <reason>` header in the YAML/MD file.
   - `search_strategy.md` could be CONSUMER-EXEMPT if treated as pure documentation. But the report argues it should be contractual — see variant 2 below.
   - False positive escape valve: `CONSUMER-EXEMPT` is auditable (quarterly spot-check).

3. **Three-variant coverage**:
   - **Variant 1 (config without consumer)**: Pre-commit orphan-config gate in `lookups/`. Covered.
   - **Variant 2 (strategy doc without implementing code)**: Harder. Requires parsing Markdown step descriptions and matching to code comments. Proposed: each Step in strategy doc must have a matching `# STRATEGY-STEP-N` comment in code. Pre-commit checks all Steps have matches. This is a weaker gate (comment presence, not behavioral verification), but catches the "described but not implemented" variant.
   - **Variant 3 (new function without full caller migration)**: Already covered by Function Replacement Convention wiki page + `_check_cdp_available` deletion in same commit. The gate is NameError (architectural elimination). For future cases: `.detection-rules` entry added when old function is deprecated.

   **Residual gap**: Variant 2 gate relies on comments, which can be perfunctory. But combined with quarterly audit, this reaches acceptable confidence.

4. **Meta-prevention**: This is the deepest challenge. If 8D reports keep producing instructions that aren't gates, the 8D process has a systemic deficiency. Proposal: **add to 8D template a mandatory "Gate Classification" field for each prevention action**. Each action must be classified as:
   - **Hard gate**: Pre-commit hook, structural test, NameError, etc.
   - **Soft gate**: CLAUDE.md rule, checklist, convention
   - **Observability**: Logging, coverage metric, alert

   Rule: Every D6 prevention action must include at least one hard gate. Soft gates are permissible only as supplements to a hard gate, never as standalone prevention. This is the 8D template's own "prevention action."

### Audit Verdict

**Addressed weaknesses from 3 rounds**:
- Q1: Added search scope blindness and inventory-checking vs forward-looking development
- Q3: Refined to memory instrument scoping gap + mandatory pattern sweep in 8D process
- Q2/Q4: Clarified technical (observability architecture) vs management (audit process) distinction
- Prevention: All actions now require hard gates, not text instructions
- Exposure quantified: 2 current orphan configs
- Three-variant coverage designed for all identified pattern variants

**Residual risks after audit**:
1. Variant 2 gate (strategy doc → code comments) is weaker than variant 1 (YAML → import). Quarterly audit mitigates but doesn't eliminate.
2. `config.yaml` unused section detection is out of scope (secrets file, different lifecycle).
3. Meta-prevention (8D template gate classification) requires adoption across all future 8Ds.

**Verdict**: Root cause analysis is sufficiently deep and covers the structural pattern. Prevention actions include hard gates at multiple levels. Proceed to D5/D6.

---

## D5: Corrective Actions (Instance-Level)

### CA1 (Q1 -- Wire recordings.yaml consumer)

| Item | Detail |
|------|--------|
| Action | Implement Chain 5 in `recording_discovery.py` to read `lookups/recordings.yaml` and scan configured SharePoint folders |
| Status | Done (commit 1bffbf7, Apr 17) |
| Evidence | Code at lines 230-302 of `recording_discovery.py` reads `lookups/recordings.yaml`, iterates folders, queries Graph API |

### CA2 (Q1 -- Wire onenote.yaml consumer)

| Item | Detail |
|------|--------|
| Action | Implement consumer code to read `lookups/onenote.yaml` and scan configured OneNote sections for recording links |
| Status | Open -- must be implemented within 1 week |
| Deadline | 2026-04-24 |
| Note | Currently the only remaining orphan config in `lookups/` |

### CA3 (Q2 -- Add source coverage logging)

| Item | Detail |
|------|--------|
| Action | Add `[COVERAGE]` log line at pipeline end: "Discovery chains executed: N/M, SharePoint folders scanned: N/M, lookups consumed: N/M" |
| Status | Open |
| Rationale | Makes "configured but not scanned" visible in every run. Does not prevent the gap but makes it detectable within 1 day. |

### CA4 (Q2 -- Add structural integration test)

| Item | Detail |
|------|--------|
| Action | Add test in `tests/test_regression.py` that verifies: for each `.yaml` file in `lookups/`, at least one `.py` file in `sources/` references its filename |
| Status | Open |
| Rationale | Catches orphan configs at test time. Pre-commit hook already runs tests. |

---

## D6: Prevention Actions (System-Level, with 10-Why Chains)

### PA1 (Q3 -- Orphan Config Gate)

**Action**: Pre-commit hook check: every `.yaml` and `.md` file in `lookups/` must either (a) be referenced by name in at least one `.py` file in `sources/`, `publishers/`, `auth/`, `main.py`, or `briefing.py`, OR (b) contain a `# CONSUMER-EXEMPT: <reason>` header line.

**10-Why Prevention Chain**:
```
Why-1:  Config files in lookups/ can be committed without a consumer.
        → Gate: pre-commit blocks commits adding/modifying lookups/ files
          without a matching consumer reference in code.

Why-2:  Even with the gate, someone could add a fake reference (e.g., a comment
        mentioning the filename without actually loading it).
        → Gate: the grep pattern requires `open(` or `yaml.safe_load` or
          `Path(` within 5 lines of the filename reference, not just any mention.

Why-3:  The gate only fires on commits touching lookups/ — what about existing
        orphans already committed before the gate?
        → Gate: add a startup check in main.py that lists all lookups/*.yaml
          files and verifies each has a registered consumer (import-time assertion).

Why-4:  The startup check only runs when the pipeline runs — if pipeline is
        broken or not run, orphans persist undetected.
        → Gate: the pre-commit hook also runs tests, and the integration test
          (CA4) catches orphans at every commit, not just pipeline runs.

Why-5:  What about non-YAML config-like files (Markdown strategy docs)?
        → Gate: search_strategy.md Steps get matching STRATEGY-STEP-N comments
          in code. Pre-commit verifies step count matches.

Why-6:  STRATEGY-STEP-N comments can be perfunctory (present but meaningless).
        → Mitigation: quarterly audit samples 3 STRATEGY-STEP comments and
          verifies they correspond to actual code logic (same as WIKI-CONSULTED
          audit).

Why-7:  The gate applies to lookups/ but the "config without consumer" pattern
        can recur in other directories (e.g., a new prompts/ or templates/ dir).
        → Gate: CLAUDE.md rule + pre-commit check generalized to any directory
          declared as "config-managed" in a .config-dirs file at repo root.

Why-8:  .config-dirs file itself could become orphan (ironic).
        → Gate: pre-commit verifies .config-dirs lists only existing directories.
          Simple structural check.

Why-9:  Gate only catches at commit-time. What about in-flight development
        where config is created but consumer is "in progress"?
        → Gate: CONSUMER-EXEMPT with reason "WIP: consumer in <branch/session>"
          is acceptable but triggers a 7-day TTL check (if file older than 7 days
          and still CONSUMER-EXEMPT: WIP, pre-commit blocks).

Why-10: TTL check requires parsing git timestamps, adding complexity.
        → Implementation: use file's git first-commit date from `git log --follow
          --diff-filter=A --format=%at -- <file>`. Compare to current time.
          If > 7 days and still WIP-exempt, block.
```

**Gate Test (Scope / Persistence / Measurability)**:

| Criterion | Assessment |
|-----------|-----------|
| **Scope** | Covers all files in directories declared as config-managed. Generalizable beyond `lookups/`. |
| **Persistence** | Pre-commit hook — runs on every commit automatically. Cannot be bypassed without `--no-verify` (which is flagged in CLAUDE.md as prohibited). |
| **Measurability** | Metric: count of blocked commits with orphan-config reason. Quarterly: count of CONSUMER-EXEMPT files with WIP status > 7 days. |

**Deployment scope**: Pre-commit hook in `daily_brief` repo. Pattern documented in wiki for reuse in other projects.

---

### PA2 (Q4 -- Integration Completeness Audit Gate)

**Action**: Pre-commit hook addition: when any source file in `sources/` is added or modified, check that the number of `# STRATEGY-STEP-` comments in all source files equals the number of `Step N` entries in `lookups/search_strategy.md`. Mismatch blocks the commit with a message listing missing steps.

**10-Why Prevention Chain**:
```
Why-1:  Strategy doc can describe N steps while code only implements M < N.
        → Gate: pre-commit counts Step entries in search_strategy.md and
          STRATEGY-STEP-N comments in source files. N != M → block.

Why-2:  What if a step is legitimately not yet implemented (WIP)?
        → Gate: strategy doc can mark a step as "# [PLANNED]" which is excluded
          from the count. Planned steps must have a deadline comment.

Why-3:  What if the strategy doc is outdated (describes steps that are no longer
        needed)?
        → Gate: if code has STRATEGY-STEP-N but doc doesn't have Step N, also
          block. Bidirectional consistency.

Why-4:  Step numbering could drift (reordering steps in doc without updating code).
        → Gate: use step NAME matching, not just number. E.g., STRATEGY-STEP:
          "SharePoint folder scan" matches "Step 6 → lookups/recordings.yaml:
          SharePoint folders" via keyword overlap.

Why-5:  Keyword matching is fuzzy and error-prone.
        → Simplification: use exact step numbers (1-8) as stable identifiers.
          Strategy doc Steps are append-only (never renumbered). If a step is
          removed, it becomes [DEPRECATED], not deleted.

Why-6:  What about other strategy/design docs outside lookups/?
        → Scope: initially only search_strategy.md. If pattern proves useful,
          extend to any doc with `## Execution Order` header.

Why-7:  The gate only catches strategy-step mismatches, not "step exists but
        implementation is wrong."
        → Complement: this gate ensures existence (structural), while functional
          correctness is tested by unit/integration tests. Two different concerns.

Why-8:  Adding STRATEGY-STEP comments to code adds noise.
        → Design: one comment per chain/step, not per line. Total: ~8 comments
          across the codebase. Low noise.

Why-9:  Pre-commit hook is growing complex (wiki check + detection check +
        orphan config + strategy step). Maintenance burden?
        → Design: modular hook — each check is a separate script called by the
          main hook. Each can be independently tested and maintained.

Why-10: Complex hooks increase commit friction, potentially leading to
        --no-verify usage.
        → Mitigation: hook runs fast (grep-based, no network calls, < 2s total).
          Clear error messages with exact fix instructions. CLAUDE.md prohibits
          --no-verify.
```

**Gate Test**:

| Criterion | Assessment |
|-----------|-----------|
| **Scope** | Covers strategy doc ↔ source code bidirectional consistency. |
| **Persistence** | Pre-commit hook — automatic on every commit. |
| **Measurability** | Metric: count of blocked commits with strategy-step mismatch. Quarterly: audit STRATEGY-STEP comment quality. |

---

### PA3 (Q3 -- Cross-Session Artifact Tracking via MEMORY.md)

**Action**: When a commit creates a config/data file without a consumer, MEMORY.md must be updated with a `pending_consumers` entry. Pre-commit hook enforces: if a new file in a config-managed directory has `CONSUMER-EXEMPT: WIP`, the commit must also modify MEMORY.md to add a tracking entry.

**Note**: This is a **soft gate** supplementing PA1's hard gate. PA1 blocks orphan configs; PA3 ensures pending work is tracked across sessions. PA3 alone would be insufficient (text instruction) — it only works because PA1 provides the enforcement backstop.

**Gate Test**:

| Criterion | Assessment |
|-----------|-----------|
| **Scope** | Cross-session memory for WIP config files. |
| **Persistence** | Pre-commit enforced (must modify MEMORY.md when adding WIP-exempt config). |
| **Measurability** | Count of pending_consumers entries in MEMORY.md. TTL enforcement from PA1 Why-9. |

---

### PA4 (Q4 -- Pipeline Source Coverage Metric)

**Action**: Add a `CoverageReport` object in `main.py` that tracks: (a) configured sources (count YAML entries in lookups/, count Steps in strategy doc), (b) executed sources (count of actually-queried chains/folders), (c) delta. Print `[COVERAGE]` summary at pipeline end. If delta > 0, add a `[WARN]` line.

**Note**: This is **observability**, not prevention. It doesn't prevent the gap but reduces detection latency from "10 days until user notices" to "1 day (next pipeline run)." Complements PA1/PA2 (which prevent at commit-time) with runtime detection.

**Gate Test**:

| Criterion | Assessment |
|-----------|-----------|
| **Scope** | Runtime observability for all configured-vs-executed sources. |
| **Persistence** | Runs on every pipeline execution automatically. |
| **Measurability** | Metric: coverage ratio per run. Alert if < 100% for > 3 consecutive days. |

---

## Prevention Audit (Separate from RC Audit)

**[PREVENTION AUDITOR]** -- Adversarial review of PA1-PA4:

1. **PA1 (orphan config gate)**: Strong. The 10-Why chain addresses escalation from basic grep to TTL-based WIP enforcement. **Challenge**: What if a developer adds the consumer reference in a test file, not production code? The gate checks `sources/`, `publishers/`, `auth/`, `main.py`, `briefing.py` — test files are excluded. A reference in `tests/test_something.py` would NOT satisfy the gate. This is correct behavior (tests don't consume config at runtime), but should be explicitly stated.

2. **PA2 (strategy-step gate)**: Moderate. The bidirectional count check is clever but keyword matching (Why-4 → Why-5 simplification) reduces to number-based identity. **Challenge**: What if two Steps merge into one implementation? E.g., Steps 3 and 4 are both implemented in the same code block. One STRATEGY-STEP-3 and STRATEGY-STEP-4 comment, or one combined comment? **Response**: Each step gets its own comment, even if co-located. Comments are cheap. This maintains the 1:1 mapping.

3. **PA3 (MEMORY.md tracking)**: Weakest action — even with pre-commit enforcement, it's a tracking mechanism, not a prevention mechanism. Its value is cross-session visibility, not gap elimination. **Assessment**: Acceptable as supplement to PA1, NOT acceptable as standalone. Report correctly labels it as soft gate.

4. **PA4 (coverage metric)**: Good observability but not prevention. **Challenge**: The `[WARN]` line in pipeline output could be ignored if it appears frequently (alert fatigue). **Mitigation needed**: Escalate to Telegram alert if coverage < 100% for > 3 consecutive runs, not just console warning. **Response**: Accepted. Added escalation to Telegram "diagnostic" topic after 3 consecutive low-coverage runs.

5. **Cross-action coverage**: Three variants identified in audit Round 3:
   - Variant 1 (config without consumer): PA1 covers.
   - Variant 2 (strategy doc without code): PA2 covers.
   - Variant 3 (new function without caller migration): Already covered by Function Replacement Convention + NameError + .detection-rules. Not in scope of this 8D's prevention (different problem, already has its own 8D).

**Prevention Audit Verdict**: PA1 is strong and well-designed. PA2 is adequate with the simplification to number-based identity. PA3 is acceptable as supplement only. PA4 needs escalation enhancement (accepted). No prevention action is text-instruction-only — all have hard gate or observability enforcement. **PASS with PA4 escalation enhancement noted.**

---

## D7: Verification Plan

### V1: PA1 (Orphan Config Gate) Verification

| Step | Method | Expected Result | Deadline |
|------|--------|----------------|----------|
| 1 | Create a test YAML in `lookups/test_orphan.yaml` with no consumer. Attempt to commit. | Commit blocked with clear error message listing the orphan file. | Within 3 days of PA1 deployment |
| 2 | Add `# CONSUMER-EXEMPT: test` to the YAML. Attempt to commit. | Commit succeeds (exempt). | Same session |
| 3 | Change exempt reason to `WIP: consumer in progress`. Wait 8 days (or fake git timestamp). Attempt to commit. | Commit blocked: WIP exempt expired after 7-day TTL. | Within 1 week |
| 4 | Verify `onenote.yaml` is flagged as orphan before its consumer is implemented. | Gate blocks any commit until onenote.yaml gets a consumer or explicit exempt. | Within 3 days |

### V2: PA2 (Strategy-Step Gate) Verification

| Step | Method | Expected Result | Deadline |
|------|--------|----------------|----------|
| 1 | Add `Step 9` to `search_strategy.md` without a `STRATEGY-STEP-9` comment anywhere. Attempt to commit. | Commit blocked: strategy step count mismatch. | Within 3 days of PA2 deployment |
| 2 | Add `# STRATEGY-STEP-9: new chain` to a source file. Attempt to commit. | Commit succeeds (counts match). | Same session |
| 3 | Remove `Step 5` from strategy doc while code still has `STRATEGY-STEP-5`. Attempt to commit. | Commit blocked: bidirectional mismatch. | Same session |

### V3: PA4 (Coverage Metric) Verification

| Step | Method | Expected Result | Deadline |
|------|--------|----------------|----------|
| 1 | Run `py -3 main.py --dry-run`. Check output for `[COVERAGE]` line. | Coverage line present with correct N/M ratios. | Within 1 week of PA4 deployment |
| 2 | Temporarily remove Chain 5 from `recording_discovery.py`. Run pipeline. | `[COVERAGE]` shows lower ratio + `[WARN]` for uncovered source. | Same session (revert after test) |
| 3 | After 3 consecutive runs with coverage < 100%, verify Telegram escalation. | Telegram "diagnostic" topic receives coverage alert. | Within 2 weeks |

### V4: End-to-End Integration Verification

| Step | Method | Expected Result | Deadline |
|------|--------|----------------|----------|
| 1 | After implementing CA2 (onenote.yaml consumer), run full pipeline and verify OneNote section scanning appears in output. | OneNote scanning results in pipeline output + `[COVERAGE]` shows N+1 sources executed. | By 2026-04-24 |
| 2 | Quarterly audit: sample 3 STRATEGY-STEP comments and 3 WIKI-CONSULTED markers. Verify they are substantive. | All sampled markers cite real wiki pages/steps with actionable findings. | 2026-07-17 (first quarterly) |

---

## D8: Lessons Learned, Horizontal Deployment, Wiki Ingest

### Lessons Learned

| # | Lesson | Impact |
|---|--------|--------|
| 1 | **Config existence ≠ capability.** A well-structured YAML file with correct data creates false confidence that the capability exists. The config is a plan, not an implementation. | Changed mental model: config files are now treated as "half artifacts" that require completion. |
| 2 | **Session-bounded development creates integration gaps.** LLM agents (and humans in different sprints) create coherent deliverables within each session but miss cross-session integration. | Added cross-session tracking mechanism (PA3) and hard gate (PA1) to bridge sessions. |
| 3 | **Zero-result success is the most dangerous outcome in source discovery.** Unlike crashes (which trigger investigation) or errors (which are logged), zero-result success is invisible. | Added source coverage metric (PA4) to distinguish "scanned 0 sources" from "scanned N sources, found 0 results." |
| 4 | **"Instructions vs Gates" applies recursively.** The previous draft proposed CLAUDE.md instructions for cross-session handoff. This draft recognizes those would fail for the same reason the strategy doc failed — text without enforcement. | All prevention actions now require at least one hard gate. |
| 5 | **8D horizontal search is mandatory.** The Apr 16 CDP 8D found and fixed one instance of "exists but not connected" without searching for other instances. Pattern-level sweep should be a standard 8D step. | Added to 8D template: mandatory "pattern sweep" between D5 and D6. |
| 6 | **Documentation quality can be inversely correlated with implementation.** The more thorough the strategy doc and config files look, the more confident the user becomes — even when implementation is incomplete. | Prevention gates check implementation existence, not documentation quality. |

### Horizontal Deployment

| Target | Adaptation | Priority |
|--------|-----------|----------|
| **This project: other config dirs** | If new directories like `prompts/`, `templates/` are created, add them to `.config-dirs` and apply the same orphan-config gate. | High |
| **This project: config.yaml sections** | Audit `config.yaml` for unused sections. Lower priority since it's a secrets file with different lifecycle. | Medium |
| **Other D-claude projects** | The "orphan config gate" pattern is generalizable. Any project with config files should have a consumer-verification mechanism. Document in wiki. | Low (no other projects with this pattern yet) |
| **8D template** | Add "pattern sweep" as mandatory step. Add "gate classification" field for prevention actions. | High (affects all future 8Ds) |

### Wiki Ingest Draft

**Title**: Configured but Disconnected Pattern (config-without-consumer anti-pattern)

**Proposed filename**: `wiki/concepts/configured-but-disconnected.md`

**Draft content** (for `raw/notes/` ingestion):

---

#### Configured but Disconnected Pattern

A config artifact (YAML, Markdown strategy doc, lookup table) exists with correct data but no code reads it. The system appears to have a capability ("we scan 3 SharePoint folders") when in reality the capability was never implemented. Both sides of the interface -- the config describing *what* to do and the code that *does* things -- are individually correct but never wired together.

**Why it's dangerous**: Config files are passive -- they don't error when unread, don't assert they have consumers, and don't signal their orphan status. Meanwhile, the config's existence creates false confidence. A user seeing `lookups/recordings.yaml` with 3 well-formatted SharePoint paths reasonably believes those paths are being scanned. The gap is invisible until someone manually traces the data flow end-to-end.

**The Zero-Result Ambiguity**: In source-discovery systems, this pattern is amplified by zero-result success. When the pipeline reports "0 recordings found," this could mean:
- All 7 sources were scanned, nothing found today (legitimate)
- Only 4 of 7 sources were scanned, 3 were never wired (bug)
- 0 sources were scanned because the entire module is broken (failure)

All three produce the same output. Without a coverage metric reporting "sources searched: N/M," the ambiguity persists indefinitely.

**Root Cause Pattern**: Session-bounded development. A config file is created in Session A as a design artifact ("what we want to scan"). Consumer code is created in Session B as an implementation artifact ("how we scan"). Neither session checks the other's output because (a) there's no cross-session state tracking for pending integrations, and (b) config files don't fail loudly when unread.

**The "Planning-as-Doing" Trap**: Creating a config file *feels* productive and *looks* like progress. The commit has a good message, the file is well-structured, the strategy doc is thorough. This creates a completion illusion -- the work feels done when only half is done. The completion of the *plan* is mistaken for the completion of the *implementation*.

**Three Variants**:
1. **Config without consumer**: YAML/JSON data file exists, no code loads it. (e.g., `lookups/recordings.yaml` for 10 days)
2. **Strategy doc without implementation**: Design doc describes N steps, code implements M < N. (e.g., `search_strategy.md` 8 steps vs 4 chains)
3. **New function without caller migration**: Replacement function exists, but old call sites still use the deprecated function. (e.g., `_ensure_cdp_has_copilot` vs `_check_cdp_available` for 7 days)

**Prevention**:
- **Hard gate**: Pre-commit hook verifying all config files in managed directories have consumer references in code. TTL on "work-in-progress" exemptions (max 7 days).
- **Coverage metric**: Pipeline runtime reporting of "configured sources vs executed sources." Alert on delta > 0 for consecutive runs.
- **Architectural elimination** (variant 3): Delete old function in same commit. NameError enforces correctness. (See: Function Replacement Convention)
- **Bidirectional doc-code sync** (variant 2): Strategy doc step count must match code step-comment count. Pre-commit enforced.

**Anti-pattern**: Using text instructions ("always check lookups/ before committing") instead of hard gates. Text instructions fail because they depend on the developer remembering to follow them -- the same developer who forgot to wire the config in the first place. Instructions without enforcement = configured but disconnected at the *process* level.

**Related wiki pages**:
- [Silent Staleness Pattern](silent-staleness.md) -- zero-result ambiguity is a form of silent staleness
- [Function Replacement Convention](function-replacement-convention.md) -- variant 3 prevention
- [Wiki-to-Code Traceability](wiki-to-code-traceability.md) -- same "instructions vs gates" lesson
- [Self-Healing Automation](self-healing-automation.md) -- self-healing can mask the disconnection (pipeline succeeds despite missing source)

---

## Timeline

| Date | Event | Commit |
|------|-------|--------|
| Apr 7 | `lookups/` directory created: `recordings.yaml` (3 SharePoint paths), `onenote.yaml` (1 OneNote section), `search_strategy.md` (8-step plan) | 8860bc2, 2991e42 |
| Apr 9 | `recording_discovery.py` created with Chains 1-3 only. Does NOT read `lookups/recordings.yaml`. `search_strategy.md` Steps 5-7 described but not implemented. | f0b7ca2 |
| Apr 9 | Chain 4 (email) added -- still no `recordings.yaml` reader | 0ba762e |
| Apr 9 | `_ensure_cdp_has_copilot` added but only wired to `summarize_meetings_via_copilot`. `fetch_all_via_copilot` still uses `_check_cdp_available`. | bc93a4f |
| Apr 16 | CDP dual-function bug discovered and fixed. `_check_cdp_available` deleted. | ffc517e, 9bf62c9 |
| Apr 16 | User discovers the `recordings.yaml` gap during 8D analysis. First draft of this report. | -- |
| Apr 17 | Chain 5 (SharePoint scan from `recordings.yaml`) implemented. | 1bffbf7 |
| Apr 17 | This full 8D report written. `onenote.yaml` still has no consumer. | -- |

**Gap durations**:
- `recordings.yaml` → consumer: 10 days (Apr 7 → Apr 17)
- `onenote.yaml` → consumer: 10+ days and counting (Apr 7 → present)
- `search_strategy.md` Steps 5-7 → implementation: 10 days for Step 5 (Apr 7 → Apr 17), Steps 6-7 partially open
- `_check` → `_ensure` caller migration: 7 days (Apr 9 → Apr 16), with 4 days of silent data loss
