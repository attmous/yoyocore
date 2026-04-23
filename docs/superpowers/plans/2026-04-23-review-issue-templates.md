# Review Issue Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship four GitHub YAML issue-form templates (architecture, code-quality, testing, docs) plus supporting config and labels so the upcoming second codebase review lands findings in a standardized, obsolescence-resistant shape.

**Architecture:** Four declarative YAML files under `.github/ISSUE_TEMPLATE/` plus a `config.yml`. Each template auto-applies a static label set; severity/effort/concern-type are captured as in-body form fields, and the reviewing agent applies matching GitHub labels post-creation via `gh issue edit --add-label`. A short README under `.github/ISSUE_TEMPLATE/` documents the contract so the reviewing agent (and future humans) know the expected body shape.

**Tech Stack:** GitHub issue forms (YAML v1), `gh` CLI, Python (only for YAML-parse verification). No application code changes.

**Spec:** [docs/superpowers/specs/2026-04-23-review-issue-templates-design.md](../specs/2026-04-23-review-issue-templates-design.md)

---

## File structure

Files created by this plan:

| Path | Responsibility |
|---|---|
| `.github/ISSUE_TEMPLATE/config.yml` | Leaves blank-issue filing enabled; no contact links. |
| `.github/ISSUE_TEMPLATE/review-architecture.yml` | Arch findings form (boundary/coupling/state/threading/etc.). |
| `.github/ISSUE_TEMPLATE/review-code-quality.yml` | Code-quality findings form (error-handling/naming/idioms/etc.). |
| `.github/ISSUE_TEMPLATE/review-testing.yml` | Test-gap findings form (coverage/brittle/mock-vs-reality/etc.). |
| `.github/ISSUE_TEMPLATE/review-docs.yml` | Docs findings form (stale/missing/inaccurate/contradictory). |
| `.github/ISSUE_TEMPLATE/README.md` | Reviewer contract: field order, label-application workflow, SHA-pinning rule. |

Files modified: none.

Labels created on the remote repo via `gh`:

- `code-quality`
- `testing`
- `docs`
- `review`
- `review:2026-04-23`

---

## Pre-flight

- [ ] **Step 1: Confirm worktree and branch**

Run:

```bash
git status
git branch --show-current
```

Expected: clean working tree on branch `claude/romantic-khorana-d1618a` (or similar review-prep branch). The spec file from the prior session is already committed.

- [ ] **Step 2: Confirm `.github/ISSUE_TEMPLATE/` does not exist yet**

Run:

```bash
ls .github/ISSUE_TEMPLATE 2>/dev/null || echo "directory absent — ok to create"
```

Expected: "directory absent — ok to create".

- [ ] **Step 3: Create the directory**

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

Expected: directory exists, no output.

---

## Task 1: `config.yml` + reviewer README

**Files:**
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/ISSUE_TEMPLATE/README.md`

- [ ] **Step 1: Write the YAML-parse verification one-liner**

This is our "test": the YAML must parse, and `blank_issues_enabled` must be `true`.

```bash
python -c "import yaml, sys; d = yaml.safe_load(open('.github/ISSUE_TEMPLATE/config.yml')); assert d['blank_issues_enabled'] is True, d; print('ok')"
```

- [ ] **Step 2: Run it to verify it fails (file doesn't exist yet)**

Expected: `FileNotFoundError` or similar, non-zero exit.

- [ ] **Step 3: Write `config.yml`**

```yaml
blank_issues_enabled: true
```

- [ ] **Step 4: Run the verification — expect pass**

```bash
python -c "import yaml, sys; d = yaml.safe_load(open('.github/ISSUE_TEMPLATE/config.yml')); assert d['blank_issues_enabled'] is True, d; print('ok')"
```

Expected: `ok`.

- [ ] **Step 5: Write the reviewer README**

Create `.github/ISSUE_TEMPLATE/README.md` with the following exact content:

```markdown
# Review issue templates

