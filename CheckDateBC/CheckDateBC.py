import os
import glob

def main():
    ap = argparse.ArgumentParser(description="Validate and fix Excel date columns (openpyxl-only).")
    ap.add_argument("--in", dest="inp", help="Input .xlsx file")
    ap.add_argument("--all", action="store_true", help="Process all .xlsx files in current folder")
    ap.add_argument("--out", dest="out", default=None, help="Output corrected .xlsx (default: append _corrected)")
    ap.add_argument("--report", dest="report", default=None, help="Issues report .xlsx (default: append _report)")
    ap.add_argument("--year-min", type=int, default=DEFAULT_YEAR_MIN, help="Minimum valid year (default 2000)")
    ap.add_argument("--year-max", type=int, default=DEFAULT_YEAR_MAX, help="Maximum valid year (default 2099)")
    ap.add_argument("--last-row", type=int, default=None, help="Only process rows up to this Excel row number (inclusive)")
    args = ap.parse_args()

    if args.all:
        files = [f for f in glob.glob("*.xlsx") if "_corrected" not in f and "_report" not in f]
        if not files:
            print("No Excel files found to process.")
            return
        for f in files:
            out = f[:-5] + "_corrected.xlsx"
            report = f[:-5] + "_report.xlsx"
            print(f"Processing {f}...")
            fixed, invalid = process_workbook(f, out, report, args.year_min, args.year_max, args.last_row)
            print(f"Done: {f} | Fixed: {fixed} | Invalid: {invalid}")
    elif args.inp:
        inp = args.inp
        out = args.out or (inp[:-5] + "_corrected.xlsx" if inp.lower().endswith(".xlsx") else inp + "_corrected.xlsx")
        report = args.report or (inp[:-5] + "_report.xlsx" if inp.lower().endswith(".xlsx") else inp + "_report.xlsx")
        fixed, invalid = process_workbook(inp, out, report, args.year_min, args.year_max, args.last_row)
        print(f"Done. Fixed: {fixed}   Invalid (flagged in report): {invalid}")
        print(f"Corrected workbook: {out}")
        print(f"Issues report: {report}")
    else:
        print("Error: Please provide --in <file.xlsx> or --all")