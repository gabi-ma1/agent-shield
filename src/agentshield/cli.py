import argparse
import sys

from rich.console import Console
from rich.table import Table

from .attacker import GOALS, run_attack, run_reverification
from .config import Config
from .harden import propose_hardening
from .nebius_client import NebiusClient
from .recon import run_recon
from .report import PipelineResult, save_report
from .target import Target

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentshield")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the full AgentShield pipeline")
    run_parser.add_argument("--target-url", required=True, help="Target agent HTTP endpoint")
    run_parser.add_argument(
        "--goal",
        choices=list(GOALS),
        default="system_prompt_leak",
        help="Attack goal to pursue",
    )
    run_parser.add_argument("--max-turns", type=int, default=8)
    run_parser.add_argument("--output-dir", default="reports")
    run_parser.add_argument(
        "--system-prompt-file",
        default=None,
        help=(
            "Path to a text file with the target's known system prompt (only if you own "
            "the target and know it). Enables a full hardened-prompt rewrite instead of a "
            "generic addendum, and is required for the Re-Verification stage."
        ),
    )
    run_parser.add_argument(
        "--skip-harden",
        action="store_true",
        help="Stop after the attack/verification stages; skip hardening and re-verification.",
    )

    args = parser.parse_args()

    if args.command == "run":
        _run(args)


def _print_session_table(title: str, session) -> None:
    table = Table(title=title)
    table.add_column("Turn")
    table.add_column("Succeeded")
    table.add_column("Severity")
    table.add_column("Reason")
    for turn in session.turns:
        table.add_row(
            str(turn.turn_number),
            "yes" if turn.verdict.succeeded else "no",
            str(turn.verdict.severity),
            turn.verdict.reason,
        )
    console.print(table)


def _run(args: argparse.Namespace) -> None:
    try:
        config = Config.from_env()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    client = NebiusClient(config)
    target = Target(args.target_url)

    original_system_prompt = None
    if args.system_prompt_file:
        original_system_prompt = open(args.system_prompt_file, encoding="utf-8").read()

    console.print(f"[bold]AgentShield[/bold] — target: [cyan]{args.target_url}[/cyan]")

    console.print("[dim]Stage 1: Recon...[/dim]")
    recon = run_recon(client, target)
    console.print(f"  {recon.summary}")

    console.print(
        f"[dim]Stage 2-3: Adaptive attack + verification "
        f"(goal={args.goal}, max {args.max_turns} turns)...[/dim]"
    )
    attack_session = run_attack(
        client,
        target,
        args.goal,
        max_turns=args.max_turns,
        recon_summary=recon.summary,
    )
    _print_session_table("Attack summary", attack_session)

    hardening = None
    reverify_session = None

    if attack_session.succeeded and not args.skip_harden:
        console.print("[dim]Stage 4: Proposing hardening...[/dim]")
        hardening = propose_hardening(
            client,
            GOALS[args.goal],
            attack_session,
            original_system_prompt=original_system_prompt,
        )
        console.print(f"  {hardening.rationale}")
        if hardening.code_patch:
            console.print(
                f"[dim]  Also generated a {hardening.code_patch_language} code patch "
                f"(see the report).[/dim]"
            )

        if hardening.hardened_system_prompt:
            console.print("[dim]Stage 5: Re-verifying against hardened target...[/dim]")
            reverify_session = run_reverification(
                client,
                args.target_url,
                args.goal,
                hardening.hardened_system_prompt,
                max_turns=args.max_turns,
                recon_summary=recon.summary,
            )
            _print_session_table("Re-verification summary", reverify_session)
        else:
            console.print(
                "[yellow]  No known original system prompt was supplied "
                "(--system-prompt-file) — generated a generic guardrail addendum instead "
                "and skipped re-verification.[/yellow]"
            )
    elif not attack_session.succeeded:
        console.print(
            "[green]No successful attack found in this run — nothing to harden.[/green]"
        )

    result = PipelineResult(
        target_url=args.target_url,
        recon=recon,
        attack_session=attack_session,
        hardening=hardening,
        reverify_session=reverify_session,
    )
    md_path, json_path = save_report(result, args.output_dir)
    console.print(f"[green]Report saved to {md_path} and {json_path}[/green]")


if __name__ == "__main__":
    main()
