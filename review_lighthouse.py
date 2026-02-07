#!/usr/bin/env python
"""Review lighthouse reports for issues and discrepancies"""

import json
from pathlib import Path

reports_dir = Path("lighthouse_reports")

# Check all lighthouse reports
print("=" * 70)
print("LIGHTHOUSE REPORTS REVIEW")
print("=" * 70)

json_files = sorted(reports_dir.glob("*.json"))
if not json_files:
    print("No lighthouse reports found!")
    exit(1)

for report_file in json_files:
    if "history" in report_file.name:
        continue  # Skip history file

    try:
        data = json.load(open(report_file, encoding="utf-8"))
    except Exception as e:
        print(f"\n❌ Failed to parse {report_file.name}: {e}")
        continue

    print(f"\n📊 Report: {report_file.name}")
    print("-" * 70)

    # Extract URL
    url = data.get("finalDisplayedUrl", "Unknown")
    print(f"   URL: {url}")

    # Extract categories
    categories = data.get("categories", {})
    print(f"   Scores:")

    for cat_name, cat_data in categories.items():
        score_val = cat_data.get("score", 0)
        if score_val is None:
            score_val = 0
        score = score_val * 100
        emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
        print(f"     {emoji} {cat_name.capitalize():25} {score:6.1f}")

    # Check for accessibility issues
    if "accessibility" in categories:
        acc_score = categories["accessibility"].get("score", 0)
        if acc_score is None:
            acc_score = 0
        if acc_score == 0 or acc_score < 0.9:
            print(
                f"\n   ⚠️  CRITICAL: Accessibility score is {acc_score} - this will fail Lighthouse CI!"
            )
            print(f"      Threshold requirement: 90 (requires score 0.90)")
            print(f"      Actual score: {acc_score * 100:.1f}")

print("\n" + "=" * 70)
