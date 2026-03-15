from datetime import date, datetime, timedelta
import os
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# Database Models
class Patient(Base):
    __tablename__ = 'patient'
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    phone = Column(String(20))
    email = Column(String(120))
    address = Column(Text)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    blood_type = Column(String(10))
    allergies = Column(Text)
    medical_history = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    records = relationship('MedicalRecord', backref='patient', lazy=True, cascade='all, delete-orphan')

class MedicalRecord(Base):
    __tablename__ = 'medical_record'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient.id'), nullable=False)
    visit_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    chief_complaint = Column(Text)
    diagnosis = Column(Text)
    treatment = Column(Text)
    medications = Column(Text)
    notes = Column(Text)
    doctor_name = Column(String(100))
    vital_signs = Column(Text)  # BP, Temperature, Pulse, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FollowUpCheckup(Base):
    """Scheduled follow-up after a consultation."""
    __tablename__ = 'follow_up_checkup'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient.id'), nullable=False)
    record_id = Column(Integer, ForeignKey('medical_record.id'))  # visit that led to this follow-up
    scheduled_at = Column(DateTime, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default='scheduled')  # scheduled, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship('Patient', backref='follow_ups')
    record = relationship('MedicalRecord', backref='follow_ups_scheduled')


# Database setup
engine = create_engine('sqlite:///emr.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

class ModernEMRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EMR System - Electronic Medical Records")
        self.root.configure(bg='#eef2f7')
        self.root.minsize(1000, 650)
        
        # Fit window to current screen (avoid off-screen on 1366x768 etc.)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = max(1000, int(sw * 0.95))
        h = max(650, int(sh * 0.90))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Start maximized (Windows-friendly "full screen" window).
        # Keeps taskbar visible; falls back safely on other platforms.
        try:
            self.root.state('zoomed')
        except Exception:
            pass
        
        # Refined color palette - clean medical look
        self.colors = {
            'primary': '#1d4ed8',      # Deeper blue
            'primary_light': '#3b82f6',
            'secondary': '#6366f1',    # Indigo
            'success': '#059669',      # Emerald
            'info': '#0891b2',        # Teal
            'warning': '#d97706',     # Amber
            'danger': '#dc2626',      # Red
            'dark': '#0f172a',
            'light': '#f8fafc',
            'white': '#ffffff',
            'bg': '#eef2f7',
            'card_bg': '#ffffff',
            'border': '#cbd5e1',
            'border_light': '#e2e8f0',
            'text': '#0f172a',
            'text_secondary': '#475569'
        }
        
        # Fonts - slightly larger for readability
        self.fonts = {
            'title': ('Segoe UI', 22, 'bold'),
            'heading': ('Segoe UI', 15, 'bold'),
            'subheading': ('Segoe UI', 12, 'bold'),
            'body': ('Segoe UI', 11),
            'small': ('Segoe UI', 10)
        }
        
        # Consistent padding
        self.pad = {'x': 28, 'y': 24}
        
        # Layout state
        self._active_nav = None
        
        self.setup_ui()
        self._build_shell()
        self.show_dashboard()
    
    def _build_shell(self):
        """Build persistent modern layout: sidebar + content."""
        # Root shell
        self.shell = tk.Frame(self.root, bg=self.colors['bg'])
        self.shell.pack(fill='both', expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(self.shell, bg=self.colors['dark'], width=240)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        brand = tk.Frame(self.sidebar, bg=self.colors['dark'])
        brand.pack(fill='x', padx=18, pady=(18, 10))
        tk.Label(brand, text="EMR", font=('Segoe UI', 18, 'bold'),
                 bg=self.colors['dark'], fg='white').pack(anchor='w')
        tk.Label(brand, text="Electronic Medical Records", font=self.fonts['small'],
                 bg=self.colors['dark'], fg='#94a3b8').pack(anchor='w', pady=(4, 0))
        
        tk.Frame(self.sidebar, bg='#1f2937', height=1).pack(fill='x', padx=18, pady=(10, 14))
        
        self.nav_buttons = {}
        
        def nav_btn(key, text, command):
            b = tk.Button(
                self.sidebar,
                text=text,
                anchor='w',
                bg=self.colors['dark'],
                fg='#cbd5e1',
                activebackground='#111827',
                activeforeground='white',
                relief='flat',
                bd=0,
                padx=18,
                pady=12,
                font=self.fonts['body'],
                cursor='hand2',
                command=command,
            )
            b.pack(fill='x', pady=2)
            self.nav_buttons[key] = b
            self._apply_hover(b, self.colors['dark'], '#0b1220', normal_fg='#cbd5e1', hover_fg='white')
        
        nav_btn('dashboard', '  Dashboard', self.show_dashboard)
        nav_btn('patients',  '  Patients', self.show_patients)
        nav_btn('new_patient', '  New Patient', self.show_new_patient)
        nav_btn('new_record', '  New Record', self.show_new_record)
        nav_btn('search', '  Search Records', self.search_records)
        nav_btn('follow_ups', '  Follow-up checkups', self.show_follow_ups)
        
        # Bottom sidebar footer
        footer = tk.Frame(self.sidebar, bg=self.colors['dark'])
        footer.pack(side='bottom', fill='x', padx=18, pady=18)
        tk.Label(footer, text="Doctor Mode", font=self.fonts['small'],
                 bg=self.colors['dark'], fg='#94a3b8').pack(anchor='w')
        tk.Label(footer, text="Local Database: emr.db", font=self.fonts['small'],
                 bg=self.colors['dark'], fg='#64748b').pack(anchor='w', pady=(2, 0))
        
        # Main area
        self.main = tk.Frame(self.shell, bg=self.colors['bg'])
        self.main.pack(side='left', fill='both', expand=True)
        
        # Content root (all pages render here)
        self.content_root = tk.Frame(self.main, bg=self.colors['bg'])
        self.content_root.pack(fill='both', expand=True)
    
    def _set_active_nav(self, key: str | None):
        self._active_nav = key
        for k, b in self.nav_buttons.items():
            if k == key:
                b.configure(bg='#111827', fg='white')
            else:
                b.configure(bg=self.colors['dark'], fg='#cbd5e1')

    def _apply_hover(self, btn: tk.Widget, normal_bg: str, hover_bg: str, normal_fg: str | None = None, hover_fg: str | None = None):
        """Add a subtle hover effect to a tk.Button."""
        def on_enter(_e):
            btn.configure(bg=hover_bg)
            if hover_fg is not None:
                btn.configure(fg=hover_fg)
        def on_leave(_e):
            btn.configure(bg=normal_bg)
            if normal_fg is not None:
                btn.configure(fg=normal_fg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
    
    def _make_scrollable(self, parent):
        """Create a canvas + vertical scrollbar; returns scrollable frame."""
        container = tk.Frame(parent, bg=parent.cget('bg'))
        container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(container, bg=parent.cget('bg'), highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview, style='Vertical.TScrollbar')
        
        scrollable = tk.Frame(canvas, bg=parent.cget('bg'))
        scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        win_id = canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_canvas_configure(evt):
            canvas.itemconfig(win_id, width=evt.width)
        canvas.bind('<Configure>', _on_canvas_configure)
        
        scrollbar.pack(side='right', fill='y', padx=(0, 6))
        canvas.pack(side='left', fill='both', expand=True)
        
        return scrollable
    
    def setup_ui(self):
        """Setup the main UI structure"""
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Consistent scrollbar width for all views
        style.configure('Vertical.TScrollbar', width=14)
        
        # Customize treeview - clean table look
        style.configure('Treeview',
                       font=self.fonts['body'],
                       rowheight=38,
                       background=self.colors['card_bg'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['card_bg'],
                       borderwidth=0)
        style.configure('Treeview.Heading',
                       font=self.fonts['subheading'],
                       background=self.colors['primary'],
                       foreground='white',
                       relief='flat',
                       borderwidth=0,
                       padding=(12, 10))
        style.map('Treeview',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])
        style.map('Treeview.Heading',
                 background=[('active', self.colors['secondary'])])
    
    def create_header(self, title, show_back=True):
        """Create page header inside the content area (not the whole window)."""
        header = tk.Frame(self.content_root, bg=self.colors['primary'], height=72)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Thin bottom accent line
        accent = tk.Frame(header, bg=self.colors['secondary'], height=3)
        accent.pack(side='bottom', fill='x')
        
        left_frame = tk.Frame(header, bg=self.colors['primary'])
        left_frame.pack(side='left', padx=self.pad['x'], pady=22)
        
        tk.Label(left_frame, text=title, font=self.fonts['title'],
                bg=self.colors['primary'], fg='white').pack(side='left')
        
        right_frame = tk.Frame(header, bg=self.colors['primary'])
        right_frame.pack(side='right', padx=self.pad['x'], pady=22)
        
        if show_back:
            back_btn = tk.Button(
                right_frame,
                text="  ◄ Dashboard  ",
                bg=self.colors['secondary'],
                fg='white',
                font=self.fonts['body'],
                padx=22,
                pady=10,
                command=self.show_dashboard,
                cursor='hand2',
                relief='flat',
                bd=0,
                activebackground=self.darken_color(self.colors['secondary']),
                activeforeground='white',
            )
            back_btn.pack(side='right')
    
    def create_card(self, parent):
        """Create a card container with soft shadow and white background"""
        shadow = tk.Frame(parent, bg=self.colors['border_light'])
        card = tk.Frame(shadow, bg=self.colors['card_bg'], relief='flat', bd=0,
                       highlightbackground=self.colors['border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=3, pady=3)
        return shadow
    
    def show_dashboard(self):
        """Display main dashboard"""
        self.clear_window()
        self._set_active_nav('dashboard')
        self.create_header("EMR Dashboard", show_back=False)
        
        main_frame = self._make_scrollable(self.content_root)
        main_frame.configure(bg=self.colors['bg'])
        # Add padding via inner frame
        inner = tk.Frame(main_frame, bg=self.colors['bg'])
        inner.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        main_frame = inner
        
        # Data
        total_patients = session.query(Patient).count()
        total_records = session.query(MedicalRecord).count()
        recent_patients = session.query(Patient).order_by(Patient.created_at.desc()).limit(6).all()
        
        # Main dashboard grid (like your screenshot)
        grid = tk.Frame(main_frame, bg=self.colors['bg'])
        grid.pack(fill='both', expand=True)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(1, weight=1)
        
        # --- Welcome banner (row 0, col 0-1) ---
        welcome_outer = self.create_card(grid)
        welcome_outer.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0, 18))
        welcome = welcome_outer.winfo_children()[0]
        welcome.configure(bg=self.colors['card_bg'])
        
        banner = tk.Frame(welcome, bg=self.colors['card_bg'])
        banner.pack(fill='both', expand=True, padx=28, pady=22)
        
        left = tk.Frame(banner, bg=self.colors['card_bg'])
        left.pack(fill='both', expand=True)
        
        tk.Label(left, text="Welcome back", font=('Segoe UI', 18, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w')
        tk.Label(left, text="Quick access to patients, records, and searches.",
                font=self.fonts['body'], bg=self.colors['card_bg'], fg=self.colors['text_secondary']).pack(anchor='w', pady=(6, 0))
        
        tk.Label(
            left,
            text=f"Patients: {total_patients}   •   Records: {total_records}",
            font=self.fonts['small'],
            bg=self.colors['card_bg'],
            fg=self.colors['text_secondary'],
        ).pack(anchor='w', pady=(14, 0))
        
        # Quick buttons row
        quick = tk.Frame(welcome, bg=self.colors['card_bg'])
        quick.pack(fill='x', padx=22, pady=(14, 20))
        
        quick_btns = [
            ("Manage Patients", self.show_patients),
            ("New Patient", self.show_new_patient),
            ("New Record", self.show_new_record),
            ("Search Records", self.search_records),
        ]
        for i, (txt, cmd) in enumerate(quick_btns):
            tk.Button(
                quick,
                text=f"  {txt}  ",
                bg=self.colors['primary'],
                fg='white',
                font=self.fonts['small'],
                padx=14,
                pady=10,
                command=cmd,
                cursor='hand2',
                relief='flat',
                bd=0,
                activebackground=self.darken_color(self.colors['primary']),
                activeforeground='white',
            ).pack(side='left', padx=(0, 10) if i < len(quick_btns) - 1 else 0, pady=6)
        
        # --- Recent Patients (row 1, col 0) ---
        recent_outer = self.create_card(grid)
        recent_outer.grid(row=1, column=0, sticky='nsew', padx=(0, 18), pady=(0, 18))
        recent = recent_outer.winfo_children()[0]
        
        tk.Label(recent, text="Recent Patients", font=self.fonts['heading'],
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=22, pady=(22, 12))
        tk.Frame(recent, bg=self.colors['border_light'], height=1).pack(fill='x', padx=22, pady=(0, 16))
        
        list_frame = tk.Frame(recent, bg=self.colors['card_bg'])
        list_frame.pack(fill='both', expand=True, padx=22, pady=(0, 22))
        
        if not recent_patients:
            tk.Label(list_frame, text="No patients yet.", font=self.fonts['body'],
                    bg=self.colors['card_bg'], fg=self.colors['text_secondary']).pack(pady=20)
        else:
            for p in recent_patients:
                row = tk.Frame(list_frame, bg=self.colors['light'],
                               highlightbackground=self.colors['border_light'], highlightthickness=1)
                row.pack(fill='x', pady=6)
                left = tk.Frame(row, bg=self.colors['light'])
                left.pack(side='left', fill='x', expand=True, padx=16, pady=12)
                tk.Label(left, text=f"{p.first_name} {p.last_name}", font=self.fonts['subheading'],
                        bg=self.colors['light'], fg=self.colors['text']).pack(anchor='w')
                tk.Label(left, text=f"ID: {p.patient_id} • {p.gender}", font=self.fonts['small'],
                        bg=self.colors['light'], fg=self.colors['text_secondary']).pack(anchor='w')
                
                tk.Button(row, text="View", bg=self.colors['info'], fg='white',
                         font=self.fonts['small'], padx=16, pady=8,
                         command=lambda pat=p: self.view_patient_details(pat),
                         cursor='hand2', relief='flat', bd=0,
                         activebackground=self.darken_color(self.colors['info']), activeforeground='white').pack(side='right', padx=14, pady=12)
        
        # --- Weekly activity chart (row 1, col 1) ---
        chart_outer = self.create_card(grid)
        chart_outer.grid(row=1, column=1, sticky='nsew', pady=(0, 18))
        chart = chart_outer.winfo_children()[0]
        
        tk.Label(chart, text="Weekly Visits", font=self.fonts['heading'],
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=22, pady=(22, 12))
        tk.Frame(chart, bg=self.colors['border_light'], height=1).pack(fill='x', padx=22, pady=(0, 16))
        
        chart_canvas = tk.Canvas(chart, height=240, bg=self.colors['card_bg'], highlightthickness=0)
        chart_canvas.pack(fill='both', expand=True, padx=22, pady=(0, 22))
        
        # Build last 7 days counts
        today = datetime.now().date()
        days = [today]
        for _ in range(6):
            days.append(days[-1].fromordinal(days[-1].toordinal() - 1))
        days = list(reversed(days))
        labels = [d.strftime('%a') for d in days]
        
        counts = []
        for d in days:
            start = datetime(d.year, d.month, d.day, 0, 0, 0)
            end = datetime(d.year, d.month, d.day, 23, 59, 59)
            c = session.query(MedicalRecord).filter(MedicalRecord.visit_date >= start, MedicalRecord.visit_date <= end).count()
            counts.append(c)
        
        max_c = max(counts) if counts else 1
        max_c = max(max_c, 1)
        
        # Draw bars responsively (fit canvas size)
        def draw_chart(_evt=None):
            chart_canvas.delete("all")
            w = max(320, int(chart_canvas.winfo_width()))
            h = max(200, int(chart_canvas.winfo_height()))
            padding = 18
            gap = 12
            usable_w = max(1, w - padding * 2)
            bar_w = max(16, int((usable_w - gap * (len(counts) - 1)) / len(counts)))
            bar_w = min(bar_w, 70)
            total_w = bar_w * len(counts) + gap * (len(counts) - 1)
            start_x = (w - total_w) // 2
            
            for i, (lab, val) in enumerate(zip(labels, counts)):
                x0 = start_x + i * (bar_w + gap)
                x1 = x0 + bar_w
                bar_h = int((h - 60) * (val / max_c))
                y1 = h - 30
                y0 = y1 - bar_h
                chart_canvas.create_rectangle(x0, y0, x1, y1, fill=self.colors['primary_light'], outline="")
                chart_canvas.create_text((x0 + x1) / 2, h - 14, text=lab, fill=self.colors['text_secondary'], font=self.fonts['small'])
                chart_canvas.create_text((x0 + x1) / 2, max(12, y0 - 10), text=str(val), fill=self.colors['text_secondary'], font=self.fonts['small'])
        
        chart_canvas.bind("<Configure>", draw_chart)
        draw_chart()
    
    def darken_color(self, color):
        """Darken hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * 0.85)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def show_patients(self):
        """Display patients list"""
        self.clear_window()
        self._set_active_nav('patients')
        self.create_header("Patient Management")
        
        main_frame = self._make_scrollable(self.content_root)
        main_frame.configure(bg=self.colors['bg'])
        inner = tk.Frame(main_frame, bg=self.colors['bg'])
        inner.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        main_frame = inner
        
        # Search card
        search_card = self.create_card(main_frame)
        search_card.pack(fill='x', pady=(0, 22))
        
        inner = search_card.winfo_children()[0]
        search_frame = tk.Frame(inner, bg=self.colors['card_bg'])
        search_frame.pack(fill='x', padx=self.pad['x'], pady=self.pad['y'])
        
        tk.Label(search_frame, text="Search Patients", font=self.fonts['heading'],
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(side='left', padx=(0, 18))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=self.fonts['body'], width=42, relief='flat', bd=0,
                               bg=self.colors['light'], highlightthickness=1,
                               highlightbackground=self.colors['border'],
                               highlightcolor=self.colors['primary'])
        search_entry.pack(side='left', padx=(0, 12))
        search_entry.bind('<KeyRelease>', lambda e: self.filter_patients())
        
        tk.Button(search_frame, text="  Search  ", bg=self.colors['primary'], fg='white',
                 font=self.fonts['body'], padx=22, pady=10, command=self.filter_patients,
                 cursor='hand2', relief='flat', bd=0,
                 activebackground=self.darken_color(self.colors['primary']), activeforeground='white').pack(side='left', padx=6)
        
        tk.Button(search_frame, text="  Add New Patient  ", bg=self.colors['success'], fg='white',
                 font=self.fonts['body'], padx=22, pady=10, command=self.show_new_patient,
                 cursor='hand2', relief='flat', bd=0,
                 activebackground=self.darken_color(self.colors['success']), activeforeground='white').pack(side='right')
        
        # Patients list card
        list_card = self.create_card(main_frame)
        list_card.pack(fill='both', expand=True)
        
        list_inner = list_card.winfo_children()[0]
        
        tk.Label(list_inner, text="Patient List", font=self.fonts['heading'],
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=self.pad['x'], pady=(self.pad['y'], 14))
        
        separator = tk.Frame(list_inner, bg=self.colors['border_light'], height=1)
        separator.pack(fill='x', padx=self.pad['x'], pady=(0, 18))
        
        tree_frame = tk.Frame(list_inner, bg=self.colors['card_bg'])
        tree_frame.pack(fill='both', expand=True, padx=self.pad['x'], pady=(0, self.pad['y']))
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y', padx=(0, 4))
        
        self.patients_tree = ttk.Treeview(tree_frame,
                                         columns=('ID', 'Name', 'DOB', 'Gender', 'Phone'),
                                         show='headings', yscrollcommand=scrollbar.set, height=18)
        scrollbar.config(command=self.patients_tree.yview)
        
        self.patients_tree.heading('ID', text='Patient ID')
        self.patients_tree.heading('Name', text='Full Name')
        self.patients_tree.heading('DOB', text='Date of Birth')
        self.patients_tree.heading('Gender', text='Sex')
        self.patients_tree.heading('Phone', text='Phone')
        
        self.patients_tree.column('ID', width=120, anchor='center')
        self.patients_tree.column('Name', width=250, anchor='w')
        self.patients_tree.column('DOB', width=120, anchor='center')
        self.patients_tree.column('Gender', width=100, anchor='center')
        self.patients_tree.column('Phone', width=150, anchor='center')
        
        self.patients_tree.pack(fill='both', expand=True)
        self.patients_tree.bind('<Double-1>', lambda e: self.view_patient())
        
        # Action buttons
        action_frame = tk.Frame(list_inner, bg=self.colors['card_bg'])
        action_frame.pack(fill='x', padx=self.pad['x'], pady=(0, self.pad['y']))
        
        tk.Button(action_frame, text="  View  ", bg=self.colors['info'], fg='white',
                 font=self.fonts['body'], padx=22, pady=11, command=self.view_patient,
                 cursor='hand2', relief='flat', bd=0,
                 activebackground=self.darken_color(self.colors['info']), activeforeground='white').pack(side='left', padx=(0, 8))
        
        tk.Button(action_frame, text="  Edit  ", bg=self.colors['warning'], fg='white',
                 font=self.fonts['body'], padx=22, pady=11, command=self.edit_patient,
                 cursor='hand2', relief='flat', bd=0,
                 activebackground=self.darken_color(self.colors['warning']), activeforeground='white').pack(side='left', padx=(0, 8))
        
        tk.Button(action_frame, text="  Delete  ", bg=self.colors['danger'], fg='white',
                 font=self.fonts['body'], padx=22, pady=11, command=self.delete_patient,
                 cursor='hand2', relief='flat', bd=0,
                 activebackground=self.darken_color(self.colors['danger']), activeforeground='white').pack(side='left')
        
        self.load_patients()
    
    def load_patients(self):
        """Load patients into treeview"""
        for item in self.patients_tree.get_children():
            self.patients_tree.delete(item)
        
        patients = session.query(Patient).order_by(Patient.created_at.desc()).all()
        for patient in patients:
            self.patients_tree.insert('', 'end', values=(
                patient.patient_id,
                f"{patient.first_name} {patient.last_name}",
                patient.date_of_birth.strftime('%Y-%m-%d'),
                patient.gender,
                patient.phone or '-'
            ), tags=(patient.id,))
    
    def filter_patients(self):
        """Filter patients based on search"""
        search_term = self.search_var.get().lower()
        
        for item in self.patients_tree.get_children():
            self.patients_tree.delete(item)
        
        query = session.query(Patient)
        if search_term:
            query = query.filter(
                (Patient.patient_id.contains(search_term)) |
                (Patient.first_name.contains(search_term)) |
                (Patient.last_name.contains(search_term)) |
                (Patient.email.contains(search_term))
            )
        
        patients = query.order_by(Patient.created_at.desc()).all()
        for patient in patients:
            self.patients_tree.insert('', 'end', values=(
                patient.patient_id,
                f"{patient.first_name} {patient.last_name}",
                patient.date_of_birth.strftime('%Y-%m-%d'),
                patient.gender,
                patient.phone or '-'
            ), tags=(patient.id,))
    
    def view_patient(self):
        """View selected patient"""
        selection = self.patients_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a patient")
            return
        
        item = self.patients_tree.item(selection[0])
        patient_id = item['tags'][0]
        patient = session.query(Patient).get(patient_id)
        if patient:
            self.view_patient_details(patient)
    
    def view_patient_details(self, patient):
        """View full patient details in the main window (no extra tab)."""
        self.clear_window()
        self._set_active_nav('patients')
        # Use header with back button (to dashboard)
        self.create_header(f"Patient: {patient.first_name} {patient.last_name}", show_back=True)
        
        # Main content (scrollable in root)
        main_frame = self._make_scrollable(self.content_root)
        main_frame.configure(bg=self.colors['bg'])
        inner = tk.Frame(main_frame, bg=self.colors['bg'])
        inner.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        main_frame = inner
        
        # Patient info card
        info_card = self.create_card(main_frame)
        info_card.pack(fill='x', pady=(0, 20))
        
        info_inner = info_card.winfo_children()[0]
        
        tk.Label(info_inner, text="Patient Information", font=self.fonts['heading'],
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=self.pad['x'], pady=(self.pad['y'], 14))
        
        separator = tk.Frame(info_inner, bg=self.colors['border_light'], height=1)
        separator.pack(fill='x', padx=self.pad['x'], pady=(0, 18))
        
        info_frame = tk.Frame(info_inner, bg=self.colors['card_bg'])
        info_frame.pack(fill='x', padx=self.pad['x'], pady=(0, self.pad['y']))
        
        info_data = [
            ("Patient ID", patient.patient_id),
            ("Name", f"{patient.first_name} {patient.last_name}"),
            ("Date of Birth", patient.date_of_birth.strftime('%Y-%m-%d')),
            ("Sex", patient.gender),
            ("Blood Type", patient.blood_type or '-'),
            ("Phone", patient.phone or '-'),
            ("Email", patient.email or '-'),
            ("Address", patient.address or '-'),
            ("Emergency Contact", f"{patient.emergency_contact_name or '-'} ({patient.emergency_contact_phone or '-'})"),
            ("Allergies", patient.allergies or 'None recorded'),
            ("Medical History", patient.medical_history or 'None recorded')
        ]
        
        for i, (label, value) in enumerate(info_data):
            row = tk.Frame(info_frame, bg=self.colors['card_bg'])
            row.grid(row=i//2, column=i%2, sticky='w', padx=16, pady=9)
            
            tk.Label(row, text=f"{label}:", font=self.fonts['body'], bg=self.colors['card_bg'],
                    width=22, anchor='w', fg=self.colors['text_secondary']).pack(side='left')
            tk.Label(row, text=str(value), font=self.fonts['body'], bg=self.colors['card_bg'],
                    anchor='w', fg=self.colors['text'], wraplength=320).pack(side='left', fill='x', expand=True)
        
        # New record button in content area
        actions_row = tk.Frame(main_frame, bg=self.colors['bg'])
        actions_row.pack(fill='x', pady=(0, 10))
        tk.Button(actions_row, text="  New Record  ", bg=self.colors['success'], fg='white',
                 font=self.fonts['body'], padx=20, pady=10,
                 command=lambda: self.show_new_record(patient.patient_id),
                 cursor='hand2', relief='flat', bd=0,
                 activebackground=self.darken_color(self.colors['success']), activeforeground='white').pack(side='right')
        
        # Medical records card
        records_card = self.create_card(main_frame)
        records_card.pack(fill='both', expand=True)
        
        records_inner = records_card.winfo_children()[0]
        
        tk.Label(records_inner, text="Medical Records", font=self.fonts['heading'],
                bg='white', fg=self.colors['text']).pack(anchor='w', padx=25, pady=(25, 15))
        
        separator2 = tk.Frame(records_inner, bg=self.colors['border'], height=1)
        separator2.pack(fill='x', padx=25, pady=(0, 20))
        
        records = session.query(MedicalRecord).filter_by(patient_id=patient.id).order_by(MedicalRecord.visit_date.desc()).all()
        
        if records:
            records_frame = tk.Frame(records_inner, bg=self.colors['card_bg'])
            records_frame.pack(fill='both', expand=True, padx=self.pad['x'], pady=(0, self.pad['y']))
            
            scrollbar = ttk.Scrollbar(records_frame)
            scrollbar.pack(side='right', fill='y', padx=(0, 4))
            
            records_tree = ttk.Treeview(records_frame, columns=('Date', 'Diagnosis', 'Doctor'),
                                       show='headings', yscrollcommand=scrollbar.set, height=10)
            scrollbar.config(command=records_tree.yview)
            
            records_tree.heading('Date', text='Visit Date')
            records_tree.heading('Diagnosis', text='Diagnosis')
            records_tree.heading('Doctor', text='Doctor')
            
            records_tree.column('Date', width=180)
            records_tree.column('Diagnosis', width=400)
            records_tree.column('Doctor', width=200)
            
            records_tree.pack(fill='both', expand=True)
            
            for record in records:
                records_tree.insert('', 'end', values=(
                    record.visit_date.strftime('%Y-%m-%d %H:%M'),
                    (record.diagnosis[:60] + '...') if record.diagnosis and len(record.diagnosis) > 60 else (record.diagnosis or '-'),
                    record.doctor_name or '-'
                ), tags=(record.id,))
            
            records_tree.bind('<Double-1>', lambda e: self.view_record_from_tree(records_tree, None))
        else:
            empty_frame = tk.Frame(records_inner, bg=self.colors['card_bg'])
            empty_frame.pack(fill='both', expand=True, padx=self.pad['x'], pady=48)
            
            tk.Label(empty_frame, text="No medical records found",
                    font=self.fonts['subheading'], fg=self.colors['text_secondary'], bg=self.colors['card_bg']).pack(pady=12)
            tk.Label(empty_frame, text="Click 'New Record' to add the first medical record",
                    font=self.fonts['small'], fg=self.colors['text_secondary'], bg=self.colors['card_bg']).pack()
    
    def view_record_from_tree(self, tree, parent_window):
        """View record from treeview (compat for old calls, ignore parent_window)."""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        record_id = item['tags'][0]
        record = session.query(MedicalRecord).get(record_id)
        if record:
            self.view_record_details(record)
    
    def edit_patient(self):
        """Edit selected patient"""
        selection = self.patients_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a patient")
            return
        
        item = self.patients_tree.item(selection[0])
        patient_id = item['tags'][0]
        patient = session.query(Patient).get(patient_id)
        if patient:
            self.show_patient_form(patient)
    
    def delete_patient(self):
        """Delete selected patient"""
        selection = self.patients_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a patient")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this patient?"):
            return
        
        item = self.patients_tree.item(selection[0])
        patient_id = item['tags'][0]
        patient = session.query(Patient).get(patient_id)
        
        if patient:
            session.delete(patient)
            session.commit()
            messagebox.showinfo("Success", "Patient deleted successfully")
            self.load_patients()
    
    def show_new_patient(self):
        """Show new patient form"""
        self.show_patient_form()
    
    def show_patient_form(self, patient=None):
        """Show patient form (new or edit) in the main window."""
        self.clear_window()
        self._set_active_nav('new_patient')
        self.create_header("New Patient" if not patient else "Edit Patient", show_back=True)
        
        # Form container (fills remaining page height)
        form_outer = tk.Frame(self.content_root, bg=self.colors['bg'])
        form_outer.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        
        # Form card
        form_card = self.create_card(form_outer)
        form_card.pack(fill='both', expand=True, padx=8, pady=8)
        
        form_inner = form_card.winfo_children()[0]
        
        # Scrollable form
        canvas = tk.Canvas(form_inner, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_inner, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        fields_frame = tk.Frame(scrollable_frame, bg='white', padx=30, pady=30)
        fields_frame.pack(fill='both', expand=True)
        
        # Form fields
        fields = [
            ("Patient ID *", "patient_id", "entry", None),
            ("First Name *", "first_name", "entry", None),
            ("Last Name *", "last_name", "entry", None),
            ("Date of Birth * (YYYY-MM-DD)", "date_of_birth", "entry", "YYYY-MM-DD"),
            ("Sex *", "gender", "combo", ['Male', 'Female']),
            ("Blood Type", "blood_type", "combo", ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
            ("Phone", "phone", "entry", None),
            ("Email", "email", "entry", None),
            ("Address", "address", "text", 3),
            ("Emergency Contact Name", "emergency_contact_name", "entry", None),
            ("Emergency Contact Phone", "emergency_contact_phone", "entry", None),
            ("Allergies", "allergies", "text", 3),
            ("Medical History", "medical_history", "text", 4)
        ]
        
        entries = {}
        row = 0
        
        for label, key, field_type, options in fields:
            tk.Label(fields_frame, text=label, font=self.fonts['body'], bg='white',
                    fg=self.colors['text'], width=26, anchor='w').grid(row=row, column=0, sticky='w', padx=10, pady=10)
            
            if field_type == "entry":
                entry = tk.Entry(fields_frame, font=self.fonts['body'], width=40, relief='flat', bd=0,
                               bg='#f1f5f9', highlightthickness=1, highlightbackground=self.colors['border'])
                entry.grid(row=row, column=1, padx=10, pady=10, sticky='ew')
                if patient:
                    if key == "date_of_birth":
                        entry.insert(0, patient.date_of_birth.strftime('%Y-%m-%d'))
                    else:
                        entry.insert(0, getattr(patient, key) or '')
                elif options:
                    entry.insert(0, options)
                if key == "patient_id" and patient:
                    entry.config(state='readonly')
                entries[key] = entry
            elif field_type == "combo":
                var = tk.StringVar(value=getattr(patient, key) if patient else '')
                combo = ttk.Combobox(fields_frame, textvariable=var, values=options or [],
                                   state='readonly', width=37, font=self.fonts['body'])
                combo.grid(row=row, column=1, padx=10, pady=10, sticky='ew')
                entries[key] = var
            elif field_type == "text":
                text = tk.Text(fields_frame, font=self.fonts['body'], width=40, height=options or 3,
                             relief='flat', bd=0, bg='#f1f5f9', highlightthickness=1,
                             highlightbackground=self.colors['border'], wrap='word')
                text.grid(row=row, column=1, padx=10, pady=10, sticky='ew')
                if patient:
                    text.insert('1.0', getattr(patient, key) or '')
                entries[key] = text
            
            row += 1
        
        fields_frame.grid_columnconfigure(1, weight=1)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y', padx=(0, 6))
        
        # Buttons
        button_frame = tk.Frame(form_inner, bg='white')
        button_frame.pack(fill='x', padx=30, pady=20)
        
        separator = tk.Frame(button_frame, bg=self.colors['border'], height=1)
        separator.pack(fill='x', pady=(0, 20))
        
        btn_container = tk.Frame(button_frame, bg='white')
        btn_container.pack()
        
        tk.Button(btn_container, text="✕ Cancel", bg='#94a3b8', fg='white',
                 font=self.fonts['body'], padx=30, pady=12, command=self.show_patients,
                 cursor='hand2', relief='flat', bd=0).pack(side='right', padx=10)
        
        def save_patient():
            try:
                allowed_sex = {"Male", "Female"}
                sex_value = (entries['gender'].get() or "").strip()
                if sex_value not in allowed_sex:
                    messagebox.showerror("Error", "Sex must be Male or Female")
                    return

                if not patient:
                    if session.query(Patient).filter_by(patient_id=entries['patient_id'].get()).first():
                        messagebox.showerror("Error", "Patient ID already exists")
                        return
                    
                    new_patient = Patient(
                        patient_id=entries['patient_id'].get(),
                        first_name=entries['first_name'].get(),
                        last_name=entries['last_name'].get(),
                        date_of_birth=datetime.strptime(entries['date_of_birth'].get(), '%Y-%m-%d').date(),
                        gender=sex_value,
                        phone=entries['phone'].get() or None,
                        email=entries['email'].get() or None,
                        address=entries['address'].get('1.0', 'end-1c') or None,
                        emergency_contact_name=entries['emergency_contact_name'].get() or None,
                        emergency_contact_phone=entries['emergency_contact_phone'].get() or None,
                        blood_type=entries['blood_type'].get() or None,
                        allergies=entries['allergies'].get('1.0', 'end-1c') or None,
                        medical_history=entries['medical_history'].get('1.0', 'end-1c') or None
                    )
                    session.add(new_patient)
                    session.commit()
                    messagebox.showinfo("Success", "Patient added successfully")
                else:
                    patient.first_name = entries['first_name'].get()
                    patient.last_name = entries['last_name'].get()
                    patient.date_of_birth = datetime.strptime(entries['date_of_birth'].get(), '%Y-%m-%d').date()
                    patient.gender = sex_value
                    patient.phone = entries['phone'].get() or None
                    patient.email = entries['email'].get() or None
                    patient.address = entries['address'].get('1.0', 'end-1c') or None
                    patient.emergency_contact_name = entries['emergency_contact_name'].get() or None
                    patient.emergency_contact_phone = entries['emergency_contact_phone'].get() or None
                    patient.blood_type = entries['blood_type'].get() or None
                    patient.allergies = entries['allergies'].get('1.0', 'end-1c') or None
                    patient.medical_history = entries['medical_history'].get('1.0', 'end-1c') or None
                    patient.updated_at = datetime.utcnow()
                    
                    session.commit()
                    messagebox.showinfo("Success", "Patient updated successfully")
                
                self.show_patients()
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid date format. Use YYYY-MM-DD\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving patient: {str(e)}")
        
        tk.Button(btn_container, text="Save Patient", bg=self.colors['success'], fg='white',
                 font=self.fonts['body'], padx=30, pady=12, command=save_patient,
                 cursor='hand2', relief='flat', bd=0).pack(side='right')
    
    def show_new_record(self, patient_id=None):
        """Show new medical record form in the main window."""
        self.clear_window()
        self._set_active_nav('new_record')
        self.create_header("New Medical Record", show_back=True)
        
        scroll_frame = self._make_scrollable(self.content_root)
        scroll_frame.configure(bg=self.colors['bg'])
        form_outer = tk.Frame(scroll_frame, bg=self.colors['bg'])
        form_outer.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        
        # Form card
        form_card = self.create_card(form_outer)
        form_card.pack(fill='both', expand=True, padx=30, pady=30)
        
        form_inner = form_card.winfo_children()[0]
        
        fields_frame = tk.Frame(form_inner, bg='white', padx=30, pady=30)
        fields_frame.pack(fill='both', expand=True)
        
        # Form fields
        tk.Label(fields_frame, text="Patient ID *", font=self.fonts['body'], bg='white',
                fg=self.colors['text'], width=26, anchor='w').grid(row=0, column=0, sticky='w', padx=10, pady=10)
        patient_id_entry = tk.Entry(fields_frame, font=self.fonts['body'], width=40, relief='flat', bd=0,
                                   bg='#f1f5f9', highlightthickness=1, highlightbackground=self.colors['border'])
        patient_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        if patient_id:
            patient_id_entry.insert(0, patient_id)
        
        tk.Label(fields_frame, text="Visit Date & Time *\n(YYYY-MM-DD HH:MM)", font=self.fonts['body'], bg='white',
                fg=self.colors['text'], width=26, anchor='w', justify='left').grid(row=1, column=0, sticky='nw', padx=10, pady=10)
        visit_date_entry = tk.Entry(fields_frame, font=self.fonts['body'], width=40, relief='flat', bd=0,
                                  bg='#f1f5f9', highlightthickness=1, highlightbackground=self.colors['border'])
        visit_date_entry.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        visit_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        tk.Label(fields_frame, text="Doctor Name", font=self.fonts['body'], bg='white',
                fg=self.colors['text'], width=26, anchor='w').grid(row=2, column=0, sticky='w', padx=10, pady=10)
        doctor_entry = tk.Entry(fields_frame, font=self.fonts['body'], width=40, relief='flat', bd=0,
                              bg='#f1f5f9', highlightthickness=1, highlightbackground=self.colors['border'])
        doctor_entry.grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        # Two-column layout: left = clinical notes, right = vital signs card
        content = tk.Frame(fields_frame, bg='white')
        content.grid(row=3, column=0, columnspan=2, sticky='nsew', padx=10, pady=(10, 0))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        
        left_col = tk.Frame(content, bg='white')
        left_col.grid(row=0, column=0, sticky='nsew', padx=(0, 14))
        right_col = tk.Frame(content, bg='white')
        right_col.grid(row=0, column=1, sticky='nsew')
        
        # Left column text areas
        text_fields = [
            ("Chief Complaint", "complaint", 3),
            ("Diagnosis", "diagnosis", 3),
            ("Treatment", "treatment", 3),
            ("Medications", "medications", 3),
            ("Notes", "notes", 6),
        ]
        
        text_entries = {}
        r = 0
        for label, key, height in text_fields:
            tk.Label(left_col, text=label, font=self.fonts['body'], bg='white',
                    fg=self.colors['text'], anchor='w').grid(row=r, column=0, sticky='w', pady=(0, 6))
            txt = tk.Text(left_col, font=self.fonts['body'], height=height,
                         relief='flat', bd=0, bg='#f1f5f9', highlightthickness=1,
                         highlightbackground=self.colors['border'], wrap='word')
            txt.grid(row=r+1, column=0, sticky='nsew', pady=(0, 14))
            left_col.grid_rowconfigure(r+1, weight=1)
            text_entries[key] = txt
            r += 2
        
        # Right column: Vital signs in a separate card/frame
        vitals_card = tk.Frame(right_col, bg=self.colors['card_bg'],
                              highlightbackground=self.colors['border'], highlightthickness=1)
        vitals_card.pack(fill='x', padx=0, pady=0)
        
        tk.Label(vitals_card, text="Vital Signs", font=self.fonts['heading'],
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=16, pady=(16, 10))
        tk.Frame(vitals_card, bg=self.colors['border_light'], height=1).pack(fill='x', padx=16, pady=(0, 12))
        
        vitals_form = tk.Frame(vitals_card, bg=self.colors['card_bg'])
        vitals_form.pack(fill='x', padx=16, pady=(0, 16))
        vitals_form.grid_columnconfigure(1, weight=1)
        
        def _vital_row(row_i, label, unit=""):
            tk.Label(vitals_form, text=label, font=self.fonts['small'],
                    bg=self.colors['card_bg'], fg=self.colors['text_secondary']).grid(row=row_i, column=0, sticky='w', pady=6)
            e = tk.Entry(vitals_form, font=self.fonts['body'], relief='flat', bd=0,
                        bg=self.colors['light'], highlightthickness=1, highlightbackground=self.colors['border'])
            e.grid(row=row_i, column=1, sticky='ew', padx=(10, 10), pady=6)
            if unit:
                tk.Label(vitals_form, text=unit, font=self.fonts['small'],
                        bg=self.colors['card_bg'], fg=self.colors['text_secondary']).grid(row=row_i, column=2, sticky='w', pady=6)
            return e
        
        vital_entries = {}
        vital_entries["bp"] = _vital_row(0, "Blood Pressure", "mmHg")
        vital_entries["temp"] = _vital_row(1, "Temperature", "°C")
        vital_entries["pulse"] = _vital_row(2, "Pulse", "bpm")
        vital_entries["resp"] = _vital_row(3, "Resp. Rate", "/min")
        vital_entries["spo2"] = _vital_row(4, "SpO₂", "%")
        vital_entries["height"] = _vital_row(5, "Height", "cm")
        vital_entries["weight"] = _vital_row(6, "Weight", "kg")
        
        nail_btn_frame = tk.Frame(right_col, bg='white')
        nail_btn_frame.pack(fill='x', pady=(12, 0))
        tk.Button(nail_btn_frame, text="  Nail Scan  ", bg=self.colors['info'], fg='white',
                 font=self.fonts['small'], padx=16, pady=8,
                 cursor='hand2', relief='flat', bd=0).pack(anchor='w')
        
        # Make bottom area stretch nicely
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = tk.Frame(form_inner, bg='white')
        button_frame.pack(fill='x', padx=30, pady=20)
        
        separator = tk.Frame(button_frame, bg=self.colors['border'], height=1)
        separator.pack(fill='x', pady=(0, 20))
        
        btn_container = tk.Frame(button_frame, bg='white')
        btn_container.pack()
        
        def save_record():
            try:
                p_id = patient_id_entry.get()
                patient = session.query(Patient).filter_by(patient_id=p_id).first()
                
                if not patient:
                    messagebox.showerror("Error", "Patient not found")
                    return
                
                visit_date_str = visit_date_entry.get()
                visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d %H:%M')
                
                vital_signs_str = "\n".join([
                    f"BP: {vital_entries['bp'].get().strip() or '-'} mmHg",
                    f"Temp: {vital_entries['temp'].get().strip() or '-'} °C",
                    f"Pulse: {vital_entries['pulse'].get().strip() or '-'} bpm",
                    f"RR: {vital_entries['resp'].get().strip() or '-'} /min",
                    f"SpO₂: {vital_entries['spo2'].get().strip() or '-'} %",
                    f"Height: {vital_entries['height'].get().strip() or '-'} cm",
                    f"Weight: {vital_entries['weight'].get().strip() or '-'} kg",
                ])
                
                record = MedicalRecord(
                    patient_id=patient.id,
                    visit_date=visit_date,
                    chief_complaint=text_entries['complaint'].get('1.0', 'end-1c') or None,
                    diagnosis=text_entries['diagnosis'].get('1.0', 'end-1c') or None,
                    treatment=text_entries['treatment'].get('1.0', 'end-1c') or None,
                    medications=text_entries['medications'].get('1.0', 'end-1c') or None,
                    vital_signs=vital_signs_str,
                    notes=text_entries['notes'].get('1.0', 'end-1c') or None,
                    doctor_name=doctor_entry.get() or None
                )
                
                session.add(record)
                session.commit()
                
                messagebox.showinfo("Success", "Medical record added successfully")
                # Offer to schedule follow-up right after consultation
                if patient and messagebox.askyesno("Follow-up checkup", "Schedule a follow-up checkup for this patient?"):
                    self.show_schedule_follow_up(patient=patient)
                elif patient:
                    self.view_patient_details(patient)
                else:
                    self.show_dashboard()
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD HH:MM")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving record: {str(e)}")
        
        def cancel_action():
            # If we came from a specific patient, try to go back to that patient's view
            if patient_id:
                existing = session.query(Patient).filter_by(patient_id=patient_id).first()
                if existing:
                    self.view_patient_details(existing)
                    return
            self.show_dashboard()
        
        tk.Button(btn_container, text="✕ Cancel", bg='#94a3b8', fg='white',
                 font=self.fonts['body'], padx=30, pady=12,
                 command=cancel_action,
                 cursor='hand2', relief='flat', bd=0).pack(side='right', padx=10)
        
        tk.Button(btn_container, text="Save Record", bg=self.colors['success'], fg='white',
                 font=self.fonts['body'], padx=30, pady=12, command=save_record,
                 cursor='hand2', relief='flat', bd=0).pack(side='right')
    
    def view_record_details(self, record):
        """View full medical record details in the main window."""
        self.clear_window()
        self._set_active_nav('search')
        self.create_header("Medical Record Details", show_back=True)
        
        # Content
        form_frame = self._make_scrollable(self.content_root)
        form_frame.configure(bg=self.colors['bg'])
        inner = tk.Frame(form_frame, bg=self.colors['card_bg'])
        inner.pack(fill='both', expand=True, padx=30, pady=30)
        
        details = [
            ("Patient", f"{record.patient.first_name} {record.patient.last_name} ({record.patient.patient_id})"),
            ("Phone", record.patient.phone or '-'),
            ("Visit Date", record.visit_date.strftime('%Y-%m-%d %H:%M')),
            ("Doctor", record.doctor_name or '-'),
            ("Chief Complaint", record.chief_complaint or '-'),
            ("Diagnosis", record.diagnosis or '-'),
            ("Treatment", record.treatment or '-'),
            ("Medications", record.medications or '-'),
            ("Vital Signs", record.vital_signs or '-'),
            ("Notes", record.notes or '-')
        ]
        
        for i, (label, value) in enumerate(details):
            row = tk.Frame(inner, bg=self.colors['card_bg'])
            row.pack(fill='x', pady=12)
            
            tk.Label(row, text=f"{label}:", font=self.fonts['body'], bg=self.colors['card_bg'],
                    width=22, anchor='w', fg=self.colors['text_secondary']).pack(side='left', padx=10)

            val_str = str(value)
            is_multiline = ("\n" in val_str) or (len(val_str) > 60)
            if is_multiline:
                lines = val_str.count("\n") + 1
                min_h = 7 if label == "Vital Signs" else 4
                height = max(min_h, min(12, lines + 1))

                text_widget = tk.Text(
                    row,
                    width=50,
                    height=height,
                    font=self.fonts['body'],
                    wrap='word',
                    relief='flat',
                    bd=0,
                    bg=self.colors['light'],
                    highlightthickness=1,
                    highlightbackground=self.colors['border'],
                )
                text_widget.insert('1.0', val_str)
                text_widget.configure(state='disabled')
                text_widget.pack(side='left', fill='x', expand=True, padx=10)
            else:
                tk.Label(
                    row,
                    text=val_str,
                    font=self.fonts['body'],
                    bg=self.colors['card_bg'],
                    anchor='w',
                    fg=self.colors['text'],
                    wraplength=450,
                ).pack(side='left', fill='x', expand=True, padx=10)
        
        btn_row = tk.Frame(inner, bg=self.colors['card_bg'])
        btn_row.pack(fill='x', pady=(8, 20))
        tk.Button(btn_row, text="  Schedule follow-up  ", bg=self.colors['success'], fg='white',
                 font=self.fonts['body'], padx=22, pady=10,
                 command=lambda: self.show_schedule_follow_up(record=record),
                 cursor='hand2', relief='flat', bd=0).pack(side='left', padx=10)
        tk.Button(inner, text="Close", bg='#94a3b8', fg='white',
                 font=self.fonts['body'], padx=25, pady=12, command=lambda: self.view_patient_details(record.patient),
                 cursor='hand2', relief='flat', bd=0).pack(pady=20)
    
    def search_records(self):
        """Search medical records in the main window"""
        self.clear_window()
        self._set_active_nav('search')
        self.create_header("Search Medical Records", show_back=True)
        
        # Scrollable content
        content = self._make_scrollable(self.content_root)
        content.configure(bg=self.colors['bg'])
        inner_content = tk.Frame(content, bg=self.colors['bg'])
        inner_content.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Search card
        search_card = self.create_card(inner_content)
        search_card.pack(fill='x', pady=(0, 22))
        
        search_inner = search_card.winfo_children()[0]
        search_frame = tk.Frame(search_inner, bg='white')
        search_frame.pack(fill='x', padx=25, pady=25)
        
        tk.Label(search_frame, text="Search:", font=self.fonts['body'], bg='white',
                fg=self.colors['text']).pack(side='left', padx=(0, 15))
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=self.fonts['body'], width=50,
                               relief='flat', bd=0, bg='#f1f5f9', highlightthickness=1,
                               highlightbackground=self.colors['border'])
        search_entry.pack(side='left', padx=(0, 10))
        
        def do_search():
            term = search_var.get()
            for item in records_tree.get_children():
                records_tree.delete(item)
            
            query = session.query(MedicalRecord).join(Patient)
            if term:
                query = query.filter(
                    (Patient.first_name.contains(term)) |
                    (Patient.last_name.contains(term)) |
                    (Patient.patient_id.contains(term)) |
                    (MedicalRecord.diagnosis.contains(term)) |
                    (MedicalRecord.doctor_name.contains(term))
                )
            
            records = query.order_by(MedicalRecord.visit_date.desc()).limit(100).all()
            
            for record in records:
                records_tree.insert('', 'end', values=(
                    record.patient.patient_id,
                    f"{record.patient.first_name} {record.patient.last_name}",
                    record.visit_date.strftime('%Y-%m-%d %H:%M'),
                    (record.diagnosis[:50] + '...') if record.diagnosis and len(record.diagnosis) > 50 else (record.diagnosis or '-'),
                    record.doctor_name or '-'
                ), tags=(record.id,))
        
        tk.Button(search_frame, text="Search", bg=self.colors['warning'], fg='white',
                 font=self.fonts['body'], padx=20, pady=8, command=do_search,
                 cursor='hand2', relief='flat', bd=0).pack(side='left')
        
        # Results card
        list_card = self.create_card(inner_content)
        list_card.pack(fill='both', expand=True, pady=(0, 30))
        
        list_inner = list_card.winfo_children()[0]
        
        tk.Label(list_inner, text="Search Results", font=self.fonts['heading'],
                bg='white', fg=self.colors['text']).pack(anchor='w', padx=25, pady=(25, 15))
        
        separator = tk.Frame(list_inner, bg=self.colors['border'], height=1)
        separator.pack(fill='x', padx=25, pady=(0, 20))
        
        tree_frame = tk.Frame(list_inner, bg='white')
        tree_frame.pack(fill='both', expand=True, padx=25, pady=(0, 25))
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y', padx=(0, 4))
        
        records_tree = ttk.Treeview(tree_frame,
                                   columns=('Patient ID', 'Patient Name', 'Visit Date', 'Diagnosis', 'Doctor'),
                                   show='headings', yscrollcommand=scrollbar.set, height=18)
        scrollbar.config(command=records_tree.yview)
        
        records_tree.heading('Patient ID', text='Patient ID')
        records_tree.heading('Patient Name', text='Patient Name')
        records_tree.heading('Visit Date', text='Visit Date')
        records_tree.heading('Diagnosis', text='Diagnosis')
        records_tree.heading('Doctor', text='Doctor')
        
        records_tree.column('Patient ID', width=120)
        records_tree.column('Patient Name', width=180)
        records_tree.column('Visit Date', width=150)
        records_tree.column('Diagnosis', width=300)
        records_tree.column('Doctor', width=150)
        
        records_tree.pack(fill='both', expand=True)
        records_tree.bind('<Double-1>', lambda e: view_selected_record())
        
        def view_selected_record():
            selection = records_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a record")
                return
            
            item = records_tree.item(selection[0])
            record_id = item['tags'][0]
            record = session.query(MedicalRecord).get(record_id)
            if record:
                self.view_record_details(record)
        
        action_frame = tk.Frame(list_inner, bg='white')
        
        action_frame.pack(fill='x', padx=25, pady=(0, 25))
        
        tk.Button(action_frame, text="View Record", bg=self.colors['info'], fg='white',
                 font=self.fonts['body'], padx=25, pady=12, command=view_selected_record,
                 cursor='hand2', relief='flat', bd=0).pack(pady=10)
        
        do_search()  # Initial load
    
    def show_follow_ups(self):
        """List scheduled follow-up checkups."""
        self.clear_window()
        self._set_active_nav('follow_ups')
        self.create_header("Follow-up checkups", show_back=True)
        
        main_frame = self._make_scrollable(self.content_root)
        main_frame.configure(bg=self.colors['bg'])
        inner = tk.Frame(main_frame, bg=self.colors['bg'])
        inner.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        
        card = self.create_card(inner)
        card.pack(fill='both', expand=True)
        list_inner = card.winfo_children()[0]
        
        tk.Label(list_inner, text="Scheduled follow-ups", font=self.fonts['heading'],
                 bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=25, pady=(25, 15))
        tk.Frame(list_inner, bg=self.colors['border_light'], height=1).pack(fill='x', padx=25, pady=(0, 18))
        
        tree_frame = tk.Frame(list_inner, bg=self.colors['card_bg'])
        tree_frame.pack(fill='both', expand=True, padx=25, pady=(0, 18))
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y', padx=(0, 4))
        
        follow_tree = ttk.Treeview(tree_frame,
                                  columns=('Patient', 'Scheduled', 'Reason', 'Status'),
                                  show='headings', yscrollcommand=scrollbar.set, height=16)
        scrollbar.config(command=follow_tree.yview)
        follow_tree.heading('Patient', text='Patient')
        follow_tree.heading('Scheduled', text='Date & Time')
        follow_tree.heading('Reason', text='Reason')
        follow_tree.heading('Status', text='Status')
        follow_tree.column('Patient', width=220)
        follow_tree.column('Scheduled', width=160)
        follow_tree.column('Reason', width=280)
        follow_tree.column('Status', width=100)
        follow_tree.pack(fill='both', expand=True)
        
        now = datetime.utcnow()
        follow_ups = session.query(FollowUpCheckup).filter(
            FollowUpCheckup.scheduled_at >= now,
            FollowUpCheckup.status == 'scheduled'
        ).order_by(FollowUpCheckup.scheduled_at).all()
        
        for fu in follow_ups:
            reason_short = (fu.reason[:40] + '...') if fu.reason and len(fu.reason) > 40 else (fu.reason or '-')
            follow_tree.insert('', 'end', values=(
                f"{fu.patient.first_name} {fu.patient.last_name} ({fu.patient.patient_id})",
                fu.scheduled_at.strftime('%Y-%m-%d %H:%M'),
                reason_short,
                fu.status
            ), tags=(fu.id,))
        
        action_frame = tk.Frame(list_inner, bg=self.colors['card_bg'])
        action_frame.pack(fill='x', padx=25, pady=(0, 25))
        
        def view_patient_from_follow():
            sel = follow_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a follow-up")
                return
            fu_id = follow_tree.item(sel[0])['tags'][0]
            fu = session.query(FollowUpCheckup).get(fu_id)
            if fu:
                self.view_patient_details(fu.patient)
        
        def new_record_for_follow():
            sel = follow_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a follow-up")
                return
            fu_id = follow_tree.item(sel[0])['tags'][0]
            fu = session.query(FollowUpCheckup).get(fu_id)
            if fu:
                self.show_new_record(fu.patient.patient_id)
        
        def mark_completed():
            sel = follow_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a follow-up")
                return
            fu_id = follow_tree.item(sel[0])['tags'][0]
            fu = session.query(FollowUpCheckup).get(fu_id)
            if fu:
                fu.status = 'completed'
                session.commit()
                messagebox.showinfo("Done", "Marked as completed")
                self.show_follow_ups()
        
        def cancel_follow():
            sel = follow_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a follow-up")
                return
            if not messagebox.askyesno("Confirm", "Cancel this follow-up?"):
                return
            fu_id = follow_tree.item(sel[0])['tags'][0]
            fu = session.query(FollowUpCheckup).get(fu_id)
            if fu:
                fu.status = 'cancelled'
                session.commit()
                self.show_follow_ups()
        
        tk.Button(action_frame, text="  View patient  ", bg=self.colors['info'], fg='white',
                 font=self.fonts['body'], padx=20, pady=10, command=view_patient_from_follow,
                 cursor='hand2', relief='flat', bd=0).pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text="  New record (visit)  ", bg=self.colors['success'], fg='white',
                 font=self.fonts['body'], padx=20, pady=10, command=new_record_for_follow,
                 cursor='hand2', relief='flat', bd=0).pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text="  Mark completed  ", bg=self.colors['primary'], fg='white',
                 font=self.fonts['body'], padx=20, pady=10, command=mark_completed,
                 cursor='hand2', relief='flat', bd=0).pack(side='left', padx=(0, 8))
        tk.Button(action_frame, text="  Cancel follow-up  ", bg=self.colors['danger'], fg='white',
                 font=self.fonts['body'], padx=20, pady=10, command=cancel_follow,
                 cursor='hand2', relief='flat', bd=0).pack(side='left')
    
    def show_schedule_follow_up(self, record=None, patient=None):
        """Schedule a follow-up checkup (from a record or for a patient)."""
        p = patient if patient else (record.patient if record else None)
        if not p:
            messagebox.showerror("Error", "No patient specified")
            return
        self.clear_window()
        self._set_active_nav('follow_ups')
        self.create_header("Schedule follow-up checkup", show_back=True)
        
        inner = tk.Frame(self.content_root, bg=self.colors['bg'])
        inner.pack(fill='both', expand=True, padx=self.pad['x'], pady=self.pad['y'])
        
        card = self.create_card(inner)
        card.pack(fill='x', padx=8, pady=8)
        form = card.winfo_children()[0]
        form.configure(bg=self.colors['card_bg'])
        
        tk.Label(form, text=f"Patient: {p.first_name} {p.last_name} ({p.patient_id})",
                 font=self.fonts['subheading'], bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', padx=22, pady=(22, 8))
        tk.Frame(form, bg=self.colors['border_light'], height=1).pack(fill='x', padx=22, pady=(0, 18))
        
        frm = tk.Frame(form, bg=self.colors['card_bg'])
        frm.pack(fill='x', padx=22, pady=(0, 22))
        frm.grid_columnconfigure(1, weight=1)
        
        tk.Label(frm, text="Date", font=self.fonts['body'], bg=self.colors['card_bg'], width=22, anchor='w').grid(row=0, column=0, sticky='w', padx=(0, 12), pady=10)
        today = date.today()
        default_date = today + timedelta(days=14)
        date_cal = DateEntry(
            frm, font=self.fonts['body'], width=18,
            mindate=today,
            date_pattern='y-mm-dd',
            state='readonly'
        )
        date_cal.set_date(default_date)

        # Popup with Confirm button: selecting a date does NOT close; only Confirm / Cancel / click-outside closes
        _top_cal = date_cal._top_cal
        _calendar = date_cal._calendar
        _saved_date_on_open = [default_date]  # so Cancel can restore

        def _close_popup():
            try:
                _top_cal.withdraw()
                date_cal.state(['!pressed'])
            except (tk.TclError, AttributeError):
                pass

        def _on_date_selected_only(event=None):
            """Update the entry when a date is clicked, but do NOT close the popup."""
            d = _calendar.selection_get()
            if d is not None:
                date_cal._set_text(date_cal.format_date(d))
                date_cal._date = d

        def _confirm_date():
            _close_popup()

        def _cancel_date():
            date_cal._set_text(date_cal.format_date(_saved_date_on_open[0]))
            date_cal._date = _saved_date_on_open[0]
            _calendar.selection_set(_saved_date_on_open[0])
            _close_popup()

        def _on_click_outside(event):
            try:
                if not _top_cal.winfo_viewable():
                    return
                x, y = event.x_root, event.y_root
                x1, y1 = _top_cal.winfo_rootx(), _top_cal.winfo_rooty()
                w1, h1 = _top_cal.winfo_width(), _top_cal.winfo_height()
                if x1 <= x <= x1 + w1 and y1 <= y <= y1 + h1:
                    return
                x2, y2 = date_cal.winfo_rootx(), date_cal.winfo_rooty()
                w2, h2 = date_cal.winfo_width(), date_cal.winfo_height()
                if x2 <= x <= x2 + w2 and y2 <= y <= y2 + h2:
                    return
                _close_popup()
            except (tk.TclError, AttributeError):
                pass

        # Don't close on focus loss — only on Confirm, Cancel, or click-outside
        _calendar.unbind('<FocusOut>')
        _calendar.unbind('<<CalendarSelected>>')
        _calendar.bind('<<CalendarSelected>>', _on_date_selected_only)

        # Add Confirm and Cancel buttons to the popup (below the calendar)
        btn_frm = tk.Frame(_top_cal)
        btn_frm.pack(fill='x', padx=6, pady=6)
        tk.Button(btn_frm, text="Cancel", font=self.fonts['body'], padx=12, pady=6,
                 command=_cancel_date, cursor='hand2').pack(side='left', padx=2)
        tk.Button(btn_frm, text="Confirm date", font=self.fonts['body'], padx=12, pady=6,
                 bg=self.colors.get('success', '#22c55e'), fg='white', relief='flat',
                 command=_confirm_date, cursor='hand2').pack(side='right', padx=2)

        root = date_cal.winfo_toplevel()
        root.bind('<ButtonPress>', _on_click_outside, add=True)

        def _make_popup_visible():
            """Ensure popup is shown, not minimized, and on top (each time it opens)."""
            try:
                _top_cal.overrideredirect(False)
                _top_cal.deiconify()
                _top_cal.lift()
                _top_cal.attributes('-topmost', True)
                date_cal.after(50, lambda: _top_cal.attributes('-topmost', False))
            except (tk.TclError, AttributeError):
                pass

        _original_drop_down = date_cal.drop_down
        def _drop_down_fixed():
            _saved_date_on_open[0] = date_cal.get_date()
            _original_drop_down()
            # Re-apply position and ensure visible (fixes popup "minimizing" on reopen)
            date_cal.update_idletasks()
            x = date_cal.winfo_rootx()
            y = date_cal.winfo_rooty() + date_cal.winfo_height()
            try:
                _top_cal.geometry('+%i+%i' % (x, y))
                _top_cal.deiconify()
                _top_cal.lift()
            except (tk.TclError, AttributeError):
                pass
            date_cal.after(30, _make_popup_visible)
        date_cal.drop_down = _drop_down_fixed
        _top_cal.bind('<Map>', lambda e: _make_popup_visible())

        date_cal.grid(row=0, column=1, sticky='w', padx=0, pady=10)

        # Time: type with AM/PM; must be within clinic hours (show error if not)
        CLINIC_START_HOUR, CLINIC_END_HOUR = 8, 17  # 8 AM to 5 PM
        tk.Label(frm, text="Time (e.g. 9:00 AM)", font=self.fonts['body'], bg=self.colors['card_bg'], width=22, anchor='w').grid(row=1, column=0, sticky='w', padx=(0, 12), pady=10)
        time_entry = tk.Entry(frm, font=self.fonts['body'], width=12, relief='flat', bd=0, bg=self.colors['light'], highlightthickness=1, highlightbackground=self.colors['border'])
        time_entry.grid(row=1, column=1, sticky='w', padx=0, pady=10)
        time_entry.insert(0, "9:00 AM")
        
        tk.Label(frm, text="Reason / notes", font=self.fonts['body'], bg=self.colors['card_bg'], width=22, anchor='w').grid(row=2, column=0, sticky='nw', padx=(0, 12), pady=10)
        reason_text = tk.Text(frm, font=self.fonts['body'], width=40, height=4, relief='flat', bd=0, bg=self.colors['light'], highlightthickness=1, highlightbackground=self.colors['border'], wrap='word')
        reason_text.grid(row=2, column=1, sticky='ew', padx=0, pady=10)
        reason_text.insert('1.0', 'Follow-up after consultation')
        
        def save():
            try:
                d = date_cal.get_date()
                time_str = time_entry.get().strip()
                # Normalize "9:00 AM" -> "09:00 AM" for parsing (single-digit hour only)
                if len(time_str) >= 2 and time_str[0].isdigit() and time_str[1] == ':':
                    time_str = '0' + time_str
                try:
                    t = datetime.strptime(time_str, '%I:%M %p').time()
                except ValueError:
                    try:
                        t = datetime.strptime(time_str, '%H:%M').time()
                    except ValueError:
                        messagebox.showerror("Error", "Invalid time. Use AM/PM (e.g. 9:00 AM or 2:30 PM).")
                        return
                # Must be within clinic hours (e.g. 8:00 AM–5:00 PM)
                if t.hour < CLINIC_START_HOUR or t.hour > CLINIC_END_HOUR:
                    messagebox.showerror("Error", "Time must be during clinic hours (8:00 AM–5:00 PM). You entered %s." % time_str)
                    return
                if t.hour == CLINIC_END_HOUR and (t.minute != 0 or t.second != 0):
                    messagebox.showerror("Error", "Time must be during clinic hours (8:00 AM–5:00 PM). You entered %s." % time_str)
                    return
                scheduled_at = datetime.combine(d, t).replace(second=0, microsecond=0)
                if scheduled_at <= datetime.utcnow():
                    messagebox.showwarning("Warning", "Schedule date/time must be in the future (choose a later time if scheduling for today)")
                    return
                # Block if anyone is already scheduled within 1 hour (before or after) this time
                one_hour = timedelta(hours=1)
                window_start = scheduled_at - one_hour
                window_end = scheduled_at + one_hour
                existing = session.query(FollowUpCheckup).filter(
                    FollowUpCheckup.status == 'scheduled',
                    FollowUpCheckup.scheduled_at > window_start,
                    FollowUpCheckup.scheduled_at < window_end
                ).first()
                if existing:
                    msg = "This time is not available. Another appointment is scheduled at %s (1-hour slots). Please choose a time at least 1 hour before or after." % existing.scheduled_at.strftime('%Y-%m-%d %I:%M %p')
                    messagebox.showerror("Time not available", msg)
                    return
                reason = reason_text.get('1.0', 'end-1c').strip() or None
                fu = FollowUpCheckup(
                    patient_id=p.id,
                    record_id=record.id if record else None,
                    scheduled_at=scheduled_at,
                    reason=reason,
                    status='scheduled'
                )
                session.add(fu)
                session.commit()
                messagebox.showinfo("Success", "Follow-up checkup scheduled")
                self.show_follow_ups()
            except ValueError as e:
                messagebox.showerror("Error", "Invalid date or time. Use YYYY-MM-DD and HH:MM")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        btn_row = tk.Frame(form, bg=self.colors['card_bg'])
        btn_row.pack(fill='x', padx=22, pady=(0, 22))
        tk.Button(btn_row, text="✕ Cancel", bg='#94a3b8', fg='white', font=self.fonts['body'], padx=25, pady=10,
                 command=self.show_follow_ups, cursor='hand2', relief='flat', bd=0).pack(side='right', padx=8)
        tk.Button(btn_row, text="Schedule follow-up", bg=self.colors['success'], fg='white', font=self.fonts['body'], padx=25, pady=10,
                 command=save, cursor='hand2', relief='flat', bd=0).pack(side='right')
    
    def clear_window(self):
        """Clear only the content area (sidebar persists)."""
        for widget in self.content_root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = ModernEMRApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
