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

import os
from dotenv import load_dotenv
if os.path.exists("/secrets/env/.env"):
    load_dotenv("/secrets/env/.env")
else:
    load_dotenv()
import subprocess
import sys
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


def run_script(script_name, args_list=None, critical=False):
    """
    Run a pipeline script as a subprocess.
    """
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    cmd = [sys.executable, script_path]
    if args_list:
        cmd.extend(args_list)
        
    cmd_str = " ".join(cmd)
    logger.info(f"[RUNNING] {cmd_str}...")

    if not os.path.exists(script_path):
        logger.error(f"[MISSING] {script_name} not found at {script_path}")
        return False

    # Pin both ends of the pipe to UTF-8. Without this the parent decodes child
    # output with the locale codec (cp1252 on Windows) and a single non-ASCII byte
    # kills the reader thread, silently discarding the whole step's output.
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1200,  # 20 minute timeout per step
            env=child_env,
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
            logger.error(f"[FAILED] {cmd_str} exited with code {result.returncode}")
            if critical:
                logger.error(f"[ABORT] {script_name} is critical. Stopping pipeline.")
                sys.exit(1)
            return False

        logger.info(f"[FINISHED] {cmd_str}")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"[TIMEOUT] {cmd_str} exceeded 20-minute timeout")
        return False
    except Exception as e:
        logger.error(f"[ERROR] {cmd_str} failed: {e}")
        if critical:
            sys.exit(1)
        return False

def get_tenants():
    try:
        import yaml
        with open("tenants.yaml", "r") as f:
            data = yaml.safe_load(f)
            return list(data.get("tenants", {}).keys())
    except Exception as e:
        logger.warning(f"Could not load tenants.yaml: {e}. Defaulting to 'asheville'.")
        return ["asheville"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-sheet", action="store_true", help="Opt in to the live Google Sheet write step.")
    parser.add_argument("--stage-approvals", action="store_true",
                        help="Queue outreach decisions in the Approval Queue. Sends nothing.")
    args = parser.parse_args()
    start_time = datetime.datetime.now()
    logger.info("=" * 60)
    logger.info("  MULTI-CITY AI — FULL AGENCY PIPELINE")
    logger.info(f"  Run started: {start_time.isoformat()}")
    logger.info("=" * 60)

    results = {}
    tenants = get_tenants()

    # Prove the environment can actually read and write before spending half an
    # hour scraping for it. Non-critical on purpose: a failure here should be
    # loudly visible in the summary, not silently abort the whole run.
    results["smoke_test"] = run_script("smoke_test.py", ["--tenant", tenants[0]], critical=False)
    if not results["smoke_test"]:
        logger.error("[SMOKE] Environment checks FAILED. The run continues, but "
                     "treat any later [PASS] with suspicion.")

    # Global steps
    results["process_intake_queue"] = run_script("process_intake_queue.py", critical=False)

    for tenant in tenants:
        logger.info("-" * 40)
        logger.info(f"  PROCESSING TENANT: {tenant.upper()}")
        logger.info("-" * 40)
        
        t_args = ["--tenant", tenant]

        # 1. Scrape New Leads
        results[f"lead_scraper_{tenant}"] = run_script("lead_scraper.py", t_args, critical=False)

        # 2. Audit Leads & Extract Contacts
        results[f"batch_audit_scanner_{tenant}"] = run_script("batch_audit_scanner.py", t_args, critical=False)

        # 3. Generate Proposals
        results[f"proposal_engine_{tenant}"] = run_script("proposal_engine.py", t_args, critical=False)

        # 4. Ask the owner for permission to send. This runs the dispatcher WITHOUT
        #    --execute, so it sends nothing: it only writes Pending rows into the
        #    Approval Queue with the exact message hash attached. Without this step
        #    the queue stays empty forever and no outreach can ever be approved,
        #    which is the gap between "the pipeline ran" and "the business operates".
        if args.stage_approvals:
            results[f"stage_approvals_{tenant}"] = run_script(
                "email_dispatcher.py", t_args + ["--stage-only"], critical=False)
        else:
            logger.info(f"[SAFE DEFAULT] Approval staging skipped for {tenant}; "
                        "pass --stage-approvals to opt in.")

        # 5. Sync Google Sheets Command Center
        if args.sync_sheet:
            results[f"live_sheets_sync_{tenant}"] = run_script("live_sheets_sync.py", t_args, critical=False)
        else:
            logger.info(f"[SAFE DEFAULT] Live Sheet sync skipped for {tenant}; pass --sync-sheet to opt in.")

    # Global steps at the end
    if args.sync_sheet:
        results["sync_master_sheet"] = run_script("sync_master_sheet.py", critical=False)
        
    logger.info("[SAFE DEFAULT] Outreach SENDING skipped; the dispatcher above ran in "
                "dry-run and only queued decisions. Sending requires --execute, by hand.")
    results["inbox_monitor"] = run_script("inbox_monitor.py", critical=False)
    results["daily_reporter"] = run_script("daily_reporter.py", critical=False)

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
