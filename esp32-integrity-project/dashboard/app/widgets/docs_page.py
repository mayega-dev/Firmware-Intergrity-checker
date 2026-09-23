"""
Documentation Page: Firmware Integrity Monitor  v2.0
Styled with a high-end dark technical-paper / engineering manual aesthetic 
matching the telemetry command & control console.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout, QPushButton,
)
from PySide6.QtCore import Qt, QTimer

# ── Distinct Dark Engineering Theme Palette ─────────────────────────────────
C_BG_APP      = "#070A10"  # Deep telemetry window background
C_BG_PANEL    = "#0B0F19"  # Elevated card surface
C_BG_SURFACE  = "#1E293B"  # Dark container / code chips
C_BORDER      = "#334155"  # Structural borders
C_BORDER_LT   = "#475569"  # Highlighted structural borders
C_TEXT_PRI    = "#F8FAFC"  # High contrast primary white text
C_TEXT_SEC    = "#94A3B8"  # Slate secondary text
C_TEXT_DIM    = "#64748B"  # Muted metadata labels
C_ACCENT      = "#38BDF8"  # Electric blue primary accent
C_ACCENT_LT   = "#7DD3FC"  # Lighter blue highlight for readability
C_ACCENT_DIM  = "#0369A1"  # Translucent soft blue tint background
C_TEAL        = "#34D399"  # Success / Safe emerald
C_ORANGE      = "#FBBF24"  # Warning amber
C_RED         = "#F87171"  # Critical red
C_PURPLE      = "#A78BFA"  # Secondary protocol accent (Violet)

FONT_MONO = "JetBrains Mono, SFMono-Regular, Consolas, monospace"
FONT_UI   = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

QSS_BASE = f"""
    QWidget {{
        background: {C_BG_APP};
        color: {C_TEXT_PRI};
    }}
