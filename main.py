from parser import parse_log
from analyzer import analyze_log
from colorama import Fore, Style
import argparse


def main():
    #read in argument
    parser = argparse.ArgumentParser()
    parser.add_argument("logfile")
    args = parser.parse_args()

    print(f"\n{Fore.CYAN}=== Analyzing {args.logfile} ==={Style.RESET_ALL}\n")
    data = parse_log(args.logfile)
    result = analyze_log(data)
    
    print(f"{Fore.GREEN}🧠 Analysis Summary:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{result}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()