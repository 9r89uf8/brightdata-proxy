"""
BrightData Proxy Test - Install Bright Data CA + Selenium-Wire CA (idempotent) + Headless Verification

Run modes:
- In AWS ECS/Fargate: inject certs via SSM -> env vars:
    BRIGHTDATA_CA_B64           (base64 of PEM)  OR BRIGHTDATA_CA_PEM (raw PEM)
    SELENIUMWIRE_CA_B64         (base64 of PEM)  OR SELENIUMWIRE_CA_PEM (raw PEM)
  Task still needs BRIGHTDATA_PROXY from SSM.

- Locally: place 'brightdata_ca.crt' next to this script (optional for Selenium-Wire;
  it can be extracted automatically if not provided via env).

Requirements:
  pip install python-dotenv selenium-wire undetected-chromedriver
"""

import os
import sys
import platform
import subprocess
import hashlib
from pathlib import Path

# --- third-party ---
try:
    from dotenv import load_dotenv
except ImportError:
    print("[ERROR] Install: pip install python-dotenv")
    sys.exit(1)

try:
    # Use selenium-wire + undetected-chromedriver
    # We import uc directly and pass seleniumwire_options into uc.Chrome()
    import seleniumwire.undetected_chromedriver as uc
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

load_dotenv()

# ---------- Config ----------
SCRIPT_DIR = Path(__file__).resolve().parent
BD_CERT_FILE = SCRIPT_DIR / "brightdata_ca.crt"
SW_CERT_FILE = SCRIPT_DIR / "seleniumwire_ca.crt"  # will be written from env or extracted
# Use a fresh profile directory to avoid cached connections
import time
PROFILE_DIR = SCRIPT_DIR / f"chrome_profile_brightdata_{int(time.time())}"

EXPECTED_BD_CA_NAME = "Bright Data"
EXPECTED_SW_CA_NAME = "Selenium Wire"

BRIGHTDATA_PROXY = os.getenv("BRIGHTDATA_PROXY")


# ---------- Utils ----------
def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}")
    sys.exit(code)


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_cert_from_env(path: Path, b64_env: str, pem_env: str, label: str) -> bool:
    """
    If 'path' doesn't exist, try to create it from base64 or raw-PEM env vars.
    Returns True if we wrote the file.
    """
    if path.exists():
        return False
    b64 = os.getenv(b64_env)
    pem = os.getenv(pem_env)
    if b64:
        import base64
        try:
            path.write_bytes(base64.b64decode(b64))
            print(f"[INFO] Wrote {label} from {b64_env} to: {path}")
            return True
        except Exception as e:
            print(f"[WARN] Failed to decode {b64_env}: {e}")
    if pem:
        try:
            path.write_text(pem, encoding="utf-8")
            print(f"[INFO] Wrote {label} from {pem_env} to: {path}")
            return True
        except Exception as e:
            print(f"[WARN] Failed to write {pem_env}: {e}")
    return False


# ---------- Local CA presence ----------
def ensure_local_bd_ca():
    """
    Ensure Bright Data CA file exists. Prefer env -> file; otherwise require local file.
    """
    wrote = write_cert_from_env(
        BD_CERT_FILE, "BRIGHTDATA_CA_B64", "BRIGHTDATA_CA_PEM", "Bright Data CA"
    )
    if not BD_CERT_FILE.exists():
        die(f"Bright Data CA not found (env or file). Expect either BRIGHTDATA_CA_B64/PEM or file: {BD_CERT_FILE}")
    if wrote:
        print(f"[INFO] Found Bright Data CA (from env): {BD_CERT_FILE}")
    else:
        print(f"[INFO] Found Bright Data CA: {BD_CERT_FILE}")


# ---------- OS helpers ----------
def is_windows(): return platform.system().lower() == "windows"
def is_macos():   return platform.system().lower() == "darwin"
def is_linux():   return platform.system().lower() == "linux"


