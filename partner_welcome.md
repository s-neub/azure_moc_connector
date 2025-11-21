Welcome to the **ModelOp Partner Demo Lab**! This "Quick Start" helps bridge the gap between the Microsoft Azure AI ecosystem and ModelOp Center's governance capabilities.

### **Why this matters to your customers**
Your enterprise clients are rapidly deploying Microsoft AI tools, but their GRC (Governance, Risk, and Compliance) teams are flying blind. They are asking questions you can now help answer:

1.  **Microsoft 365 Copilot (The "Shadow AI" Risk):**
    * *The Fear:* "Employees are pasting sensitive project data into Copilot to write summaries. How do we know if PII is leaking into the model context?"
    * *The Solution:* Use this tool's **Real Data Mode** to ingest actual Copilot chat logs and run ModelOp's PII Monitor to flag violations instantly.

2.  **Azure OpenAI Custom Bots (The "Brand Risk"):**
    * *The Fear:* "We built a customer support bot on GPT-4. What if it starts giving rude or toxic answers to our VIP clients?"
    * *The Solution:* Use this tool's **Simulation Mode** to generate "toxic" test cases and demonstrate how ModelOp's Toxicity Monitor catches bad behavior *before* it reaches a customer.

3.  **Power Virtual Agents (The "Accuracy" Risk):**
    * *The Fear:* "Our HR bot is answering questions about 401k matching. If it hallucinates a wrong policy, we could be liable."
    * *The Solution:* This tool generates "Ground Truth" reference data alongside the bot's answers, allowing ModelOp's Accuracy Monitor to mathematically prove if the bot is hallucinating.

---

### **How to use this tool**
This script is designed for every stage of your prospect's journey:

1.  **Simulate Data (Default):** Out of the box, it uses local AI to generate realistic "Corporate Helpdesk" conversations. It intentionally injects defects (PII leaks, toxicity) so you can show the dashboard "lighting up" with alerts during a demo.
2.  **Connect Real Data:** By toggling a single flag in `config.yaml`, you can connect this script to a customer's *actual* Azure Tenant to audit their live Copilot usage.

**Quick Start Steps:**
1.  **Install the "Brains":** Install [Ollama](https://ollama.com/) to power the local AI simulation.
2.  **Configure:** Open `config.yaml` to choose between "Simulation Mode" or "Real Azure Mode".
3.  **Run:** Run `python azure_copilot_etl_advanced.py`. It will auto-generate the datasets you need.
4.  **Upload:** The script updates `baseline_data.json` and `comparator_data.json`. Upload these to the **Partner Demo Lab** (Stage 3 in your guide).

Full instructions are in the **README.md**.