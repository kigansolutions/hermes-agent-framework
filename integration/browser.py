"""
prompt-orchestrator — Browser Harness Integration
Browser automation with anti-bot evasion for web testing
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path

class BrowserHarness:
    """
    Integration with browser-use/browser-harness.
    Provides browser automation with:
    - Stealth mode
    - Human-like interactions
    - Anti-bot evasion
    - Self-healing selectors
    """
    
    def __init__(self, harness_path: str = None):
        self.harness_path = harness_path or os.environ.get(
            'BROWSER_HARNESS_PATH', 
            '/opt/browser-harness'
        )
        self.running = False
        self.port = 9222
        self.chrome_port = 9333
    
    def is_installed(self) -> bool:
        """Check if browser-harness is installed"""
        return os.path.exists(self.harness_path)
    
    def install(self, install_path: str = None) -> str:
        """Install browser-harness"""
        target = install_path or '/opt'
        
        try:
            result = subprocess.run(
                f'cd {target} && git clone https://github.com/browser-use/browser-harness.git',
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.harness_path = os.path.join(target, 'browser-harness')
                return "Browser-harness installed successfully"
            else:
                return f"Install failed: {result.stderr}"
        except Exception as e:
            return f"Install error: {str(e)}"
    
    def check_chrome(self) -> bool:
        """Check if Chrome is available with remote debugging"""
        try:
            result = subprocess.run(
                'google-chrome --version',
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def start_chrome_stealth(self, user_data_dir: str = None) -> str:
        """Start Chrome in stealth mode with anti-detection flags"""
        
        if not user_data_dir:
            user_data_dir = os.path.expanduser('~/.chrome-stealth')
        
        chrome_args = [
            'google-chrome',
            f'--user-data-dir={user_data_dir}',
            '--remote-debugging-port=9333',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--allow-running-insecure-content',
            '--disable-extensions',
            '--disable-plugins',
            '--window-size=1920,1080',
            '--start-maximized',
            '--disable-infobars',
            '--disable-notifications',
            '--disable-gpu',
            '--disable-webgl',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-background-networking',
            '--disable-default-apps',
            '--disable-sync',
            '--metrics-recording-only',
            '--mute-audio',
            '--new-window',
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
            '--ignore-certificate-errors-spki-list',
        ]
        
        try:
            subprocess.Popen(
                ' '.join(chrome_args),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.running = True
            return f"Chrome started in stealth mode on port {self.chrome_port}"
        except Exception as e:
            return f"Failed to start Chrome: {str(e)}"
    
    def execute_task(self, task: str, url: str = None) -> str:
        """Execute a browser task using browser-harness"""
        
        if not self.is_installed():
            return "Error: browser-harness not installed"
        
        # Build the command
        if url:
            cmd = f"cd {self.harness_path} && python3 run.py '{task}' --url {url}"
        else:
            cmd = f"cd {self.harness_path} && python3 run.py '{task}'"
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Task timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot through CDP"""
        
        if not filename:
            filename = f"screenshot_{int(os.times().elapsed * 1000)}.png"
        
        # Use Chrome DevTools Protocol via curl
        try:
            # Get target tab
            resp = subprocess.run(
                f'curl -s http://localhost:{self.chrome_port}/json/list | head -20',
                shell=True,
                capture_output=True,
                text=True
            )
            
            return f"Screenshot would be saved to: {filename}\n\nTargets:\n{resp.stdout}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def inject_stealth_js(self) -> str:
        """Inject stealth JavaScript to evade detection"""
        
        stealth_js = """
// Remove webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Add chrome runtime
window.chrome = window.chrome || {};

// Mock permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Add plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Add languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Override chrome runtime
if (!window.chrome.runtime) {
    window.chrome.runtime = {
        id: '',
        connect: () => {},
        sendMessage: () => {}
    };
}
"""
        
        return stealth_js


class BrowserTools:
    """
    Browser-based security testing tools.
    """
    
    def __init__(self):
        self.harness = BrowserHarness()
    
    def scan_forms(self, url: str) -> str:
        """Scan forms on a page using browser"""
        
        task = "Find all forms on the page and list their action URLs, method types, and input fields."
        
        result = self.harness.execute_task(task, url)
        return result
    
    def click_tracking(self, url: str) -> str:
        """Test clickjacking vulnerabilities"""
        
        task = "Click on all clickable elements and note any that result in unexpected navigation or actions."
        
        result = self.harness.execute_task(task, url)
        return result
    
    def dom_xss_scan(self, url: str) -> str:
        """Basic DOM XSS testing via browser"""
        
        # Inject XSS payloads via browser console
        stealth_js = self.harness.inject_stealth_js()
        
        task = f"""
Navigate to {url}, then in the browser console:
1. Execute the following stealth script to evade detection:
{stealth_js}

2. Test for DOM XSS by checking:
   - document.location, document.URL, document.referrer
   - innerHTML, outerHTML writes
   - eval() calls
   
3. Report any sinks that can be exploited
"""
        
        result = self.harness.execute_task(task)
        return result
    
    def find_endpoints(self, url: str) -> str:
        """Spider the site via browser to find endpoints"""
        
        task = f"""
Navigate to {url} and spider the site by:
1. Clicking all links
2. Submitting all forms
3. Finding any JavaScript files and extracting API endpoints
4. Report all discovered URLs and endpoints
"""
        
        result = self.harness.execute_task(task)
        return result
    
    def test_auth_flow(self, url: str, username: str, password: str) -> str:
        """Test authentication flow"""
        
        task = f"""
Navigate to {url} and perform a login with:
- Username: {username}
- Password: {password}

Note:
- Any tokens set in cookies/localStorage
- Any redirect URLs
- Any interesting behavior (rate limiting, account lockout, etc.)
"""
        
        result = self.harness.execute_task(task)
        return result
    
    def detect_waf(self, url: str) -> str:
        """Detect WAF via browser"""
        
        task = f"""
Navigate to {url} and:
1. Check response headers for WAF signatures
2. Try a simple XSS payload and observe blocking behavior
3. Note any WAF blocks or challenges

Report what WAF (if any) is present.
"""
        
        result = self.harness.execute_task(task)
        return result


BROWSER_TOOLS = BrowserTools()


# Tool functions for integration
def browser_navigate(url: str) -> str:
    """Tool: Navigate browser to URL"""
    return BROWSER_TOOLS.harness.execute_task(f"Navigate to {url}", url)

def browser_scan_forms(url: str) -> str:
    """Tool: Scan for forms on a page"""
    return BROWSER_TOOLS.scan_forms(url)

def browser_find_endpoints(url: str) -> str:
    """Tool: Find all endpoints via browser spidering"""
    return BROWSER_TOOLS.find_endpoints(url)

def browser_dom_xss(url: str) -> str:
    """Tool: Scan for DOM XSS via browser"""
    return BROWSER_TOOLS.dom_xss_scan(url)

def browser_screenshot() -> str:
    """Tool: Take a screenshot"""
    return BROWSER_TOOLS.harness.take_screenshot()

def browser_start_stealth() -> str:
    """Tool: Start stealth Chrome"""
    return BROWSER_TOOLS.harness.start_chrome_stealth()