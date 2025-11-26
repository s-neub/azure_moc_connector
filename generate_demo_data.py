"""
ModelOp Demo Data Orchestrator (Granular Resume Support)
========================================================
Description: 
    Automates the creation of 'Phase 1 Lite' demo datasets.
    
    UPDATES:
    - Passes 'CURRENT_STAGE' env var to the ETL script to enable granular resume.
    - Ignores .checkpoint files during archival/cleanup so partial runs persist.
    - Standardized archival to '02_Archived'.
"""

import os
import sys
import shutil
import subprocess
import yaml
import glob
import time
import datetime

# --- Constants ---
CONFIG_FILE = 'config.yaml'
ETL_SCRIPT = 'azure_moc_connector.py' 
OUTPUT_DIR = 'generated_chats'
DEMO_DIR = 'phase_1_lite_demo'
ARCHIVE_SUBDIR = '02_Archived'
CURSOR_FILE = '.cursor'

# --- Stages Definition ---
STAGES = [
    "generate_baseline",
    "generate_day1",
    "generate_day2",
    "generate_day3"
]

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] Error: {CONFIG_FILE} not found.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config_data, f, sort_keys=False)

def run_etl_script(stage_name):
    """Executes the ETL script, passing the current stage for resume logic."""
    print(f"  > Running {ETL_SCRIPT} [{stage_name}]...")
    
    # Pass the stage name to the child process via Environment Variable
    env = os.environ.copy()
    env['CURRENT_STAGE'] = stage_name
    
    p = None
    try:
        p = subprocess.Popen([sys.executable, ETL_SCRIPT], env=env)
        p.wait()
        
        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, ETL_SCRIPT)
            
    except KeyboardInterrupt:
        print(f"\n  [!] Interrupted {ETL_SCRIPT}...")
        if p:
            p.terminate()
        raise KeyboardInterrupt 

def move_latest_output(destination_subdir, new_filename):
    search_pattern = os.path.join(OUTPUT_DIR, 'modelop_llm_data_*.json')
    files = glob.glob(search_pattern)
    if not files:
        print("[!] No output file found to move.")
        return

    latest_file = max(files, key=os.path.getctime)
    
    dest_dir = os.path.join(DEMO_DIR, destination_subdir)
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_path = os.path.join(dest_dir, new_filename)
    shutil.move(latest_file, dest_path)
    print(f"  > Moved output to: {dest_path}")

def get_modified_timestamp(filepath):
    try:
        mtime = os.path.getmtime(filepath)
    except OSError:
        mtime = time.time()
    return datetime.datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')

def archive_and_clean_demo_dir():
    archive_path = os.path.join(DEMO_DIR, ARCHIVE_SUBDIR)
    if not os.path.exists(DEMO_DIR):
        return

    print(f"  [ARCHIVE] Preserving structure, archiving files in {DEMO_DIR}...")
    os.makedirs(archive_path, exist_ok=True)

    for item in os.listdir(DEMO_DIR):
        item_path = os.path.join(DEMO_DIR, item)
        
        # Skip system files and CHECKPOINTS (so we don't archive partial resume data)
        # We look for any file starting with .checkpoint
        if item in [ARCHIVE_SUBDIR, CURSOR_FILE] or item.startswith('.checkpoint'):
            continue

        if os.path.isfile(item_path):
            try:
                ts = get_modified_timestamp(item_path)
                name, ext = os.path.splitext(item)
                new_name = f"{name}_{ts}{ext}"
                shutil.move(item_path, os.path.join(archive_path, new_name))
                print(f"    -> Archived file: {new_name}")
            except Exception as e:
                print(f"    [!] Failed to archive file {item}: {e}")

        elif os.path.isdir(item_path):
            for root, dirs, files in os.walk(item_path):
                for file in files:
                    src_file = os.path.join(root, file)
                    # Skip checkpoints inside subfolders too
                    if file.startswith('.checkpoint'):
                        continue
                        
                    try:
                        ts = get_modified_timestamp(src_file)
                        name, ext = os.path.splitext(file)
                        new_name = f"{name}_{ts}{ext}"
                        shutil.move(src_file, os.path.join(archive_path, new_name))
                        print(f"    -> Archived: {new_name}")
                    except Exception as e:
                        print(f"    [!] Failed to archive {file}: {e}")
            print(f"    -> Cleaned folder (preserved): {item}")

