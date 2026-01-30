from setup_environment.env_setup import setup_environment
from setup_seed_data.seed_data import seed_data
from stage_1_golden_sets.golden_set import run_golden_set

if __name__ == '__main__':
    setup_environment()
    seed_data()
    run_golden_set()