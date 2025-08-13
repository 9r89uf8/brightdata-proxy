"""
Browser Setup Module - Mobile Chrome with Bright Data Proxy
Handles all browser initialization, proxy configuration, and CA certificates.

Changes in this version:
- Detect installed Chrome and pin ChromeDriver (version_main) to that major version.
- Apply mobile emulation via Chrome DevTools Protocol after launch
  (avoids 'unrecognized chrome option: mobileEmulation').
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import time
import random
import re
import shutil
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("[ERROR] Install: pip install python-dotenv")
    sys.exit(1)

try:
    import seleniumwire.undetected_chromedriver as uc
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

load_dotenv()


class BrowserSetup:
    """Handles browser initialization with optional mobile emulation and proxy"""

    def __init__(self, headless: bool = True, mobile: bool = True):
        self.headless = headless
        self.mobile = mobile
        self.script_dir = Path(__file__).resolve().parent
        self.bd_cert_file = self.script_dir / "brightdata_ca.crt"
        self.sw_cert_file = self.script_dir / "seleniumwire_ca.crt"
        self.profile_dir = self.script_dir / f"chrome_profile_{int(time.time())}"
        self.proxy = os.getenv("BRIGHTDATA_PROXY")

        if not self.proxy:
            self._die("BRIGHTDATA_PROXY not set in .env or environment")

    def _die(self, msg: str, code: int = 1):
        """Exit with error message"""
        print(f"[ERROR] {msg}")
        sys.exit(code)

    # ---------------------------
    # Certificates
    # ---------------------------

    def _write_cert_from_env(self, path: Path, b64_env: str, pem_env: str, label: str) -> bool:
        """Write certificate from environment variables"""
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

    def _ensure_certificates(self):
        """Ensure CA certificates are available"""
        # Bright Data CA
        self._write_cert_from_env(
            self.bd_cert_file, "BRIGHTDATA_CA_B64", "BRIGHTDATA_CA_PEM", "Bright Data CA"
        )
        if not self.bd_cert_file.exists():
            self._die(f"Bright Data CA not found. Set BRIGHTDATA_CA_B64/PEM or place: {self.bd_cert_file}")

        # Selenium-Wire CA
        self._write_cert_from_env(
            self.sw_cert_file, "SELENIUMWIRE_CA_B64", "SELENIUMWIRE_CA_PEM", "Selenium-Wire CA"
        )
        if not self.sw_cert_file.exists():
            print("[INFO] Extracting Selenium-Wire CA...")
            try:
                subprocess.run([sys.executable, "-m", "seleniumwire", "extractcert"],
                               check=True, cwd=str(self.script_dir))
                ca_in_cwd = self.script_dir / "ca.crt"
                if ca_in_cwd.exists():
                    ca_in_cwd.replace(self.sw_cert_file)
                    print(f"[INFO] Saved Selenium-Wire CA to: {self.sw_cert_file}")
                else:
                    self._die("Could not find extracted Selenium-Wire CA")
            except subprocess.CalledProcessError as e:
                self._die(f"Failed to extract Selenium-Wire CA: {e}")

    def _install_certificates(self):
        """Install certificates to system trust store (platform-specific)"""
        system = platform.system().lower()

        if system == "linux":
            self._install_linux_certs()
        elif system == "darwin":
            self._install_macos_certs()
        elif system == "windows":
            self._install_windows_certs()
        else:
            self._die(f"Unsupported OS for certificate installation: {system}")

    def _install_linux_certs(self):
        """Install certificates on Linux using NSS"""
        nssdb = os.path.expanduser("~/.pki/nssdb")
        os.makedirs(nssdb, exist_ok=True)

        for cert_file, cert_name in [(self.bd_cert_file, "Bright Data"),
                                     (self.sw_cert_file, "Selenium Wire")]:
            try:
                output = subprocess.check_output(
                    ["certutil", "-d", f"sql:{nssdb}", "-L"],
                    stderr=subprocess.DEVNULL
                ).decode("utf-8", "ignore")

                if cert_name not in output:
                    subprocess.run(
                        ["certutil", "-d", f"sql:{nssdb}", "-A",
                         "-t", "C,,", "-n", cert_name, "-i", str(cert_file)],
                        check=True
                    )
                    print(f"[INFO] Installed {cert_name} CA into NSS DB")
                else:
                    print(f"[INFO] {cert_name} CA already in NSS DB")
            except FileNotFoundError:
                self._die("certutil not found. Install: sudo apt-get install libnss3-tools")

    def _install_macos_certs(self):
        """Install certificates on macOS"""
        for cert_file, cert_name in [(self.bd_cert_file, "Bright Data"),
                                     (self.sw_cert_file, "Selenium Wire")]:
            try:
                output = subprocess.check_output(
                    ["security", "find-certificate", "-a", "-c", cert_name,
                     "/Library/Keychains/System.keychain"],
                    stderr=subprocess.DEVNULL
                ).decode("utf-8", "ignore")

                if cert_name not in output:
                    subprocess.run(
                        ["sudo", "security", "add-trusted-cert", "-d",
                         "-r", "trustRoot", "-k", "/Library/Keychains/System.keychain",
                         str(cert_file)],
                        check=True
                    )
                    print(f"[INFO] Installed {cert_name} CA into macOS Keychain")
                else:
                    print(f"[INFO] {cert_name} CA already in macOS Keychain")
            except Exception as e:
                print(f"[WARN] Could not install {cert_name} CA: {e}")

    def _install_windows_certs(self):
        """Install certificates on Windows"""
        for cert_file, cert_name in [(self.bd_cert_file, "Bright Data"),
                                     (self.sw_cert_file, "Selenium Wire")]:
            try:
                output = subprocess.check_output(
                    ["certutil", "-user", "-store", "Root"],
                    stderr=subprocess.DEVNULL, shell=True
                ).decode("utf-8", "ignore")

                if cert_name.lower() not in output.lower():
                    subprocess.run(
                        ["certutil", "-user", "-addstore", "-f", "Root", str(cert_file)],
                        check=True, shell=True
                    )
                    print(f"[INFO] Installed {cert_name} CA into Windows Store")
                else:
                    print(f"[INFO] {cert_name} CA already in Windows Store")
            except Exception as e:
                print(f"[WARN] Could not install {cert_name} CA: {e}")

    # ---------------------------
    # Chrome detection & version pinning
    # ---------------------------

    def _find_chrome_binary(self) -> Optional[str]:
        """Find the Chrome binary. CHROME_PATH can override."""
        env_path = os.getenv("CHROME_PATH")
        if env_path and Path(env_path).exists():
            return env_path

        system = platform.system().lower()
        candidates = []

        if system == "windows":
            candidates.extend([
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ])
        elif system == "darwin":
            candidates.extend([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ])
        else:  # linux
            candidates.extend([
                shutil.which("google-chrome"),
                shutil.which("google-chrome-stable"),
                shutil.which("chrome"),
                shutil.which("chromium"),
                shutil.which("chromium-browser"),
            ])

        for p in candidates:
            if p and Path(p).exists():
                return p

        # last resort: PATH lookup
        which_any = shutil.which("chrome") or shutil.which("google-chrome")
        return which_any

    def _chrome_major_version(self) -> Optional[int]:
        """Return installed Chrome major version, or None if unknown. CHROME_VERSION_MAIN can override."""
        override = os.getenv("CHROME_VERSION_MAIN")
        if override and override.isdigit():
            try:
                return int(override)
            except ValueError:
                pass

        chrome_bin = self._find_chrome_binary()
        if not chrome_bin:
            print("[WARN] Could not locate Chrome binary to detect version.")
            return None

        try:
            out = subprocess.check_output([chrome_bin, "--version"], text=True, stderr=subprocess.STDOUT)
            # Examples:
            # Windows: "Google Chrome 138.0.7204.184"
            # macOS:   "Google Chrome 138.0.###"
            # Linux:   "Google Chrome 138.0.###"
            m = re.search(r"(\d+)\.", out)
            major = int(m.group(1)) if m else None
            if major:
                print(f"[INFO] Detected Chrome major version: {major}")
            else:
                print(f"[WARN] Unable to parse Chrome version from: {out.strip()}")
            return major
        except Exception as e:
            print(f"[WARN] Failed to query Chrome version: {e}")
            return None

    def _setup_page_stealth(self, driver):
        """Set up automatic stealth application on new pages"""
        try:
            # Use CDP to apply stealth on every page load
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    // Auto-apply stealth on page load
                    if (!window.__stealthApplied) {
                        window.__stealthApplied = true;
                        
                        // Override webdriver
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => false,
                            configurable: false
                        });
                        
                        // Hide automation
                        if (window.chrome) {
                            window.chrome.runtime = undefined;
                        }
                    }
                """
            })
            print("[INFO] Set up automatic stealth on page navigation")
        except Exception as e:
            print(f"[WARN] Could not set up page stealth: {e}")
    
    # ---------------------------
    # Stealth JavaScript patches
    # ---------------------------
    
    def _apply_stealth_scripts(self, driver):
        """Apply JavaScript patches to hide automation traces"""
        
        # Enhanced stealth with proper plugin emulation
        stealth_js = """
        // Check if already applied
        if (window.__stealthApplied) {
            return 'Stealth already applied';
        }
        window.__stealthApplied = true;
        
        // Remove webdriver property (with check)
        try {
            if (navigator.webdriver !== false) {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            }
        } catch (e) {
            // Property already defined
        }
        
        // Realistic plugins array
        const pluginData = [
            {name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}
        ];
        
        const plugins = pluginData.map(p => {
            const plugin = {};
            plugin.name = p.name;
            plugin.filename = p.filename;
            plugin.description = p.description;
            plugin.length = 1;
            plugin[0] = {
                type: 'application/pdf',
                suffixes: 'pdf',
                description: 'Portable Document Format'
            };
            return plugin;
        });
        
        try {
            Object.defineProperty(navigator, 'plugins', {
                get: () => plugins,
            });
        } catch (e) {}
        
        // Proper languages
        try {
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        } catch (e) {}
        
        try {
            Object.defineProperty(navigator, 'language', {
                get: () => 'en-US',
            });
        } catch (e) {}
        
        // Hide chrome automation
        if (window.chrome) {
            window.chrome.runtime = undefined;
            window.chrome.loadTimes = function() {};
            window.chrome.csi = function() {};
        }
        
        // Override permissions
        if (navigator.permissions && navigator.permissions.query) {
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        }
        
        // Realistic screen properties
        try {
            Object.defineProperty(screen, 'availWidth', {
                get: () => screen.width,
            });
        } catch (e) {}
        
        try {
            Object.defineProperty(screen, 'availHeight', {
                get: () => screen.height - 40,
            });
        } catch (e) {}
        
        // WebGL Vendor and Renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.apply(this, arguments);
        };
        
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter2.apply(this, arguments);
        };
        
        // Battery API
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1,
            });
        }
        
        // Hide automation in console
        const originalLog = console.log;
        console.log = function(...args) {
            if (args.some(arg => typeof arg === 'string' && 
                (arg.includes('webdriver') || arg.includes('automation')))) {
                return;
            }
            originalLog.apply(console, args);
        };
        """
        
        try:
            driver.execute_script(stealth_js)
            print("[INFO] Applied enhanced stealth JavaScript patches")
        except Exception as e:
            print(f"[WARN] Could not apply stealth scripts: {e}")

    # ---------------------------
    # Mobile emulation (CDP)
    # ---------------------------

    def _apply_mobile_emulation(self, driver):
        """
        Apply mobile emulation via CDP after browser launch.
        Emulates Android Chrome mobile for better consistency.
        """
        # Pixel 6 Pro dimensions
        width, height, dpr = 412, 915, 3.5
        # Android Chrome UA - matches Chrome browser better than iOS Safari
        ua = (
            "Mozilla/5.0 (Linux; Android 14; Pixel 6 Pro) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Mobile Safari/537.36"
        )

        # Resize window (best-effort) for non-headless; not critical in headless.
        try:
            driver.set_window_size(width, height)
        except Exception:
            pass

        # Device metrics & touch emulation
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": dpr,
            "mobile": True
        })
        driver.execute_cdp_cmd("Emulation.setTouchEmulationEnabled", {
            "enabled": True,
            "maxTouchPoints": 5
        })

        # User-Agent override
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": ua
        })

    # ---------------------------
    # Driver creation
    # ---------------------------

    def create_driver(self) -> uc.Chrome:
        """Create and configure Chrome driver with optional mobile emulation"""

        # Ensure certificates are ready
        self._ensure_certificates()
        self._install_certificates()

        # Selenium-wire proxy options
        seleniumwire_options = {
            "proxy": {
                "http": self.proxy,
                "https": self.proxy,
                "no_proxy": "localhost,127.0.0.1",
            },
            "verify_ssl": False,
            "disable_capture": False,
            "suppress_connection_errors": True,
        }

        # Chrome options with enhanced stealth
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument(f"--user-data-dir={str(self.profile_dir)}")
        
        # Basic stealth options
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Enhanced anti-detection
        chrome_options.add_argument("--disable-automation")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-extensions-file-access-check")
        chrome_options.add_argument("--disable-extensions-http-throttling")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-component-extensions-with-background-pages")
        
        # Language and locale
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
        
        # Preferences to hide automation
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,  # Block notifications
                "geolocation": 2,    # Block location requests
            },
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 1,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        # Add preferences - this is generally well-supported
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Note: Removed 'useAutomationExtension' and 'excludeSwitches' experimental options
        # as they cause compatibility issues with undetected-chromedriver + selenium-wire.
        # The stealth is maintained through:
        # 1. Command-line arguments like --disable-automation
        # 2. JavaScript patches applied after browser launch
        # 3. Human-like behavior patterns

        if self.headless:
            # New headless mode; works better with UC
            chrome_options.add_argument("--headless=new")

        # Optional: set explicit binary if found (can help UC pick the right driver)
        chrome_bin = self._find_chrome_binary()
        if chrome_bin:
            try:
                chrome_options.binary_location = chrome_bin
                print(f"[INFO] Using Chrome binary: {chrome_bin}")
            except Exception as e:
                print(f"[WARN] Could not set binary_location: {e}")

        # Random window size variations for desktop, non-headless
        if not self.mobile and not self.headless:
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            chrome_options.add_argument(f"--window-size={width},{height}")

        print(f"[INFO] Starting Chrome (mobile={self.mobile}, headless={self.headless})")
        print(f"[INFO] Profile: {self.profile_dir}")

        # Pin driver to installed Chrome's major version if we can detect it
        vmain = self._chrome_major_version()
        kwargs = {
            "options": chrome_options,
            "seleniumwire_options": seleniumwire_options,
        }
        if vmain:
            kwargs["version_main"] = vmain  # e.g., 138 to match your current Chrome

        # Create driver
        driver = uc.Chrome(**kwargs)

        # Apply stealth JavaScript patches
        self._apply_stealth_scripts(driver)
        
        # Set up automatic stealth application on navigation
        self._setup_page_stealth(driver)

        # Apply mobile emulation AFTER driver starts
        if self.mobile:
            self._apply_mobile_emulation(driver)

        # Verify proxy is working
        self._verify_proxy(driver)

        return driver

    # ---------------------------
    # Proxy verification
    # ---------------------------

    def _verify_proxy(self, driver):
        """Verify proxy connection is working"""
        print("\n" + "=" * 60)
        print("[INFO] Verifying proxy connection...")

        try:
            driver.get("https://api.ipify.org?format=text")
            ip_addr = driver.find_element("tag name", "body").text.strip()
            print(f"[PROXY CHECK] Current IP: {ip_addr}")

            if not ip_addr:
                self._die("Could not get IP address - proxy might not be working")

            print("[PROXY CHECK] Proxy appears to be working!")
            print("=" * 60 + "\n")

        except Exception as e:
            self._die(f"Proxy verification failed: {e}")


def create_browser(headless: bool = False, mobile: bool = True) -> uc.Chrome:
    """Convenience function to create a browser instance"""
    setup = BrowserSetup(headless=headless, mobile=mobile)
    return setup.create_driver()
