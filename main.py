import os
import requests
import urllib3
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer, Static, Digits

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
TOKEN = os.getenv("HA_KEY")
HA_URL = os.getenv("URL")

if not TOKEN:
    raise ValueError("Critical Error: 'HA_KEY' not found in .env file.")


BATTERY_GROUPS = {
    "1": {"prefix": "1"},
    "2": {"prefix": "c8_47_80_2f_7f_c9"},
    "3": {"prefix": "c8_47_80_2f_4b_d8"},
    "4": {"prefix": "4"},
    "5": {"prefix": "c8_47_80_30_5f_d7"},
    "6": {"prefix": "c8_47_80_30_37_de"},
}


class BatteryPack(Static):
    """A visual widget module representing one system panel."""

    def __init__(self, group_name, config, **kwargs):
        super().__init__(**kwargs)
        self.group_name = group_name
        self.config = config
        self.prefix = config["prefix"]

    def compose(self) -> ComposeResult:
        yield Static(f"[b]System {self.group_name}[/b]", classes="pack-title")
        yield Digits("00%", id=f"dig-{self.group_name}", classes="pack-digits")
        yield Static(
            "Loading data...", id=f"stats-{self.group_name}", classes="pack-stats"
        )

    def display_error(self, message):
        """Displays error logs natively in the specific panel block."""
        # Truncate messages to keep the panel structure neat
        clean_msg = str(message)[:60].replace("\n", " ")
        self.query_one(f"#stats-{self.group_name}", Static).update(
            f"[red]Err: {clean_msg}[/]"
        )

    def update_data(self, states):
        pref = self.prefix

        bat = states.get(f"sensor.{pref}_battery", {}).get("state", "0")
        chg = (
            states.get(f"binary_sensor.{pref}_charging", {}).get("state", "off").upper()
        )
        cur = states.get(f"sensor.{pref}_current", {}).get("state", "N/A")
        cyc = states.get(f"sensor.{pref}_cycles", {}).get("state", "N/A")
        pwr = states.get(f"sensor.{pref}_power", {}).get("state", "N/A")
        run = states.get(f"sensor.{pref}_runtime", {}).get("state", "N/A")
        nrg = states.get(f"sensor.{pref}_stored_energy", {}).get("state", "N/A")
        tmp = states.get(f"sensor.{pref}_temperature", {}).get("state", "N/A")
        vol = states.get(f"sensor.{pref}_voltage", {}).get("state", "N/A")

        bat_val = int(bat) if bat.isdigit() else 0
        color = "green" if bat_val > 50 else ("orange" if bat_val > 20 else "red")
        flash = " [blink][yellow][C][/yellow][/blink]" if chg == "ON" else ""

        self.query_one(f"#dig-{self.group_name}", Digits).update(f"{bat_val}%")

        stats_text = (
            f"[{color}]* Status:[/] {'Charging' if chg == 'ON' else 'Discharging'}{flash}\n"
            f"  P: {pwr} W  |  V: {vol} V  |  I: {cur} A\n"
            f"  Cycles: {cyc}  |  Energy: {nrg} kWh\n"
            f"  Temp: {tmp} C  |  Run: {run} min"
        )
        self.query_one(f"#stats-{self.group_name}", Static).update(stats_text)


class BatteryApp(App):
    """The central User Interface Grid Engine."""

    TITLE = "Home Assistant Battery Monitoring Grid"
    CSS = """
    Grid {
        grid-size: 2 3;
        grid-gutter: 2 1;
        padding: 1;
    }
    BatteryPack {
        background: $surface;
        border: solid $primary;
        padding: 1 2;
        border-title-align: center;
    }
    .pack-title {
        text-align: center;
        color: $accent;
    }
    .pack-digits {
        text-align: center;
        margin: 0 0 1 0;
    }
    .pack-stats {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Grid():
            for g_id, config in BATTERY_GROUPS.items():
                yield BatteryPack(group_name=g_id, config=config, id=f"pack-{g_id}")
        yield Footer()

    def on_mount(self) -> None:
        self.headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        }
        self.set_interval(4.0, self.refresh_ha_metrics)
        self.refresh_ha_metrics()

    def refresh_ha_metrics(self) -> None:
        try:
            r = requests.get(HA_URL, headers=self.headers, timeout=3, verify=False)
            if r.status_code == 200:
                try:
                    states_lookup = {item["entity_id"]: item for item in r.json()}
                    for g_id in BATTERY_GROUPS.keys():
                        self.query_one(f"#pack-{g_id}", BatteryPack).update_data(
                            states_lookup
                        )
                except ValueError:
                    # Capture case where HTTP 200 is returned but the text body isn't JSON
                    for g_id in BATTERY_GROUPS.keys():
                        self.query_one(f"#pack-{g_id}", BatteryPack).display_error(
                            f"Bad JSON: {r.text[:30]}"
                        )
            else:
                # Capture standard server error pages (404, 500, etc.)
                for g_id in BATTERY_GROUPS.keys():
                    self.query_one(f"#pack-{g_id}", BatteryPack).display_error(
                        f"HTTP {r.status_code}: {r.text[:20]}"
                    )
        except Exception as e:
            error_msg = str(e).split(":")[-1].strip() or "Connection Timeout"
            for g_id in BATTERY_GROUPS.keys():
                self.query_one(f"#pack-{g_id}", BatteryPack).display_error(error_msg)


if __name__ == "__main__":
    BatteryApp().run()
