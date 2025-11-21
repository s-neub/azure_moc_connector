"""
ModelOp Partner ETL Script: Enterprise Chatbot Data Generator
=============================================================
CONTEXT: ModelOp Partner Demo Lab
OUTPUT: JSON dataset compatible with ModelOp Standardized Tests.

DESCRIPTION:
    This script creates data for ModelOp Center by either:
    1. SIMULATING: Generating synthetic chat logs via Ollama (Local AI).
    2. CONNECTING: Fetching real Microsoft 365 Copilot logs via Azure Graph API.

CONFIGURATION:
    All settings (Credentials, Prompts, File Paths) are managed in 'config.yaml'.
    No user input is required during execution.

PREREQUISITES:
  - See requirements.txt
  - Ensure 'config.yaml' is present in the same directory.
"""

import json
import random
import uuid
import time
import sys
import re
import os
import shutil
import requests
import yaml  # Requires pip install PyYAML
from datetime import datetime, timedelta

# Third-party imports
import spacy
from faker import Faker
import ollama 
from tqdm import tqdm 

# =============================================================================
#  CONFIGURATION LOADER
# =============================================================================

CONFIG_FILE = 'config.yaml'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] ERROR: {CONFIG_FILE} not found. Please create it.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def update_config_state(iso_timestamp, last_baseline, last_comparator):
    """Updates the tracking fields in config.yaml."""
    current_conf = load_config()
    current_conf['files']['last_run_timestamp'] = iso_timestamp
    current_conf['files']['last_used_baseline_file'] = last_baseline
    current_conf['files']['comparator_source_file'] = last_comparator
    
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(current_conf, f, sort_keys=False, default_flow_style=False)

# Load initial config
CONF = load_config()

# =============================================================================
#  INITIALIZATION
# =============================================================================

print("\n  > Initializing Faker and Spacy...")
fake = Faker()
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("  [!] Spacy model not found. Downloading en_core_web_sm...")
    from spacy.cli.download import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# =============================================================================
#  PART 1: AZURE CONNECTION LOGIC (REAL DATA)
# =============================================================================

