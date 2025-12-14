#!/usr/bin/env python
"""
Script to track Lighthouse scores over time.

This script parses Lighthouse JSON reports, extracts category scores,
and stores them in a JSON file with timestamps for trend analysis.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_lighthouse_reports(reports_dir: Path) -> List[Path]:
    """Find all Lighthouse JSON report files."""
    if not reports_dir.exists():
        return []
    
    json_files = list(reports_dir.glob('*.json'))
    # Filter out non-Lighthouse reports (check for 'categories' key)
    lighthouse_reports = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'categories' in data:
                    lighthouse_reports.append(json_file)
        except (json.JSONDecodeError, IOError):
            continue
    
    return lighthouse_reports


def extract_scores(report_path: Path) -> Optional[Dict]:
    """Extract scores from a Lighthouse JSON report."""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        categories = data.get('categories', {})
        
        scores = {
            'performance': round((categories.get('performance', {}).get('score', 0) or 0) * 100, 1),
            'accessibility': round((categories.get('accessibility', {}).get('score', 0) or 0) * 100, 1),
            'best_practices': round((categories.get('best-practices', {}).get('score', 0) or 0) * 100, 1),
            'seo': round((categories.get('seo', {}).get('score', 0) or 0) * 100, 1),
        }
        
        # Calculate average (always divide by 4 categories, even if some are 0)
        scores['average'] = round(
            sum(scores.values()) / 4, 1
        )
        
        return scores
    except (json.JSONDecodeError, IOError, KeyError) as e:
        print(f"Error extracting scores from {report_path}: {e}", file=sys.stderr)
        return None


def load_score_history(history_file: Path) -> List[Dict]:
    """Load existing score history."""
    if not history_file.exists():
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_score_history(history_file: Path, history: List[Dict]):
    """Save score history to file."""
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def compare_scores(current: Dict, previous: Optional[Dict]) -> Dict:
    """Compare current scores with previous scores."""
    if not previous:
        return {
            'performance': {'change': 0, 'status': 'new'},
            'accessibility': {'change': 0, 'status': 'new'},
            'best_practices': {'change': 0, 'status': 'new'},
            'seo': {'change': 0, 'status': 'new'},
            'average': {'change': 0, 'status': 'new'},
        }
    
    comparison = {}
    for key in ['performance', 'accessibility', 'best_practices', 'seo', 'average']:
        change = current.get(key, 0) - previous.get(key, 0)
        if change > 0:
            status = 'improved'
        elif change < 0:
            status = 'degraded'
        else:
            status = 'unchanged'
        
        comparison[key] = {
            'change': round(change, 1),
            'status': status
        }
    
    return comparison


def generate_trend_report(history: List[Dict], limit: int = 10) -> str:
    """Generate a text report of score trends."""
    if not history:
        return "No score history available."
    
    recent = history[-limit:]
    report_lines = [
        f"Lighthouse Score Trends (Last {len(recent)} runs)",
        "=" * 60,
        ""
    ]
    
    for entry in recent:
        timestamp = entry.get('timestamp', 'Unknown')
        scores = entry.get('scores', {})
        report_lines.append(f"Date: {timestamp}")
        report_lines.append(f"  Performance: {scores.get('performance', 0)}")
        report_lines.append(f"  Accessibility: {scores.get('accessibility', 0)}")
        report_lines.append(f"  Best Practices: {scores.get('best_practices', 0)}")
        report_lines.append(f"  SEO: {scores.get('seo', 0)}")
        report_lines.append(f"  Average: {scores.get('average', 0)}")
        report_lines.append("")
    
    return "\n".join(report_lines)


def main():
    """Main function to track Lighthouse scores."""
    # Configuration
    reports_dir = project_root / 'lighthouse_reports'
    history_file = project_root / 'lighthouse_scores_history.json'
    
    # Find Lighthouse reports
    reports = find_lighthouse_reports(reports_dir)
    
    if not reports:
        print(f"No Lighthouse reports found in {reports_dir}")
        print("Run Lighthouse CI first to generate reports.")
        return 1
    
    # Extract scores from the most recent report
    # Sort by modification time, get the most recent
    most_recent = max(reports, key=lambda p: p.stat().st_mtime)
    print(f"Processing report: {most_recent.name}")
    
    scores = extract_scores(most_recent)
    if not scores:
        print("Failed to extract scores from report.")
        return 1
    
    # Load existing history
    history = load_score_history(history_file)
    
    # Get previous scores for comparison
    previous_scores = None
    if history:
        previous_scores = history[-1].get('scores')
    
    # Compare with previous
    comparison = compare_scores(scores, previous_scores)
    
    # Create new entry
    entry = {
        'timestamp': datetime.now().isoformat(),
        'report_file': most_recent.name,
        'scores': scores,
        'comparison': comparison
    }
    
    # Add to history
    history.append(entry)
    
    # Keep only last 100 entries
    history = history[-100:]
    
    # Save history
    save_score_history(history_file, history)
    
    # Print results
    print("\n" + "=" * 60)
    print("Lighthouse Scores")
    print("=" * 60)
    print(f"Performance: {scores['performance']}")
    print(f"Accessibility: {scores['accessibility']}")
    print(f"Best Practices: {scores['best_practices']}")
    print(f"SEO: {scores['seo']}")
    print(f"Average: {scores['average']}")
    print()
    
    if previous_scores:
        print("Changes from previous run:")
        for key, comp in comparison.items():
            if key != 'average':  # Skip average in detailed comparison
                change_str = f"+{comp['change']}" if comp['change'] > 0 else str(comp['change'])
                status_emoji = "📈" if comp['status'] == 'improved' else "📉" if comp['status'] == 'degraded' else "➡️"
                print(f"  {key.capitalize()}: {change_str} {status_emoji}")
        print()
    
    # Generate trend report
    trend_report = generate_trend_report(history, limit=5)
    print(trend_report)
    
    print(f"\nScore history saved to: {history_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
