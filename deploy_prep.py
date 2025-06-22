import os
import sys
import subprocess
import logging
import toml
from datetime import datetime

REQUIRED_FILES = [
    'app.py',
    'requirements.txt',
    '.streamlit/config.toml',
    'README.md',
]

REPORT_FILE = 'deployment_report.txt'

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def check_files():
    missing = []
    for f in REQUIRED_FILES:
        if not os.path.isfile(f):
            missing.append(f)
    return missing

def check_requirements():
    compatible = True
    issues = []
    try:
        with open('requirements.txt') as f:
            lines = f.readlines()
        found_streamlit = any('streamlit' in l.lower() for l in lines)
        if not found_streamlit:
            compatible = False
            issues.append('streamlit not found in requirements.txt')
        for l in lines:
            if l.strip().startswith('python'):
                if not any(v in l for v in ['3.9', '3.10', '3.11']):
                    compatible = False
                    issues.append(f'Python version in requirements.txt may not be compatible: {l.strip()}')
    except Exception as e:
        compatible = False
        issues.append(f'Error reading requirements.txt: {e}')
    return compatible, issues

def check_config_toml():
    try:
        with open('.streamlit/config.toml', 'r') as f:
            toml.load(f)
        return True, None
    except Exception as e:
        return False, str(e)

def test_local_app():
    try:
        import streamlit
    except ImportError:
        return False, 'streamlit not installed in this environment.'
    try:
        result = subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.headless', 'true', '--server.port', '9999'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr.decode()[:500]
    except Exception as e:
        return False, str(e)

def generate_report(results):
    with open(REPORT_FILE, 'w') as f:
        f.write(f"Deployment Readiness Report - {datetime.now()}\n\n")
        for section, (ok, details) in results.items():
            f.write(f"{section}: {'PASS' if ok else 'FAIL'}\n")
            if details:
                if isinstance(details, list):
                    for d in details:
                        f.write(f"  - {d}\n")
                else:
                    f.write(f"  {details}\n")
            f.write("\n")
    logging.info(f"Deployment report generated: {REPORT_FILE}")

def main():
    logging.info("Checking required files...")
    missing = check_files()
    files_ok = not missing
    if files_ok:
        logging.info("All required files are present.")
    else:
        logging.error(f"Missing files: {missing}")

    logging.info("Checking requirements.txt...")
    req_ok, req_issues = check_requirements()
    if req_ok:
        logging.info("requirements.txt looks compatible.")
    else:
        logging.error(f"Requirements issues: {req_issues}")

    logging.info("Checking .streamlit/config.toml syntax...")
    config_ok, config_issue = check_config_toml()
    if config_ok:
        logging.info(".streamlit/config.toml syntax is valid.")
    else:
        logging.error(f"Config TOML error: {config_issue}")

    logging.info("Testing local app startup (optional)...")
    app_ok, app_issue = test_local_app()
    if app_ok:
        logging.info("App started successfully (headless test).")
    else:
        logging.warning(f"App startup test failed or skipped: {app_issue}")

    results = {
        'Required Files': (files_ok, missing if not files_ok else None),
        'Requirements.txt': (req_ok, req_issues if not req_ok else None),
        'Config TOML': (config_ok, config_issue if not config_ok else None),
        'Local App Test': (app_ok, app_issue if not app_ok else None),
    }
    generate_report(results)
    if all(ok for ok, _ in results.values()):
        logging.info("\033[92mDeployment preparation PASSED. Ready for Streamlit Cloud!\033[0m")
    else:
        logging.error("\033[91mDeployment preparation FAILED. See deployment_report.txt for details.\033[0m")

if __name__ == '__main__':
    main() 