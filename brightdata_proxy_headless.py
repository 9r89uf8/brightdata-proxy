"""
BrightData Proxy Test - Install Bright Data CA + Selenium-Wire CA (idempotent) + Headless Verification

Requirements:
  pip install python-dotenv selenium-wire undetected-chromedriver

.env must include:
  BRIGHTDATA_PROXY=http://user:pass@brd.superproxy.io:33335

Place Bright Data CA file next to this script as:
  brightdata_ca.crt
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
    import seleniumwire.undetected_chromedriver as uc
except ImportError:
    print("[ERROR] Install: pip install selenium-wire undetected-chromedriver")
    sys.exit(1)

load_dotenv()

# ---------- Config ----------
SCRIPT_DIR = Path(__file__).resolve().parent
BD_CERT_FILE = SCRIPT_DIR / "brightdata_ca.crt"
SW_CERT_FILE = SCRIPT_DIR / "seleniumwire_ca.crt"  # we'll extract or copy here
PROFILE_DIR = SCRIPT_DIR / "chrome_profile_brightdata"

EXPECTED_BD_CA_NAME = "Bright Data"
EXPECTED_SW_CA_NAME = "Selenium Wire"

BRIGHTDATA_PROXY = os.getenv("BRIGHTDATA_PROXY")


# ---------- Utils ----------
def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}")
    sys.exit(code)


# ---------- Local CA presence ----------
def ensure_local_bd_ca():
    if not BD_CERT_FILE.exists():
        die(f"Bright Data CA not found next to script: {BD_CERT_FILE}")
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
        return subprocess.check_output(["certutil", "-d", f"sql:{nssdb}", "-L"],
                                       stderr=subprocess.DEVNULL).decode("utf-8", "ignore")
    except Exception:
        return ""

def nss_add(nickname: str, crt_path: Path):
    nssdb = os.path.expanduser("~/.pki/nssdb")
    os.makedirs(nssdb, exist_ok=True)
    try:
        subprocess.run(["certutil", "-d", f"sql:{nssdb}", "-A",
                        "-t", "C,,", "-n", nickname, "-i", str(crt_path)],
                       check=True)
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
    subprocess.run(["sudo", "security", "add-trusted-cert", "-d",
                    "-r", "trustRoot", "-k", "/Library/Keychains/System.keychain", str(crt_path)],
                   check=True)

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

# Selenium-Wire CA: extract and install
def ensure_sw_ca_file():
    if SW_CERT_FILE.exists():
        print(f"[INFO] Selenium-Wire CA present: {SW_CERT_FILE}")
        return
    # Try CLI extractor; most versions write 'ca.crt' in CWD
    print("[INFO] Extracting Selenium-Wire CA...")
    try:
        subprocess.run([sys.executable, "-m", "seleniumwire", "extractcert"],
                       check=True, cwd=str(SCRIPT_DIR))
    except subprocess.CalledProcessError as e:
        die(f"Failed to extract Selenium-Wire CA: {e}")
    # Move/rename if necessary
    ca_in_cwd = SCRIPT_DIR / "ca.crt"
    if ca_in_cwd.exists():
        ca_in_cwd.replace(SW_CERT_FILE)
        print(f"[INFO] Saved Selenium-Wire CA to: {SW_CERT_FILE}")
    else:
        # Some versions may already place a file named differently; fallback:
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


# ---------- Verification helpers ----------
def try_openssl():
    try:
        subprocess.check_output(["openssl", "version"], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def parse_chain_with_openssl(der_bytes: bytes) -> str:
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as tf:
        tf.write(der_bytes)
        tmp = tf.name
    try:
        subject = subprocess.check_output(
            ["openssl", "x509", "-inform", "DER", "-noout", "-subject", "-in", tmp],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", "ignore").strip()
        issuer = subprocess.check_output(
            ["openssl", "x509", "-inform", "DER", "-noout", "-issuer", "-in", tmp],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", "ignore").strip()
        return f"{subject} | {issuer}"
    finally:
        try: os.remove(tmp)
        except Exception: pass


def verify_certificate_chain(driver, expected_substrs):
    """Best-effort: print chain; return True if any expected substrings appear."""
    import base64
    try:
        try:
            driver.execute_cdp_cmd("Security.enable", {})
        except Exception:
            pass
        res = driver.execute_cdp_cmd("Security.getCertificate", {"origin": driver.current_url})
        if isinstance(res, dict) and "certificates" in res:
            certs = res["certificates"]
        elif isinstance(res, dict) and "tableNames" in res:
            certs = res["tableNames"]
        elif isinstance(res, list):
            certs = res
        else:
            certs = []

        if not certs:
            print("[WARN] Could not retrieve certificate chain from DevTools.")
            return False

        print("[INFO] Certificate chain entries:", len(certs))
        found = False
        if try_openssl():
            for idx, c in enumerate(certs, start=1):
                # Handle PEM or base64 DER
                if "BEGIN CERTIFICATE" in c:
                    from tempfile import NamedTemporaryFile
                    with NamedTemporaryFile("w", delete=False) as tf:
                        tf.write(c)
                        pem_path = tf.name
                    try:
                        subject = subprocess.check_output(
                            ["openssl", "x509", "-inform", "PEM", "-noout", "-subject", "-in", pem_path],
                            stderr=subprocess.DEVNULL
                        ).decode("utf-8", "ignore").strip()
                        issuer = subprocess.check_output(
                            ["openssl", "x509", "-inform", "PEM", "-noout", "-issuer", "-in", pem_path],
                            stderr=subprocess.DEVNULL
                        ).decode("utf-8", "ignore").strip()
                        line = f"{subject} | {issuer}"
                        print(f"  [{idx}] {line}")
                        if any(s.lower() in line.lower() for s in expected_substrs):
                            found = True
                    finally:
                        try: os.remove(pem_path)
                        except Exception: pass
                else:
                    try:
                        der = base64.b64decode(c)
                        info = parse_chain_with_openssl(der)
                        print(f"  [{idx}] {info}")
                        if any(s.lower() in info.lower() for s in expected_substrs):
                            found = True
                    except Exception as e:
                        print(f"  [{idx}] (unable to parse cert): {e}")
        else:
            print("[WARN] OpenSSL not found; skipping issuer/subject parsing.")
        return found
    except Exception as e:
        print(f"[ERROR] Certificate chain check failed: {e}")
        return False


# ---------- Main proxy test ----------
def run_test(headless: bool = True):
    if not BRIGHTDATA_PROXY:
        die("BRIGHTDATA_PROXY not set in .env")

    seleniumwire_options = {
        "proxy": {
            "http": BRIGHTDATA_PROXY,
            "https": BRIGHTDATA_PROXY,
            "no_proxy": "localhost,127.0.0.1",
        },
        # Upstream (Bright Data) verification off for Selenium-Wire's local proxy:
        "verify_ssl": False,
        # We don't need request capture; but Selenium-Wire may still MITM without its CA installed:
        "disable_capture": True,
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
    driver.get("https://api.ipify.org?format=text")
    ip_addr = driver.find_element("tag name", "body").text.strip()
    print(f"[SUCCESS] Proxy IP: {ip_addr}")

    # 2) Visit an HTTPS site
    driver.get("https://www.google.com")
    print(f"[INFO] Navigated to: {driver.current_url}")

    # 3) Chrome should mark the page 'secure'
    try:
        driver.execute_cdp_cmd("Security.enable", {})
    except Exception:
        pass
    # --- replace the current "secure" check block in run_test(...) with this ---

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

    driver.quit()
    print("[RESULT] ✅ Proxy + CA trust validated (HTTPS secure context + cross-origin fetch succeeded).")



if __name__ == "__main__":
    # Ensure CA files
    ensure_local_bd_ca()
    ensure_sw_ca_file()

    # Install to system/user trust stores (idempotent)
    install_bd_ca_idempotent()
    install_sw_ca_idempotent()

    # Run the test
    run_test(headless=True)