# Home Assistant Battery UI (`habatteryui`)

A lightweight, real-time Terminal User Interface (TUI) grid for monitoring 6 distinct battery storage banks directly from your command line. Built with Python 3.12.3, Async Textual, and powered by the Home Assistant REST API.

## Features
- **2x3 Grid Layout**: Mirroring native dashboard vertical and horizontal stacks directly into terminal cards.
- **ASCII Optimized**: No complex emojis or non-standard UTF-8 symbols—guaranteed to render flawlessly in old Windows CMD, PowerShell, or SSH sessions.
- **Auto-Refreshing Engine**: Requests state updates securely over a 4-second asynchronous loop without flickering the interface.

---

## Architecture Requirements

### 1. Home Assistant Configuration (`configuration.yaml`)
The Home Assistant REST API layer must be explicitly enabled. Ensure your configuration file contains the `api:` directive:

```yaml
default_config:

# Enable the REST API engine for external script access
api:
```
*Remember to restart Home Assistant after updating your configuration.*

### 2. Environment Variables (`.env`)
Create a `.env` file in the project root to store your Long-Lived Access Token securely. **Do not commit this file to Git.**

```text
HA_KEY="your_long_lived_access_token_here"
```

---

## Installation & Setup

This project utilizes `uv` for fast, deterministic dependency tracking and environment isolation.

### 1. Clone & Enter Project Workspace
```bash
git clone https://github.com/kvsh443/HaBatteryUI
cd HaBatteryUI
```

### 2. Build the Isolated Environment
Force `uv` to construct a clean Python 3.12.3 environment and populate dependencies specified in `pyproject.toml`:

```bash
# Remove old environments if switching runtimes
rm -rf .venv

# Create virtual environment and sync packages
uv venv --python 3.12.3
uv sync
```

---

## Usage

To fetch live telemetry metrics and execute the visual monitoring console grid layout, run:

```bash
uv run python main.py
```

### Keybindings & Controls
- `Ctrl + C`: Cleanly exit the terminal app grid interface loop.

---

## Monitored Metric Layout
Each system card tracks the following telemetry array:
- **Status**: Visual charging flags with an active blinking `[C]` notification loop when pulling power.
- **Power Vectors**: Power (W), Voltage (V), and Current (A).
- **Health Tracking**: Total Cycle counts and Cumulative Stored Energy (kWh).
- **Core Environment**: Temperature (C) and Expected Runtime (min).