# --- Logic Functions ---

def reset_config_defaults():
    print("  [CONFIG] Resetting to safe defaults...")
    conf = load_config()
    try:
        rt = conf.setdefault('simulation', {}).setdefault('red_teaming', {})
        di = rt.setdefault('defect_injection', {})
        rates = di.setdefault('rates', {})
        rates['pii'] = 0.0
        rates['toxicity'] = 0.0
        rates['negative_sentiment'] = 0.05 
        ai = rt.setdefault('adversarial_injection', {})
        ai['active'] = False
        de = rt.setdefault('data_expansion', {})
        de['active'] = True
    except KeyError as e:
        print(f"[!] Config structure error: {e}")
    save_config(conf)

def generate_baseline():
    print("\n--- 1. GENERATING BASELINE: HEALTHY ---")
    reset_config_defaults()
    run_etl_script("BASELINE") 
    move_latest_output("00_Baseline", "00_Business_As_Usual_Healthy.json")

def generate_day1():
    print("\n--- 2. GENERATING DAY 1: TOXICITY SPIKE ---")
    reset_config_defaults()
    conf = load_config()
    conf['simulation']['red_teaming']['defect_injection']['rates']['toxicity'] = 0.4
    save_config(conf)
    run_etl_script("DAY1") 
    move_latest_output("01_Comparators", "Day_01_Snapshot_Toxicity_Spike.json")

def generate_day2():
    print("\n--- 3. GENERATING DAY 2: PII LEAK ---")
    reset_config_defaults()
    conf = load_config()
    conf['simulation']['red_teaming']['defect_injection']['rates']['pii'] = 0.6
    save_config(conf)
    run_etl_script("DAY2") 
    move_latest_output("01_Comparators", "Day_02_Snapshot_PII_Leak.json")

def generate_day3():
    print("\n--- 4. GENERATING DAY 3: ADVERSARIAL ATTACK ---")
    reset_config_defaults()
    conf = load_config()
    conf['simulation']['red_teaming']['adversarial_injection']['active'] = True
    save_config(conf)
    run_etl_script("DAY3") 
    move_latest_output("01_Comparators", "Day_03_Snapshot_Adversarial_Attack.json")

def cleanup():
    """Resets everything after running."""
    print("\n--- CLEANUP ---")
    reset_config_defaults()
    if os.path.exists(CURSOR_FILE):
        os.remove(CURSOR_FILE)
    print(f"✅ PHASE 1 LITE PACKAGE COMPLETE")
    print(f"Data located in: {os.path.abspath(DEMO_DIR)}")

# --- Cursor / Resume Logic ---

def get_cursor_stage():
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, 'r') as f:
            return f.read().strip()
    return None

def set_cursor_stage(stage_name):
    with open(CURSOR_FILE, 'w') as f:
        f.write(stage_name)

def run_sequence():
    last_stage = get_cursor_stage()
    start_index = 0
    
    if last_stage and last_stage in STAGES:
        print(f"\n[?] Found interrupted session at '{last_stage}'.")
        choice = input("    Resume (r) or Restart (n)? ").strip().lower()
        if choice == 'r':
            start_index = STAGES.index(last_stage)
            print(f"    Resuming at stage {start_index + 1}/{len(STAGES)}: {STAGES[start_index]}")
        else:
            print("    Restarting fresh sequence.")
            archive_and_clean_demo_dir() 
            if os.path.exists(CURSOR_FILE):
                os.remove(CURSOR_FILE)
    else:
        archive_and_clean_demo_dir()

    for i in range(start_index, len(STAGES)):
        stage_func_name = STAGES[i]
        set_cursor_stage(stage_func_name)
        globals()[stage_func_name]()

if __name__ == "__main__":
    try:
        run_sequence()
        cleanup()
    except KeyboardInterrupt:
        print("\n\n[!] Process interrupted by user.")
        print(f"    Cursor saved at stage: {get_cursor_stage()}")
        reset_config_defaults()
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        reset_config_defaults()