"""


class DocumentationPage(QWidget):
    """
    Renders full project documentation natively inside the app using 
    a clean dark engineering manual aesthetic.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QSS_BASE)

        self._active_key: str | None = None
        self._section_widgets: dict[str, tuple[QWidget, QPushButton | None]] = {}
        self._pending_sidebar_btns: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top Sub-Header Bar ───────────────────────────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(50)
        topbar.setStyleSheet(
            f"background: {C_BG_PANEL}; border-bottom: 2px solid {C_ACCENT};"
        )
        topbar_lay = QHBoxLayout(topbar)
        topbar_lay.setContentsMargins(28, 0, 28, 0)
        topbar_lay.setSpacing(16)

        brand = QLabel("📖  FIRMWARE INTEGRITY MONITOR   —   ENGINEERING SPECIFICATION")
        brand.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-family: {FONT_MONO}; font-size: 12px; "
            f"font-weight: 700; letter-spacing: 0.8px; background: transparent;"
        )
        topbar_lay.addWidget(brand)
        topbar_lay.addStretch()

        meta = QLabel("DOCS v2.0   ·   SPECIFICATION MANUAL")
        meta.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-family: {FONT_MONO}; font-size: 11px; "
            f"font-weight: 600; background: transparent;"
        )
        topbar_lay.addWidget(meta)
        root.addWidget(topbar)

        # ── Body Layout (Sidebar + Scroll Area) ──────────────────────────────
        body_widget = QWidget()
        body_widget.setStyleSheet(f"background: {C_BG_APP};")
        body_lay = QHBoxLayout(body_widget)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(
            f"background: {C_BG_PANEL}; border-right: 1px solid {C_BORDER};"
        )
        sidebar_scroll = QScrollArea(sidebar)
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setStyleSheet("background: transparent; border: none;")
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sidebar_content = QWidget()
        sidebar_content.setStyleSheet("background: transparent;")
        self._sidebar_lay = QVBoxLayout(sidebar_content)
        self._sidebar_lay.setContentsMargins(0, 24, 0, 24)
        self._sidebar_lay.setSpacing(18)

        self._add_sidebar_group("1. System Guide", [
            ("Overview",       "overview"),
            ("Architecture",   "architecture"),
            ("Wire Protocol",  "protocol"),
            ("App Views",      "pages"),
        ])
        self._add_sidebar_group("2. Implementation", [
            ("Running Locally", "local_run"),
            ("Docker Deployment","docker"),
            ("Hardware Wiring",  "wiring"),
        ])
        self._add_sidebar_group("3. Reference", [
            ("Troubleshooting",  "troubleshoot"),
            ("Known Limitations","limitations"),
        ])

        self._sidebar_lay.addStretch()
        sidebar_scroll.setWidget(sidebar_content)

        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        sidebar_lay.addWidget(sidebar_scroll)
        body_lay.addWidget(sidebar)

        # ── Main Content Scroll Area ─────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: {C_BG_APP}; border: none; }}
            QScrollBar:vertical {{
                background: {C_BG_SURFACE}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {C_BORDER_LT}; border-radius: 4px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {C_ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setStyleSheet(f"background: {C_BG_APP};")
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(56, 48, 56, 72)
        self._lay.setSpacing(0)

        # ── Build Documentation Sections ─────────────────────────────────────
        self._build_hero()

        for key, builder in [
            ("overview",      self._build_section_overview),
            ("architecture",  self._build_section_architecture),
            ("protocol",      self._build_section_protocol),
            ("pages",         self._build_section_pages),
            ("local_run",     self._build_section_local_run),
            ("docker",        self._build_section_docker),
            ("wiring",        self._build_section_wiring),
            ("troubleshoot",  self._build_section_troubleshoot),
            ("limitations",   self._build_section_limitations),
        ]:
            self._begin_section(key)
            builder()
            self._end_section()

        self._lay.addStretch()
        self.scroll.setWidget(self._content)
        body_lay.addWidget(self.scroll)
        root.addWidget(body_widget)

        self._patch_sidebar_refs()

    def _begin_section(self, key: str):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setObjectName(f"sec_{key}")
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)
        self._outer_lay = self._lay
        self._lay.addWidget(container)
        self._lay = container_lay
        self._pending_key = key
        self._pending_container = container

    def _end_section(self):
        self._section_widgets[self._pending_key] = (self._pending_container, None)
        self._lay = self._outer_lay

    def _scroll_to_section(self, key: str):
        if key not in self._section_widgets:
            return
        container, _ = self._section_widgets[key]
        def _do_scroll():
            pos = container.mapTo(self._content, container.rect().topLeft())
            self.scroll.verticalScrollBar().setValue(pos.y())
        QTimer.singleShot(0, _do_scroll)
        self._set_active(key)

    def _set_active(self, key: str):
        for _, (_, btn) in self._section_widgets.items():
            if btn:
                btn.setStyleSheet(self._sidebar_btn_qss(False))
        _, sidebar_btn = self._section_widgets.get(key, (None, None))
        if sidebar_btn:
            sidebar_btn.setStyleSheet(self._sidebar_btn_qss(True))
        self._active_key = key

    def _patch_sidebar_refs(self):
        for key, btn in self._pending_sidebar_btns.items():
            if key in self._section_widgets:
                container, _ = self._section_widgets[key]
                self._section_widgets[key] = (container, btn)

    def _sidebar_btn_qss(self, active: bool) -> str:
        if active:
            return (
                f"QPushButton {{"
                f"  color: {C_ACCENT}; background: #0B2341; border: none; "
                f"  border-left: 4px solid {C_ACCENT}; text-align: left; "
                f"  padding: 8px 20px; font-family: {FONT_UI}; font-size: 13px; font-weight: 700;"
                f"}}"
            )
        return (
            f"QPushButton {{"
            f"  color: {C_TEXT_SEC}; background: transparent; border: none; "
            f"  border-left: 4px solid transparent; text-align: left; "
            f"  padding: 8px 20px; font-family: {FONT_UI}; font-size: 13px; font-weight: 500;"
            f"}}"
            f"QPushButton:hover {{"
            f"  color: {C_ACCENT}; background: {C_BG_SURFACE}; "
            f"  border-left: 4px solid {C_BORDER_LT};"
            f"}}"
        )

    def _add_sidebar_group(self, title: str, links: list):
        group = QWidget()
        group.setStyleSheet("background: transparent;")
        gl = QVBoxLayout(group)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(4)

        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-family: {FONT_MONO}; font-size: 10px; "
            f"font-weight: 700; letter-spacing: 1.5px; padding: 0 20px 8px;"
        )
        gl.addWidget(lbl)

        for text, key in links:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._sidebar_btn_qss(False))
            btn.clicked.connect(lambda checked=False, k=key: self._scroll_to_section(k))
            gl.addWidget(btn)
            self._pending_sidebar_btns[key] = btn

        self._sidebar_lay.addWidget(group)

    def _div(self, spacing_before: int = 36):
        self._lay.addSpacing(spacing_before)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {C_BORDER}; border: none;")
        self._lay.addWidget(line)

    def _eyebrow(self, text: str):
        self._lay.addSpacing(16)
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {C_ACCENT}; font-family: {FONT_MONO}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.5px;"
        )
        self._lay.addWidget(lbl)
        self._lay.addSpacing(6)

    def _h2(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-family: {FONT_UI}; font-size: 24px; "
            f"font-weight: 800; border-bottom: 2px solid {C_BORDER}; padding-bottom: 12px;"
        )
        self._lay.addWidget(lbl)
        self._lay.addSpacing(16)

    def _h3(self, text: str, color: str = None):
        color = color or C_ACCENT_LT
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-family: {FONT_UI}; font-size: 16px; "
            f"font-weight: 700; margin-top: 20px;"
        )
        self._lay.addWidget(lbl)
        self._lay.addSpacing(8)

    def _para(self, text: str):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-family: {FONT_UI}; "
            f"font-size: 14px; line-height: 1.8; margin-bottom: 10px;"
        )
        self._lay.addWidget(lbl)

    def _code(self, text: str):
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {C_BG_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 6px;"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(20, 16, 20, 16)
        lbl = QLabel(text)
        lbl.setWordWrap(False)
        lbl.setTextFormat(Qt.PlainText)
        lbl.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-family: {FONT_MONO}; "
            f"font-size: 12px; background: transparent; line-height: 1.7;"
        )
        fl.addWidget(lbl)
        self._lay.addWidget(frame)
        self._lay.addSpacing(16)

    def _card_grid(self, cards: list, cols: int = 2):
        gw = QWidget()
        gw.setStyleSheet("background: transparent;")
        grid = QGridLayout(gw)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        for i, (title, color, body) in enumerate(cards):
            card = QFrame()
            card.setStyleSheet(
                f"background: {C_BG_PANEL}; border: 1px solid {C_BORDER}; "
                f"border-top: 4px solid {color}; border-radius: 8px;"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(22, 20, 22, 20)
            cl.setSpacing(10)
            t = QLabel(title)
            t.setStyleSheet(
                f"color: {C_TEXT_PRI}; font-family: {FONT_UI}; font-size: 15px; "
                f"font-weight: 700; background: transparent; border: none;"
            )
            cl.addWidget(t)
            b = QLabel(body)
            b.setWordWrap(True)
            b.setStyleSheet(
                f"color: {C_TEXT_SEC}; font-family: {FONT_UI}; font-size: 13px; "
                f"line-height: 1.7; background: transparent; border: none;"
            )
            cl.addWidget(b)
            grid.addWidget(card, i // cols, i % cols)
        self._lay.addWidget(gw)
        self._lay.addSpacing(16)

    def _table(self, headers: list, rows: list):
        t = QFrame()
        t.setStyleSheet(
            f"background: {C_BG_PANEL}; border: 1px solid {C_BORDER}; border-radius: 8px;"
        )
        tl = QVBoxLayout(t)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)
        hrow = QFrame()
        hrow.setStyleSheet(
            f"background: {C_BG_SURFACE}; border-bottom: 2px solid {C_BORDER};"
        )
        hrl = QHBoxLayout(hrow)
        hrl.setContentsMargins(18, 12, 18, 12)
        hrl.setSpacing(0)
        for i, h in enumerate(headers):
            hl = QLabel(h.upper())
            hl.setStyleSheet(
                f"color: {C_TEXT_PRI}; font-family: {FONT_MONO}; font-size: 11px; "
                f"font-weight: 700; letter-spacing: 1px; background: transparent; border: none;"
            )
            hrl.addWidget(hl, 1 if i > 0 else 0)
            if i == 0:
                hl.setFixedWidth(200)
        tl.addWidget(hrow)
        for ri, row in enumerate(rows):
            rframe = QFrame()
            rframe.setStyleSheet(
                f"background: {C_BG_PANEL if ri % 2 == 0 else C_BG_SURFACE}; "
                f"border-bottom: 1px solid {C_BORDER};"
            )
            rl = QHBoxLayout(rframe)
            rl.setContentsMargins(18, 12, 18, 12)
            rl.setSpacing(0)
            for ci, cell in enumerate(row):
                cl = QLabel(str(cell))
                cl.setWordWrap(True)
                if ci == 0:
                    cl.setStyleSheet(
                        f"color: {C_ACCENT_LT}; font-family: {FONT_MONO}; font-size: 12px; "
                        f"font-weight: 600; background: transparent; border: none;"
                    )
                    cl.setFixedWidth(200)
                    rl.addWidget(cl)
                else:
                    cl.setStyleSheet(
                        f"color: {C_TEXT_SEC}; font-family: {FONT_UI}; font-size: 13px; "
                        f"background: transparent; border: none;"
                    )
                    rl.addWidget(cl, 1)
            tl.addWidget(rframe)
        self._lay.addWidget(t)
        self._lay.addSpacing(16)

    def _step_list(self, steps: list):
        for i, step in enumerate(steps):
            title, body = step[0], step[1]
            code = step[2] if len(step) > 2 else None
            row = QFrame()
            row.setStyleSheet("background: transparent; border: none;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(16)
            rl.setAlignment(Qt.AlignTop)
            num = QLabel(str(i + 1))
            num.setFixedSize(28, 28)
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(
                f"color: #070A10; background: {C_ACCENT}; "
                f"border-radius: 14px; font-family: {FONT_MONO}; "
                f"font-size: 12px; font-weight: 700;"
            )
            rl.addWidget(num, 0, Qt.AlignTop)
            inner = QWidget()
            inner.setStyleSheet("background: transparent;")
            il = QVBoxLayout(inner)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(6)
            tl = QLabel(title)
            tl.setStyleSheet(
                f"color: {C_TEXT_PRI}; font-family: {FONT_UI}; font-size: 15px; font-weight: 700;"
            )
            il.addWidget(tl)
            bl = QLabel(body)
            bl.setWordWrap(True)
            bl.setStyleSheet(
                f"color: {C_TEXT_SEC}; font-family: {FONT_UI}; font-size: 13px; line-height: 1.7;"
            )
            il.addWidget(bl)
            if code:
                cf = QFrame()
                cf.setStyleSheet(
                    f"background: {C_BG_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 6px;"
                )
                cfl = QVBoxLayout(cf)
                cfl.setContentsMargins(16, 12, 16, 12)
                cl = QLabel(code)
                cl.setStyleSheet(
                    f"color: {C_TEXT_PRI}; font-family: {FONT_MONO}; "
                    f"font-size: 12px; background: transparent; border: none;"
                )
                cfl.addWidget(cl)
                il.addWidget(cf)
            rl.addWidget(inner, 1)
            self._lay.addWidget(row)
            self._lay.addSpacing(16)

    def _callout(self, icon: str, text: str, color: str):
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {C_BG_PANEL}; border: 1px solid {C_BORDER}; "
            f"border-left: 4px solid {color}; border-radius: 6px;"
        )
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(18, 14, 18, 14)
        fl.setSpacing(14)
        ic = QLabel(icon)
        ic.setStyleSheet(
            f"color: {color}; font-size: 15px; font-weight: bold; background: transparent; border: none;"
        )
        ic.setFixedWidth(22)
        fl.addWidget(ic, 0, Qt.AlignTop)
        tx = QLabel(text)
        tx.setWordWrap(True)
        tx.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-family: {FONT_UI}; font-size: 13px; "
            f"line-height: 1.7; background: transparent; border: none;"
        )
        fl.addWidget(tx, 1)
        self._lay.addWidget(frame)
        self._lay.addSpacing(14)

    # ════════════════════════════════════════════════════════════════════════
    # Section builders
    # ════════════════════════════════════════════════════════════════════════

    def _build_hero(self):
        hero = QFrame()
        hero.setStyleSheet(
            f"background: {C_BG_PANEL}; border: 1px solid {C_BORDER}; "
            f"border-top: 4px solid {C_ACCENT}; border-radius: 10px;"
        )
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(40, 36, 40, 36)
        hl.setSpacing(14)
        
        eye = QLabel("ESP32 MICROCONTROLLER EMBEDDED SECURITY   ·   RUNTIME INTEGRITY SUITE")
        eye.setStyleSheet(
            f"color: {C_ACCENT}; font-family: {FONT_MONO}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1.5px; background: transparent; border: none;"
        )
        hl.addWidget(eye)
        
        title = QLabel("Firmware Integrity Monitor & Sentinel Dashboard")
        title.setStyleSheet(
            f"color: {C_TEXT_PRI}; font-family: {FONT_UI}; font-size: 28px; "
            f"font-weight: 800; background: transparent; border: none;"
        )
        hl.addWidget(title)
        
        desc = QLabel(
            "An enterprise-grade hardware-software integrity verification system. The microcontroller continuously "
            "computes runtime SHA-256 hashes of its firmware partition and monitors anti-rollback counters. "
            "This desktop companion application connects over a dedicated serial UART link via PySide6 and device_link "
            "workers to ingest, classify, log, and render high-precision security telemetry."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {C_TEXT_SEC}; font-family: {FONT_UI}; font-size: 14px; "
            f"line-height: 1.8; background: transparent; border: none;"
        )
        hl.addWidget(desc)
        
        chips_frame = QFrame()
        chips_frame.setStyleSheet("background: transparent; border: none;")
        cfl = QHBoxLayout(chips_frame)
        cfl.setContentsMargins(0, 6, 0, 0)
        cfl.setSpacing(10)
        
        for label, fg, bg in [
            ("Python 3.11+",     C_ACCENT,  "#0B2341"),
            ("PySide6 · Qt6",    C_PURPLE,  "#241842"),
            ("ESP-IDF v5.3.1",   C_TEAL,    "#063220"),
            ("SHA-256 Crypto",   C_ACCENT,  "#0B2341"),
            ("Docker / X11",     C_ORANGE,  "#3F2A05"),
            ("PySerial UART",    C_PURPLE,  "#241842"),
        ]:
            c = QLabel(label)
            c.setStyleSheet(
                f"color: {fg}; background: {bg}; border: 1px solid {fg}; "
                f"border-radius: 12px; padding: 5px 14px; "
                f"font-family: {FONT_MONO}; font-size: 11px; font-weight: 600;"
            )
            cfl.addWidget(c)
        cfl.addStretch()
        hl.addWidget(chips_frame)
        
        self._lay.addWidget(hero)
        self._lay.addSpacing(36)

    def _build_section_overview(self):
        self._eyebrow("01 — SYSTEM OVERVIEW")
        self._h2("Operational Profile & Module Layout")
        self._para(
            "The Firmware Integrity Monitor is structured around a modular Python backend package (`dashboard/app/`) "
            "coordinated via `main_window.py` and structured firmware code under `firmware/main/`."
        )
        self._para(
            "The architecture cleanly separates core logic (`models.py`, `protocol.py`, `device_link.py`) "
            "from user-interface widgets (`stat_card.py`, `status_hero.py`, `timeline.py`) and page views."
        )
        self._card_grid([
            ("Real-Time Telemetry", C_ACCENT,
             "Live status ingestion via device_link workers. Instant visual parsing through status_hero and stat_cards."),
            ("Custom Event Timeline", C_PURPLE,
             "Custom-painted rolling event strip (timeline.py) tracking successful validation sweeps and security triggers."),
            ("Interactive Console", C_ORANGE,
             "Raw traffic inspector (console_page.py) with command dispatch capabilities for polling and tampering simulation."),
            ("Forensic Logging & CSV", C_TEAL,
             "Complete searchable log view (log_page.py) with one-click CSV export mapped to persistent volumes."),
        ])
        self._lay.addSpacing(24)

    def _build_section_architecture(self):
        self._div()
        self._eyebrow("02 — SYSTEM ARCHITECTURE")
        self._h2("Component Topology & Project Tree Model")
        self._para(
            "The repository follows a clean two-tier layout separating the desktop control application (`dashboard/`) "
            "from the embedded ESP-IDF firmware (`firmware/`) and container orchestration files."
        )
        
        # ── Professional Architectural Tree Card ─────────────────────────────
        arch_card = QFrame()
        arch_card.setStyleSheet(
            f"background: {C_BG_PANEL}; border: 1px solid {C_BORDER}; "
            f"border-radius: 8px;"
        )
        arch_lay = QVBoxLayout(arch_card)
        arch_lay.setContentsMargins(24, 20, 24, 20)
        arch_lay.setSpacing(12)

        tree_header = QLabel("PROJECT REPOSITORY TOPOLOGY HIERARCHY")
        tree_header.setStyleSheet(
            f"color: {C_ACCENT}; font-family: {FONT_MONO}; font-size: 11px; "
            f"font-weight: 700; letter-spacing: 1px; background: transparent; border: none;"
        )
        arch_lay.addWidget(tree_header)

        tree_content = QFrame()
        tree_content.setStyleSheet(
            f"background: {C_BG_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 6px;"
        )
        tcl = QVBoxLayout(tree_content)
        tcl.setContentsMargins(16, 14, 16, 14)
        tcl.setSpacing(4)

        tree_text = QLabel(
            f"<span style='color: {C_ACCENT_LT}; font-weight: 750;'>esp32-integrity-project/</span><br>"
            f"<span style='color: {C_TEXT_SEC};'>├──</span> <span style='color: {C_TEXT_PRI}; font-weight: 600;'>dashboard/app/</span><br>"
            f"<span style='color: {C_TEXT_SEC};'>│   ├──</span> <span style='color: {C_TEXT_SEC};'>resources/ <span style='color: {C_TEXT_DIM};'>(theme.qss)</span></span><br>"
            f"<span style='color: {C_TEXT_SEC};'>│   └──</span> <span style='color: {C_TEXT_SEC};'>widgets/ <span style='color: {C_TEXT_DIM};'>(console, dashboard, docs, log, settings, sidebar, stat_card, status_hero, timeline)</span></span><br>"
            f"<span style='color: {C_TEXT_SEC};'>├──</span> <span style='color: {C_PURPLE}; font-weight: 600;'>Core Modules:</span> <span style='color: {C_TEXT_DIM};'>(main_window.py, device_link.py, models.py, protocol.py)</span><br>"
            f"<span style='color: {C_TEXT_SEC};'>├──</span> <span style='color: {C_ORANGE}; font-weight: 600;'>scripts/ & packaging/</span> <span style='color: {C_TEXT_DIM};'>(run-with-device.sh)</span><br>"
            f"<span style='color: {C_TEXT_SEC};'>└──</span> <span style='color: {C_TEAL}; font-weight: 750;'>firmware/main/</span> <span style='color: {C_TEXT_DIM};'>(crypto.c/h, rollback.c, logger.c/h, serial_comm.c/h, main.c)</span>"
        )
        tree_text.setTextFormat(Qt.RichText)
        tree_text.setStyleSheet(
            f"font-family: {FONT_MONO}; font-size: 12px; background: transparent; line-height: 1.6;"
        )
        tcl.addWidget(tree_text)
        arch_lay.addWidget(tree_content)

        self._lay.addWidget(arch_card)
        self._lay.addSpacing(20)

    def _build_section_protocol(self):
        self._h3("Wire Protocol & Command Reference")
        self._para(
            "Communication between the microcontroller and the desktop app (`protocol.py`) utilizes structured, newline-terminated ASCII frames."
        )
        self._code(
            "Incoming Frames (from device):\n"
            "::STATUS:<fw_version>:<hardware_revision>::   (sent once, at boot)\n"
            "::ALERT:<LEVEL>:<EVENT_CODE>::                (sent per security event)\n\n"
            "Outgoing Commands (to device):\n"
            "::POLL::      Trigger an immediate verification sweep\n"
            "::TAMPER::    Debug builds only (ENABLE_TAMPER_SIMULATION=1) - injects test tamper event"
        )
        self._table(
            ["Event Code", "Severity Level", "System Reaction & Description"],
            [
                ["STATUS_SAFE", "INFO (Emerald)", "Runtime integrity check passed — active firmware matches golden baseline."],
                ["FIRMWARE_TAMPERED", "CRITICAL (Red)", "Integrity violation detected — running firmware hash mismatch."],
                ["ROLLBACK_ATTEMPT_BLOCKED", "CRITICAL (Red)", "Boot halted — attempted execution of version below anti-rollback floor."],
            ]
        )
        self._lay.addSpacing(20)

    def _build_section_pages(self):
        self._div()
        self._eyebrow("03 — INTERFACE VIEWS")
        self._h2("Dashboard View Hierarchy")
        self._card_grid([
            ("Dashboard (dashboard_page.py)", C_ACCENT,
             "Headline status indicator via status_hero, summary metrics via stat_cards, and rolling visual event timeline."),
            ("Alert Log (log_page.py)", C_PURPLE,
             "Complete, searchable, filterable history of every security event encountered during the current session, with CSV export."),
            ("Device Console (console_page.py)", C_ORANGE,
             "Raw traffic feed displaying incoming wire packets directly, plus guarded command buttons for ::POLL:: and ::TAMPER::."),
            ("Settings (settings_page.py)", C_TEAL,
             "Connection management: port enumeration (auto-grouping ESP32 bridge chips), baud rate, and Simulation Mode."),
        ])
        self._lay.addSpacing(24)

    def _build_section_local_run(self):
        self._div()
        self._eyebrow("04 — DEPLOYMENT & SETUP")
        self._h2("Local Execution (Native Python)")
        self._para(
            "To deploy and run the dashboard natively on Linux, macOS, or Windows without containerization:"
        )
        self._step_list([
            ("Clone and configure virtual environment", "",
             "python3 -m venv venv\n"
             "source venv/bin/activate        # Windows: venv\\Scripts\\activate"),
            ("Install project dependencies", "",
             "pip install -r requirements.txt"),
            ("Launch application instance",
             "Enable Simulation Mode if no physical device is attached, or execute via scripts/run-with-device.sh.",
             "python main.py"),
        ])
        self._callout("ℹ", (
            "Operating without hardware? Check <b>Simulation mode</b> in the Settings tab and click Connect. "
            "It automatically generates synthetic telemetry locally for full UI verification."
        ), C_ACCENT)
        self._lay.addSpacing(20)

    def _build_section_docker(self):
        self._h3("Containerized Execution (Docker & Compose)")
        self._para(
            "Because this tool renders a native GUI interface, running inside Docker requires X11 window server forwarding "
            "along with device node mapping, supported by scripts in `firmware/scripts/` and `docker-compose.yml`."
        )
        self._step_list([
            ("Authorize X11 display forwarding (Linux host)",
             "Grants container authorization to draw on your local X server display.",
             "export DISPLAY\n"
             "xhost +local:docker"),
            ("Run simulation instance", "",
             "docker compose up --build"),
            ("Run with physical hardware passthrough",
             "Passes the specified serial device node directly into the container runtime.",
             "PORT=/dev/ttyUSB0 docker compose run --rm dashboard-hw"),
        ])
        self._callout("⚠", (
            "File Persistence Note: Ensure volume mounts are configured (`-v ./exports:/data/exports`) "
            "so exported audit reports survive container teardown."
        ), C_ORANGE)
        self._lay.addSpacing(20)

    def _build_section_wiring(self):
        self._div()
        self._eyebrow("05 — HARDWARE CONFIGURATION")
        self._h2("Physical Wiring & UART Topologies")
        self._para(
            "The alert UART channel is physically separate from the microcontroller's primary flashing/debug port. "
            "Choose one of the following integration topologies supported by `firmware/main/serial_comm.c`:"
        )
        self._step_list([
            ("Topology A: Single Cable Multiplexing",
             "Configure firmware via `idf.py menuconfig` (or docker-menuconfig.sh script) to route security alerts over UART0.",
             "idf.py menuconfig\n"
             "  -> Component config -> ESP System Settings -> Channel for console output -> 'No console output'\n"
             "  -> Firmware Integrity Checker -> ALERT_UART_PORT_NUM = 0"),
            ("Topology B: Dedicated Dual-Cable (Recommended)",
             "Retain console debugging output on UART0 while connecting an independent USB-to-TTL adapter to designated alert pins (GPIO17 TX, GPIO18 RX).",
             "Adapter TX -> Board RX\n"
             "Adapter RX -> Board TX\n"
             "Adapter GND -> Board GND"),
        ])
        self._lay.addSpacing(24)

    def _build_section_troubleshoot(self):
        self._div()
        self._eyebrow("06 — REFERENCE & DIAGNOSTICS")
        self._h2("Troubleshooting Matrix")
        self._table(
            ["Symptom / Error", "Root Cause & Corrective Action"],
            [
                ["'No serial ports found' in Settings", "Device enumeration failure. Inspect physical USB cabling, check `ls /dev/ttyUSB*` (Linux) or Device Manager (Windows). Verify container `--device` mappings if running via Docker."],
                ["Board missing from 'ESP32 devices detected'", "USB-to-UART bridge chip VID/PID not matched in whitelist (CP210x, CH340/343, FTDI). Select device manually under 'Other serial ports'."],
                ["Dashboard window fails to render", "X11 display authorization missing. Execute `xhost +local:docker` on host Linux, or ensure VcXsrv / XQuartz is active for WSL2 / macOS environments."],
                ["Exported CSV files missing on host", "Container running without persistent volume binding. Verify `./exports` is correctly mapped to `/data/exports` in `docker-compose.yml`."],
            ]
        )
        self._lay.addSpacing(20)

    def _build_section_limitations(self):
        self._h3("Known Architectural Limitations")
        self._para(
            "• <b>Self-Referential Baseline:</b> The reference golden hash is computed locally within firmware components (`crypto.c`, `rollback.c`) "
            "during initial provisioning rather than signed via a remote HSM, protecting against post-boot alterations.<br>"
            "• <b>Direct Serial Transport:</b> Telemetry relies entirely on point-to-point UART framing rather than networked protocols "
            "(MQTT/TLS), restricting observation to hardware physically tethered to the host workstation."
        )
        self._lay.addSpacing(24)