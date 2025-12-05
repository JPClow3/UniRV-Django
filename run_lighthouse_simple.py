"""
Simple Lighthouse runner that works around Windows temp file issues.
Uses Node.js directly with increased timeouts and better error handling.
"""
import os
import subprocess
import sys
import json
import time
from pathlib import Path

def run_lighthouse(url, output_path):
    """Run Lighthouse on a URL and save results."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use npx with increased timeout and Windows-friendly flags
    cmd = [
        'npx', '--yes', 'lighthouse',
        url,
        '--output=json',
        f'--output-path={output_path}',
        '--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage --disable-gpu --disable-setuid-sandbox',
        '--quiet',
        '--max-wait-for-load=60000',  # 60 seconds
        '--max-wait-for-fcp=30000',   # 30 seconds
    ]
    
    env = {
        **dict(os.environ),
        'PUPPETEER_SKIP_CHROMIUM_DOWNLOAD': '1',
        'LIGHTHOUSE_CHROMIUM_PATH': '',  # Use system Chrome
    }
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes total timeout
            shell=True,  # Windows needs shell
            env=env
        )
        
        if result.returncode == 0 and output_path.exists():
            return True, None
        else:
            error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Lighthouse timed out after 3 minutes"
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_lighthouse_simple.py <url> [output_path]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'lighthouse_reports_simple/home.json'
    
    print(f"Running Lighthouse on {url}...")
    success, error = run_lighthouse(url, output_path)
    
    if success:
        print(f"✅ Lighthouse audit completed. Results saved to {output_path}")
        
        # Parse and display scores
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            categories = data.get('categories', {})
            print("\n📊 Scores:")
            for cat_name, cat_data in categories.items():
                score = cat_data.get('score', 0) * 100
                emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
                print(f"  {emoji} {cat_name.capitalize()}: {score:.1f}")
        except Exception as e:
            print(f"⚠️  Could not parse scores: {e}")
    else:
        print(f"❌ Lighthouse failed: {error}")
        sys.exit(1)

if __name__ == '__main__':
    main()

