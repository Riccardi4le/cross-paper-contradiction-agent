import argparse
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cpc-agent",
        description="Cross-Paper Contradiction Agent — finds and diagnoses conflicts between research papers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py paper1.pdf paper2.pdf paper3.pdf
  python main.py --topic "intermittent fasting" papers/*.pdf
  python main.py --model llama3.1:8b --output-dir ./results paper1.pdf paper2.pdf
        """,
    )
    parser.add_argument("papers", nargs="+", help="PDF files to analyze")
    parser.add_argument("--model", default=None, help="Groq model override (default: from .env or llama-3.3-70b-versatile)")
    parser.add_argument("--topic", default=None, help="Topic label for the contradiction map")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: ./output/)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.model:
        os.environ["GROQ_MODEL"] = args.model
    if args.output_dir:
        os.environ["CPC_OUTPUT_DIR"] = args.output_dir

    from cpc_agent.config import GROQ_MODEL, OUTPUT_DIR
    from cpc_agent.llm import health_check
    from cpc_agent.graph import build_graph

    console.print(Panel.fit(
        "[bold cyan]Cross-Paper Contradiction Agent[/bold cyan]\n"
        "Finds and diagnoses conflicts between research papers.",
        border_style="cyan",
    ))

    pdf_paths = []
    for p in args.papers:
        path = Path(p).resolve()
        if not path.exists():
            console.print(f"[red]File not found: {p}[/red]")
            sys.exit(1)
        if path.suffix.lower() != ".pdf":
            console.print(f"[yellow]Warning: {p} is not a PDF — skipping.[/yellow]")
            continue
        pdf_paths.append(str(path))

    if len(pdf_paths) < 2:
        console.print("[red]Need at least 2 PDF files to detect contradictions.[/red]")
        sys.exit(1)

    console.print(f"Model: [bold]{GROQ_MODEL}[/bold] (Groq)")
    console.print(f"Papers: [bold]{len(pdf_paths)}[/bold]")
    console.print(f"Output: [bold]{OUTPUT_DIR}[/bold]\n")

    health_check()

    topic = args.topic
    if not topic:
        names = [Path(p).stem[:20] for p in pdf_paths[:3]]
        topic = ", ".join(names) + (" ..." if len(pdf_paths) > 3 else "")

    initial_state = {
        "pdf_paths": pdf_paths,
        "topic": topic,
        "papers": [],
        "all_claims": [],
        "claims_per_paper": {},
        "clusters": [],
        "conflict_verdicts": {},
        "contradictions": [],
        "output_path": "",
        "errors": [],
    }

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]Done![/bold green]\n\n"
        f"Papers:          {len(final_state['papers'])}\n"
        f"Claims:          {len(final_state['all_claims'])}\n"
        f"Clusters:        {len(final_state['clusters'])}\n"
        f"Contradictions:  {len(final_state['contradictions'])}\n\n"
        f"Output: [bold]{final_state['output_path']}[/bold]",
        border_style="green",
    ))

    if final_state["errors"]:
        console.print(f"\n[yellow]{len(final_state['errors'])} non-fatal error(s) during run:[/yellow]")
        for err in final_state["errors"]:
            console.print(f"  [yellow]•[/yellow] {err}")


if __name__ == "__main__":
    main()
