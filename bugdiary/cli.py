from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, config, diffs, git, hooks
from .card import ORIGINS, parse_label
from .check import DEFAULT_TOP, check, retrieve
from .github import GitHubError
from .github import note as github_note
from .learn import LearnError, Note, from_git, learn, remember
from .memory import Diary
from .ollama import Ollama, OllamaError
from .render import Style, card_lines, list_lines, report_json, report_lines, search_lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bugdiary",
        description="Keeps a diary of the bugs you fixed, and reads it back before you repeat one.",
    )
    parser.add_argument("--version", action="version", version=f"bugdiary {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-C", "--repo", type=Path, default=Path.cwd(), help="repository (default: current directory)")
    common.add_argument("--memory", help="diary folder (default: BUGDIARY_HOME, then bugdiary.yml, then ~/.bugdiary)")
    common.add_argument(
        "--project", help="project name (default: bugdiary.yml, then the origin remote, then the folder)"
    )
    common.add_argument("--model", help="Ollama model that writes and compares cards (default: gemma4:26b)")
    common.add_argument("--embed-model", help="Ollama embedding model (default: embeddinggemma)")
    commands = parser.add_subparsers(dest="command", required=True)

    learn_parser = commands.add_parser("learn", parents=[common], help="learn the lesson of a bug fix")
    learn_parser.add_argument("revisions", nargs="*", default=["HEAD"], help="commits or ranges A..B (default: HEAD)")
    learn_parser.add_argument("--origin", choices=ORIGINS, default="unknown", help="where the bug was found")
    learn_parser.add_argument("--issue", action="append", default=[], help="GitHub issue to read with gh")
    learn_parser.add_argument("--pr", action="append", default=[], help="GitHub pull request to read with gh")
    learn_parser.add_argument("--note", action="append", default=[], help="extra context, such as an incident report")
    learn_parser.add_argument("--note-file", action="append", default=[], type=Path, help="file with extra context")
    learn_parser.add_argument("--dry-run", action="store_true", help="show the card without saving it")
    learn_parser.add_argument("--force", action="store_true", help="save it even if the model sees no bug fix")
    learn_parser.add_argument("--json", action="store_true", help="print the cards as JSON")
    learn_parser.add_argument("--quiet", action="store_true", help="print nothing")
    learn_parser.set_defaults(handler=run_learn)

    check_parser = commands.add_parser("check", parents=[common], help="compare a change with the diary")
    scope = check_parser.add_mutually_exclusive_group()
    scope.add_argument("--staged", action="store_true", help="check the staged change only")
    scope.add_argument("--base", help="check the branch against a base, as a pull request would (BASE...HEAD)")
    scope.add_argument("--commit", help="check a commit or a range A..B")
    scope.add_argument("--diff", help="check a unified diff file, or - for stdin")
    check_parser.add_argument("--top", type=int, default=DEFAULT_TOP, help="lessons to compare (default: 3)")
    check_parser.add_argument("--all", action="store_true", help="also show lessons that do not apply")
    check_parser.add_argument("--json", action="store_true", help="print the report as JSON")
    check_parser.add_argument("--strict", action="store_true", help="exit with 1 when a known bug comes back")
    check_parser.set_defaults(handler=run_check)

    search_parser = commands.add_parser("search", parents=[common], help="find lessons about a topic")
    search_parser.add_argument("query", nargs="+")
    search_parser.add_argument("--top", type=int, default=5)
    search_parser.set_defaults(handler=run_search)

    list_parser = commands.add_parser("list", parents=[common], help="list the diary")
    list_parser.add_argument("--all-projects", action="store_true", help="list every project, not just this one")
    list_parser.set_defaults(handler=run_list)

    show_parser = commands.add_parser("show", parents=[common], help="show one card")
    show_parser.add_argument("card")
    show_parser.set_defaults(handler=run_show)

    forget_parser = commands.add_parser("forget", parents=[common], help="remove one card")
    forget_parser.add_argument("card")
    forget_parser.set_defaults(handler=run_forget)

    hook_parser = commands.add_parser("hook", parents=[common], help="install or remove the git hooks")
    hook_parser.add_argument("action", choices=["install", "uninstall"])
    hook_parser.add_argument("--strict", action="store_true", help="block the commit when a known bug comes back")
    hook_parser.add_argument("--no-learn", action="store_true", help="do not learn from commits named fix...")
    hook_parser.set_defaults(handler=run_hook)
    return parser


def make_llm(args: argparse.Namespace) -> Ollama:
    return Ollama(model=args.model, embed_model=args.embed_model)


def open_diary(settings: config.Settings) -> Diary:
    return Diary(settings.diary_path)


def require_repo(settings: config.Settings, path: Path) -> Path:
    if settings.repo is None:
        raise git.GitError(f"{path} is not inside a git repository")
    return settings.repo


