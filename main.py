from log_parser import parse_log
from analyzer import analyze_log
from colorama import Fore, Style
import argparse
import sys


def main():
    ap = argparse.ArgumentParser(description="Analyze a log file with Gemini")
    ap.add_argument("logfile", help="path to the log file")
    args = ap.parse_args()

    print(f"\n{Fore.CYAN}=== Analyzing {args.logfile} ==={Style.RESET_ALL}\n")
    try:
        data = parse_log(args.logfile)
        result = analyze_log(data)
    except FileNotFoundError:
        sys.exit(f"{Fore.RED}File not found: {args.logfile}{Style.RESET_ALL}")
    except RuntimeError as e:
        sys.exit(f"{Fore.RED}{e}{Style.RESET_ALL}")

    print(f"{Fore.GREEN}Analysis Summary:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{result}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()