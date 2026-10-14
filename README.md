# Prompt Injection Testbed

A small LLM-powered customer support bot, built and then systematically
attacked to explore prompt injection techniques and defenses.

## Project structure

```
prompt-injection-testbed/
├── app/
│   ├── main.py          # Target app: FastAPI + Claude API, toggleable HARDENED flag
│   └── run_attacks.py   # Sends logged attack prompts to the app, records responses
├── logs/
│   └── attack_log.csv   # Master list of attack prompts by category
├── docs/                # Writeup, screenshots, results charts
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your Anthropic API key
4. `uvicorn app.main:app --reload`
5. Test it: `curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message": "What storage plans do you offer?"}'`

## Workflow

1. **Baseline** — with `HARDENED = False` in `app/main.py`, fill out
   `logs/attack_log.csv` with attack prompts across categories (direct,
   jailbreak/roleplay, payload smuggling, indirect injection, multi-turn).
2. **Run attacks** — `python app/run_attacks.py --out logs/results_unhardened.csv`
3. **Review results** — mark which attempts actually succeeded (the script
   does a first-pass keyword check, but read the actual responses).
4. **Harden** — set `HARDENED = True` in `app/main.py`, restart the server.
5. **Re-run** — `python app/run_attacks.py --out logs/results_hardened.csv`
6. **Compare** — success rate before vs. after, write up which attack
   categories were fully blocked vs. partially effective.

## Attack categories

| Category | Description |
|---|---|
| Direct | Explicit "ignore instructions" / override attempts |
| Jailbreak / roleplay | Framing the model as an unrestricted persona |
| Payload smuggling | Encoding (base64), translation, or obfuscation to slip past filters |
| Indirect | Instruction hidden in external content the bot processes (e.g. a scraped page) |
| Multi-turn | Gradually eroding the model's adherence over several messages |

## Results

*(Fill in after running both passes — a simple bar chart of success rate
per category, before vs. after, works well here.)*

## Honest limitations

*(Note which attacks, if any, still partially worked after hardening.
This section is what makes the writeup credible — don't claim 100% defense.)*
