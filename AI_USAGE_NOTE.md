# AI Usage Note

**Tool used:** OpenAI Codex (this coding agent). It inspected the assignment PDF and empty workspace, found and downloaded the stated data snapshot, wrote the research engine, tests, notebook, figures, and submission notes, and ran the calculations. The figures and statistics come from the saved data and code, not from AI estimation.

**Decisions in this session:** The agent fixed the primary −2% / five-session rule, next-open entry, 10 bps per-side total drag, non-overlap convention, and 2022 split before reading event outcomes. These are research assumptions for the applicant to review; no human choice beyond the supplied request is claimed.

**Suggestions changed or rejected:** The assignment's conceptual close-to-close forward-return example was changed to next-open execution because a close-based signal cannot enter earlier on the signal day. Searching for the best historical threshold or horizon was rejected. A first code draft allowed a window to cross a missing source bar; a synthetic test exposed this incorrect behavior and it was fixed before final outputs. A first plotting draft also mislabeled the baseline comparison and was corrected.

**Learning:** Explicit timing, source-bar checks, and tests are essential even in a small event study. A positive OOS sample mean can coexist with weak statistical evidence and a negative development result. The applicant should independently review the source, research assumptions, and outputs before submission.
