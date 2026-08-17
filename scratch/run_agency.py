"""
Asheville AI — Full Agency Pipeline
Runs the complete automated business pipeline:
  1. Scrape new leads
  2. Audit lead websites
  3. Generate proposals
  4. Dispatch outreach emails
  5. Sync Google Sheets Command Center
  6. Check inbox for replies
  7. Send daily report to Thomas

Each step is isolated — one failure does NOT kill the rest of the pipeline.
All output is logged to agency_cron.log for debugging on headless servers.
"""

import subprocess
import sys
import os
import datetime
import logging
import argparse

# === Logging Setup ===
# Log to both console and file so output is visible in cron and SSH
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agency_cron.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def run_script(script_name, critical=False):
    """
    Run a pipeline script as a subprocess.
    
    Args:
        script_name: Python script filename to run
        critical: If True, pipeline stops on failure. If False, log error and continue.
    
    Returns:
        True if script succeeded, False if it failed.
    """
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    logger.info(f"[RUNNING] {script_name}...")

    if not os.path.exists(script_path):
        logger.error(f"[MISSING] {script_name} not found at {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per step
        )

        # Log stdout
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                logger.info(f"  [{script_name}] {line}")

        # Log stderr
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                logger.warning(f"  [{script_name} STDERR] {line}")

        if result.returncode != 0:
            logger.error(f"[FAILED] {script_name} exited with code {result.returncode}")
            if critical:
                logger.error(f"[ABORT] {script_name} is critical. Stopping pipeline.")
                sys.exit(1)
            return False

        logger.info(f"[FINISHED] {script_name}")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"[TIMEOUT] {script_name} exceeded 5-minute timeout")
        return False
    except Exception as e:
        logger.error(f"[ERROR] {script_name} failed: {e}")
        if critical:
            sys.exit(1)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-sheet", action="store_true", help="Opt in to the live Google Sheet write step.")
    args = parser.parse_args()
    start_time = datetime.datetime.now()
    logger.info("=" * 60)
    logger.info("  ASHEVILLE AI — FULL AGENCY PIPELINE")
    logger.info(f"  Run started: {start_time.isoformat()}")
    logger.info("=" * 60)

    results = {}

    # Stage private intake records as Atlas change packets. This step never
    # writes Google Sheets or performs an external business action.
    results["process_intake_queue"] = run_script("process_intake_queue.py", critical=False)

    # 1. Scrape New Leads (non-critical — has fallback targets)
    results["lead_scraper"] = run_script("lead_scraper.py", critical=False)

    # 2. Audit Leads & Extract Contacts (non-critical — has fallback targets)
    results["batch_audit_scanner"] = run_script("batch_audit_scanner.py", critical=False)

    # 3. Generate Proposals
    results["proposal_engine"] = run_script("proposal_engine.py", critical=False)

    # External outreach is intentionally excluded. Run email_dispatcher.py separately;
    # live sending also requires --execute and exact G2/G3 approval records.
    logger.info("[SAFE DEFAULT] Outreach dispatch skipped; use the gated dispatcher separately.")

    # 5. Sync Google Sheets Command Center
    if args.sync_sheet:
        results["live_sheets_sync"] = run_script("live_sheets_sync.py", critical=False)
    else:
        logger.info("[SAFE DEFAULT] Live Sheet sync skipped; pass --sync-sheet to opt in.")

    # 6. Check Inbox for Replies
    results["inbox_monitor"] = run_script("inbox_monitor.py", critical=False)

    # Email reports are external actions and are intentionally not automated here.
    logger.info("[SAFE DEFAULT] Daily report email skipped; run its gated workflow separately.")

    # === Summary ===
    elapsed = datetime.datetime.now() - start_time
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    logger.info("")
    logger.info("=" * 60)
    logger.info("  PIPELINE COMPLETE")
    logger.info(f"  Duration: {elapsed}")
    logger.info(f"  Results: {passed} passed, {failed} failed")
    for name, ok in results.items():
        status = "[PASS]" if ok else "[FAIL]"
        logger.info(f"    {status}  {name}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