# ---------- Install to trust store (idempotent) ----------
# Linux (Chrome uses NSS in ~/.pki/nssdb)
def nss_list() -> str:
    nssdb = os.path.expanduser("~/.pki/nssdb")
    try:
        return subprocess.check_output(
            ["certutil", "-d", f"sql:{nssdb}", "-L"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", "ignore")
    except Exception:
        return ""


def nss_add(nickname: str, crt_path: Path):
    nssdb = os.path.expanduser("~/.pki/nssdb")
    os.makedirs(nssdb, exist_ok=True)
    try:
        subprocess.run(
            ["certutil", "-d", f"sql:{nssdb}", "-A",
             "-t", "C,,", "-n", nickname, "-i", str(crt_path)],
            check=True
        )
    except FileNotFoundError:
        die("certutil (libnss3-tools) not found. Install it (e.g., sudo apt-get install libnss3-tools).")


# macOS (System keychain; needs sudo once)
def macos_has_cert(name_substr: str) -> bool:
    try:
        out = subprocess.check_output(
            ["security", "find-certificate", "-a", "-c", name_substr, "/Library/Keychains/System.keychain"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", "ignore")
        return name_substr in out
    except Exception:
        return False


def macos_add_cert(crt_path: Path):
    subprocess.run(
        ["sudo", "security", "add-trusted-cert", "-d",
         "-r", "trustRoot", "-k", "/Library/Keychains/System.keychain", str(crt_path)],
        check=True
    )


# Windows (CurrentUser Root; no admin needed)
def win_store_contains(name_substr: str) -> bool:
    try:
        out = subprocess.check_output(
            ["certutil", "-user", "-store", "Root"],
            stderr=subprocess.DEVNULL, shell=True
        ).decode("utf-8", "ignore")
        return name_substr.lower() in out.lower()
    except Exception:
        return False


def win_add_cert_user(crt_path: Path):
    subprocess.run(
        ["certutil", "-user", "-addstore", "-f", "Root", str(crt_path)],
        check=True, shell=True
    )


# Bright Data CA install
def install_bd_ca_idempotent():
    if is_linux():
        if EXPECTED_BD_CA_NAME in nss_list():
            print("[INFO] Bright Data CA already in NSS DB — skipping.")
        else:
            nss_add(EXPECTED_BD_CA_NAME, BD_CERT_FILE)
            print("[INFO] Installed Bright Data CA into NSS DB.")
    elif is_macos():
        if macos_has_cert(EXPECTED_BD_CA_NAME):
            print("[INFO] Bright Data CA already in macOS System Keychain — skipping.")
        else:
            macos_add_cert(BD_CERT_FILE)
            print("[INFO] Installed Bright Data CA into macOS System Keychain.")
    elif is_windows():
        if win_store_contains(EXPECTED_BD_CA_NAME):
            print("[INFO] Bright Data CA already in CurrentUser Root — skipping.")
        else:
            win_add_cert_user(BD_CERT_FILE)
            print("[INFO] Installed Bright Data CA into Windows CurrentUser Root.")
    else:
        die("Unsupported OS for Bright Data CA install.")


# Selenium-Wire CA: prefer env; else extract; then install
def ensure_sw_ca_file():
    wrote = write_cert_from_env(
        SW_CERT_FILE, "SELENIUMWIRE_CA_B64", "SELENIUMWIRE_CA_PEM", "Selenium-Wire CA"
    )
    if SW_CERT_FILE.exists():
        if wrote:
            print(f"[INFO] Selenium-Wire CA present (from env): {SW_CERT_FILE}")
        else:
            print(f"[INFO] Selenium-Wire CA present: {SW_CERT_FILE}")
        return

    # Fallback: extract from selenium-wire
    print("[INFO] Extracting Selenium-Wire CA...")
    try:
        subprocess.run([sys.executable, "-m", "seleniumwire", "extractcert"],
                       check=True, cwd=str(SCRIPT_DIR))
    except subprocess.CalledProcessError as e:
        die(f"Failed to extract Selenium-Wire CA: {e}")

    ca_in_cwd = SCRIPT_DIR / "ca.crt"
    if ca_in_cwd.exists():
        ca_in_cwd.replace(SW_CERT_FILE)
        print(f"[INFO] Saved Selenium-Wire CA to: {SW_CERT_FILE}")
    else:
        die("Could not find extracted Selenium-Wire CA (expected 'ca.crt').")


def install_sw_ca_idempotent():
    if is_linux():
        if EXPECTED_SW_CA_NAME in nss_list():
            print("[INFO] Selenium-Wire CA already in NSS DB — skipping.")
        else:
            nss_add(EXPECTED_SW_CA_NAME, SW_CERT_FILE)
            print("[INFO] Installed Selenium-Wire CA into NSS DB.")
    elif is_macos():
        if macos_has_cert(EXPECTED_SW_CA_NAME):
            print("[INFO] Selenium-Wire CA already in macOS System Keychain — skipping.")
        else:
            macos_add_cert(SW_CERT_FILE)
            print("[INFO] Installed Selenium-Wire CA into macOS System Keychain.")
    elif is_windows():
        if win_store_contains(EXPECTED_SW_CA_NAME):
            print("[INFO] Selenium-Wire CA already in CurrentUser Root — skipping.")
        else:
            win_add_cert_user(SW_CERT_FILE)
            print("[INFO] Installed Selenium-Wire CA into Windows CurrentUser Root.")
    else:
        die("Unsupported OS for Selenium-Wire CA install.")


# ---------- Main proxy test ----------
def run_test(headless: bool = True):
    if not BRIGHTDATA_PROXY:
        die("BRIGHTDATA_PROXY not set (in .env locally or injected via ECS task secrets)")
    
    print(f"[DEBUG] Using proxy: {BRIGHTDATA_PROXY}")
    print(f"[DEBUG] Proxy host extracted from URL...")

    seleniumwire_options = {
        "proxy": {
            "http": BRIGHTDATA_PROXY,
            "https": BRIGHTDATA_PROXY,
            "no_proxy": "localhost,127.0.0.1",
        },
        # Upstream (Bright Data) verification off for Selenium-Wire's local proxy:
        "verify_ssl": False,
        # Enable capture to ensure proxy is properly used:
        "disable_capture": False,
        "suppress_connection_errors": True,
    }

    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument(f"--user-data-dir={str(PROFILE_DIR)}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if headless:
        chrome_options.add_argument("--headless=new")

    print(f"[INFO] Starting Chrome with profile: {PROFILE_DIR} (headless={headless})")
    driver = uc.Chrome(
        options=chrome_options,
        seleniumwire_options=seleniumwire_options,
        version_main=138,
    )

    # 1) Confirm IP is proxied
    print("\n" + "="*60)
    print("[INFO] Checking if proxy is working...")
    driver.get("https://api.ipify.org?format=text")
    ip_addr = driver.find_element("tag name", "body").text.strip()
    print(f"[PROXY CHECK] Current IP Address: {ip_addr}")
    print(f"[PROXY CHECK] If this is your real IP, the proxy is NOT working!")
    print(f"[PROXY CHECK] If this is a Bright Data IP, the proxy IS working!")
    print("="*60 + "\n")

    # 2) Visit an HTTPS site
    driver.get("https://www.google.com")
    print(f"[INFO] Navigated to: {driver.current_url}")

    # 3) Quick signals from the page
    proto = driver.execute_script("return location.protocol")
    is_secure_ctx = driver.execute_script("return window.isSecureContext === true")
    title = driver.title
    print(f"[INFO] protocol: {proto}, isSecureContext: {is_secure_ctx}, title: {title!r}")

    # Fail fast if Chrome shows a TLS interstitial
    if "Your connection is not private" in title or "Privacy error" in title:
        driver.quit()
        die("Chrome shows TLS interstitial. Check CA installs & proxy.")

    # If HTTPS + secure context are true, that’s our primary success signal now
    if not (proto == "https:" and is_secure_ctx):
        driver.quit()
        die("Page is not a secure HTTPS context. Check CA installs & proxy.")

    # Extra sanity: CORS-agnostic fetch (no-cors) should resolve if TLS is OK
    ok_fetch = driver.execute_async_script("""
      const done = arguments[0];
      fetch('https://example.com', {mode: 'no-cors', cache: 'no-store'})
        .then(() => done(true))
        .catch(() => done(false));
    """)
    print(f"[INFO] example.com fetch ok: {ok_fetch}")

    if not ok_fetch:
        driver.quit()
        die("Secondary HTTPS fetch failed; likely a certificate issue on proxy/chain.")

    print("[RESULT] ✅ Proxy + CA trust validated (HTTPS secure context + cross-origin fetch succeeded).")
    print("[INFO] Browser is now at Google.com - keeping it open for interaction...")
    
    # Keep browser open for user interaction
    input("Press Enter to close the browser...")
    driver.quit()


if __name__ == "__main__":
    # Ensure CA files exist (prefer env → file)
    ensure_local_bd_ca()
    ensure_sw_ca_file()

    # Install into system/user trust stores (idempotent)
    install_bd_ca_idempotent()
    install_sw_ca_idempotent()

    # Run the test
    run_test(headless=False)
