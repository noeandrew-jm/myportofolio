"""Run the browser tutorial against an isolated local Django test server."""

import argparse
import importlib.util
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Jalankan tanpa jendela browser.")
    parser.add_argument("--browser", choices=("chrome", "edge", "firefox"), default="chrome")
    args = parser.parse_args()

    for module in ("django", "dotenv", "selenium"):
        if importlib.util.find_spec(module) is None:
            parser.exit(1, "Dependency belum lengkap. Jalankan: python -m pip install -r requirements-dev.txt\n")

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
    # This entry point always selects its own local database, even if .env is
    # configured for PWS. It never connects to the normal development database.
    os.environ["PRODUCTION"] = "False"
    os.environ["DJANGO_SETTINGS_MODULE"] = "e2e.settings"
    os.environ["E2E_BROWSER"] = args.browser
    os.environ["E2E_HEADLESS"] = "1" if args.headless else "0"

    import django
    from django.test.runner import DiscoverRunner

    django.setup()
    print("E2E memakai server 127.0.0.1 dan database uji sementara; data lokal/PWS tidak diubah.", flush=True)
    runner = DiscoverRunner(verbosity=2, interactive=False)
    failures = runner.run_tests(["e2e.browser_checks"])
    if failures:
        print("[FAIL] Pengujian E2E gagal. Periksa rincian di atas.", flush=True)
        return 1
    print("Semua pengujian E2E berhasil!", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
