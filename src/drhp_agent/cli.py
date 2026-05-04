"""CLI entry point for the DRHP Capital Structure Agent.

Usage:
    python -m drhp_agent --input data/ --output out/
"""
from __future__ import annotations
import argparse, logging, sys

log = logging.getLogger("drhp_agent")


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="drhp-agent",
        description="DRHP Capital Structure Drafting Agent — extract authorised share capital history from regulatory filings.",
    )
    parser.add_argument("--input", "-i", required=True, help="Path to data directory with SH-7 folders")
    parser.add_argument("--output", "-o", default="out", help="Output directory (default: out/)")
    parser.add_argument("--company", "-c", default="Acme Analytics Private Limited", help="Company name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    from .ingest import ingest_folder
    from .classify import classify_documents
    from .extract import extract_events
    from .reconcile import reconcile
    from .render import write_outputs
    from .llm import get_token_usage

    log.info("=== DRHP Capital Structure Agent ===")
    log.info("Input:  %s", args.input)
    log.info("Output: %s", args.output)

    # Stage 1 — Ingest
    log.info("Stage 1: Ingesting documents...")
    documents = ingest_folder(args.input)
    log.info("  → %d documents parsed", len(documents))

    # Stage 2 — Classify
    log.info("Stage 2: Classifying documents...")
    classified = classify_documents(documents)
    for c in classified:
        log.info("  %s → %s (conf=%.2f)", c.doc.id, c.doc_type.value, c.confidence)

    # Stage 3 — Extract
    log.info("Stage 3: Extracting structured data...")
    events = extract_events(classified)
    log.info("  → %d events extracted", len(events))

    # Stage 4 — Reconcile
    log.info("Stage 4: Reconciling & validating...")
    events = reconcile(events)
    total_flags = sum(len(e.flags) for e in events)
    error_flags = sum(1 for e in events for f in e.flags if f.severity.value == "error")
    log.info("  → %d flags (%d errors)", total_flags, error_flags)

    # Stage 5 — Render
    log.info("Stage 5: Rendering outputs...")
    write_outputs(events, args.output, args.company)

    # Token usage
    usage = get_token_usage()
    log.info("Token usage: %s", usage)

    # Exit code
    if error_flags > 0:
        log.warning("Exiting with code 1 due to %d error-level flags", error_flags)
        sys.exit(1)
    else:
        log.info("Done. All outputs in %s/", args.output)
        sys.exit(0)


if __name__ == "__main__":
    main()
