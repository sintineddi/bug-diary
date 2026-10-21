# Bug Diary

Nobody writes the post-mortem. Bug Diary writes it from the fix, and reads it back to you before you make the same mistake again, in this repository or in another one.

```text
billing-worker $ bugdiary check
⚠ Bug pattern already met in another project: race condition in asynchronous resource rotation
  Precedent   BUG-0001 · api · 4244a5a5 · fixed 2026-10-20 · production
  Past bug    users logged out when two requests refresh an expired token at once
  Lesson      Use a shared promise to deduplicate concurrent asynchronous operations that modify
              shared state.
  In this change
    src/client.ts:8  if (this.token.expired) {
    src/client.ts:9  this.token = await this.auth.refresh(this.token.refreshToken);
  Check       Does the bearer method share an ongoing refresh promise between concurrent calls?
  Test        Trigger two concurrent calls to invoices() and verify that auth.refresh runs once.
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

Options: `--model` (any Ollama model, `gemma4:26b` by default), `--embed-model` (`embeddinggemma` by default), `--top` (lessons compared per check, 3 by default), `--strict` (exit 1 when a known bug comes back).

## Demo

`python demo/toy.py` builds two small repositories, teaches the diary a token refresh race fixed in the first one, then checks two changes in the second: one that repeats the bug, and one that already shares the refresh.

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
