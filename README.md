# Bug Diary

Nobody writes the post-mortem. Bug Diary writes it from the fix, and reads it back to you before you make the same mistake again, in this repository or in another one.

```text
billing-worker $ bugdiary check
⚠ Bug pattern already met in another project: race condition in asynchronous resource rotation
  Precedent   BUG-0001 · api · 493bb438 · fixed 2026-10-21 · production
  Past bug    users logged out when two requests refresh an expired token at once
  Cause       The second refresh sent a token the first one had already rotated, so the server
              revoked the whole session.
  Lesson      Use a shared promise to deduplicate concurrent asynchronous operations that mutate
              shared state.
  In this change
    src/client.ts:8  if (this.token.expired) {
    src/client.ts:9  this.token = await this.auth.refresh(this.token.refreshToken);
  Why         The bearer method performs an asynchronous token refresh without any mechanism to
              deduplicate concurrent calls, meaning multiple simultaneous requests will trigger
              multiple refresh calls.
  Check       Are you using a shared promise or a locking mechanism to ensure that multiple
              concurrent calls to bearer() do not trigger multiple calls to auth.refresh()?
  Test        Call billingClient.invoices() and billingClient.payments() simultaneously using
              Promise.all and verify that auth.refresh is called exactly once.
```

- **`bugdiary learn <commit>`**: Gemma 4 reads a bug fix (the diff, the new test, the commit message, the issue or pull request if you name one) and writes a card: symptom, root cause, pattern, fix, guard, lesson, and the condition the regression test encodes.
- **`bugdiary check`**: before you commit, Gemma describes what your change does, EmbeddingGemma finds the closest lessons in the diary, and Gemma compares your change with each of them.
- **One diary for all your repositories**, in `~/.bugdiary/diary.db` (SQLite). A lesson learned in one repository is checked in all the others.
- **`bugdiary hook install`**: checks every commit, and quietly learns from every commit whose message starts with `fix`.

The model suggests, the code checks:

- A symptom or a cause marked *stated* must be found, nearly word for word, in the commit message, the test, the issue or the changelog. Otherwise it is marked *inferred from the code*, or *unknown*. Bug Diary does not invent the business impact of a one-line fix.
- Function names the model cites must exist in the fix; the others are dropped.
- A test found in the fix is recorded as found, not as run.
- An alert must quote lines that are really in your change. A "this is already protected" verdict must quote the protection. Otherwise the verdict is dropped.

Everything runs on your machine: your code, your fixes and your diary never leave it.

## Run it

You need Python 3.10 or later, git, and [Ollama](https://ollama.com).

```sh
ollama pull gemma4:26b
ollama pull embeddinggemma
python3 -m venv .venv
.venv/bin/pip install -e .
```

Then, in any repository:

```sh
bugdiary learn HEAD --origin production
bugdiary learn a1b2c3d..e4f5a6b --issue 42
bugdiary check
bugdiary check --base main
bugdiary search "duplicate webhook"
bugdiary list --all-projects
bugdiary hook install
```

`--issue` and `--pr` read GitHub with [`gh`](https://cli.github.com). `--note-file` adds any text, such as an incident report. `check` looks at everything you have not committed yet (`--staged` for the index only, `--base main` for a branch, `--commit` for a commit, `--diff file.patch` for a patch).

A `bugdiary.yml` at the root of a repository can name the project and the diary folder:

```yaml
project: billing-worker
memory: ~/team-diary
```

Options: `--model` (any Ollama model, `gemma4:26b` by default), `--embed-model` (`embeddinggemma` by default), `--top` (lessons compared per check, 3 by default), `--by-kind` (compare once per kind of bug, showing the model up to six past fixes of that kind: faster and more cautious), `--strict` (exit 1 when a known bug comes back, or when the check could not finish).

## Demo

`python demo/toy.py` builds two small repositories, teaches the diary a token refresh race fixed in the first one, then checks two changes in the second: one that repeats the bug, and one that already shares the refresh.

## Benchmark

`bench/` asks whether a diary of past fixes could have warned about later bugs, on real history.

- `bench/families.json` (summary in [bench/FAMILIES.md](bench/FAMILIES.md)) lists 153 security advisories, each checked against its fix commit, in four families of bugs that keep coming back: credentials kept across a redirect (47 fixes in 22 repositories), archive extraction escaping its folder (48), prototype pollution (42), HTTP request smuggling (16).
- The diary learns only the fixes published before 2021-01-01 (60, plus 6 ordinary bug fixes from `bench/extra.json`).
- For each of the 92 later fixes, Bug Diary checks the vulnerable code and the fixed code (each shown as new code, 30 lines of context around the fix), plus 21 ordinary commits from the same repositories.
- The same model without the diary, asked to review each change, is the baseline (`bench/blind.py`).

```sh
.venv/bin/python -m bench.run fetch
.venv/bin/python -m bench.run learn --variant full
.venv/bin/python -m bench.run detect --variant full
.venv/bin/python -m bench.run blind
.venv/bin/python -m bench.report
```

`fetch` downloads the commits, files and advisories with [`gh`](https://cli.github.com) into `bench/cache/`. Results go to `bench/results/<model>/`, and the report to `bench/results/<model>/RESULTS.md`. `--variant code`, `code+tests` or `code+tests+message` learn the diary from less context.

### Results with `gemma4:26b`

Full tables in [bench/results/gemma4-26b/RESULTS.md](bench/results/gemma4-26b/RESULTS.md). For each later bug, a useful warning fires on the vulnerable version and stays quiet on the fixed one:

| | warns on the vulnerable version only | on both | on neither | on the fixed version only | ordinary commits with a warning | median time |
|---|---|---|---|---|---|---|
| Bug Diary | 24 | 9 | 54 | 5 | 1 of 21 | 38 s |
| `--by-kind` | 18 | 3 | 68 | 3 | 1 of 21 | 22 s |
| the same model without the diary | 1 | 89 | 1 | 1 | 18 of 21 | 7 s |

- The diary found a lesson of the right family for 90 of the 92 later bugs. Of the 33 warnings on vulnerable code that cited the right family, 30 relied only on lessons from other repositories, and 14 only on lessons learned from code in another language.
- Without the diary, the model finds a problem in almost every change, fixed or not.
- The hard case is a comeback: when the code already carries the guard of an earlier, incomplete fix, the model calls it protected. A prompt that told the model "a guard can be incomplete" (`detect-top3-v2.jsonl`, not kept in the code) warned on both versions of 40 bugs.
- From the diff alone, the model left the symptom unknown for 37 of the 66 fixes and inferred it for 29; with the commit message, the pull request and the advisory, 62 symptoms were quoted from a source.


## Tests

```sh
.venv/bin/python -m unittest discover -s tests -t .
```

## Open pieces and their licences

| Piece | Role | Licence |
|---|---|---|
| [Gemma 4](https://ai.google.dev/gemma) `gemma4:26b` | writes the cards, compares changes with them | Apache 2.0 |
| [EmbeddingGemma](https://ai.google.dev/gemma/docs/embeddinggemma) `embeddinggemma` | finds the lessons close to a change | Gemma Terms of Use |
| [Ollama](https://github.com/ollama/ollama) | runs both models locally | MIT |
| SQLite (Python standard library) | stores the diary | public domain |
