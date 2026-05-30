import os
import requests
import urllib3
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer, Static, Digits
from textual.containers import Grid, Horizontal, Vertical
from rich.markup import escape


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
        yield Static(
            f" 🔋 [bold white]System {self.group_name}[/]", classes="pack-title"
        )
        with Horizontal():
            with Vertical(classes="gauge-container"):
                yield Static("", id=f"gauge-{self.group_name}", classes="gauge-arc")
                yield Digits("00", id=f"dig-{self.group_name}", classes="pack-digits")
            with Vertical(classes="stats-container"):
                yield Static(
                    "Loading details...",
                    id=f"stats-{self.group_name}",
                    classes="pack-stats",
                )

    def display_error(self, message):
        clean_msg = str(message)[:60].replace("\n", " ")
        self.query_one(f"#stats-{self.group_name}", Static).update(
            f"[red]Err: {escape(clean_msg)}[/]"
        )

    def update_data(self, states):
        pref = self.prefix

        def fmt(val, dec=1):
            try:
                return f"{float(val):.{dec}f}"
            except (ValueError, TypeError):
                return "N/A"

        bat = states.get(f"sensor.{pref}_battery", {}).get("state", "0")
        chg = (
            states.get(f"binary_sensor.{pref}_charging", {}).get("state", "off").upper()
        )
        cur = fmt(states.get(f"sensor.{pref}_current", {}).get("state", "N/A"), 2)
        cyc = fmt(states.get(f"sensor.{pref}_cycles", {}).get("state", "0"), 0)
        pwr = fmt(states.get(f"sensor.{pref}_power", {}).get("state", "N/A"), 1)
        run = fmt(states.get(f"sensor.{pref}_runtime", {}).get("state", "N/A"), 2)
        nrg = fmt(states.get(f"sensor.{pref}_stored_energy", {}).get("state", "N/A"), 1)
        tmp = fmt(states.get(f"sensor.{pref}_temperature", {}).get("state", "N/A"), 1)
        vol = fmt(states.get(f"sensor.{pref}_voltage", {}).get("state", "N/A"), 1)

        bat_val = int(bat) if bat.isdigit() else 0
        bat_color = (
            "#48C774" if bat_val >= 75 else ("#FFDD57" if bat_val >= 35 else "#F14668")
        )

        # Power bar visual representation
        pwr_val = abs(float(pwr)) if pwr != "N/A" else 0
        bar_filled = min(int(pwr_val / 30), 8)
        pwr_bar = (
            f" [{'#48C774' if chg == 'ON' else '#FFDD57'}]"
            + "█" * bar_filled
            + "░" * (8 - bar_filled)
            + "[/]"
        )

        # 1. Update native Digits for maximum font visibility
        digits_widget = self.query_one(f"#dig-{self.group_name}", Digits)
        digits_widget.update(f"{bat_val}%")
        digits_widget.styles.color = bat_color

        # 2. Dynamic Segment Coloring for the gauge arc above the digits
        bg_color = "#2A3B4D"
        c1 = bat_color if bat_val > 0 else bg_color
        c2 = bat_color if bat_val >= 25 else bg_color
        c3 = bat_color if bat_val >= 50 else bg_color
        c4 = bat_color if bat_val >= 75 else bg_color

        gauge_text = f"   [{c2}]▄▄████████▄▄[/]\n [{c1}]▄██▀▀[/]        [{c3}]▀▀██▄[/]"
        self.query_one(f"#gauge-{self.group_name}", Static).update(gauge_text)

        # 3. Dynamic Side Details
        status_text = (
            "[bold #48C774] CHARGING ⬆[/]"
            if chg == "ON"
            else "[bold #FFDD57] DISCHARGING ⬇[/]"
        )
        stats_text = (
            f"       {status_text}\n\n"
            f"[bold #8F9CA6]POWER & CURRENT[/]\n"
            f"P: [bold white]{pwr} W[/] {pwr_bar}\n"
            f"I: [bold white]{cur} A[/]\n\n"
            f"⚡ [bold #00D2FF]Energy: {nrg} kWh[/]\n"
            f"[bold #8F9CA6]VOLTAGE & LIFE[/]\n"
            f"V: [bold white]{vol} V[/] [#30404D][/]\n"
            f"Cycles: [bold white]{cyc}[/]\n\n"
            f"[bold #8F9CA6]OPERATING CONDITIONS[/]\n"
            f"🌡️ [white]Temp:[/ white] [bold white]{tmp}°C[/] [red]■■[/]\n"
            f"⏱️ [white]Run:[/ white]  [bold white]{run} min[/]"
        )
        self.query_one(f"#stats-{self.group_name}", Static).update(stats_text)


class BatteryApp(App):
    """The central User Interface Grid Engine."""

    TITLE = "Home Assistant Battery Monitoring Grid"
    CSS = """
    Screen {
        background: #11161B;
    }
    Header {
        background: #182026;
        color: #00D2FF;
        text-style: bold;
    }
    Grid {
        grid-size: 3 2;
        grid-gutter: 2 2;
        padding: 1 2;
    }
    BatteryPack {
        background: #182026;
        border: tall #2A3B4D;
        padding: 0;
        height: 100%;
    }
    .pack-title {
        color: #E1E8ED;
        text-style: bold;
        background: #202B36;
        padding: 0 1;
        height: 1;
    }
    .gauge-container {
        width: 45%;
        align: center middle;
        text-align: center;
        padding-top: 1;
    }
    .gauge-arc {
        text-align: center;
        height: 2;
    }
    .pack-digits {
        text-align: center;
        margin: 0;
        padding: 0;
        height: 3;
    }
    .stats-container {
        width: 55%;
        padding: 1 1 0 1;
    }
    .pack-stats {
        color: #A7B6C2;
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
                    for g_id in BATTERY_GROUPS.keys():
                        self.query_one(f"#pack-{g_id}", BatteryPack).display_error(
                            f"Bad JSON: {r.text[:30]}"
                        )
            else:
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
