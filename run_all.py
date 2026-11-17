"""Re-run everything from the original CSVs in ./data. Usage: python run_all.py  (about 10-20 min)."""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__)); os.chdir(here)
steps = ['02_value_tables.py', '03_backtest.py', '03b_backtest_long.py', '04_predictions_cross.py', '05_organic.py',
         '06_plan.py', '06b_plan_final.py', '07_creative_analysis.py', '08_creative_plan.py', '09_report.py']
for s in steps:
    print('>>', s, flush=True)
    r = subprocess.run([sys.executable, '-I', os.path.join('code', s)])
    if r.returncode: sys.exit(f'{s} failed')
