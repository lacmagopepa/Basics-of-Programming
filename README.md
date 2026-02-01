# Beer Game 2.0 Interactive (Pygame)

A modern, interactive **Beer Distribution Game** simulator built with **Pygame**.  
It models a 4‑tier supply chain (Retailer → Wholesaler → Distributor → Factory) and lets **1–4 human players** play on the **same machine**, while remaining tiers are controlled by AI policies.

## What the game simulates

Each week, the supply chain goes through a realistic loop:

1. **Customer demand** occurs at the Retailer.
2. **Shipments arrive** (delayed by *Shipping Lead Time*).
3. Each tier **ships** what it can (inventory-limited) to satisfy its downstream demand.
4. Each tier **places an order** upstream (delayed by *Information Lead Time*).
5. The Factory **produces** and adds production to its pipeline.
6. **Costs** are computed (holding, backlog/lost sales, production) and logged.

At the end, the game shows **results + bullwhip analysis**, and you can **export a CSV log**.

---

## ⚡ Quick Start (Portable Version)

**This project includes a self-contained Python environment!**

### Windows Users - Just Double-Click:
1. **To play the game:** Double-click `run_game.bat`
2. **To view analysis:** Double-click `run_notebook.bat`

That's it! No installation needed.

📖 **See [PORTABLE_SETUP.md](PORTABLE_SETUP.md) for full details**

---

## Requirements (Manual Setup)

- Python **3.10+**
- Packages:
  - `pygame`
  - `numpy` (used by some demand utilities)
  - `pandas`, `matplotlib` (for analysis)
  - `jupyter` (for notebooks)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## How to run

### Portable Version (Recommended):
```bash
run_game.bat        # Windows
```

### Manual:
From the project root (the folder that contains `main.py`):

```bash
python main.py
```

---

## Running Tests

The `tests/` folder contains test scripts for validating simulation behavior.

### Important: Path Setup for Tests

Test files need to import modules from the project root. To run a test script:

1. **Edit the test file** (e.g., `tests/test_10_weeks_order_20.py`)
2. **Update line 2** with the absolute path to the project root:
   ```python
   import sys
   sys.path.insert(0, r"C:\Users\lacma\Downloads\pygame_team_4_fixed_v2\pygame_team_4")
   ```
   Replace with **your actual project path** (the folder containing `main.py`)

3. **Run the test:**
   ```bash
   python tests/test_10_weeks_order_20.py
   ```

**Why `sys.path.insert(0, ...)`?**  
When running a script from the `tests/` subfolder, Python doesn't automatically know where to find the project modules (`simulation/`, `ui/`, etc.). The `sys.path.insert(0, ...)` line adds the project root to Python's search path, allowing imports like `from simulation.simulation_engine import SimulationEngine` to work correctly.

**Alternative:** Run tests from the project root using Python's module syntax:
```bash
python -m tests.test_10_weeks_order_20
```
This way you don't need to modify `sys.path`.

---

## Screens & how to use them

### 1) Start screen (cup screen)
- When the app opens, you see the start screen.
- **Audio:** `game_start.mp3` plays for ~3 seconds.
- Choose:
  - **Login / Start** to proceed
  - **About** to see info about the project

### 2) Login screen (username/password)
Use these default credentials:

- **Username:** `beer`
- **Password:** `beer`

If correct, you’ll be taken to **Game Configuration**.

### 3) Game Configuration screen
This is where you set up the simulation before starting.

#### A) Number of Players
Pick **1–4** human players.  
Any remaining roles become **AI-controlled**.

#### B) Select Human Roles (Tier)
After choosing player count, select which roles are **Human**. Others become **AI**.
- **Auto Assign**: assigns roles automatically
- **Done**: confirm your selection

#### C) Demand Scenario
Controls the customer demand pattern at the Retailer:

- **Step Change (STEP)**  
  Classic Beer Game: demand is **low first**, then **jumps up** later.
- **Random (Poisson) (POISSON)**  
  Demand varies randomly around an average (Poisson process).
- **Trend + Noise (TREND_NOISE)**  
  Demand increases gradually over time with random noise.

> The **Noise amplitude** parameter (Advanced Options) affects the “Trend + Noise” scenario.

#### D) AI Policy (for AI roles)
AI roles place orders using the selected policy:

- **Base‑Stock**  
  Orders up to a target “inventory position” (simple, stable).
- **PI Controller**  
  Uses a proportional/integral‑style rule (more reactive; can reduce or worsen oscillations depending on tuning).

---

## Advanced Options (what each parameter means)

Open **Advanced Options** to tune the simulation.

### Controls inside Advanced Options
- **Touch / Pen:** tap a row, then use **+ / −** or **Toggle**
- **Keyboard:**  
  **UP/DOWN** select, **LEFT/RIGHT** change, **ENTER** toggle, **ESC** close

### Parameters

#### Game duration (weeks)
Total number of weeks the simulation runs (e.g., 25).

#### Shipping lead time
Delay (in weeks) for **physical shipments** moving downstream.  
Higher values make the system slower to respond and typically **increase oscillations**.

**Note on pipeline visibility:**
- **ship_lt = 1**: Shipments appear at position **t+1** (next week arrival)
- **ship_lt = 2 or higher**: Shipments appear at positions **t+1 and t+2** (arrivals in 1 and 2 weeks)
- The **t+2 position is only visible when ship_lt > 1**

Each tier can see upcoming shipments in their pipeline, constrained by `min(order_amount, supplier_inventory)` to reflect realistic availability.

#### Information lead time
Delay (in weeks) for **orders/information** moving upstream.  
Higher values make upstream roles see demand later, which can **amplify the bullwhip effect**.