def gather_notes(args: argparse.Namespace, repo: Path) -> list[Note]:
    notes = [Note("note", "", text) for text in args.note]
    notes += [Note("note", path.name, path.read_text(encoding="utf-8", errors="replace")) for path in args.note_file]
    notes += [github_note(repo, "issue", number) for number in args.issue]
    notes += [github_note(repo, "pr", number) for number in args.pr]
    return notes


def run_learn(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    repo = require_repo(settings, args.repo)
    llm = make_llm(args)
    notes = gather_notes(args, repo)
    diary = None if args.dry_run else open_diary(settings)
    style = Style.for_stream(sys.stdout)
    output = []
    for revision in args.revisions:
        fix = from_git(repo, revision, settings.project)
        fix.notes = notes
        learned = learn(llm, fix, args.origin)
        saved = diary is not None and (learned.is_bug_fix or args.force)
        warning = remember(diary, llm, learned.card) if saved else None
        output.append({"card": learned, "saved": saved, "warning": warning})
    if args.quiet:
        return 0
    if args.json:
        print(json.dumps([learned_json(item) for item in output], indent=2, ensure_ascii=False))
        return 0
    for item in output:
        learned = item["card"]
        print("\n".join(card_lines(learned.card, style, learned.seconds)))
        if not learned.is_bug_fix and not item["saved"]:
            print(
                style.yellow(
                    f"  Not saved: the model does not see a bug fix here ({learned.reason}). --force keeps it."
                )
            )
        elif args.dry_run:
            print(style.dim("  Dry run: not saved."))
        if item["warning"]:
            print(style.yellow(f"  Saved without its search vector: {item['warning']}"))
        print()
    return 0


def learned_json(item: dict) -> dict:
    learned = item["card"]
    card = learned.card
    return {
        "id": card.label if item["saved"] else None,
        "saved": item["saved"],
        "is_bug_fix": learned.is_bug_fix,
        "not_a_bug_fix_reason": learned.reason,
        "seconds": round(learned.seconds, 1),
        "project": card.project,
        "revision": card.revision,
        "fixed_at": card.fixed_at,
        "origin": card.origin,
        "model": card.model,
        **card.body(),
    }


def change_text(args: argparse.Namespace, repo: Path | None) -> str:
    if args.diff:
        if args.diff == "-":
            return sys.stdin.read()
        return Path(args.diff).read_text(encoding="utf-8", errors="replace")
    if repo is None:
        raise git.GitError(f"{args.repo} is not inside a git repository (use --diff FILE)")
    if args.staged:
        return git.staged_diff(repo)
    if args.base:
        return git.branch_diff(repo, args.base)
    if args.commit:
        return git.commit_diff(repo, args.commit)
    return git.worktree_diff(repo)


def run_check(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    files = diffs.parse(change_text(args, settings.repo))
    report = check(make_llm(args), open_diary(settings), files, settings.project, args.top)
    if args.json:
        print(json.dumps(report_json(report), indent=2, ensure_ascii=False))
    else:
        print("\n".join(report_lines(report, Style.for_stream(sys.stdout), args.all)))
    return 1 if args.strict and report.alerts else 0


def run_search(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    ranked = retrieve(make_llm(args), open_diary(settings), [" ".join(args.query)], args.top)
    print("\n".join(search_lines(ranked, Style.for_stream(sys.stdout))))
    return 0


def run_list(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    diary = open_diary(settings)
    print("\n".join(list_lines(diary.cards(None if args.all_projects else settings.project))))
    if not args.all_projects:
        others = [f"{name} ({count})" for name, count in diary.projects() if name != settings.project]
        if others:
            print(f"Other projects in this diary: {', '.join(others)}. --all-projects lists them.")
    return 0


def run_show(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    card = open_diary(settings).get(parse_label(args.card))
    if card is None:
        raise ValueError(f"no card {args.card}")
    print("\n".join(card_lines(card, Style.for_stream(sys.stdout))))
    return 0


def run_forget(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    card_id = parse_label(args.card)
    if not open_diary(settings).forget(card_id):
        raise ValueError(f"no card {args.card}")
    print(f"Forgot BUG-{card_id:04d}.")
    return 0


def run_hook(args: argparse.Namespace) -> int:
    settings = config.load(args.repo, args.project, args.memory)
    repo = require_repo(settings, args.repo)
    if args.action == "install":
        for path in hooks.install(repo, args.strict, not args.no_learn):
            print(f"Installed {path}")
    else:
        removed = hooks.uninstall(repo)
        print("\n".join(f"Removed {path}" for path in removed) or "No Bug Diary hook to remove.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (git.GitError, OllamaError, LearnError, GitHubError, hooks.HookError, ValueError, OSError) as error:
        print(f"bugdiary: {error}", file=sys.stderr)
        return 2
