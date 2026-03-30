"""
ui.py – Tkinter UI for the ERP-Based Integrated Student Management System.

All business logic / DB calls are imported from logic.py.
Run this file directly to launch the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime

# ── Import all business logic ──────────────────
from logic import (
    init_db, verify_login,
    get_dashboard_stats, get_recent_students,
    search_students, get_student, add_student, update_student,
    delete_student, export_students_csv,
    get_students_for_course, get_existing_attendance, save_attendance,
    search_grades, upsert_grade,
    get_all_fees, add_fee, mark_fee_paid,
    get_all_courses, get_course_codes, add_course, delete_course,
    get_all_users, add_user, delete_user,
    get_student_name_map,
)


# ─────────────────────────────────────────────
#  COLOUR / STYLE CONSTANTS  (minimalist)
# ─────────────────────────────────────────────

BG      = "#F7F7F5"
SURFACE = "#FFFFFF"
BORDER  = "#E4E4E0"
TEXT    = "#1A1A18"
MUTED   = "#9A9A95"
ACCENT  = "#2563EB"
DANGER  = "#DC2626"
SUCCESS = "#16A34A"

FONT_H1   = ("Georgia", 22, "bold")
FONT_H2   = ("Georgia", 15, "bold")
FONT_BODY = ("Helvetica Neue", 11)
FONT_MONO = ("Courier New", 10)
FONT_SM   = ("Helvetica Neue", 9)


# ─────────────────────────────────────────────
#  REUSABLE WIDGET HELPERS
# ─────────────────────────────────────────────

def card(parent, **kw):
    return tk.Frame(parent, bg=SURFACE, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER, **kw)


def label(parent, text, font=FONT_BODY, fg=TEXT, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=parent["bg"], **kw)


def btn(parent, text, cmd, fg=SURFACE, bg=ACCENT, **kw):
    return tk.Button(
        parent, text=text, command=cmd,
        font=FONT_BODY, fg=fg, bg=bg,
        relief="flat", cursor="hand2",
        padx=14, pady=6,
        activebackground=ACCENT, activeforeground=SURFACE, **kw,
    )


def entry(parent, textvariable=None, width=28, **kw):
    return tk.Entry(
        parent, textvariable=textvariable, width=width,
        font=FONT_BODY, relief="flat", bg=BG,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT, insertbackground=TEXT, **kw,
    )


def separator(parent):
    return tk.Frame(parent, bg=BORDER, height=1)


def make_tree(parent, cols, heights=400):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Minimal.Treeview",
                    background=SURFACE, foreground=TEXT,
                    rowheight=28, fieldbackground=SURFACE,
                    borderwidth=0, font=FONT_BODY)
    style.configure("Minimal.Treeview.Heading",
                    background=BG, foreground=MUTED,
                    font=FONT_SM, relief="flat", borderwidth=0)
    style.map("Minimal.Treeview",
              background=[("selected", "#EFF6FF")],
              foreground=[("selected", ACCENT)])

    frame = tk.Frame(parent, bg=SURFACE)
    tree = ttk.Treeview(frame, columns=cols, show="headings",
                        style="Minimal.Treeview", height=heights)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="w")
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return frame, tree


# ─────────────────────────────────────────────
#  LOGIN WINDOW
# ─────────────────────────────────────────────

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student ERP")
        self.geometry("380x460")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._build()
        self.eval("tk::PlaceWindow . center")

    def _build(self):
        outer = tk.Frame(self, bg=BG)
        outer.place(relx=.5, rely=.5, anchor="center")

        label(outer, "⬡ ERP", font=("Georgia", 13), fg=ACCENT).pack()
        label(outer, "Student Management", font=FONT_H1).pack(pady=(4, 2))
        label(outer, "Sign in to continue", font=FONT_SM, fg=MUTED).pack(pady=(0, 30))

        self.uvar = tk.StringVar(value="admin")
        self.pvar = tk.StringVar()

        for lbl, var, show in [("Username", self.uvar, ""),
                                ("Password", self.pvar, "•")]:
            tk.Label(outer, text=lbl, font=FONT_SM, fg=MUTED, bg=BG, anchor="w").pack(fill="x")
            e = entry(outer, textvariable=var, show=show, width=34)
            e.pack(pady=(2, 14), ipady=6)

        btn(outer, "Sign In", self._login, width=34).pack(fill="x", ipady=4)
        label(outer, "Default: admin / admin123", font=FONT_SM, fg=MUTED).pack(pady=(14, 0))
        self.bind("<Return>", lambda e: self._login())

    def _login(self):
        result = verify_login(self.uvar.get().strip(), self.pvar.get())
        if result:
            uid, role = result
            self.destroy()
            MainApp(uid, role, self.uvar.get().strip()).mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


# ─────────────────────────────────────────────
#  MAIN APP SHELL
# ─────────────────────────────────────────────

class MainApp(tk.Tk):
    def __init__(self, uid, role, username):
        super().__init__()
        self.uid      = uid
        self.role     = role
        self.username = username
        self.title("Student ERP System")
        self.geometry("1180x700")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._build()
        self.eval("tk::PlaceWindow . center")
        self._switch("Dashboard")

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = tk.Frame(self, bg=TEXT, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self._build_sidebar()

        # Content area
        self.content = tk.Frame(self, bg=BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Top bar
        topbar = tk.Frame(self.content, bg=SURFACE,
                          highlightthickness=1, highlightbackground=BORDER)
        topbar.grid(row=0, column=0, sticky="ew", ipady=8)
        self.page_title = tk.Label(topbar, text="", font=FONT_H2, fg=TEXT, bg=SURFACE)
        self.page_title.pack(side="left", padx=24)
        tk.Label(topbar, text=f"👤 {self.username}  [{self.role}]",
                 font=FONT_SM, fg=MUTED, bg=SURFACE).pack(side="right", padx=24)

        # Page container
        self.page_frame = tk.Frame(self.content, bg=BG)
        self.page_frame.grid(row=1, column=0, sticky="nsew")
        self.page_frame.grid_rowconfigure(0, weight=1)
        self.page_frame.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self):
        tk.Label(self.sidebar, text="⬡ ERP", font=("Georgia", 14, "bold"),
                 fg=SURFACE, bg=TEXT).pack(pady=(24, 4))
        tk.Label(self.sidebar, text="Student System",
                 font=FONT_SM, fg=MUTED, bg=TEXT).pack()
        tk.Frame(self.sidebar, bg="#2E2E2C", height=1).pack(fill="x", pady=18, padx=16)

        pages = ["Dashboard", "Students", "Attendance", "Grades", "Fees", "Courses"]
        if self.role == "admin":
            pages.append("Users")

        icons = {
            "Dashboard": "⊞", "Students": "◈", "Attendance": "◷",
            "Grades": "◉", "Fees": "◎", "Courses": "⊟", "Users": "⊕",
        }

        self.nav_btns = {}
        self._current = None

        for name in pages:
            f = tk.Frame(self.sidebar, bg=TEXT, cursor="hand2")
            f.pack(fill="x", padx=8, pady=1)
            lbl = tk.Label(f, text=f"  {icons.get(name, '')}  {name}",
                           font=FONT_BODY, fg="#CCCCCA", bg=TEXT,
                           anchor="w", padx=8, pady=8)
            lbl.pack(fill="x")
            for w in (f, lbl):
                w.bind("<Button-1>", lambda e, n=name: self._switch(n))
                w.bind("<Enter>",    lambda e, w=lbl: w.config(fg=SURFACE))
                w.bind("<Leave>",    lambda e, w=lbl, n=name: w.config(
                    fg=SURFACE if self._current == n else "#CCCCCA"))
            self.nav_btns[name] = (f, lbl)

        tk.Frame(self.sidebar, bg="#2E2E2C", height=1).pack(fill="x", pady=16, padx=16)
        lo = tk.Label(self.sidebar, text="  ⏻  Log out",
                      font=FONT_BODY, fg="#CCCCCA", bg=TEXT,
                      anchor="w", padx=8, pady=8, cursor="hand2")
        lo.pack(fill="x", padx=8)
        lo.bind("<Button-1>", self._logout)

    def _switch(self, name):
        if self._current and self._current in self.nav_btns:
            f, lbl = self.nav_btns[self._current]
            f.config(bg=TEXT); lbl.config(bg=TEXT, fg="#CCCCCA")
        self._current = name
        f, lbl = self.nav_btns[name]
        f.config(bg=ACCENT); lbl.config(bg=ACCENT, fg=SURFACE)
        self.page_title.config(text=name)
        for w in self.page_frame.winfo_children():
            w.destroy()
        pages = {
            "Dashboard":  DashboardPage,
            "Students":   StudentsPage,
            "Attendance": AttendancePage,
            "Grades":     GradesPage,
            "Fees":       FeesPage,
            "Courses":    CoursesPage,
            "Users":      UsersPage,
        }
        pages.get(name, DashboardPage)(self.page_frame, self.role).pack(fill="both", expand=True)

    def _logout(self, event=None):
        if messagebox.askyesno("Log Out", "Log out and return to login screen?"):
            self.destroy()
            LoginWindow().mainloop()


# ─────────────────────────────────────────────
#  DASHBOARD PAGE
# ─────────────────────────────────────────────

class DashboardPage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        pad = dict(padx=28, pady=22)
        stats = get_dashboard_stats()

        # Stats row
        stats_row = tk.Frame(self, bg=BG)
        stats_row.pack(fill="x", **pad)
        for i, (title, val, color) in enumerate([
            ("Total Students",  stats["students"], ACCENT),
            ("Courses Offered", stats["courses"],  SUCCESS),
            ("Present Today",   stats["present"],  "#D97706"),
            ("Pending Fees",    stats["pending"],  DANGER),
        ]):
            c_ = card(stats_row, padx=20, pady=18)
            c_.grid(row=0, column=i, padx=8, sticky="ew")
            stats_row.columnconfigure(i, weight=1)
            tk.Frame(c_, bg=color, width=4).pack(side="left", fill="y")
            inner = tk.Frame(c_, bg=SURFACE)
            inner.pack(side="left", padx=14)
            label(inner, str(val), font=("Georgia", 26, "bold"), fg=color).pack(anchor="w")
            label(inner, title, font=FONT_SM, fg=MUTED).pack(anchor="w")

        # Mid section
        mid = tk.Frame(self, bg=BG)
        mid.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        mid.columnconfigure(0, weight=2)
        mid.columnconfigure(1, weight=1)

        # Recent students table
        c1 = card(mid)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        label(c1, "Recent Students", font=FONT_H2).pack(anchor="w", padx=16, pady=(14, 8))
        separator(c1).pack(fill="x")
        tf, tree = make_tree(c1, ("ID", "Name", "Course", "Semester"), heights=8)
        tf.pack(fill="both", expand=True, padx=4, pady=4)
        for row in get_recent_students():
            tree.insert("", "end", values=row)

        # Quick actions
        c2 = card(mid)
        c2.grid(row=0, column=1, sticky="nsew")
        label(c2, "Quick Actions", font=FONT_H2).pack(anchor="w", padx=16, pady=(14, 8))
        separator(c2).pack(fill="x")
        for txt, cmd in [
            ("＋  Add Student",     lambda: None),
            ("✓   Mark Attendance", lambda: None),
            ("⬇   Export Data",    lambda: None),
        ]:
            tk.Button(c2, text=txt, command=cmd,
                      font=FONT_BODY, fg=TEXT, bg=BG,
                      relief="flat", anchor="w", padx=16, pady=10,
                      highlightthickness=1, highlightbackground=BORDER,
                      cursor="hand2").pack(fill="x", padx=12, pady=4)


# ─────────────────────────────────────────────
#  STUDENTS PAGE
# ─────────────────────────────────────────────

class StudentsPage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=16)
        label(bar, "Students", font=FONT_H2).pack(side="left")
        btn(bar, "＋ Add Student", self._add).pack(side="right", padx=4)
        btn(bar, "⬇ Export CSV", self._export, bg=TEXT).pack(side="right", padx=4)

        sbar = tk.Frame(self, bg=BG)
        sbar.pack(fill="x", padx=24, pady=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._load())
        label(sbar, "Search:", fg=MUTED).pack(side="left")
        entry(sbar, textvariable=self.search_var, width=32).pack(side="left", padx=8, ipady=4)

        c = card(self)
        c.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        cols = ("ID", "Name", "Email", "Phone", "Course", "Semester", "DOB")
        tf, self.tree = make_tree(c, cols, heights=16)
        tf.pack(fill="both", expand=True, padx=4, pady=4)
        for col in cols:
            self.tree.column(col, width=110)
        self.tree.bind("<Double-1>", self._edit)
        self._load()

        btbar = tk.Frame(self, bg=BG)
        btbar.pack(fill="x", padx=24, pady=(0, 12))
        btn(btbar, "✕ Delete Selected", self._delete, bg=DANGER).pack(side="left")

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in search_students(self.search_var.get()):
            self.tree.insert("", "end", values=row)

    def _add(self):
        StudentDialog(self, "Add Student", None, self._load)

    def _edit(self, event):
        sel = self.tree.focus()
        if not sel: return
        sid = self.tree.item(sel)["values"][0]
        StudentDialog(self, "Edit Student", sid, self._load)

    def _delete(self):
        sel = self.tree.focus()
        if not sel: return
        sid = self.tree.item(sel)["values"][0]
        if messagebox.askyesno("Delete", f"Delete student {sid}?"):
            delete_student(sid)
            self._load()

    def _export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path: return
        export_students_csv(path)
        messagebox.showinfo("Exported", f"Saved to {path}")


class StudentDialog(tk.Toplevel):
    FIELDS = [
        ("Student ID",              "student_id"),
        ("Full Name",               "name"),
        ("Email",                   "email"),
        ("Phone",                   "phone"),
        ("Course",                  "course"),
        ("Semester",                "semester"),
        ("Date of Birth (YYYY-MM-DD)", "dob"),
        ("Address",                 "address"),
    ]

    def __init__(self, parent, title, student_id, refresh_cb):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.refresh_cb = refresh_cb
        self.student_id = student_id
        self.vars = {}
        self._build()
        if student_id:
            self._load_data(student_id)
        self.grab_set()
        self.eval(f"tk::PlaceWindow {self} center")

    def _build(self):
        tk.Label(self, text=self.title(), font=FONT_H2,
                 fg=TEXT, bg=BG).pack(padx=24, pady=(18, 4), anchor="w")
        separator(self).pack(fill="x", padx=24, pady=6)

        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=24, pady=8)
        for i, (lbl, key) in enumerate(self.FIELDS):
            r, col = divmod(i, 2)
            tk.Label(grid, text=lbl, font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(
                row=r*2, column=col, sticky="w", padx=(0, 30), pady=(6, 1))
            v = tk.StringVar()
            self.vars[key] = v
            entry(grid, textvariable=v).grid(row=r*2+1, column=col, sticky="ew", padx=(0, 30), ipady=4)

        separator(self).pack(fill="x", padx=24, pady=10)
        bbar = tk.Frame(self, bg=BG)
        bbar.pack(padx=24, pady=(0, 18), anchor="e")
        btn(bbar, "Cancel", self.destroy, fg=TEXT, bg=BORDER).pack(side="left", padx=(0, 8))
        btn(bbar, "Save", self._save).pack(side="left")

    def _load_data(self, sid):
        row = get_student(sid)
        if row:
            for (_, key), val in zip(self.FIELDS, row):
                self.vars[key].set(val or "")

    def _save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["student_id"] or not data["name"]:
            messagebox.showwarning("Validation", "Student ID and Name are required.")
            return
        if self.student_id:
            update_student(self.student_id, data)
        else:
            if not add_student(data):
                messagebox.showerror("Error", "Student ID already exists.")
                return
        self.refresh_cb()
        self.destroy()


# ─────────────────────────────────────────────
#  ATTENDANCE PAGE
# ─────────────────────────────────────────────

class AttendancePage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=16)
        label(bar, "Attendance", font=FONT_H2).pack(side="left")

        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=24, pady=(0, 12))

        label(ctrl, "Date:", fg=MUTED).pack(side="left")
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        entry(ctrl, textvariable=self.date_var, width=14).pack(side="left", padx=(6, 16), ipady=4)

        label(ctrl, "Course:", fg=MUTED).pack(side="left")
        self.course_var = tk.StringVar()
        courses = get_course_codes()
        cb = ttk.Combobox(ctrl, textvariable=self.course_var, values=courses, width=12, state="readonly")
        cb.pack(side="left", padx=(6, 16))
        if courses: cb.current(0)

        btn(ctrl, "Load Students",   self._load,  ).pack(side="left", padx=4)
        btn(ctrl, "Save Attendance", self._save, bg=SUCCESS).pack(side="left", padx=4)

        c_frame = card(self)
        c_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        header = tk.Frame(c_frame, bg=BG)
        header.pack(fill="x", padx=8, pady=(8, 2))
        for txt, w in [("Student ID", 120), ("Name", 200), ("Status", 120)]:
            tk.Label(header, text=txt, font=FONT_SM, fg=MUTED, bg=BG,
                     width=w//8, anchor="w").pack(side="left")
        separator(c_frame).pack(fill="x")

        canvas = tk.Canvas(c_frame, bg=SURFACE, bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(c_frame, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=SURFACE)
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.status_vars = {}

    def _load(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.status_vars.clear()

        date   = self.date_var.get()
        course = self.course_var.get()
        students = get_students_for_course(course)
        existing = get_existing_attendance(date, course)

        for sid, name in students:
            row = tk.Frame(self.scroll_frame, bg=SURFACE)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=sid,  font=FONT_MONO, fg=MUTED, bg=SURFACE, width=15, anchor="w").pack(side="left")
            tk.Label(row, text=name, font=FONT_BODY, fg=TEXT,  bg=SURFACE, width=25, anchor="w").pack(side="left")
            var = tk.StringVar(value=existing.get(sid, "Present"))
            self.status_vars[sid] = var
            for st, clr in [("Present", SUCCESS), ("Absent", DANGER), ("Late", "#D97706")]:
                tk.Radiobutton(row, text=st, variable=var, value=st,
                               font=FONT_SM, fg=clr, bg=SURFACE,
                               selectcolor=SURFACE, activebackground=SURFACE).pack(side="left", padx=6)

    def _save(self):
        if not self.status_vars:
            messagebox.showwarning("No Data", "Load students first.")
            return
        save_attendance(self.date_var.get(), self.course_var.get(),
                        {sid: v.get() for sid, v in self.status_vars.items()})
        messagebox.showinfo("Saved", "Attendance saved successfully.")


# ─────────────────────────────────────────────
#  GRADES PAGE
# ─────────────────────────────────────────────

class GradesPage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=16)
        label(bar, "Grades", font=FONT_H2).pack(side="left")
        btn(bar, "＋ Add / Update Grade", self._add).pack(side="right")

        fbar = tk.Frame(self, bg=BG)
        fbar.pack(fill="x", padx=24, pady=(0, 10))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._load())
        label(fbar, "Search:", fg=MUTED).pack(side="left")
        entry(fbar, textvariable=self.search_var, width=28).pack(side="left", padx=8, ipady=4)

        c = card(self)
        c.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        cols = ("Student ID", "Student Name", "Course", "Semester", "Marks", "Grade")
        tf, self.tree = make_tree(c, cols, heights=16)
        tf.pack(fill="both", expand=True, padx=4, pady=4)
        self._load()

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in search_grades(self.search_var.get()):
            self.tree.insert("", "end", values=row)

    def _add(self):
        GradeDialog(self, self._load)


class GradeDialog(tk.Toplevel):
    def __init__(self, parent, refresh_cb):
        super().__init__(parent)
        self.title("Add / Update Grade")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.refresh_cb = refresh_cb
        self._build()
        self.grab_set()
        self.eval(f"tk::PlaceWindow {self} center")

    def _build(self):
        label(self, "Grade Entry", font=FONT_H2).pack(padx=24, pady=(18, 4), anchor="w")
        separator(self).pack(fill="x", padx=24, pady=6)

        g = tk.Frame(self, bg=BG)
        g.pack(padx=24, pady=8)

        students = get_student_name_map()
        courses  = get_course_codes()

        fields = [("Student", "student", students),
                  ("Course",  "course",  courses)]
        self.vars = {}
        for i, (lbl, key, vals) in enumerate(fields):
            tk.Label(g, text=lbl, font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(
                row=0, column=i, sticky="w", padx=(0, 20))
            v = tk.StringVar()
            self.vars[key] = v
            cb = ttk.Combobox(g, textvariable=v, values=vals, width=22, state="readonly")
            cb.grid(row=1, column=i, padx=(0, 20), pady=(2, 10))
            if vals: cb.current(0)

        tk.Label(g, text="Semester",      font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(row=2, column=0, sticky="w")
        tk.Label(g, text="Marks (0–100)", font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(row=2, column=1, sticky="w")
        self.sem_var   = tk.StringVar(value="1")
        self.marks_var = tk.StringVar()
        entry(g, textvariable=self.sem_var,   width=10).grid(row=3, column=0, sticky="w", ipady=4)
        entry(g, textvariable=self.marks_var, width=10).grid(row=3, column=1, sticky="w", ipady=4)

        separator(self).pack(fill="x", padx=24, pady=10)
        bbar = tk.Frame(self, bg=BG)
        bbar.pack(padx=24, pady=(0, 18), anchor="e")
        btn(bbar, "Cancel", self.destroy, fg=TEXT, bg=BORDER).pack(side="left", padx=(0, 8))
        btn(bbar, "Save", self._save).pack(side="left")

    def _save(self):
        sid_raw = self.vars["student"].get().split("–")[0].strip()
        course  = self.vars["course"].get().strip()
        try:
            sem   = int(self.sem_var.get())
            marks = float(self.marks_var.get())
        except ValueError:
            messagebox.showwarning("Validation", "Enter valid semester and marks.")
            return
        upsert_grade(sid_raw, course, sem, marks)
        self.refresh_cb()
        self.destroy()


# ─────────────────────────────────────────────
#  FEES PAGE
# ─────────────────────────────────────────────

class FeesPage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=16)
        label(bar, "Fee Management", font=FONT_H2).pack(side="left")
        btn(bar, "＋ Add Fee",   self._add).pack(side="right", padx=4)
        btn(bar, "✓ Mark Paid", self._mark_paid, bg=SUCCESS).pack(side="right", padx=4)

        c = card(self)
        c.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        cols = ("ID", "Student ID", "Amount", "Paid", "Due Date", "Status", "Description")
        tf, self.tree = make_tree(c, cols, heights=16)
        tf.pack(fill="both", expand=True, padx=4, pady=4)
        self._load()

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in get_all_fees():
            tag = "paid" if row[5] == "Paid" else "pending"
            self.tree.insert("", "end", values=row, tags=(tag,))
        self.tree.tag_configure("paid",    foreground=SUCCESS)
        self.tree.tag_configure("pending", foreground=DANGER)

    def _add(self):
        FeeDialog(self, self._load)

    def _mark_paid(self):
        sel = self.tree.focus()
        if not sel: return
        fid = self.tree.item(sel)["values"][0]
        mark_fee_paid(fid)
        self._load()


class FeeDialog(tk.Toplevel):
    def __init__(self, parent, refresh_cb):
        super().__init__(parent)
        self.title("Add Fee Record")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.refresh_cb = refresh_cb
        self._build()
        self.grab_set()
        self.eval(f"tk::PlaceWindow {self} center")

    def _build(self):
        label(self, "New Fee", font=FONT_H2).pack(padx=24, pady=(18, 4), anchor="w")
        separator(self).pack(fill="x", padx=24, pady=6)

        g = tk.Frame(self, bg=BG)
        g.pack(padx=24, pady=8)
        self.vars = {}
        fields = [
            ("Student ID",             "student_id"),
            ("Amount",                 "amount"),
            ("Due Date (YYYY-MM-DD)",  "due_date"),
            ("Description",            "description"),
        ]
        for i, (lbl, key) in enumerate(fields):
            r, col = divmod(i, 2)
            tk.Label(g, text=lbl, font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(
                row=r*2, column=col, sticky="w", padx=(0, 24), pady=(6, 1))
            v = tk.StringVar()
            self.vars[key] = v
            entry(g, textvariable=v).grid(row=r*2+1, column=col, sticky="ew", padx=(0, 24), ipady=4)

        separator(self).pack(fill="x", padx=24, pady=10)
        bbar = tk.Frame(self, bg=BG)
        bbar.pack(padx=24, pady=(0, 18), anchor="e")
        btn(bbar, "Cancel", self.destroy, fg=TEXT, bg=BORDER).pack(side="left", padx=(0, 8))
        btn(bbar, "Save",   self._save).pack(side="left")

    def _save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["student_id"] or not data["amount"]:
            messagebox.showwarning("Validation", "Student ID and Amount are required.")
            return
        try:
            float(data["amount"])
        except ValueError:
            messagebox.showwarning("Validation", "Amount must be a number.")
            return
        add_fee(data["student_id"], data["amount"], data["due_date"], data["description"])
        self.refresh_cb()
        self.destroy()


# ─────────────────────────────────────────────
#  COURSES PAGE
# ─────────────────────────────────────────────

class CoursesPage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=16)
        label(bar, "Courses", font=FONT_H2).pack(side="left")
        btn(bar, "＋ Add Course", self._add).pack(side="right")

        c = card(self)
        c.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        cols = ("Code", "Name", "Department", "Credits")
        tf, self.tree = make_tree(c, cols, heights=18)
        tf.pack(fill="both", expand=True, padx=4, pady=4)
        for col, w in zip(cols, [100, 240, 140, 80]):
            self.tree.column(col, width=w)
        self._load()

        btbar = tk.Frame(self, bg=BG)
        btbar.pack(fill="x", padx=24, pady=(0, 12))
        btn(btbar, "✕ Delete", self._delete, bg=DANGER).pack(side="left")

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in get_all_courses():
            self.tree.insert("", "end", values=row)

    def _add(self):
        d = tk.Toplevel(self)
        d.title("Add Course"); d.configure(bg=BG); d.resizable(False, False)
        label(d, "New Course", font=FONT_H2).pack(padx=24, pady=(18, 4), anchor="w")
        separator(d).pack(fill="x", padx=24, pady=6)
        g = tk.Frame(d, bg=BG); g.pack(padx=24, pady=8)
        vs = {}
        for i, (lbl, key) in enumerate([("Code","code"),("Name","name"),
                                         ("Department","dept"),("Credits","credits")]):
            r, col = divmod(i, 2)
            tk.Label(g, text=lbl, font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(
                row=r*2, column=col, sticky="w", padx=(0, 20), pady=(6, 1))
            v = tk.StringVar(); vs[key] = v
            entry(g, textvariable=v).grid(row=r*2+1, column=col, sticky="ew", padx=(0, 20), ipady=4)
        separator(d).pack(fill="x", padx=24, pady=10)
        bbar = tk.Frame(d, bg=BG); bbar.pack(padx=24, pady=(0, 18), anchor="e")

        def save():
            if not add_course(vs["code"].get(), vs["name"].get(),
                              vs["dept"].get(), vs["credits"].get()):
                messagebox.showerror("Error", "Course code already exists.")
                return
            self._load(); d.destroy()

        btn(bbar, "Cancel", d.destroy, fg=TEXT, bg=BORDER).pack(side="left", padx=(0, 8))
        btn(bbar, "Save", save).pack(side="left")
        d.grab_set(); d.eval(f"tk::PlaceWindow {d} center")

    def _delete(self):
        sel = self.tree.focus()
        if not sel: return
        code = self.tree.item(sel)["values"][0]
        if messagebox.askyesno("Delete", f"Delete course {code}?"):
            delete_course(code)
            self._load()


# ─────────────────────────────────────────────
#  USERS PAGE  (admin only)
# ─────────────────────────────────────────────

class UsersPage(tk.Frame):
    def __init__(self, parent, role):
        super().__init__(parent, bg=BG)
        self.role = role
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=16)
        label(bar, "User Management", font=FONT_H2).pack(side="left")
        btn(bar, "＋ Add User", self._add).pack(side="right")

        c = card(self)
        c.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        cols = ("ID", "Username", "Role")
        tf, self.tree = make_tree(c, cols, heights=18)
        tf.pack(fill="both", expand=True, padx=4, pady=4)
        self._load()

        btbar = tk.Frame(self, bg=BG)
        btbar.pack(fill="x", padx=24, pady=(0, 12))
        btn(btbar, "✕ Delete Selected", self._delete, bg=DANGER).pack(side="left")

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in get_all_users():
            self.tree.insert("", "end", values=row)

    def _add(self):
        d = tk.Toplevel(self); d.title("Add User"); d.configure(bg=BG); d.resizable(False, False)
        label(d, "New User", font=FONT_H2).pack(padx=24, pady=(18, 4), anchor="w")
        separator(d).pack(fill="x", padx=24, pady=6)
        g = tk.Frame(d, bg=BG); g.pack(padx=24, pady=8)
        uv = tk.StringVar(); pv = tk.StringVar(); rv = tk.StringVar(value="staff")
        for i, (lbl, v, show) in enumerate([("Username", uv, ""), ("Password", pv, "•")]):
            tk.Label(g, text=lbl, font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(
                row=i*2, column=0, sticky="w", pady=(6, 1))
            entry(g, textvariable=v, show=show).grid(row=i*2+1, column=0, sticky="ew", ipady=4)
        tk.Label(g, text="Role", font=FONT_SM, fg=MUTED, bg=BG, anchor="w").grid(
            row=4, column=0, sticky="w", pady=(10, 1))
        rf = tk.Frame(g, bg=BG); rf.grid(row=5, column=0, sticky="w")
        for role in ("staff", "admin"):
            tk.Radiobutton(rf, text=role.capitalize(), variable=rv, value=role,
                           font=FONT_BODY, bg=BG, fg=TEXT,
                           selectcolor=BG).pack(side="left", padx=6)
        separator(d).pack(fill="x", padx=24, pady=10)
        bbar = tk.Frame(d, bg=BG); bbar.pack(padx=24, pady=(0, 18), anchor="e")

        def save():
            if not uv.get() or not pv.get():
                messagebox.showwarning("Validation", "Username and password required.")
                return
            if not add_user(uv.get(), pv.get(), rv.get()):
                messagebox.showerror("Error", "Username already exists.")
                return
            self._load(); d.destroy()

        btn(bbar, "Cancel", d.destroy, fg=TEXT, bg=BORDER).pack(side="left", padx=(0, 8))
        btn(bbar, "Save", save).pack(side="left")
        d.grab_set(); d.eval(f"tk::PlaceWindow {d} center")

    def _delete(self):
        sel = self.tree.focus()
        if not sel: return
        uid = self.tree.item(sel)["values"][0]
        if messagebox.askyesno("Delete", "Delete this user?"):
            delete_user(uid)
            self._load()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()