Four YAML issue forms for the YoYoPod codebase review workflow:

| Template | Lens |
|---|---|
| `review-architecture.yml` | Boundaries, coupling, state ownership, threading, layering, dependency direction. |
| `review-code-quality.yml` | Error handling, logging, dead code, naming, idioms, perf hot-paths, security. |
| `review-testing.yml` | Coverage gaps, brittle tests, mocks-vs-reality, CI gate gaps, missing integration. |
| `review-docs.yml` | Stale, missing, inaccurate, or contradictory documentation. |

## Obsolescence-prevention contract

Every template enforces:

1. **Source commit SHA is required.** Every finding pins to the exact snapshot it was reviewed against.
2. **No SLOC fields.** Findings are observational, not line-count heuristics.
3. **"Suggested direction" not "Proposed fix".** Framing survives reorganization even when specific mechanisms rot.
4. **File paths primary, line numbers optional.** Paths are stabler across refactors.

## Reviewer workflow (for agents using `gh` CLI)

YAML issue forms enforce field validation only for web submissions. Agents filing via
`gh issue create --body` must mirror the field schema in their rendered body and apply
severity/effort/review-round labels manually:

```bash
gh issue create \
  --title "[Arch] <short finding title>" \
  --body "$(cat <<'EOF'
### Finding ID
A01

### Source commit SHA
<full SHA>

### Concern type
boundary

### Invariant violated
rules/architecture.md §"Dependency Direction"

### Severity
high

### Effort
medium

### Files affected
yoyopod/core/loop.py
yoyopod/core/application.py

### Finding
<what's wrong, observed at the pinned SHA>

### Impact
<what breaks / what rule or doc it violates>

### Suggested direction
<observational guidance, not prescriptive file splits>

### References
rules/architecture.md
docs/SYSTEM_ARCHITECTURE.md
EOF
)" \
  --label "architecture" \
  --label "review" \
  --label "review:2026-04-23" \
  --label "severity:high" \
  --label "effort:medium"
```

Template files under this directory are the schema contract. Field order and labels
in the body must match the corresponding `.yml` file's `body:` entries.

## See also

- Spec: [docs/superpowers/specs/2026-04-23-review-issue-templates-design.md](../../docs/superpowers/specs/2026-04-23-review-issue-templates-design.md)
```

- [ ] **Step 6: Commit**

```bash
git add .github/ISSUE_TEMPLATE/config.yml .github/ISSUE_TEMPLATE/README.md
git commit -m "$(cat <<'EOF'
chore(github): add issue-template config and reviewer README

Scaffolds .github/ISSUE_TEMPLATE/ with a config.yml that leaves blank
issues enabled and a README describing the reviewer contract (SHA
pinning, no SLOC, observational "suggested direction" framing, and the
gh CLI labeling workflow for agent-filed findings).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `review-architecture.yml`

**Files:**
- Create: `.github/ISSUE_TEMPLATE/review-architecture.yml`

