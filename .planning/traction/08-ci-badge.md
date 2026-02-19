# CI Badge Setup

---

## Step 1: Create the GitHub Actions workflow

Create the file `.github/workflows/tests.yml` in the repo root with this exact content:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-mock

      - name: Run tests
        run: python -m pytest test/ -q
```

---

## Step 2: Add badge to README.md

Add this markdown near the top of `README.md`, just below the project title:

```markdown
![Tests](https://github.com/JoeyBe1/skill-split/actions/workflows/tests.yml/badge.svg)
```

Full example of how the top of README.md should look:

```markdown
# skill-split

![Tests](https://github.com/JoeyBe1/skill-split/actions/workflows/tests.yml/badge.svg)

Section-level SQLite library for Claude Code skills...
```

---

## Step 3: Verify it works

After pushing `.github/workflows/tests.yml` to `main`:

1. Go to: https://github.com/JoeyBe1/skill-split/actions
2. Confirm the "Tests" workflow appears and runs
3. Confirm it passes (green checkmark)
4. The badge in README.md will update automatically

---

## Notes

- The badge is a live SVG — it updates in real time as CI runs
- If tests are currently at 518/518 passing, this will immediately show green
- The `pull_request` trigger means PRs will also run CI before merge
- Python version is set to `3.13` to match the current `__pycache__` filenames in the repo; adjust if needed
