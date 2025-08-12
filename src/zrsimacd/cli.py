import argparse
import os
import sys
import runpy
from pathlib import Path
from dotenv import load_dotenv

def _scripts_dir() -> Path:
    # Scripts are shipped inside the package under zrsimacd/scripts
    return Path(__file__).resolve().parent / "scripts"

def _exec(script_name: str, argv=None):
    """Execute a bundled script as if it was run directly."""
    script_path = _scripts_dir() / script_name
    if not script_path.exists():
        print(f"Script not found: {script_path}", file=sys.stderr)
        sys.exit(2)
    # pass through arguments to the script via sys.argv
    if argv is None:
        argv = sys.argv[:1] + []
    sys.argv = [str(script_path)] + (argv or [])
    runpy.run_path(str(script_path), run_name="__main__")

def main():
    load_dotenv()  # so scripts can read env like TINKOFF_TOKEN
    parser = argparse.ArgumentParser(prog="zrsimacd", description="RSI/MACD toolkit & Tinkoff fetcher")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fetch", help="Fetch candles via Tinkoff API (runs main_data_parser.py)")
    sub.add_parser("futures", help="Futures utilities (runs futures_expire_order.py)")
    sub.add_parser("indicators", help="Compute RSI/MACD from CSV (runs rsi_and_macd_calculation_V3.py)")
    sub.add_parser("analyze", help="Run final RSI/MACD analysis (runs analiz_danniv_v11_Finalv1.py)")
    sub.add_parser("report", help="Trades report utilities (runs analiz_trades_report_END.py)")

    args, rest = parser.parse_known_args()

    mapping = {
        "fetch": "main_data_parser.py",
        "futures": "futures_expire_order.py",
        "indicators": "rsi_and_macd_calculation_V3.py",
        "analyze": "analiz_danniv_v11_Finalv1.py",
        "report": "analiz_trades_report_END.py",
    }
    script = mapping[args.cmd]
    _exec(script, argv=rest)

if __name__ == "__main__":
    main()