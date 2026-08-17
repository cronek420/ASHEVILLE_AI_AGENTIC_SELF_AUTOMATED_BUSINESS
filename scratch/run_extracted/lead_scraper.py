import json
import time
import urllib.parse
import logging
import argparse
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SERVICES = [
    "plumber", "roofer", "electrician", "hvac", "landscaping",
    "restaurant", "spa", "tree service", "pressure washing",
    "pest control", "dentist", "auto repair"
]

# Hardcoded fallback targets from known Asheville businesses.
# Used when DuckDuckGo scraping fails (rate limits, network errors, etc.)
# We will use this globally for safety if live scrape fails.
FALLBACK_TARGETS = [
    {"domain": "wardph.com", "url": "https://wardph.com", "name": "Ward Plumbing Heating and Air"},
    {"domain": "whiteandwilliams.com", "url": "https://whiteandwilliams.com", "name": "White and Williams Co"},
    {"domain": "ashevilleelectrician.com", "url": "https://ashevilleelectrician.com", "name": "Asheville Electrician"},
    {"domain": "ashevilletreeservice.com", "url": "https://ashevilletreeservice.com", "name": "Asheville Tree Service"},
    {"domain": "bakerroofing.com", "url": "https://bakerroofing.com", "name": "Baker Roofing"},
    {"domain": "ashevillepressurewashing.com", "url": "https://ashevillepressurewashing.com", "name": "Asheville Pressure Washing"},
    {"domain": "ashevillelawncare.com", "url": "https://ashevillelawncare.com", "name": "Asheville Lawn Care"},
    {"domain": "ashevillepestcontrol.com", "url": "https://ashevillepestcontrol.com", "name": "Asheville Pest Control"},
    {"domain": "ashevillefamilydentistry.com", "url": "https://ashevillefamilydentistry.com", "name": "Asheville Family Dentistry"},
    {"domain": "wncsoftwash.com", "url": "https://wncsoftwash.com", "name": "WNC Soft Wash"},
    {"domain": "mostlyfrenchauto.com", "url": "https://mostlyfrenchauto.com", "name": "Mostly French Auto"},
    {"domain": "experttransmissionasheville.com", "url": "https://experttransmissionasheville.com", "name": "Expert Transmission Asheville"},
    {"domain": "organicmechanic.com", "url": "https://organicmechanic.com", "name": "Organic Mechanic"},
    {"domain": "apexbugs.com", "url": "https://apexbugs.com", "name": "Apex Pest Control"},
    {"domain": "gibsonpest.com", "url": "https://gibsonpest.com", "name": "Gibson Pest Control"},
    {"domain": "gillespiedental.com", "url": "https://gillespiedental.com", "name": "Gillespie Dental"},
    {"domain": "mountainscapenc.com", "url": "https://mountainscapenc.com", "name": "Mountainscape NC"},
    {"domain": "lawnscapesasheville.com", "url": "https://lawnscapesasheville.com", "name": "Lawnscapes Asheville"},
    {"domain": "mountainpressurewash.com", "url": "https://mountainpressurewash.com", "name": "Mountain Pressure Wash"},
]

IGNORE_DOMAINS = [
    "yelp.com", "angi.com", "bbb.org", "facebook.com", "instagram.com",
    "yellowpages.com", "homeadvisor.com", "thumbtack.com", "linkedin.com",
    "tripadvisor.com", "houzz.com", "expertise.com", "mapquest.com",
    "zoominfo.com", "google.com", "apple.com", "wikipedia.org",
]

def load_tenant_config(tenant_id):
    try:
        with open("tenants.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data.get("tenants", {}).get(tenant_id)
    except FileNotFoundError:
        return None

def scrape_leads(tenant):
    all_domains = set()
    leads = []
    
    tenant_config = load_tenant_config(tenant)
    if not tenant_config:
        logger.warning(f"Tenant '{tenant}' not found in tenants.yaml. Defaulting to Asheville NC.")
        location = "Asheville NC"
    else:
        location = tenant_config.get("location", "Asheville NC")

    queries = [f"{location} {service}" for service in SERVICES]

    logger.info(f"Scraping leads for {tenant} ({location}) across {len(queries)} queries...")

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo-search package not installed. Using fallback targets.")
        _save_leads(FALLBACK_TARGETS, tenant)
        return

    max_retries = 2
    with DDGS() as ddgs:
        for query in queries:
            logger.info(f"Searching: {query}")
            for attempt in range(max_retries + 1):
                try:
                    results = list(ddgs.text(query, max_results=20))
                    time.sleep(3)  # Pace requests to avoid rate limits
                    for r in results:
                        url = r.get("href", "")
                        title = r.get("title", "")
                        if url:
                            parsed = urllib.parse.urlparse(url)
                            domain = parsed.netloc.replace("www.", "")
                            if domain and not any(ign in domain for ign in IGNORE_DOMAINS):
                                if domain not in all_domains:
                                    all_domains.add(domain)
                                    leads.append({
                                        "domain": domain,
                                        "url": url,
                                        "name": title.split("-")[0].split("|")[0].strip()
                                    })
                    break  # Success, move to next query
                except Exception as e:
                    if attempt < max_retries:
                        wait_time = 5 * (attempt + 1)
                        logger.warning(f"Attempt {attempt+1} failed for '{query}': {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries+1} attempts failed for '{query}': {e}")

    if len(leads) == 0:
        logger.warning(f"Live scraping returned 0 leads. Falling back to {len(FALLBACK_TARGETS)} hardcoded targets.")
        leads = FALLBACK_TARGETS

    _save_leads(leads, tenant)


def _save_leads(leads, tenant):
    logger.info(f"Total unique leads: {len(leads)}")
    filename = f"scraped_leads_{tenant}.json"
    with open(filename, "w") as f:
        json.dump(leads, f, indent=2)
    logger.info(f"Saved leads to {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="asheville", help="Tenant ID (e.g., asheville, charlotte)")
    args = parser.parse_args()
    
    scrape_leads(args.tenant)
