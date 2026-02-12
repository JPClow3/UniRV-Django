#!/usr/bin/env python
"""
Unified Lighthouse test runner for AgroHub (UniRV-Django).

Simplifies and consolidates Lighthouse testing across platforms (Windows, macOS, Linux).
Uses Lighthouse CLI (Node.js) or LHCI for batch runs with proper error handling.

Usage:
    # Single URL audit
    python scripts/lighthouse_runner.py --url http://localhost:8000/

    # Batch audit (all URLs from config)
    python scripts/lighthouse_runner.py --all

    # Batch audit with score tracking
    python scripts/lighthouse_runner.py --all --track

    # CI mode (multiple runs per URL)
    python scripts/lighthouse_runner.py --ci --all

    # Review latest reports
    python scripts/lighthouse_runner.py --review

    # Clean up old reports
    python scripts/lighthouse_runner.py --clean
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LighthouseRunner:
    """Unified Lighthouse test runner."""

    def __init__(
        self,
        report_dir: str = "lighthouse_reports",
        config_file: str = ".lighthouserc.json",
    ):
        self.project_root = Path(__file__).parent.parent
        self.report_dir = Path(report_dir)
        self.config_file = self.project_root / config_file
        self.history_file = self.report_dir / "lighthouse_scores_history.json"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load Lighthouse configuration from JSON."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_file}: {e}")

    def _check_server(self, url: str, timeout: int = 5) -> bool:
        """Check if server is running and accessible."""
        try:
            import requests

            response = requests.get(url, timeout=timeout)
            return response.status_code < 500
        except Exception:
            return False

    def _get_urls(self, mode: str = "local") -> List[str]:
        """Get URLs from config based on mode."""
        collect_config = self.config.get("ci", {}).get("collect", {})
        urls = collect_config.get("url", [])

        if mode == "ci":
            # In CI mode, use all URLs
            return urls
        elif mode == "local":
            # In local mode, skip dashboard URLs that require auth
            dashboard_urls = [
                u for u in urls if "/dashboard/" in u or "/cadastrar/" in u
            ]
            return [u for u in urls if u not in dashboard_urls]

        return urls

    def _run_lighthouse_cli(
        self, url: str, output_path: Path, runs: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """Run Lighthouse CLI (single-run) or LHCI (multi-run)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if runs == 1:
            # Use standard Lighthouse CLI for single runs
            return self._run_cli_single(url, output_path)
        else:
            # Use LHCI for multiple runs and assertions
            return self._run_cli_multi(url, output_path, runs)

    def _run_cli_single(
        self, url: str, output_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Run single Lighthouse audit."""
        cmd = [
            "npx",
            "--yes",
            "lighthouse",
            url,
            "--output=json",
            f"--output-path={output_path}",
            "--quiet",
            "--chrome-flags=--no-sandbox --disable-dev-shm-usage --disable-gpu",
            "--max-wait-for-load=120000",
            "--max-wait-for-fcp=60000",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                check=False,
                cwd=str(self.project_root),
            )

            if result.returncode == 0 and output_path.exists():
                return True, None
            else:
                error = result.stderr[:200] if result.stderr else result.stdout[:200]
                return False, f"Lighthouse failed: {error}"

        except subprocess.TimeoutExpired:
            return False, "Lighthouse timeout (5 minutes)"
        except FileNotFoundError:
            return False, "Lighthouse not found; run: npm install"
        except Exception as e:
            return False, str(e)

    def _run_cli_multi(
        self, url: str, output_path: Path, runs: int
    ) -> Tuple[bool, Optional[str]]:
        """Run multiple Lighthouse audits with LHCI assertions."""
        # For now, just repeat single runs and merge results
        # TODO: Use LHCI autorun with config if needed for CI/CD
        results = []

        for i in range(runs):
            temp_path = output_path.parent / f"{output_path.stem}_run{i+1}.json"
            success, error = self._run_cli_single(url, temp_path)

            if not success:
                return False, error

            with open(temp_path, "r", encoding="utf-8") as f:
                results.append(json.load(f))

        # Merge results (average scores)
        merged = self._merge_results(results)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)

        # Clean up temp files
        for i in range(runs):
            temp_path = output_path.parent / f"{output_path.stem}_run{i+1}.json"
            temp_path.unlink(missing_ok=True)

        return True, None

    def _merge_results(self, results: List[Dict]) -> Dict:
        """Merge multiple Lighthouse results into average."""
        if not results:
            return results[0] if results else {}

        if len(results) == 1:
            return results[0]

        # Average the category scores
        base = results[0].copy()
        categories = base.get("categories", {})

        for category_name in categories:
            scores = [
                r.get("categories", {}).get(category_name, {}).get("score", 0)
                for r in results
            ]
            avg_score = sum(scores) / len(scores) if scores else 0
            categories[category_name]["score"] = round(avg_score, 3)

        # Set metadata
        base["lighthouseVersion"] = results[0].get("lighthouseVersion", "")
        if "fetchTime" not in base:
            base["fetchTime"] = datetime.utcnow().isoformat()

        return base

    def _extract_scores(self, report_path: Path) -> Optional[Dict]:
        """Extract scores from Lighthouse JSON report."""
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            categories = data.get("categories", {})
            return {
                "performance": round(
                    (categories.get("performance", {}).get("score", 0) or 0) * 100, 1
                ),
                "accessibility": round(
                    (categories.get("accessibility", {}).get("score", 0) or 0) * 100, 1
                ),
                "best_practices": round(
                    (categories.get("best-practices", {}).get("score", 0) or 0) * 100, 1
                ),
                "seo": round((categories.get("seo", {}).get("score", 0) or 0) * 100, 1),
            }
        except (json.JSONDecodeError, IOError, KeyError) as e:
            return None

    def _print_scores(self, scores: Dict, url: str = ""):
        """Pretty-print Lighthouse scores."""
        print()
        if url:
            print(f"📊 {url}")
        print("-" * 60)

        for category, score in scores.items():
            if category == "average":
                print("-" * 60)
                emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
                print(f"{emoji} Average: {score:.1f}")
            else:
                emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
                formatted_cat = category.replace("_", " ").title()
                print(f"{emoji} {formatted_cat:20} {score:6.1f}")

        print()

    def run_url(
        self, url: str, output_name: Optional[str] = None, runs: int = 1
    ) -> bool:
        """Run Lighthouse on a single URL."""
        # Check server
        test_url = url.rsplit("?", 1)[0].rsplit("#", 1)[0]  # Remove query/fragment
        if not self._check_server(test_url):
            print(f"❌ Server not responding: {test_url}")
            return False

        # Generate output name
        if not output_name:
            output_name = test_url.split("://")[1].replace("/", "_").replace(":", "-")
            if output_name.endswith("_"):
                output_name = output_name[:-1]

        output_path = self.report_dir / f"{output_name}.json"

        print(f"🔍 Auditing: {url}")
        print(f"   Output: {output_path.name}")

        success, error = self._run_lighthouse_cli(url, output_path, runs)

        if success:
            print(f"✅ Completed")

            # Extract and display scores
            scores = self._extract_scores(output_path)
            if scores:
                scores["average"] = sum(scores.values()) / len(scores)
                self._print_scores(scores)

            return True
        else:
            print(f"❌ Failed: {error}")
            return False

    def run_batch(
        self, mode: str = "local", runs: int = 1, track: bool = False
    ) -> bool:
        """Run Lighthouse on batch of URLs."""
        urls = self._get_urls(mode)

        if not urls:
            print("❌ No URLs configured")
            return False

        print(f"🚀 Running Lighthouse on {len(urls)} URLs (runs={runs}, mode={mode})")
        print("=" * 60)

        failed_urls = []

        for i, url in enumerate(urls, 1):
            success = self.run_url(url, runs=runs)
            if not success:
                failed_urls.append(url)

        print("=" * 60)

        if track:
            self.track_scores()

        if failed_urls:
            print(f"\n⚠️  {len(failed_urls)} URLs failed:")
            for url in failed_urls:
                print(f"   - {url}")
            return False
        else:
            print(f"\n✅ All {len(urls)} URLs audited successfully")
            return True

    def review(self) -> None:
        """Review latest Lighthouse reports."""
        if not self.report_dir.exists():
            print("❌ No reports found")
            return

        reports = sorted(self.report_dir.glob("*.json"))
        reports = [r for r in reports if "history" not in r.name]

        if not reports:
            print("❌ No reports found")
            return

        print("📋 Lighthouse Reports Review")
        print("=" * 60)

        all_scores = {}

        for report_file in reports:
            url_name = report_file.stem
            scores = self._extract_scores(report_file)

            if scores:
                scores["average"] = sum(scores.values()) / len(scores)
                all_scores[url_name] = scores
                self._print_scores(scores, url_name)

        if all_scores:
            avg_of_avgs = sum(s["average"] for s in all_scores.values()) / len(
                all_scores
            )
            print("=" * 60)
            print(f"🎯 Overall Average: {avg_of_avgs:.1f}")
            print("=" * 60)

    def track_scores(self) -> None:
        """Track scores in history file."""
        reports = sorted(self.report_dir.glob("*.json"))
        reports = [r for r in reports if "history" not in r.name]

        if not reports:
            print("❌ No reports to track")
            return

        history = self._load_history()

        # Create entry for each report
        entry = {"timestamp": datetime.now().isoformat(), "reports": {}}

        all_scores = {}
        for report_file in reports:
            url_name = report_file.stem
            scores = self._extract_scores(report_file)
            if scores:
                scores["average"] = sum(scores.values()) / len(scores)
                entry["reports"][url_name] = scores
                all_scores[url_name] = scores

        entry["overall_average"] = (
            sum(s["average"] for s in all_scores.values()) / len(all_scores)
            if all_scores
            else 0
        )

        history.append(entry)
        history = history[-100:]  # Keep last 100 entries

        self._save_history(history)

        print(f"📊 Tracked scores (overall avg: {entry['overall_average']:.1f})")

    def _load_history(self) -> List[Dict]:
        """Load score history."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_history(self, history: List[Dict]) -> None:
        """Save score history."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def clean(self, days: int = 7) -> None:
        """Clean old reports (older than N days)."""
        from datetime import timedelta

        if not self.report_dir.exists():
            print("No reports to clean")
            return

        cutoff = datetime.now() - timedelta(days=days)
        cutoff_ts = cutoff.timestamp()

        cleaned = 0
        for report_file in self.report_dir.glob("*.json"):
            if report_file.stat().st_mtime < cutoff_ts:
                report_file.unlink()
                cleaned += 1

        print(f"🧹 Cleaned {cleaned} reports older than {days} days")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Lighthouse test runner for AgroHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single URL to audit")
    group.add_argument("--all", action="store_true", help="Audit all URLs (local mode)")
    group.add_argument("--review", action="store_true", help="Review latest reports")
    group.add_argument("--clean", action="store_true", help="Clean old reports")
    group.add_argument(
        "--ci", action="store_true", help="CI mode (all URLs with multiple runs)"
    )

    parser.add_argument("--track", action="store_true", help="Track scores in history")
    parser.add_argument(
        "--runs", type=int, default=1, help="Number of runs per URL (default: 1)"
    )
    parser.add_argument(
        "--report-dir", default="lighthouse_reports", help="Report directory"
    )
    parser.add_argument("--config", default=".lighthouserc.json", help="Config file")
    parser.add_argument(
        "--days", type=int, default=7, help="Days to keep (for --clean)"
    )

    args = parser.parse_args()

    try:
        runner = LighthouseRunner(report_dir=args.report_dir, config_file=args.config)

        if args.review:
            runner.review()
            return 0

        if args.clean:
            runner.clean(args.days)
            return 0

        if args.url:
            success = runner.run_url(args.url, runs=args.runs)
            return 0 if success else 1

        if args.all:
            success = runner.run_batch(mode="local", runs=args.runs, track=args.track)
            return 0 if success else 1

        if args.ci:
            success = runner.run_batch(mode="ci", runs=args.runs or 3, track=args.track)
            return 0 if success else 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