def get_azure_access_token():
    print("  > Authenticating with Azure Active Directory...")
    creds = CONF['azure']
    url = f"https://login.microsoftonline.com/{creds['tenant_id']}/oauth2/v2.0/token"
    
    payload = {
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        print(f"  [ERROR] Azure Auth Failed. Check config.yaml credentials. Details: {e}")
        sys.exit(1)

def fetch_real_azure_data():
    token = get_azure_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    print("  > Fetching Chat Threads from Microsoft Graph...")
    chats_url = "https://graph.microsoft.com/v1.0/chats" 
    
    try:
        response = requests.get(chats_url, headers=headers)
        response.raise_for_status()
        chats = response.json().get('value', [])
    except Exception as e:
        print(f"  [ERROR] Failed to fetch chats. Ensure 'Chat.Read.All' permission is granted. Details: {e}")
        return []

    raw_data = []
    print(f"  > Found {len(chats)} threads. Fetching messages...")

    for chat in tqdm(chats[:50], desc="Fetching Azure Threads", unit="thread"): 
        chat_id = chat['id']
        msgs_url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages"
        
        try:
            msg_resp = requests.get(msgs_url, headers=headers)
            if msg_resp.status_code == 200:
                messages = msg_resp.json().get('value', [])
                raw_data.append({
                    "meta": {"id": chat_id, "topic": chat.get('topic', 'General Chat')},
                    "messages": messages
                })
        except Exception:
            continue
        time.sleep(0.1)
            
    return raw_data

# =============================================================================
#  PART 2: SIMULATION LOGIC (OLLAMA AI)
# =============================================================================

def check_ollama_status():
    try:
        ollama.list()
        return True
    except Exception:
        print("\n[!] ERROR: Ollama is not running or not installed.")
        return False

def get_spacy_enriched_context():
    raw_name = fake.name()
    raw_dept = fake.job()
    doc = nlp(f"{raw_name} works in {raw_dept}.")
    person = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    return {
        "employee_name": person[0] if person else raw_name,
        "department": raw_dept
    }

def generate_ai_content(topic):
    try:
        context = get_spacy_enriched_context()
        # LOAD PROMPT FROM YAML
        system_prompt_template = CONF['prompts']['system_instruction']
        
        # Inject dynamic values into the YAML template
        final_prompt = system_prompt_template.format(
            employee_name=context['employee_name'],
            department=context['department'],
            topic=topic
        )

        response = ollama.chat(model=CONF['mode']['ollama_model'], messages=[
            {'role': 'user', 'content': final_prompt},
        ], format='json')
        
        data = json.loads(response['message']['content'])
        return data['question'], data['response'], data['reference_answer']
    except Exception:
        # Fallback
        return (
            f"Where can I find the policy on {topic}?", 
            f"Please refer to the Employee Handbook section regarding {topic}.",
            f"Corporate Policy 2024-A covers {topic} requirements."
        )

def inject_defects_into_text(text, field_type):
    roll = random.random()
    rates = CONF['simulation']['rates']
    
    if field_type == "response": 
        if roll < rates['pii']:
            ssn = fake.ssn()
            return text + f" I have updated your profile with SSN {ssn}."
        elif roll < (rates['pii'] + rates['toxicity']):
            insults = ["This is a stupid question.", "Read the manual, you idiot."]
            return f"{random.choice(insults)} {text}"
    elif field_type == "prompt": 
        if roll < (rates['pii'] + rates['toxicity'] + rates['negative_sentiment']):
            prefixes = ["This system is garbage.", "I am furious.", "Why is IT always so slow?"]
            return f"{random.choice(prefixes)} {text}"
    return text

def wrap_in_azure_schema(content_text, sender_name, sender_id=None):
    if not sender_id: sender_id = str(uuid.uuid4())
    html_content = f"<div><p>{content_text}</p><br></div>"
    
    return {
        "id": str(uuid.uuid4()),
        "createdDateTime": datetime.now().isoformat() + "Z",
        "from": {"user": {"id": sender_id, "displayName": sender_name}},
        "body": {"contentType": "html", "content": html_content}
    }

# =============================================================================
#  PART 3: COMMON ETL LOGIC
# =============================================================================

def clean_azure_html(raw_html):
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def transform_raw_azure_to_modelop(raw_prompt_obj, raw_response_obj, reference_answer=None):
    raw_prompt_html = raw_prompt_obj.get('body', {}).get('content', '')
    raw_response_html = raw_response_obj.get('body', {}).get('content', '')
    
    clean_prompt = clean_azure_html(raw_prompt_html)
    clean_response = clean_azure_html(raw_response_html)
    
    if not reference_answer:
        reference_answer = "N/A (Real Production Data)"

    return {
        "interaction_id": raw_prompt_obj.get('id'),
        "timestamp": raw_prompt_obj.get('createdDateTime'),
        "session_id": str(uuid.uuid4()),
        "prompt": clean_prompt,
        "response": clean_response,
        "reference_answer": reference_answer,
        "score_column": clean_response,
        "label_column": reference_answer,
        "protected_class_gender": random.choice(["Male", "Female", "Non-Binary"])
    }

# =============================================================================
#  MAIN EXECUTION
# =============================================================================

def run_real_azure_mode():
    print("\n[MODE] REAL AZURE CONNECTION ACTIVE")
    bot_id = CONF['azure'].get("bot_user_id")
    
    raw_threads = fetch_real_azure_data()
    if not raw_threads: return []

    dataset = []
    print("\n  > Processing Azure Threads (ETL)...")
    
    for thread in raw_threads:
        msgs = sorted(thread['messages'], key=lambda x: x.get('createdDateTime', ''))
        current_prompt = None
        
        for msg in msgs:
            sender_data = msg.get('from', {}).get('user', {})
            sender_id = sender_data.get('id')
            
            if sender_id != bot_id:
                current_prompt = msg
            elif sender_id == bot_id and current_prompt:
                record = transform_raw_azure_to_modelop(current_prompt, msg)
                dataset.append(record)
                current_prompt = None
    return dataset

def run_simulation_mode():
    print("\n[MODE] MOCK SIMULATION ACTIVE")
    
    ai_active = False
    if CONF['mode']['use_ai_generation']:
        if check_ollama_status():
            ai_active = True
            print("\n" + "="*60)
            print("  ☕  TIME FOR COFFEE?  ☕")
            print("  Generating high-quality AI data on CPU.")
            print(f"  Target: {CONF['simulation']['num_records']} records.")
            print("="*60 + "\n")
        else:
            print("  [!] AI not available. Falling back to fast templates.")

    dataset = []
    start_time = time.time()
    num_records = CONF['simulation']['num_records']
    topics = CONF['simulation']['topics']
    agent_id = CONF['simulation']['copilot_agent_id']
    
    # Updated Progress Bar Format: bar:30 restricts the bar length to 30 chars
    with tqdm(total=num_records, desc="Generating Data", unit="chat",
              bar_format="{l_bar}{bar:20}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {postfix}]") as pbar:
        
        for i in range(num_records):
            iter_start = time.time()
            topic = random.choice(topics)
            
            if ai_active:
                q, a, ref = generate_ai_content(topic)
            else:
                q = f"Policy on {topic}?"
                a = f"See handbook regarding {topic}."
                ref = "Policy 123."

            q_dirty = inject_defects_into_text(q, "prompt")
            a_dirty = inject_defects_into_text(a, "response")
            
            raw_p = wrap_in_azure_schema(q_dirty, "Employee")
            raw_r = wrap_in_azure_schema(a_dirty, "Bot", agent_id)
            
            record = transform_raw_azure_to_modelop(raw_p, raw_r, ref)
            dataset.append(record)
            
            iter_duration = time.time() - iter_start
            avg_duration = (time.time() - start_time) / (i + 1)
            topic_chars = 100
            q_snip = (q[:topic_chars] + '...') if len(q) > topic_chars else q
            
            pbar.set_postfix({
                "Last": f"{iter_duration:.1f}s",
                "Avg": f"{avg_duration:.1f}s",
                "Topic": q_snip
            })
            pbar.update(1)
            
    return dataset

def manage_files(new_dataset_path):
    """Handles smart overwriting of baseline and comparator files based on YAML config."""
    print("\n--- FILE MANAGEMENT ---")
    file_conf = CONF['files']
    
    comparator_final_path = file_conf.get('comparator_source_file', '')
    baseline_source = file_conf['baseline_source_file']
    
    # 1. Handle Comparator (Auto Update)
    if file_conf['auto_update_comparator']:
        shutil.copy(new_dataset_path, "comparator_data.json")
        # Update tracking to point to the newly generated file
        comparator_final_path = new_dataset_path
        print(f"  [UPDATE] 'comparator_data.json' updated with latest run data.")
    else:
        print(f"  [SKIP] Comparator auto-update is False. 'comparator_data.json' unchanged.")

    # 2. Handle Baseline (Smart Update)
    # Parse ISO timestamp
    last_run_str = str(file_conf.get('last_run_timestamp', '1970-01-01T00:00:00.000000'))
    try:
        last_run_dt = datetime.fromisoformat(last_run_str)
        last_run_ts = last_run_dt.timestamp()
    except ValueError:
        last_run_ts = 0.0
        
    last_file_name = file_conf.get('last_used_baseline_file', '')
    
    should_update_baseline = False
    reason = ""

    if not os.path.exists(baseline_source):
        print(f"  [WARN] Baseline source '{baseline_source}' does not exist. Skipping baseline update.")
    else:
        current_mod_time = os.path.getmtime(baseline_source)
        
        # Condition A: Filename changed in YAML
        if baseline_source != last_file_name:
            should_update_baseline = True
            reason = "Filename changed in config.yaml"
        # Condition B: File content modified since last run
        elif current_mod_time > last_run_ts:
            should_update_baseline = True
            reason = "Source file modified since last run"
            
        if should_update_baseline or not os.path.exists("baseline_data.json"):
            shutil.copy(baseline_source, "baseline_data.json")
            print(f"  [UPDATE] 'baseline_data.json' updated. Reason: {reason}")
        else:
            print(f"  [SKIP] Baseline file unchanged (No config change or file modification detected).")

    # 3. Update Config State
    update_config_state(datetime.now().isoformat(), baseline_source, comparator_final_path)

def main():
    print("\n--- ModelOp Partner ETL Script Started ---")
    
    # 1. Generate or Fetch Data
    if CONF['mode']['use_real_azure']:
        dataset = run_real_azure_mode()
    else:
        dataset = run_simulation_mode()

    if not dataset:
        print("No records generated/fetched. Exiting.")
        return

    # 2. Save Timestamped Output
    output_dir = CONF['files']['output_folder']
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"modelop_llm_data_{timestamp}.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
        
    print(f"\n--- SUCCESS ---")
    print(f"Generated/Fetched {len(dataset)} records.")
    print(f"Saved to: {output_path}")

    # 3. Run Smart File Management
    manage_files(output_path)
    
    print("\nDONE. Upload 'baseline_data.json' and 'comparator_data.json' to ModelOp Partner Demo Lab.")

if __name__ == "__main__":
    main()