- [ ] **Step 1: Write the YAML-parse + schema verification**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-architecture.yml'))
assert doc['name'] == 'Review finding — Architecture'
assert doc['title'] == '[Arch] '
assert set(doc['labels']) == {'architecture', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'concern-type', 'invariant-violated',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
print('ok')
PY
```

- [ ] **Step 2: Run to verify it fails (file absent)**

Expected: `FileNotFoundError`.

- [ ] **Step 3: Write `review-architecture.yml`**

```yaml
name: Review finding — Architecture
description: File a clean-architecture finding from a codebase review (boundaries, coupling, state ownership, threading, layering).
title: "[Arch] "
labels: ["architecture", "review"]
body:
  - type: markdown
    attributes:
      value: |
        Use this form for architecture findings produced during a codebase review.
        See `.github/ISSUE_TEMPLATE/README.md` for the reviewer contract.

  - type: input
    id: finding-id
    attributes:
      label: Finding ID
      description: Short reviewer-assigned ID, e.g. `A01`. Optional but helpful for cross-referencing a review summary issue.
      placeholder: A01
    validations:
      required: false

  - type: input
    id: source-commit-sha
    attributes:
      label: Source commit SHA
      description: The exact commit SHA the finding was observed against. Pins the finding so it remains triage-able after future refactors.
      placeholder: 8f624ed2...
    validations:
      required: true

  - type: dropdown
    id: concern-type
    attributes:
      label: Concern type
      description: Which architectural concern does this finding hit?
      options:
        - boundary
        - coupling
        - state-ownership
        - threading
        - layering
        - dependency-direction
    validations:
      required: true

  - type: input
    id: invariant-violated
    attributes:
      label: Invariant violated
      description: Which rule, doc, or architectural invariant does this finding violate? Reference the rule or doc section if possible.
      placeholder: rules/architecture.md §"Dependency Direction"
    validations:
      required: false

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - critical
        - high
        - medium
        - low
    validations:
      required: true

  - type: dropdown
    id: effort
    attributes:
      label: Effort
      options:
        - small
        - medium
        - large
    validations:
      required: true

  - type: textarea
    id: files-affected
    attributes:
      label: Files affected
      description: Code paths, one per line. Line numbers are optional — paths are primary because they survive refactors better than line numbers.
      placeholder: |
        yoyopod/core/loop.py
        yoyopod/core/application.py
    validations:
      required: true

  - type: textarea
    id: finding
    attributes:
      label: Finding
      description: What's wrong, observed at the pinned SHA. Describe the current behaviour concretely.
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impact
      description: What breaks, what's risked, or which rule/doc it violates. Explain why this finding matters.
    validations:
      required: true

  - type: textarea
    id: suggested-direction
    attributes:
      label: Suggested direction
      description: Observational, not prescriptive. State a principle or invariant to restore — avoid prescribing exact file splits or method signatures, since they rot when the codebase reorganizes.
    validations:
      required: false

  - type: textarea
    id: references
    attributes:
      label: References
      description: Links to `rules/*.md`, `docs/*.md`, prior issues, or external best-practice references.
    validations:
      required: false
```

- [ ] **Step 4: Run verification — expect pass**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-architecture.yml'))
assert doc['name'] == 'Review finding — Architecture'
assert doc['title'] == '[Arch] '
assert set(doc['labels']) == {'architecture', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'concern-type', 'invariant-violated',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
print('ok')
PY
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add .github/ISSUE_TEMPLATE/review-architecture.yml
git commit -m "$(cat <<'EOF'
chore(github): add review-architecture issue form

YAML issue form for architecture findings. Enforces SHA pinning and
uses observational "suggested direction" framing instead of prescriptive
fix proposals.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `review-code-quality.yml`

**Files:**
- Create: `.github/ISSUE_TEMPLATE/review-code-quality.yml`

- [ ] **Step 1: Write the YAML-parse + schema verification**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-code-quality.yml'))
assert doc['name'] == 'Review finding — Code quality'
assert doc['title'] == '[CQ] '
assert set(doc['labels']) == {'code-quality', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'concern-type',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
options = {o for b in doc['body'] if b.get('id') == 'concern-type' for o in b['attributes']['options']}
assert {'error-handling', 'logging', 'dead-code', 'naming', 'idioms', 'perf-hotpath', 'security'} <= options
print('ok')
PY
```

- [ ] **Step 2: Run to verify it fails (file absent)**

Expected: `FileNotFoundError`.

- [ ] **Step 3: Write `review-code-quality.yml`**

```yaml
name: Review finding — Code quality
description: File a code-quality finding from a codebase review (error handling, logging, dead code, naming, idioms, perf hot-paths, security).
title: "[CQ] "
labels: ["code-quality", "review"]
body:
  - type: markdown
    attributes:
      value: |
        Use this form for code-quality findings produced during a codebase review.
        Perf and security findings ride on this form via the `Concern type` dropdown
        until finding volume justifies their own templates.
        See `.github/ISSUE_TEMPLATE/README.md` for the reviewer contract.

  - type: input
    id: finding-id
    attributes:
      label: Finding ID
      description: Short reviewer-assigned ID, e.g. `CQ01`. Optional but helpful for cross-referencing a review summary issue.
      placeholder: CQ01
    validations:
      required: false

  - type: input
    id: source-commit-sha
    attributes:
      label: Source commit SHA
      description: The exact commit SHA the finding was observed against. Pins the finding so it remains triage-able after future refactors.
      placeholder: 8f624ed2...
    validations:
      required: true

  - type: dropdown
    id: concern-type
    attributes:
      label: Concern type
      description: Which code-quality concern does this finding hit?
      options:
        - error-handling
        - logging
        - dead-code
        - naming
        - idioms
        - perf-hotpath
        - security
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - critical
        - high
        - medium
        - low
    validations:
      required: true

  - type: dropdown
    id: effort
    attributes:
      label: Effort
      options:
        - small
        - medium
        - large
    validations:
      required: true

  - type: textarea
    id: files-affected
    attributes:
      label: Files affected
      description: Code paths, one per line. Line numbers are optional — paths are primary because they survive refactors better than line numbers.
      placeholder: |
        yoyopod/core/bus.py
    validations:
      required: true

  - type: textarea
    id: finding
    attributes:
      label: Finding
      description: What's wrong, observed at the pinned SHA. Describe the current behaviour concretely.
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impact
      description: What breaks, what's risked, or which rule/doc it violates. Explain why this finding matters.
    validations:
      required: true

  - type: textarea
    id: suggested-direction
    attributes:
      label: Suggested direction
      description: Observational, not prescriptive. State a principle or property to restore.
    validations:
      required: false

  - type: textarea
    id: references
    attributes:
      label: References
      description: Links to `rules/*.md`, `docs/*.md`, prior issues, or external best-practice references.
    validations:
      required: false
```

- [ ] **Step 4: Run verification — expect pass**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-code-quality.yml'))
assert doc['name'] == 'Review finding — Code quality'
assert doc['title'] == '[CQ] '
assert set(doc['labels']) == {'code-quality', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'concern-type',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
options = {o for b in doc['body'] if b.get('id') == 'concern-type' for o in b['attributes']['options']}
assert {'error-handling', 'logging', 'dead-code', 'naming', 'idioms', 'perf-hotpath', 'security'} <= options
print('ok')
PY
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add .github/ISSUE_TEMPLATE/review-code-quality.yml
git commit -m "$(cat <<'EOF'
chore(github): add review-code-quality issue form

YAML issue form for code-quality findings. Perf and security findings
ride on this form via the concern-type dropdown until volume justifies
their own templates.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `review-testing.yml`

**Files:**
- Create: `.github/ISSUE_TEMPLATE/review-testing.yml`

- [ ] **Step 1: Write the YAML-parse + schema verification**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-testing.yml'))
assert doc['name'] == 'Review finding — Testing'
assert doc['title'] == '[Test] '
assert set(doc['labels']) == {'testing', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'gap-type', 'test-gap-or-assertion',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
options = {o for b in doc['body'] if b.get('id') == 'gap-type' for o in b['attributes']['options']}
assert {'missing-coverage', 'brittle-test', 'mock-vs-reality', 'CI-gate-gap', 'integration-gap'} <= options
print('ok')
PY
```

- [ ] **Step 2: Run to verify it fails (file absent)**

Expected: `FileNotFoundError`.

- [ ] **Step 3: Write `review-testing.yml`**

```yaml
name: Review finding — Testing
description: File a testing finding from a codebase review (missing coverage, brittle tests, mock-vs-reality drift, CI gate gaps, integration gaps).
title: "[Test] "
labels: ["testing", "review"]
body:
  - type: markdown
    attributes:
      value: |
        Use this form for testing findings produced during a codebase review.
        See `.github/ISSUE_TEMPLATE/README.md` for the reviewer contract.

  - type: input
    id: finding-id
    attributes:
      label: Finding ID
      description: Short reviewer-assigned ID, e.g. `T01`. Optional but helpful for cross-referencing a review summary issue.
      placeholder: T01
    validations:
      required: false

  - type: input
    id: source-commit-sha
    attributes:
      label: Source commit SHA
      description: The exact commit SHA the finding was observed against.
      placeholder: 8f624ed2...
    validations:
      required: true

  - type: dropdown
    id: gap-type
    attributes:
      label: Gap type
      description: What kind of testing gap is this?
      options:
        - missing-coverage
        - brittle-test
        - mock-vs-reality
        - CI-gate-gap
        - integration-gap
    validations:
      required: true

  - type: textarea
    id: test-gap-or-assertion
    attributes:
      label: Test gap or failing assertion
      description: The concrete test shape that's missing or broken. A minimal failing assertion, a behaviour currently uncovered, or the specific CI step that isn't gating what it should.
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - critical
        - high
        - medium
        - low
    validations:
      required: true

  - type: dropdown
    id: effort
    attributes:
      label: Effort
      options:
        - small
        - medium
        - large
    validations:
      required: true

  - type: textarea
    id: files-affected
    attributes:
      label: Files affected
      description: Production code paths and/or test paths, one per line.
      placeholder: |
        yoyopod/core/bus.py
        tests/core/test_bus.py
    validations:
      required: true

  - type: textarea
    id: finding
    attributes:
      label: Finding
      description: What's wrong or missing, observed at the pinned SHA.
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impact
      description: What regressions could slip through, or what's currently asserted that doesn't reflect production behaviour.
    validations:
      required: true

  - type: textarea
    id: suggested-direction
    attributes:
      label: Suggested direction
      description: Observational, not prescriptive. The shape of the test to add, or the mock to replace with an integration path.
    validations:
      required: false

  - type: textarea
    id: references
    attributes:
      label: References
      description: Links to `rules/*.md`, `docs/*.md`, prior issues, or external references.
    validations:
      required: false
```

- [ ] **Step 4: Run verification — expect pass**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-testing.yml'))
assert doc['name'] == 'Review finding — Testing'
assert doc['title'] == '[Test] '
assert set(doc['labels']) == {'testing', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'gap-type', 'test-gap-or-assertion',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
options = {o for b in doc['body'] if b.get('id') == 'gap-type' for o in b['attributes']['options']}
assert {'missing-coverage', 'brittle-test', 'mock-vs-reality', 'CI-gate-gap', 'integration-gap'} <= options
print('ok')
PY
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add .github/ISSUE_TEMPLATE/review-testing.yml
git commit -m "$(cat <<'EOF'
chore(github): add review-testing issue form

YAML issue form for testing findings: coverage gaps, brittle tests,
mock-vs-reality drift, CI gate gaps, integration gaps.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `review-docs.yml`

**Files:**
- Create: `.github/ISSUE_TEMPLATE/review-docs.yml`

- [ ] **Step 1: Write the YAML-parse + schema verification**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-docs.yml'))
assert doc['name'] == 'Review finding — Docs'
assert doc['title'] == '[Docs] '
assert set(doc['labels']) == {'docs', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'doc-problem', 'doc-location',
    'what-it-should-say',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
options = {o for b in doc['body'] if b.get('id') == 'doc-problem' for o in b['attributes']['options']}
assert {'stale', 'missing', 'inaccurate', 'contradictory'} <= options
# doc-location must be required
loc_field = next(b for b in doc['body'] if b.get('id') == 'doc-location')
assert loc_field.get('validations', {}).get('required') is True
print('ok')
PY
```

- [ ] **Step 2: Run to verify it fails (file absent)**

Expected: `FileNotFoundError`.

- [ ] **Step 3: Write `review-docs.yml`**

```yaml
name: Review finding — Docs
description: File a documentation finding from a codebase review (stale, missing, inaccurate, or contradictory docs).
title: "[Docs] "
labels: ["docs", "review"]
body:
  - type: markdown
    attributes:
      value: |
        Use this form for documentation findings produced during a codebase review.
        See `.github/ISSUE_TEMPLATE/README.md` for the reviewer contract.

  - type: input
    id: finding-id
    attributes:
      label: Finding ID
      description: Short reviewer-assigned ID, e.g. `D01`. Optional but helpful for cross-referencing a review summary issue.
      placeholder: D01
    validations:
      required: false

  - type: input
    id: source-commit-sha
    attributes:
      label: Source commit SHA
      description: The exact commit SHA the finding was observed against.
      placeholder: 8f624ed2...
    validations:
      required: true

  - type: dropdown
    id: doc-problem
    attributes:
      label: Doc problem
      description: What's wrong with the documentation?
      options:
        - stale
        - missing
        - inaccurate
        - contradictory
    validations:
      required: true

  - type: input
    id: doc-location
    attributes:
      label: Doc location
      description: Path to the affected doc, or "N/A — doc missing" if the doc should exist but does not.
      placeholder: docs/SYSTEM_ARCHITECTURE.md
    validations:
      required: true

  - type: textarea
    id: what-it-should-say
    attributes:
      label: What it should say
      description: The corrected or intended content. Optional — reviewers may flag a problem without yet knowing the resolution.
    validations:
      required: false

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - critical
        - high
        - medium
        - low
    validations:
      required: true

  - type: dropdown
    id: effort
    attributes:
      label: Effort
      options:
        - small
        - medium
        - large
    validations:
      required: true

  - type: textarea
    id: files-affected
    attributes:
      label: Files affected
      description: Doc paths (plus any related code paths), one per line.
      placeholder: |
        docs/SYSTEM_ARCHITECTURE.md
        yoyopod/core/application.py
    validations:
      required: true

  - type: textarea
    id: finding
    attributes:
      label: Finding
      description: What the doc currently says (or fails to say), observed at the pinned SHA.
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impact
      description: Who's misled and how. What decisions are people making based on the stale/inaccurate content.
    validations:
      required: true

  - type: textarea
    id: suggested-direction
    attributes:
      label: Suggested direction
      description: Observational, not prescriptive. What the correct narrative should convey rather than verbatim replacement text (that goes in "What it should say").
    validations:
      required: false

  - type: textarea
    id: references
    attributes:
      label: References
      description: Links to related docs, rules, or prior issues.
    validations:
      required: false
```

- [ ] **Step 4: Run verification — expect pass**

```bash
python - <<'PY'
import yaml
doc = yaml.safe_load(open('.github/ISSUE_TEMPLATE/review-docs.yml'))
assert doc['name'] == 'Review finding — Docs'
assert doc['title'] == '[Docs] '
assert set(doc['labels']) == {'docs', 'review'}
ids = [b.get('id') for b in doc['body'] if b['type'] != 'markdown']
expected = [
    'finding-id', 'source-commit-sha', 'doc-problem', 'doc-location',
    'what-it-should-say',
    'severity', 'effort', 'files-affected', 'finding', 'impact',
    'suggested-direction', 'references',
]
assert ids == expected, (ids, expected)
options = {o for b in doc['body'] if b.get('id') == 'doc-problem' for o in b['attributes']['options']}
assert {'stale', 'missing', 'inaccurate', 'contradictory'} <= options
loc_field = next(b for b in doc['body'] if b.get('id') == 'doc-location')
assert loc_field.get('validations', {}).get('required') is True
print('ok')
PY
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add .github/ISSUE_TEMPLATE/review-docs.yml
git commit -m "$(cat <<'EOF'
chore(github): add review-docs issue form

YAML issue form for documentation findings (stale, missing, inaccurate,
contradictory). "Doc location" is required; "What it should say" is
optional so reviewers can flag a problem without yet knowing the exact
replacement.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Full-suite verification locally

**Files:** none (verification only)

This task ensures every template parses and conforms to schema in one pass, before pushing.

- [ ] **Step 1: Run the cross-template verification**

```bash
python - <<'PY'
import yaml
from pathlib import Path

expected_by_file = {
    '.github/ISSUE_TEMPLATE/review-architecture.yml': {
        'name': 'Review finding — Architecture',
        'title': '[Arch] ',
        'labels': {'architecture', 'review'},
    },
    '.github/ISSUE_TEMPLATE/review-code-quality.yml': {
        'name': 'Review finding — Code quality',
        'title': '[CQ] ',
        'labels': {'code-quality', 'review'},
    },
    '.github/ISSUE_TEMPLATE/review-testing.yml': {
        'name': 'Review finding — Testing',
        'title': '[Test] ',
        'labels': {'testing', 'review'},
    },
    '.github/ISSUE_TEMPLATE/review-docs.yml': {
        'name': 'Review finding — Docs',
        'title': '[Docs] ',
        'labels': {'docs', 'review'},
    },
}

# Common field IDs present in every template
common_ids = {
    'finding-id', 'source-commit-sha', 'severity', 'effort',
    'files-affected', 'finding', 'impact', 'suggested-direction', 'references',
}

for path, expected in expected_by_file.items():
    assert Path(path).exists(), f'missing: {path}'
    doc = yaml.safe_load(open(path))
    assert doc['name'] == expected['name'], (path, doc['name'])
    assert doc['title'] == expected['title'], (path, doc['title'])
    assert set(doc['labels']) == expected['labels'], (path, doc['labels'])
    ids = {b.get('id') for b in doc['body'] if b['type'] != 'markdown'}
    missing = common_ids - ids
    assert not missing, (path, missing)

cfg = yaml.safe_load(open('.github/ISSUE_TEMPLATE/config.yml'))
assert cfg['blank_issues_enabled'] is True
assert Path('.github/ISSUE_TEMPLATE/README.md').exists()
print('all templates ok')
PY
```

Expected: `all templates ok`.

- [ ] **Step 2: Run the project quality gate**

Per `CLAUDE.md`, we run the same gate CI runs. These changes don't touch Python code, but the rule is unconditional.

```bash
uv run python scripts/quality.py gate
```

Expected: gate passes (no new format/lint/type findings introduced by these YAML files; the gate paths are Python-only).

- [ ] **Step 3: Run the project test suite**

```bash
uv run pytest -q
```

Expected: test suite passes on Linux CI. On Windows, known platform-specific failures exist per `CLAUDE.md` — only flag NEW failures vs. main. YAML file additions should not affect any test.

---

## Task 7: Push branch and open PR

**Files:** none (remote interaction)

This task pushes the branch and opens a PR. The PR is review-only scaffolding — no code changes — so it should be straightforward to merge.

- [ ] **Step 1: Push the branch**

```bash
git push -u origin HEAD
```

Expected: push succeeds; the remote prints a link to open a PR.

- [ ] **Step 2: Open the PR**

```bash
gh pr create --title "chore(github): add review issue-form templates" --body "$(cat <<'EOF'
## Summary

- Adds four YAML issue-form templates under `.github/ISSUE_TEMPLATE/` for the upcoming second codebase review: architecture, code-quality, testing, docs.
- Adds `config.yml` (leaves blank issues enabled) and a reviewer README documenting the contract.
- Every form requires a source commit SHA so findings pin to a reviewed snapshot — prior review (#224–#235) rotted because findings referenced paths/line counts that the arch rework deleted. Observational "Suggested direction" framing replaces prescriptive "Proposed fix" for the same reason.
- No application code changes.

## Spec

- [docs/superpowers/specs/2026-04-23-review-issue-templates-design.md](docs/superpowers/specs/2026-04-23-review-issue-templates-design.md)

## Follow-up (post-merge)

Labels need to be created on the remote repo before the review round runs. See Task 8 in the plan — these require an explicit OK from the user before the agent runs `gh label create` against the shared repo.

## Test plan

- [x] Each YAML template parses via `python -c "import yaml; yaml.safe_load(open('...'))"`.
- [x] Each template has the expected `name`, `title`, `labels`, and field-id set verified by a cross-template check in Task 6.
- [x] `uv run python scripts/quality.py gate` passes.
- [x] `uv run pytest -q` passes on Linux CI.
- [ ] After merge: open `https://github.com/moustafattia/yoyopod-core/issues/new/choose` in a browser and confirm all four templates appear with their fields rendered correctly.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR URL returned. Record the URL; the user may want to review before merging.

- [ ] **Step 3: Report the PR URL to the user**

Display the PR URL as a markdown link so the user can open it.

---

## Task 8: Create the remote labels (gated on user approval)

**Files:** none (remote interaction with shared state)

> **⚠️ This task modifies shared repo state.** `gh label create` creates labels visible to everyone and affecting future automations. Do NOT run without explicit user approval. If the user hasn't confirmed, pause and ask.

- [ ] **Step 1: Ask the user to confirm label creation**

Prompt the user:

> "Ready to create the review labels on the remote repo (`code-quality`, `testing`, `docs`, `review`, `review:2026-04-23`)? These are new labels that will be visible in the repo issue sidebar. OK to proceed, or wait until the PR merges?"

Wait for explicit approval. If the user says wait, stop this task and mark the plan complete with a note that labels are pending.

- [ ] **Step 2: Create `code-quality` label**

```bash
gh label create code-quality --repo moustafattia/yoyopod-core --color fbca04 --description "Code-quality finding: error handling, naming, idioms, logging, dead code, perf hot-paths, security"
```

Expected: label created, or a message that it already exists (idempotent — non-fatal).

- [ ] **Step 3: Create `testing` label**

```bash
gh label create testing --repo moustafattia/yoyopod-core --color 0e8a16 --description "Testing finding: coverage gaps, brittle tests, mock-vs-reality drift, CI gate gaps"
```

Expected: label created, or "already exists".

- [ ] **Step 4: Create `docs` label**

```bash
gh label create docs --repo moustafattia/yoyopod-core --color 0075ca --description "Docs finding: stale, missing, inaccurate, or contradictory documentation"
```

Expected: label created, or "already exists".

- [ ] **Step 5: Create `review` label**

```bash
gh label create review --repo moustafattia/yoyopod-core --color 5319e7 --description "Stable parent label for findings produced by any codebase review round"
```

Expected: label created, or "already exists".

- [ ] **Step 6: Create `review:2026-04-23` label**

```bash
gh label create review:2026-04-23 --repo moustafattia/yoyopod-core --color 5319e7 --description "Findings from the 2026-04-23 codebase review round"
```

Expected: label created, or "already exists".

- [ ] **Step 7: Verify all five labels exist**

```bash
gh label list --repo moustafattia/yoyopod-core --json name --jq '.[].name' | grep -E "^(code-quality|testing|docs|review|review:2026-04-23)$" | sort
```

Expected: all five label names printed, one per line, in sorted order:

```
code-quality
docs
review
review:2026-04-23
testing
```

---

## Done criteria

- [ ] All four templates under `.github/ISSUE_TEMPLATE/` parse as valid YAML and pass the Task 6 cross-template verification.
- [ ] `.github/ISSUE_TEMPLATE/config.yml` exists and sets `blank_issues_enabled: true`.
- [ ] `.github/ISSUE_TEMPLATE/README.md` documents the reviewer contract.
- [ ] `uv run python scripts/quality.py gate` and `uv run pytest -q` pass.
- [ ] Branch pushed, PR opened.
- [ ] (Gated on user OK) Five new labels live on `moustafattia/yoyopod-core`.
- [ ] (Post-merge, manual) Visual confirmation at `https://github.com/moustafattia/yoyopod-core/issues/new/choose`.
