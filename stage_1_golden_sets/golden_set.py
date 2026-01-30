import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stage_1_golden_sets.evaluator import run_eval

def run_golden_set():
    print("\n" + "="*60)
    print("RUNNING GOLDEN SET EVALUATION")
    print("="*60 + "\n")
    
    run_eval()
    
    print("\n" + "="*60)
    print("GOLDEN SET EVALUATION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_golden_set()
