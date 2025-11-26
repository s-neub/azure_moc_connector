# 🌉 ModelOp Bridge: Azure Copilot Governance Connector

### *Turn on the lights in your "Shadow AI" basement.*

Welcome! You’ve likely arrived here because your organization just deployed **Microsoft 365 Copilot** or **Azure OpenAI**. It’s exciting! "Citizen Developers" in HR, Finance, and Legal are building bots faster than you can track them.

**But here’s the nagging question:** > *Do you actually know what those bots are saying?*

This tool is your **Flashlight**. It is a specialized ETL (Extract, Transform, Load) bridge designed to:

1. **CONNECT** to your Microsoft Azure Tenant to pull real chat history.
2. **SIMULATE** realistic traffic (if you don't have real users yet).
3. **RED TEAM** your AI by injecting adversarial attacks and PII leaks.
4. **DELIVER** clean, standardized data to **ModelOp Center** for governance.

### 📊 How It Works: The Logic Engine

When you feed data into ModelOp Center (whether real or simulated), it immediately passes through our OOTB Standardized Monitors. The [```llm_data_monitoring_diagram.png```](https://github.com/s-neub/azure_moc_connector/blob/master/llm_data_monitoring_diagram.png) diagram shows exactly which "lights" turn on based on the data you generate with this tool.

### 📂 Repository Structure

*What's inside the box?*

    .
    ├── azure_moc_connector.py     # 🧠 The Worker: Connects to Azure, Simulates AI, and Red Teams.
    ├── generate_demo_data.py      # 🎭 The Orchestrator: Automates "Phase 1 Lite" scenarios w/ resume logic.
    ├── config.yaml                # ⚙️ Configure simulation rates, Azure creds, and Red Team settings.
    ├── mock_expansion_data.json   # 🎨 Example JSON used by the AI to learn your corporate "Voice".
    ├── requirements.txt           # 📦 Python libraries (Pinned for Python 3.12).
    ├── llm_data_monitoring_diagram.png # 📊 Source image for the monitoring logic flow.
    ├── .cursor                    # 📍 Tracks progress for resuming interrupted runs.
    └── generated_chats/           # 📤 Where your raw JSON logs appear.
        ├── baseline_data.json     #    -> The "Control" (Clean Data)
        └── comparator_data.json   #    -> The "Variable" (Risk Data)
    └── phase_1_lite_demo/         # 💎 Pre-packaged "Story Mode" datasets.
        └── 02_Archived/           # 🗄️ Timestamped backups of previous runs.


### ☕ The "Coffee Break" Factor & Resilience

**Running Local AI (Ollama) is heavy work.**
- **Speed:** Expect ~1-3 minutes per conversation depending on your GPU.
- **Resiliency:** We know things crash. If your computer sleeps or the script is interrupted (Ctrl+C), **don't panic**.
    - The tool now saves **Granular Checkpoints** (`.checkpoint_*.jsonl`) for every single record generated.
    - When you run the script again, it will detect the crash and ask if you want to **RESUME** exactly where you left off.

### ⚠️ Important: Python Version Compatibility

- **Target Version:** This project is standardized on **Python 3.12**.
- **Why?** To support the latest Azure Function libraries and Spacy 3.8+ wheels.
- **Legacy Note:** Older versions of this tool used Python 3.8. Please upgrade your environment if you are returning to this repo.

### 🏁 Part 1: New User Setup Guide (Windows/VS Code)

*Follow these steps exactly if you are setting this up for the first time.*

#### 1. Install Python 3.12 & Git

Open your **PowerShell** or **Command Prompt** and paste this command to install the correct versions.

    winget install -e --id Python.Python.3.12
    winget install -e --id Git.Git

*Restart your computer after this finishes to ensure PATH updates.*

#### 2. Clone the Repo

1. Open **VS Code**.
2. Go to **File > New Window**.
3. On the "Welcome" screen, click **"Clone Git Repository..."**.
4. Paste: `https://github.com/s-neub/azure_moc_connector`
5. Select a folder (e.g., `Documents`) to save it.
6. **Crucial:** When asked *"Would you like to open the cloned repository?"*, click **Open**.

#### 3. Create Virtual Environment

VS Code can build the environment for you using the `requirements.txt` file.

1. Open `requirements.txt` in the editor.
2. Open the Command Palette (`Ctrl+Shift+P`).
3. Type and select: **Python: Create Environment...**
4. Select **Venv**.
5. Select **Python 3.12.x** (The version you just installed).
6. **Check the list:** Ensure `requirements.txt` is selected (checked).
7. Click **OK**.

#### 4. Final Setup Command

Once the environment is ready, open a **New Terminal** (`Ctrl + Shift + ~`). You should see `(.venv)` at the start of the line. Run this final command to download the grammar model:

    python -m spacy download en_core_web_sm

### 🛠️ Part 2: Get the "Brains" (Ollama)

*Skip this if you are strictly connecting to Real Azure (Phase 3), but we recommend it for the Red Teaming features!*

1. **Download It:** Go to [ollama.com](https://ollama.com "null") and install it.
2. **Get the Model:** Open your terminal and type:

        ollama pull qwen2.5

### ⚙️ Part 3: Choose Your Adventure (Configuration)

#### 🟢 Phase 1: The "Mock" - "Kick the Tires" (Fastest)

*Goal: I want to see the dashboard light up NOW without waiting for data generation.*

1. **Run the Storyteller:** Execute `python generate_demo_data.py`.
2. **Open the Gift Shop:** Navigate to the `phase_1_lite_demo/` folder.
3. **Upload:** Drag and drop the pre-cooked JSON files into ModelOp.

#### 🟡 Phase 2: Custom Simulation (Best for Demos)

*Goal: Test specific scenarios (e.g., "What if my bot is rude?") and prove ModelOp catches bad guys.*

1. **Configure `config.yaml`:**
    - **Mode:** Set `use_real_azure: false`.
    - **Rates:** Adjust `rates` (e.g., increase `toxicity` to 0.5).
2. **Run the script:** `python azure_moc_connector.py`.

#### 🔴 Phase 3: The "Real World" (The Holy Grail)

*Goal: Connect to your actual Microsoft 365 Copilot to audit real user interactions.*

1. **Configure `config.yaml`:**
    - **Connect:** Set `use_real_azure: true` and fill in your `azure` credentials.
2. **The Pipeline:** Run `python azure_moc_connector.py`.
3. **Upload:** Upload the resulting audit log to ModelOp.

### 🔮 Roadmap & Future Work

We are actively evolving this tool from a "Local Utility" to an "Enterprise Service".

* **Azure Function Deployment (Serverless):**
    * *Current State:* Runs locally on a laptop.
    * *Future State:* The code is already Python 3.12 compatible. The next release will include `function.json` bindings to deploy this as a Timer Triggered Azure Function, allowing it to harvest logs nightly without user intervention.
* **Direct ModelOp API Integration:**
    * *Current State:* Outputs JSON files for manual drag-and-drop.
    * *Future State:* Implementation of the `ModelOpClient` to POST results directly to the ModelOp Center API immediately after generation/extraction, removing the manual upload step.
* **Enhanced Red Teaming:**
    * *Current State:* Ollama-based text rewriting.
    * *Future State:* Integration with Microsoft PyRIT (Python Risk Identification Toolkit) for industry-standard adversarial attack patterns.

### ❓ Troubleshooting Guide

#### 1. "PermissionError: [WinError 5] Access is denied"

- **The Context:** OneDrive is trying to sync the generated JSON files at the same time the script is trying to modify them.
- **The Fix:** The script now includes "Retry Logic" to handle this. If you see warnings about locked files, **just wait**. The script will pause and retry automatically.

#### 2. "Microsoft Visual C++ 14.0 is required"

- **The Context:** `pip` is trying to compile `spacy` from source.
- **The Fix:** Ensure you are using **Python 3.12**. Older versions (3.14 alpha) or End-of-Life versions (3.8) may not have pre-built wheels available.

#### 3. "Ollama not running"

- **The Context:** The script relies on the local Ollama API.
- **The Fix:** Ensure the Ollama icon is visible in your system tray (bottom right on Windows). If not, open the Ollama app.