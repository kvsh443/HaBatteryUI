import os
import requests
import urllib3
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer, Static, Digits, ProgressBar
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
            # Left column: Battery & Status
            with Vertical(classes="gauge-container"):
                yield ProgressBar(
                    total=100,
                    show_eta=False,
                    show_percentage=False,
                    id=f"bar-{self.group_name}",
                )
                yield Digits("00", id=f"dig-{self.group_name}", classes="pack-digits")
                yield Static("", id=f"status-{self.group_name}", classes="status-badge")
                yield Static("TEMP (C)", classes="metric-header temp-header")
                yield Digits(
                    "00.0", id=f"tmp-dig-{self.group_name}", classes="metric-digits"
                )

            # Mid column: Power & Voltage & Run
            with Vertical(classes="col-mid"):
                yield Static("POWER (W)", classes="metric-header")
                yield Digits(
                    "0.0", id=f"pwr-dig-{self.group_name}", classes="metric-digits"
                )
                yield Static("VOLTAGE (V)", classes="metric-header")
                yield Digits(
                    "0.0", id=f"vol-dig-{self.group_name}", classes="metric-digits"
                )
                yield Static("RUN (MIN)", classes="metric-header")
                yield Digits(
                    "0.0", id=f"run-dig-{self.group_name}", classes="metric-digits"
                )

            # Right column: Current, Energy & Cycles
            with Vertical(classes="col-right"):
                yield Static("CURRENT (A)", classes="metric-header")
                yield Digits(
                    "0.00", id=f"cur-dig-{self.group_name}", classes="metric-digits"
                )
                yield Static("ENERGY (KWH)", classes="metric-header")
                yield Digits(
                    "0.0", id=f"nrg-dig-{self.group_name}", classes="metric-digits"
                )
                yield Static("CYCLES", classes="metric-header")
                yield Digits(
                    "0", id=f"cyc-dig-{self.group_name}", classes="metric-digits"
                )

    def display_error(self, message):
        clean_msg = str(message)[:60].replace("\n", " ")
        self.query_one(f"#status-{self.group_name}", Static).update(
            f"[red]Err: {escape(clean_msg)}[/]"
        )

    def update_data(self, states):
        pref = self.prefix

        def fmt(val, dec=1):
            try:
                # Digits widget only supports numbers, decimals, spaces, and '-'
                return f"{float(val):.{dec}f}"
            except (ValueError, TypeError):
                return "0.0"

        bat = states.get(f"sensor.{pref}_battery", {}).get("state", "0")
        chg = (
            states.get(f"binary_sensor.{pref}_charging", {}).get("state", "off").upper()
        )
        cur = fmt(states.get(f"sensor.{pref}_current", {}).get("state", "0"), 2)
        cyc = fmt(states.get(f"sensor.{pref}_cycles", {}).get("state", "0"), 0)
        pwr = fmt(states.get(f"sensor.{pref}_power", {}).get("state", "0"), 1)
        run = fmt(states.get(f"sensor.{pref}_runtime", {}).get("state", "0"), 1)
        nrg = fmt(states.get(f"sensor.{pref}_stored_energy", {}).get("state", "0"), 1)
        tmp = fmt(states.get(f"sensor.{pref}_temperature", {}).get("state", "0"), 1)
        vol = fmt(states.get(f"sensor.{pref}_voltage", {}).get("state", "0"), 1)

        bat_val = int(bat) if bat.isdigit() else 0
        bat_color = (
            "#48C774" if bat_val >= 75 else ("#FFDD57" if bat_val >= 35 else "#F14668")
        )

        # Update all 8 individual Digits widgets directly
        self.query_one(f"#dig-{self.group_name}", Digits).update(f"{bat_val}%")
        self.query_one(f"#dig-{self.group_name}", Digits).styles.color = bat_color

        self.query_one(f"#tmp-dig-{self.group_name}", Digits).update(tmp)
        self.query_one(f"#tmp-dig-{self.group_name}", Digits).styles.color = "#FF8080"

        pwr_wid = self.query_one(f"#pwr-dig-{self.group_name}", Digits)
        pwr_wid.update(pwr)
        pwr_wid.styles.color = "#00D2FF" if chg == "ON" else "#FFDD57"

        self.query_one(f"#vol-dig-{self.group_name}", Digits).update(vol)
        self.query_one(f"#vol-dig-{self.group_name}", Digits).styles.color = "#E1E8ED"

        self.query_one(f"#run-dig-{self.group_name}", Digits).update(run)
        self.query_one(f"#run-dig-{self.group_name}", Digits).styles.color = "#85A5FF"

        self.query_one(f"#cur-dig-{self.group_name}", Digits).update(cur)
        self.query_one(f"#cur-dig-{self.group_name}", Digits).styles.color = "#FFD666"

        self.query_one(f"#nrg-dig-{self.group_name}", Digits).update(nrg)
        self.query_one(f"#nrg-dig-{self.group_name}", Digits).styles.color = "#73D13D"

        self.query_one(f"#cyc-dig-{self.group_name}", Digits).update(cyc)
        self.query_one(f"#cyc-dig-{self.group_name}", Digits).styles.color = "#B37FEB"

        # Update responsive native ProgressBar
        bar_widget = self.query_one(f"#bar-{self.group_name}", ProgressBar)
        bar_widget.progress = bat_val
        bar_widget.styles.bar_complete_color = bat_color
        bar_widget.styles.bar_background_color = "#2A3B4D"

        # Dynamic Status Badge
        status_text = (
            "[bold #48C774]CHARGING[/]"
            if chg == "ON"
            else "[bold #FFDD57]DISCHARGING[/]"
        )
        self.query_one(f"#status-{self.group_name}", Static).update(status_text)


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
        width: 30%;
        align: center middle;
        text-align: center;
        padding: 1 1 0 1;
    }
    ProgressBar {
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    .pack-digits {
        text-align: center;
        height: 3;
        margin-bottom: 1;
    }
    .status-badge {
        text-align: center;
        height: 1;
    }
    .col-mid {
        width: 35%;
        padding: 1 1 0 1;
    }
    .col-right {
        width: 35%;
        padding: 1 1 0 1;
    }
    .metric-header {
        color: #8F9CA6;
        text-style: bold;
        height: 1;
    }
    .metric-digits {
        height: 3;
        margin-bottom: 1;
    }
    .temp-header {
        margin-top: 1;
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
