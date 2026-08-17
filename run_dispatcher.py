import os
import sys
import subprocess
import datetime
import logging

LOG_FILE = "agency_cron.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

def get_tenants():
    try:
        import yaml
        with open("tenants.yaml", "r") as f:
            data = yaml.safe_load(f)
            return list(data.get("tenants", {}).keys())
    except Exception as e:
        logger.warning(f"Could not load tenants.yaml: {e}. Defaulting to 'asheville'.")
        return ["asheville"]

def run_script(script_name, args_list=None):
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
    # kills the reader thread, silently discarding the whole step's output — which
    # on this path is the record of what was sent to a prospect.
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
            timeout=300,
            env=child_env,
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                logger.info(f"  [{script_name}] {line}")

        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                logger.warning(f"  [{script_name} STDERR] {line}")

        if result.returncode != 0:
            logger.error(f"[FAILED] {cmd_str} exited with code {result.returncode}")
            return False

        logger.info(f"[FINISHED] {cmd_str}")
        return True

    except Exception as e:
        logger.error(f"[ERROR] {cmd_str} failed: {e}")
        return False

def main():
    start_time = datetime.datetime.now()
    logger.info("=" * 60)
    logger.info("  MULTI-CITY AI - OUTREACH DISPATCHER")
    logger.info(f"  Run started: {start_time.isoformat()}")
    logger.info("=" * 60)

    tenants = get_tenants()
    results = {}

    for tenant in tenants:
        logger.info("-" * 40)
        logger.info(f"  DISPATCHING TENANT: {tenant.upper()}")
        logger.info("-" * 40)
        
        t_args = ["--execute", "--tenant", tenant]
        results[tenant] = run_script("email_dispatcher.py", t_args)

    logger.info("=" * 60)
    logger.info("  DISPATCH COMPLETE")
    for tenant, ok in results.items():
        status = "[PASS]" if ok else "[FAIL]"
        logger.info(f"    {status}  {tenant.upper()}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
