"""
Clinic Visit Sorter - Desktop Graphical User Interface (GUI)
CIT AI-Native Engineering Programme · Semester 1 · Assessment 5

Built using Python's standard tkinter and ttk libraries (zero external installations needed).
Features:
- Live Dashboard cards: Total Students, See Now, Today, Routine, Red Flags.
- Interactive Priority Queue Table with color-coded urgency rows.
- Dynamic filtering (All, See Now, Today, Routine, Red Flags).
- Search bar to filter notes, symptoms, student IDs.
- 'Run Sorting / Triage' button to trigger classification and report generation.
- Full inspection modal for student notes & triage summaries.
- One-click access to generated nurse_queue.csv and summary.txt.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

# Import our verified core logic from main.py
from main import load_visits, classify, PRIORITY_ORDER, write_reports

# Ensure UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class ClinicSorterGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Clinic Visit Sorter - Nurse Triage Dashboard")
        self.geometry("1150x720")
        self.minsize(950, 600)
        self.configure(bg="#F1F5F9")

        # Color Palette
        self.colors = {
            "bg": "#F8FAFC",
            "sidebar": "#0F172A",
            "card_bg": "#FFFFFF",
            "text_main": "#0F172A",
            "text_muted": "#64748B",
            "see_now": "#DC2626",      # Crimson Red
            "today": "#D97706",         # Amber Orange
            "routine": "#16A34A",       # Forest Green
            "accent": "#2563EB",        # Royal Blue
            "border": "#E2E8F0"
        }

        self.data_records = []
        self.filtered_records = []

        self.build_ui()
        self.load_and_run_pipeline()

    def build_ui(self):
        # Top Header Bar
        header = tk.Frame(self, bg=self.colors["sidebar"], height=65)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="🏥 CLINIC VISIT SORTER",
            font=("Segoe UI", 16, "bold"),
            fg="#FFFFFF",
            bg=self.colors["sidebar"]
        )
        title_lbl.pack(side=tk.LEFT, padx=20, pady=12)

        subtitle_lbl = tk.Label(
            header,
            text="College Health Centre • Nurse Triage & Prioritization Console",
            font=("Segoe UI", 10),
            fg="#94A3B8",
            bg=self.colors["sidebar"]
        )
        subtitle_lbl.pack(side=tk.LEFT, padx=5, pady=16)

        # Action Buttons in Header
        btn_refresh = tk.Button(
            header,
            text="🔄 Re-Run Triage",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.load_and_run_pipeline
        )
        btn_refresh.pack(side=tk.RIGHT, padx=15, pady=14)

        btn_summary = tk.Button(
            header,
            text="📊 View summary.txt",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#FFFFFF",
            activebackground="#475569",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.open_summary_modal
        )
        btn_summary.pack(side=tk.RIGHT, padx=5, pady=14)

        # Metric Cards Container
        self.cards_frame = tk.Frame(self, bg=self.colors["bg"], pady=12, padx=20)
        self.cards_frame.pack(side=tk.TOP, fill=tk.X)

        self.card_total = self.create_metric_card(self.cards_frame, "Total Students", "30", "#3B82F6")
        self.card_see_now = self.create_metric_card(self.cards_frame, "SEE NOW (Urgent)", "0", self.colors["see_now"])
        self.card_today = self.create_metric_card(self.cards_frame, "TODAY", "0", self.colors["today"])
        self.card_routine = self.create_metric_card(self.cards_frame, "ROUTINE", "0", self.colors["routine"])
        self.card_red_flags = self.create_metric_card(self.cards_frame, "Red-Flag Cases", "0", "#9333EA")

        # Controls & Filter Bar
        ctrl_frame = tk.Frame(self, bg=self.colors["bg"], padx=20, pady=6)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        lbl_filter = tk.Label(ctrl_frame, text="Filter By Priority:", font=("Segoe UI", 9, "bold"), bg=self.colors["bg"], fg=self.colors["text_main"])
        lbl_filter.pack(side=tk.LEFT, padx=(0, 8))

        self.filter_var = tk.StringVar(value="All")
        for f_label in ["All", "see_now", "today", "routine", "Red Flags Only"]:
            rb = tk.Radiobutton(
                ctrl_frame,
                text=f_label.replace("_", " ").title(),
                variable=self.filter_var,
                value=f_label,
                font=("Segoe UI", 9),
                bg=self.colors["bg"],
                activebackground=self.colors["bg"],
                command=self.apply_filters
            )
            rb.pack(side=tk.LEFT, padx=5)

        # Search Bar
        lbl_search = tk.Label(ctrl_frame, text="Search Note / ID:", font=("Segoe UI", 9, "bold"), bg=self.colors["bg"], fg=self.colors["text_main"])
        lbl_search.pack(side=tk.RIGHT, padx=(10, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.apply_filters())
        search_entry = tk.Entry(ctrl_frame, textvariable=self.search_var, font=("Segoe UI", 9), width=22)
        search_entry.pack(side=tk.RIGHT, padx=4)

        # Treeview / Table Frame
        table_frame = tk.Frame(self, bg="#FFFFFF", padx=20, pady=10)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("id", "time", "priority", "red_flag", "category", "summary", "note")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("time", text="Arrival")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("red_flag", text="Red Flag?")
        self.tree.heading("category", text="Category")
        self.tree.heading("summary", text="Symptom Summary (Max 12 Words)")
        self.tree.heading("note", text="Original Student Note")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("time", width=70, anchor="center")
        self.tree.column("priority", width=90, anchor="center")
        self.tree.column("red_flag", width=85, anchor="center")
        self.tree.column("category", width=95, anchor="center")
        self.tree.column("summary", width=320, anchor="w")
        self.tree.column("note", width=380, anchor="w")

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<Double-1>", self.on_item_double_click)

        # Style Treeview
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#E2E8F0", foreground="#1E293B")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)

        # Color row tags
        self.tree.tag_configure("see_now", background="#FEE2E2", foreground="#991B1B")    # Soft Red
        self.tree.tag_configure("today", background="#FEF3C7", foreground="#92400E")      # Soft Amber
        self.tree.tag_configure("routine", background="#DCFCE7", foreground="#166534")    # Soft Green

        # Status Bar
        self.status_bar = tk.Label(
            self,
            text="Ready • Double-click any row to view complete patient details",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            fg="#475569",
            anchor="w",
            padx=15,
            pady=4
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_metric_card(self, parent, title, initial_val, accent_color):
        card = tk.Frame(parent, bg="#FFFFFF", bd=1, relief=tk.SOLID, padx=14, pady=10)
        card.configure(highlightbackground="#E2E8F0", highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)

        lbl_title = tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"), fg=self.colors["text_muted"], bg="#FFFFFF")
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(card, text=initial_val, font=("Segoe UI", 20, "bold"), fg=accent_color, bg="#FFFFFF")
        lbl_val.pack(anchor="w", pady=(2, 0))

        return lbl_val

    def load_and_run_pipeline(self):
        system_prompt = ""
        if os.path.exists("system_prompt.txt"):
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()

        api_key = os.environ.get("LLM_API_KEY")

        visits = load_visits("visits.csv")
        if not visits:
            messagebox.showerror("Error", "Could not load records from visits.csv")
            return

        processed = []
        for v in visits:
            res = classify(v["note"], system_prompt, api_key)
            processed.append({
                "id": v["id"],
                "time": v["time"],
                "note": v["note"],
                "category": res["category"],
                "priority": res["priority"],
                "summary": res["summary"],
                "is_red_flag": res["is_red_flag"]
            })

        # Sort queue
        self.data_records = sorted(
            processed,
            key=lambda item: (PRIORITY_ORDER.get(item["priority"], 99), item["time"])
        )

        # Write reports
        write_reports(self.data_records, "nurse_queue.csv", "summary.txt")

        # Update metric cards
        total_cnt = len(self.data_records)
        c_see_now = sum(1 for s in self.data_records if s["priority"] == "see_now")
        c_today = sum(1 for s in self.data_records if s["priority"] == "today")
        c_routine = sum(1 for s in self.data_records if s["priority"] == "routine")
        c_rf = sum(1 for s in self.data_records if s["is_red_flag"])

        self.card_total.config(text=str(total_cnt))
        self.card_see_now.config(text=str(c_see_now))
        self.card_today.config(text=str(c_today))
        self.card_routine.config(text=str(c_routine))
        self.card_red_flags.config(text=str(c_rf))

        self.status_bar.config(text=f"Queue updated • {total_cnt} students processed • nurse_queue.csv & summary.txt regenerated successfully")
        self.apply_filters()

    def apply_filters(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_choice = self.filter_var.get()
        query = self.search_var.get().strip().lower()

        for s in self.data_records:
            # Priority / Red Flag filter
            if filter_choice == "Red Flags Only" and not s["is_red_flag"]:
                continue
            elif filter_choice in ["see_now", "today", "routine"] and s["priority"] != filter_choice:
                continue

            # Text Search filter
            if query:
                combined_text = f"{s['id']} {s['category']} {s['summary']} {s['note']}".lower()
                if query not in combined_text:
                    continue

            tag = s["priority"]
            rf_str = "⚠️ YES" if s["is_red_flag"] else "NO"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    s["id"],
                    s["time"],
                    s["priority"].upper(),
                    rf_str,
                    s["category"].title(),
                    s["summary"],
                    s["note"]
                ),
                tags=(tag,)
            )

    def on_item_double_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        values = self.tree.item(selected_item[0], "values")
        if not values:
            return

        detail_win = tk.Toplevel(self)
        detail_win.title(f"Patient Detail - Student {values[0]}")
        detail_win.geometry("540x380")
        detail_win.configure(bg="#FFFFFF", padx=20, pady=20)

        tk.Label(detail_win, text=f"Student ID: {values[0]}", font=("Segoe UI", 14, "bold"), bg="#FFFFFF", fg="#0F172A").pack(anchor="w")
        tk.Label(detail_win, text=f"Arrival Time: {values[1]}  |  Category: {values[4]}", font=("Segoe UI", 10), bg="#FFFFFF", fg="#64748B").pack(anchor="w", pady=(0, 10))

        pri_color = self.colors["see_now"] if "SEE_NOW" in values[2] else (self.colors["today"] if "TODAY" in values[2] else self.colors["routine"])
        tk.Label(detail_win, text=f"Priority: {values[2]}  (Red Flag: {values[3]})", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg=pri_color).pack(anchor="w", pady=(0, 15))

        tk.Label(detail_win, text="AI Symptom Summary (No Diagnosis):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        sum_box = tk.Text(detail_win, height=3, font=("Segoe UI", 10), bg="#F8FAFC", relief=tk.SOLID, bd=1)
        sum_box.insert(tk.END, values[5])
        sum_box.configure(state="disabled")
        sum_box.pack(fill=tk.X, pady=(2, 12))

        tk.Label(detail_win, text="Original Student Arrival Note:", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        note_box = tk.Text(detail_win, height=3, font=("Segoe UI", 10), bg="#F8FAFC", relief=tk.SOLID, bd=1)
        note_box.insert(tk.END, values[6])
        note_box.configure(state="disabled")
        note_box.pack(fill=tk.X, pady=(2, 12))

        btn_close = tk.Button(detail_win, text="Close", font=("Segoe UI", 9, "bold"), bg="#0F172A", fg="#FFFFFF", padx=15, pady=4, command=detail_win.destroy)
        btn_close.pack(anchor="e")

    def open_summary_modal(self):
        if not os.path.exists("summary.txt"):
            messagebox.showinfo("Summary", "summary.txt has not been generated yet.")
            return

        with open("summary.txt", "r", encoding="utf-8") as f:
            content = f.read()

        win = tk.Toplevel(self)
        win.title("Health Centre Administrative Summary (summary.txt)")
        win.geometry("520x480")
        win.configure(bg="#FFFFFF", padx=15, pady=15)

        tk.Label(win, text="Administrative Summary", font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#0F172A").pack(anchor="w", pady=(0, 8))

        text_area = tk.Text(win, wrap=tk.WORD, font=("Consolas", 10), bg="#F8FAFC", relief=tk.SOLID, bd=1)
        text_area.insert(tk.END, content)
        text_area.configure(state="disabled")
        text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Button(win, text="Close", font=("Segoe UI", 9), bg="#0F172A", fg="#FFFFFF", padx=12, pady=4, command=win.destroy).pack(anchor="e")


if __name__ == "__main__":
    app = ClinicSorterGUI()
    app.mainloop()