#### PI alpha (α), PI beta (β), PI gamma (γ)
Used by the **PI Controller** AI policy.

- **α (alpha):** how strongly the AI reacts to the gap between target and inventory position  
- **β (beta):** how strongly the AI reacts to backlog (unmet demand)  
- **γ (gamma):** included for tuning extensions; may be lightly used depending on implementation

> Tip: aggressive parameters can cause huge over‑ordering and big bullwhip.

#### Random seed mode
Controls reproducibility:
- **FIXED**: same randomness each run (useful for testing/comparison)
- **RANDOM**: different results each run

#### Fixed seed value
The seed used when Random seed mode is **FIXED**.

#### Initial inventory: Retailer / Wholesaler / Distributor / Factory
Starting stock (units) at each tier.

#### Order handling
How unmet demand is treated:

- **BACKORDER**  
  Unmet demand becomes backlog and must be satisfied later.
- **LOST_SALES**  
  Unmet demand disappears (not carried forward). This usually reduces backlog but can lower service level.

#### Holding cost per unit
Cost per unit held in inventory each week.

#### Backorder cost per unit
Cost per unit of backlog (unmet demand) each week.

#### Production cost per unit
Cost per unit produced by the Factory (based on Factory’s placed order).

#### Noise amplitude
Controls how “noisy” demand is in **Trend + Noise** scenario.  
Bigger values = more random variation.

---

## Playing the game (Game Screen)

### Controls
- **TAB**: switch between human tiers (if more than one human role)
- **Type digits**: enter your order quantity
- **BACKSPACE**: delete
- **ENTER** or **ORDER** button: submit

A week only advances when **all human tiers have submitted** their orders.

### What you see
Each role shows the key Beer‑Game values for the current week:
- **Incoming order / demand** (who is demanding from you)
- **Incoming shipment**
- **Inventory / backlog**
- **Shipments sent**
- **Costs**

---

## End of game outputs

### End Screen
At the end you get:
- **Overall Results**
  - Total cost
  - Average inventory
  - Service level
- **Bullwhip Effect Analysis (bar chart)**
- **Per‑Tier Breakdown** table
- **Key Insights** (quick summary)
- Buttons:
  - **View Analysis**: time-series charts
  - **Export CSV**: exports logs to a timestamped file
  - **Play Again**
  - **Exit**

### What “Service level” means (in this project)
Service level is computed as an approximate **fill rate**:

> **Service level ≈ (total shipped by Retailer) / (total customer demand)**

### What “Bullwhip” means (in this project)
Bullwhip is computed as a **variance ratio**:

> **bullwhip(role) = Var(orders(role)) / Var(customer demand)**

Retailer is shown as the baseline (≈ 1.0) when orders match demand variability.

---

## CSV logging & export

### Live log file
During the game, data is written to:

- `logs/game.csv`

### Exported CSV file
When you press **Export CSV** on the results screen, the game copies the log to:

- `exports/beer_game_log_YYYYMMDD_HHMMSS.csv`

### Columns in the CSV (main ones)
- `week`
- `role`
- `customer_demand` (Retailer’s customer demand)
- `stage_demand` (the demand each tier receives from downstream that week)
- `order_placed`
- `shipment_sent`
- `inventory_start`, `inventory_end`
- `backlog_start`, `backlog_end`
- `holding_cost`, `backlog_cost`, `production_cost`
- `total_cost`, `cumulative_cost`

---

## Audio behavior

The project supports these sound files in `assets/`:

- `game_start.mp3` — plays ~3s when entering Start screen
- `game_play.mp3` — loops while playing on the Game screen
- `game_over.mp3` — plays ~5s when entering End screen
- `game_click.mp3` — plays up to ~3s on each button/tap action

---

## Project structure (high level)

```
pygame_team_4/
  main.py
  config.py
  assets/
  ui/
    pygame_ui.py
    sound_manager.py
    screens/
      login_screen.py
      auth_screen.py
      config_screen.py
      game_screen.py
      end_screen.py
      analysis_screen.py
  simulation/
    simulation_engine.py
    logger.py
  persistence/
    csv_export.py
    analysis_tools.py
  logs/
    game.csv
  exports/
    (created when exporting)
```

---

## Troubleshooting

- **No sound?**
  - Ensure the mp3 files exist in `assets/`
  - Make sure your system audio output works
  - Some systems need `pygame.mixer.init()` to succeed (already handled best-effort)

- **Assets not found?**
  - Run the game **from the project root** (same folder as `main.py`)
  - Keep the `assets/` folder in place

- **Touch/pen clicks not registering?**
  - The project maps `FINGERDOWN` (touch) to button clicks for supported screens.


## Analysis deliverables (requirements)

This repository includes:

- `exports/batch/*.csv` — **CSV logs for all demand scenarios** and control configurations (AI Base-Stock, AI PI, Human(heuristic)).
- `BeerGame_Analysis.ipynb` (and `analysis/BeerGame_Analysis.ipynb`) — analysis notebook that produces:
  - Summary tables (total cost, avg inventory/backlog, service level, bullwhip ratio **Var[orders]/Var[demand]**)
  - Plots over time (inventory, backlog, orders, shipments per tier)
  - Bullwhip bar chart by tier
  - Policy comparison (Base-Stock vs PI vs Human-control)
  - Reflection (≤ 1 page)

### Regenerating the batch CSV logs

From the repo root:

```bash
python analysis/batch_generate_logs.py
```

### Running the notebook

Open `BeerGame_Analysis.ipynb` in Jupyter / VS Code and run all cells.

Recommended packages (analysis only):

```bash
pip install pandas numpy matplotlib
```
