
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# -------------------------
# Core helpers (self-contained)
# -------------------------

def normalise_string(x):
    if pd.isna(x):
        return np.nan
    s = str(x)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)  # collapse whitespace
    s = s.upper()
    return s

def normalise_phone(x):
    if pd.isna(x):
        return np.nan
    s = re.sub(r"[^\d+]", "", str(x))  # keep digits and leading +
    return s if s else np.nan

def load_table(path: Path, sheet: Optional[str] = None) -> pd.DataFrame:
    ext = path.suffix.lower()
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path, sheet_name=sheet) if sheet else pd.read_excel(path)
    elif ext in [".csv", ".txt"]:
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin-1")
    else:
        raise ValueError(f"Unsupported file type: {ext} for {path}")

def pick_first_present(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    # Case- and punctuation-insensitive
    norm_cols = {re.sub(r"[\W_]+", " ", c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = re.sub(r"[\W_]+", " ", cand).strip().lower()
        if key in norm_cols:
            return norm_cols[key]
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

ATTRIBUTE_ALIASES: Dict[str, List[str]] = {
    "Supplier Name": ["Supplier Name", "Vendor Name", "Name", "Supplier", "Vendor"],
    "Supplier Number": ["Supplier Number", "Vendor Number", "Supplier ID", "Vendor ID", "Supplier No", "Vendor No", "Number", "ID", "Reference"],
    "Alternate Name": ["Alternate Name", "Alt Name", "AKA", "Also Known As"],
    "CIS Supplier": ["CIS Supplier", "CIS"],
    "Unique Tax Reference UTR": ["Unique Tax Reference UTR", "UTR", "Unique Tax Reference", "Unique Taxpayer Reference"],
    "Tax Registration Number": ["Tax Registration Number", "Tax Reg Number", "TRN", "VAT Number", "VAT Registration Number", "Tax Number"],
    "First Name": ["First Name", "Given Name", "Forename"],
    "Last Name": ["Last Name", "Surname", "Family Name"],
    "Phone": ["Phone", "Telephone", "Tel", "Phone Number", "Mobile", "Mobile Phone"],
    "E-Mail": ["E-Mail", "Email", "E-mail", "Mail", "Email Address"],
    "Address Name": ["Address Name", "Address", "Address Line 1", "Address1", "Street"],
    "Pay": ["Pay"],
    "Site Purchasing": ["Site Purchasing", "Purchasing Site", "Site", "Site Name"],
    "Payment Terms": ["Payment Terms", "Terms", "Payment Term"],
    "Bank Currency": ["Bank Currency", "Currency", "Bank Curr", "Curr"],
}

KEY_ALIASES = {
    "name": ["Supplier Name", "Vendor Name", "Name", "Supplier", "Vendor"],
    "number": ["Supplier Number", "Vendor Number", "Supplier ID", "Vendor ID", "Supplier No", "Vendor No", "Number", "ID"],
    "reference": ["Reference", "Ref", "Supplier Ref", "Vendor Ref"],
}

def build_match_index(df: pd.DataFrame, id_priority: List[str]) -> pd.DataFrame:
    out = df.copy()
    resolved = {}
    for key, cands in KEY_ALIASES.items():
        col = pick_first_present(df, cands)
        resolved[key] = col

    out["_key_name"] = df[resolved["name"]].map(normalise_string) if resolved.get("name") else np.nan
    out["_key_number"] = df[resolved["number"]].map(normalise_string) if resolved.get("number") else np.nan
    out["_key_reference"] = df[resolved["reference"]].map(normalise_string) if resolved.get("reference") else np.nan
    out["_match_priority"] = None
    out.attrs["_key_columns_resolved"] = resolved
    return out

def match_other_to_master(master_idx: pd.DataFrame, other_idx: pd.DataFrame, id_priority: List[str]) -> Tuple[pd.DataFrame, str]:
    for key in id_priority:
        left_key = f"_key_{key}"
        right_key = f"_key_{key}"
        if left_key in master_idx.columns and right_key in other_idx.columns:
            if master_idx[left_key].notna().any() and other_idx[right_key].notna().any():
                merged = master_idx.merge(
                    other_idx,
                    how="left",
                    left_on=left_key,
                    right_on=right_key,
                    suffixes=("", "_other"),
                )
                merged["_match_priority"] = key
                return merged, key

    cross_pairs = [("number", "reference"), ("name", "reference"), ("number", "name")]
    for l, r in cross_pairs:
        lcol = f"_key_{l}"
        rcol = f"_key_{r}"
        if lcol in master_idx.columns and rcol in other_idx.columns:
            if master_idx[lcol].notna().any() and other_idx[rcol].notna().any():
                merged = master_idx.merge(
                    other_idx,
                    how="left",
                    left_on=lcol,
                    right_on=rcol,
                    suffixes=("", "_other"),
                )
                merged["_match_priority"] = f"{l}->{r}"
                return merged, f"{l}->{r}"

    merged = master_idx.copy()
    for c in other_idx.columns:
        if c not in merged.columns:
            merged[c] = np.nan
    merged["_match_priority"] = "unmatched"
    return merged, "unmatched"

def resolve_attribute_column(df: pd.DataFrame, attribute: str) -> Optional[str]:
    cands = ATTRIBUTE_ALIASES.get(attribute, [attribute])
    return pick_first_present(df, cands)

def compute_presence_by_file(
    master: pd.DataFrame,
    others: List[Tuple[str, pd.DataFrame]],
    attributes: List[str],
    id_priority: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    name_col = resolve_attribute_column(master, "Supplier Name")
    number_col = resolve_attribute_column(master, "Supplier Number")
    if name_col is None and number_col is None:
        raise ValueError("Master file must have at least 'Supplier Name' or 'Supplier Number'.")

    master_idx = master.copy()
    master_idx["_key_name"] = master[name_col].map(normalise_string) if name_col else np.nan
    master_idx["_key_number"] = master[number_col].map(normalise_string) if number_col else np.nan
    master_idx["_key_reference"] = np.nan
    canonical_label = master_idx["_key_name"].fillna(master_idx["_key_number"]).fillna("UNKNOWN")
    master_idx["_supplier_label"] = canonical_label

    presence_records = []
    match_records = []

    for file_label, df in others:
        other_idx = build_match_index(df, id_priority)
        merged, how_matched = match_other_to_master(master_idx, other_idx, id_priority)
        match_records.append({"File": file_label, "Matched On": how_matched})

        for attr in attributes:
            col = resolve_attribute_column(df, attr)
            if col is None:
                has = pd.Series(False, index=merged.index)
            else:
                series = merged[col]
                if attr in ("Supplier Name","Alternate Name","First Name","Last Name","E-Mail","Address Name","Site Purchasing","Payment Terms","Bank Currency"):
                    series = series.map(lambda x: np.nan if pd.isna(x) else str(x).strip())
                elif attr in ("Phone",):
                    series = series.map(normalise_phone)
                else:
                    series = series.map(lambda x: np.nan if (pd.isna(x) or (isinstance(x, str) and str(x).strip()=='')) else x)

                has = series.notna()

            for sup, flag in zip(merged["_supplier_label"], has):
                presence_records.append({
                    "Supplier": sup,
                    "Attribute": attr,
                    "File": file_label,
                    "HasData": bool(flag),
                })

    presence_df = pd.DataFrame(presence_records)
    counts = presence_df.groupby(["Supplier", "Attribute"], as_index=False)["HasData"].sum()
    counts_wide = counts.pivot(index="Supplier", columns="Attribute", values="HasData").fillna(0).astype(int).reset_index()
    match_log_df = pd.DataFrame(match_records)
    return counts_wide, presence_df, match_log_df

ATTRIBUTES = [
    "Supplier Name","Supplier Number","Alternate Name","CIS Supplier","Unique Tax Reference UTR",
    "Tax Registration Number","First Name","Last Name","Phone","E-Mail","Address Name",
    "Pay","Site Purchasing","Payment Terms","Bank Currency"
]

DEFAULT_ID_PRIORITY = ["name","number","reference"]

def get_excel_sheets(path: Path) -> List[str]:
    try:
        if path.suffix.lower() in [".xlsx", ".xls"]:
            xf = pd.ExcelFile(path)
            return list(xf.sheet_names)
    except Exception:
        return []
    return []

# -------------------------
# GUI
# -------------------------

class SupplierAuditApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Supplier Data Coverage Audit")
        self.geometry("820x620")
        self.minsize(820, 620)

        # State
        self.avi_path: Optional[Path] = None
        self.avi_sheet: Optional[str] = None
        self.other_files: List[Path] = []
        self.other_sheets: Dict[Path, Optional[str]] = {}
        self.id_priority = DEFAULT_ID_PRIORITY.copy()
        self.output_path: Optional[Path] = None

        self._build_widgets()

    def _build_widgets(self):
        pad = 8

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=pad, pady=pad)

        # AVI file picker
        avi_frame = ttk.LabelFrame(frm, text="AVI Supplier List (Master)")
        avi_frame.pack(fill="x", padx=pad, pady=(0, pad))

        self.avi_label = ttk.Label(avi_frame, text="No file selected")
        self.avi_label.pack(side="left", padx=pad, pady=pad)

        ttk.Button(avi_frame, text="Select AVI file...", command=self.pick_avi).pack(side="right", padx=pad, pady=pad)

        # AVI sheet selector (populated after selecting excel)
        sheet_row = ttk.Frame(avi_frame)
        sheet_row.pack(fill="x", padx=pad, pady=(0, pad))
        ttk.Label(sheet_row, text="Sheet (optional):").pack(side="left")
        self.avi_sheet_combo = ttk.Combobox(sheet_row, state="disabled", width=40)
        self.avi_sheet_combo.pack(side="left", padx=(pad, 0))

        # Others
        others_frame = ttk.LabelFrame(frm, text="Other Supplier Files (5 expected; N supported)")
        others_frame.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        btns = ttk.Frame(others_frame)
        btns.pack(fill="x", padx=pad, pady=pad)
        ttk.Button(btns, text="Add files...", command=self.add_others).pack(side="left", padx=(0, pad))
        ttk.Button(btns, text="Remove selected", command=self.remove_selected).pack(side="left", padx=(0, pad))
        ttk.Button(btns, text="Clear", command=self.clear_others).pack(side="left", padx=(0, pad))
        ttk.Button(btns, text="Set sheet for selected…", command=self.set_sheet_selected).pack(side="left")

        self.listbox = tk.Listbox(others_frame, selectmode=tk.EXTENDED, height=10)
        self.listbox.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        # Options
        opts = ttk.LabelFrame(frm, text="Options")
        opts.pack(fill="x", padx=pad, pady=(0, pad))

        ttk.Label(opts, text="ID match priority (comma-separated):").pack(side="left", padx=(pad, 4))
        self.id_priority_var = tk.StringVar(value="name,number,reference")
        self.id_entry = ttk.Entry(opts, textvariable=self.id_priority_var, width=35)
        self.id_entry.pack(side="left", padx=(0, pad))

        ttk.Button(opts, text="Choose output…", command=self.choose_output).pack(side="right", padx=pad)

        self.output_label = ttk.Label(opts, text="No output file selected")
        self.output_label.pack(side="right", padx=(0, pad))

        # Run
        run_frame = ttk.Frame(frm)
        run_frame.pack(fill="x", padx=pad, pady=(pad, 0))
        self.run_btn = ttk.Button(run_frame, text="Run & Export", command=self.run_export)
        self.run_btn.pack(side="right")

        self.status_var = tk.StringVar(value="Status: idle")
        ttk.Label(run_frame, textvariable=self.status_var).pack(side="left")

    # ----- callbacks
    def pick_avi(self):
        p = filedialog.askopenfilename(
            title="Select AVI Supplier List",
            filetypes=[("Spreadsheets", "*.xlsx *.xls *.csv *.txt"), ("All files", "*.*")],
        )
        if not p:
            return
        self.avi_path = Path(p)
        self.avi_label.configure(text=str(self.avi_path))

        # Populate sheet names if Excel
        sheets = get_excel_sheets(self.avi_path)
        if sheets:
            self.avi_sheet_combo.configure(state="readonly", values=sheets)
            self.avi_sheet_combo.set(sheets[0])
        else:
            self.avi_sheet_combo.configure(state="disabled", values=[])
            self.avi_sheet_combo.set("")
        self.status_var.set("Status: AVI file selected")

    def add_others(self):
        paths = filedialog.askopenfilenames(
            title="Select other supplier files",
            filetypes=[("Spreadsheets", "*.xlsx *.xls *.csv *.txt"), ("All files", "*.*")],
        )
        if not paths:
            return
        for p in paths:
            path = Path(p)
            if path not in self.other_files:
                self.other_files.append(path)
                self.other_sheets[path] = None
                self.listbox.insert(tk.END, self._display_label(path))
        self.status_var.set(f"Status: {len(self.other_files)} file(s) selected")

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        sel.reverse()
        for idx in sel:
            path = self._path_from_label(self.listbox.get(idx))
            if path in self.other_files:
                self.other_files.remove(path)
                self.other_sheets.pop(path, None)
            self.listbox.delete(idx)
        self.status_var.set(f"Status: {len(self.other_files)} file(s) selected")

    def clear_others(self):
        self.other_files.clear()
        self.other_sheets.clear()
        self.listbox.delete(0, tk.END)
        self.status_var.set("Status: cleared other files")

    def set_sheet_selected(self):
        if not self.listbox.curselection():
            messagebox.showinfo("Set sheet", "Select one file in the list first.")
            return
        idxs = list(self.listbox.curselection())
        if len(idxs) != 1:
            messagebox.showinfo("Set sheet", "Please select exactly one file.")
            return
        label = self.listbox.get(idxs[0])
        path = self._path_from_label(label)
        sheets = get_excel_sheets(path)
        if not sheets:
            messagebox.showinfo("Set sheet", "Selected file is not an Excel workbook or has no readable sheets.")
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Select sheet for {path.name}")
        dlg.geometry("360x120")
        ttk.Label(dlg, text="Sheet:").pack(padx=8, pady=(12, 4))
        combo = ttk.Combobox(dlg, state="readonly", values=sheets)
        combo.set(sheets[0])
        combo.pack(padx=8, pady=4, fill="x")

        def apply_sheet():
            sel = combo.get()
            self.other_sheets[path] = sel
            # Update list display
            self._refresh_listbox()
            dlg.destroy()

        ttk.Button(dlg, text="OK", command=apply_sheet).pack(pady=8)

    def choose_output(self):
        p = filedialog.asksaveasfilename(
            title="Choose output Excel file",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="supplier_audit_output.xlsx",
        )
        if not p:
            return
        self.output_path = Path(p)
        self.output_label.configure(text=str(self.output_path))

    def run_export(self):
        try:
            self._run_export_impl()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Status: error")

    def _run_export_impl(self):
        if not self.avi_path:
            raise ValueError("Select the AVI Supplier List file.")
        if not self.other_files:
            raise ValueError("Add at least one other supplier file (5 expected).")
        if not self.output_path:
            raise ValueError("Choose an output Excel file.")

        idp_text = self.id_priority_var.get().strip()
        id_priority = [x.strip().lower() for x in idp_text.split(",") if x.strip()]
        if not id_priority:
            id_priority = DEFAULT_ID_PRIORITY

        # Load master
        avi_sheet = self.avi_sheet_combo.get().strip() if self.avi_sheet_combo.cget("state") == "readonly" else None
        master_df = load_table(self.avi_path, avi_sheet if avi_sheet else None)

        # Load others
        others = []
        for path in self.other_files:
            sheet = self.other_sheets.get(path)
            df = load_table(path, sheet)
            label = path.name if not sheet else f"{path.name}:{sheet}"
            others.append((label, df))

        counts_wide, presence_df, match_log_df = compute_presence_by_file(master_df, others, ATTRIBUTES, id_priority)

        # Ensure all expected columns present
        cols_order = ["Supplier"] + [a for a in ATTRIBUTES]
        for c in cols_order:
            if c not in counts_wide.columns:
                counts_wide[c] = 0
        counts_wide = counts_wide[cols_order]

        with pd.ExcelWriter(self.output_path, engine="xlsxwriter") as writer:
            counts_wide.to_excel(writer, index=False, sheet_name="summary_counts")
            presence_df.to_excel(writer, index=False, sheet_name="by_file_presence")
            match_log_df.to_excel(writer, index=False, sheet_name="match_log")

        self.status_var.set(f"Status: export complete -> {self.output_path}")
        messagebox.showinfo("Done", f"Export complete:\n{self.output_path}")

    # ----- helpers
    def _display_label(self, path: Path) -> str:
        sh = self.other_sheets.get(path)
        return f"{str(path)} [{sh}]" if sh else str(path)

    def _path_from_label(self, label: str) -> Path:
        # Label may have optional " [sheet]" suffix
        if label.endswith("]") and " [" in label:
            core = label[: label.rfind(" [")]
            return Path(core)
        return Path(label)

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for p in self.other_files:
            self.listbox.insert(tk.END, self._display_label(p))

if __name__ == "__main__":
    app = SupplierAuditApp()
    app.mainloop()
