"""
Mood - Main application entry
Dark, minimal media organizer + mood slideshow.
"""

import sys
import os
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Set

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QScrollArea, QGridLayout, QFrame, QMessageBox, QInputDialog,
    QSplitter, QSizePolicy, QProgressBar, QLineEdit, QCheckBox,
    QComboBox, QSpinBox, QStackedWidget, QAbstractItemView, QDialog, QMenu, QTabWidget,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QToolButton, QSlider
)
from PySide6.QtCore import (
    Qt, QSize, QTimer, QThread, Signal, QUrl, QPoint, QRect, QRectF, QPointF,
    QObject, QRunnable, QThreadPool, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QPixmap, QImage, QFont, QColor, QPalette, QKeySequence,
    QShortcut, QDragEnterEvent, QDropEvent, QPainter, QBrush, QPen,
    QPainterPath, QAction
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

import config
from database import Database
from converter import process_file, process_files_parallel, detect_media_type
from thumbnails import get_thumbnail
from logger import log
from crypto_vault import vault, folder_id_for_name
from settings_store import load_settings, save_settings


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
STYLE = f"""
QMainWindow {{
    background-color: {config.COLOR_BG};
}}
QWidget {{
    background-color: transparent;
    color: {config.COLOR_TEXT};
    font-family: "SF Pro Text", "SF Pro Display", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}
QMainWindow > QWidget {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_BG}, stop:1 {config.COLOR_BG_2});
}}
QDialog {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_BG}, stop:1 {config.COLOR_BG_2});
}}
QToolTip {{
    background-color: rgba(30,30,34,0.96);
    color: {config.COLOR_TEXT};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 6px 10px;
}}
QPushButton {{
    background-color: rgba(128,128,138,0.22);
    color: {config.COLOR_TEXT};
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 15px;
    padding: 10px 18px;
    min-height: 20px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: rgba(140,140,150,0.34);
    border: 1px solid rgba(255,255,255,0.14);
}}
QPushButton:pressed {{
    background-color: rgba(120,120,128,0.5);
}}
QPushButton:disabled {{
    color: rgba(255,255,255,0.35);
    background-color: rgba(120,120,128,0.12);
    border: 1px solid rgba(255,255,255,0.04);
}}
QPushButton#primary {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_ACCENT_HOVER}, stop:1 {config.COLOR_ACCENT});
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 15px;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5cb0ff, stop:1 {config.COLOR_ACCENT_HOVER});
}}
QPushButton#primary:pressed {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_ACCENT}, stop:1 {config.COLOR_ACCENT_2});
}}
QPushButton#danger {{
    background-color: rgba(255,69,58,0.16);
    color: {config.COLOR_DANGER};
    border: 1px solid rgba(255,69,58,0.28);
    border-radius: 15px;
}}
QPushButton#danger:hover {{
    background-color: rgba(255,69,58,0.28);
}}
QListWidget {{
    background-color: rgba(44,44,48,0.55);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    outline: none;
    padding: 6px;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-radius: 10px;
    margin: 2px 3px;
}}
QListWidget::item:selected {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_ACCENT_HOVER}, stop:1 {config.COLOR_ACCENT});
    color: white;
}}
QListWidget::item:hover:!selected {{
    background-color: rgba(140,140,150,0.22);
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255,255,255,0.22);
    border-radius: 4px;
    min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QLabel {{
    color: {config.COLOR_TEXT};
}}
QLabel#dim {{
    color: {config.COLOR_TEXT_DIM};
}}
QLabel#pill {{
    background-color: rgba(120,120,128,0.18);
    border-radius: 12px;
    padding: 10px 12px;
    color: {config.COLOR_TEXT_DIM};
}}
QLineEdit, QSpinBox, QComboBox {{
    background-color: rgba(120,120,128,0.18);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 9px 14px;
    color: {config.COLOR_TEXT};
    selection-background-color: {config.COLOR_ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1.5px solid {config.COLOR_ACCENT};
    background-color: rgba(120,120,128,0.22);
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox QAbstractItemView {{
    background-color: {config.COLOR_SURFACE};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    selection-background-color: {config.COLOR_ACCENT};
    padding: 4px;
}}
QProgressBar {{
    background-color: rgba(120,120,128,0.18);
    border: none;
    border-radius: 5px;
    text-align: center;
    height: 6px;
    max-height: 6px;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {config.COLOR_ACCENT}, stop:1 {config.COLOR_ACCENT_HOVER});
    border-radius: 5px;
}}
QFrame#card {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(58,58,64,0.55), stop:1 rgba(36,36,40,0.55));
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 22px;
}}
QTabWidget {{
    background: transparent;
}}
QTabWidget::pane {{
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    background: rgba(44,44,46,0.55);
    top: 8px;
    padding: 14px;
    margin-top: 4px;
}}
QTabBar {{
    alignment: left;
}}
QTabBar::tab {{
    background: transparent;
    color: {config.COLOR_TEXT_DIM};
    padding: 11px 20px;
    margin: 4px 6px 8px 0;
    border-radius: 14px;
    font-weight: 600;
    min-height: 20px;
}}
QTabBar::tab:selected {{
    background: rgba(120,120,128,0.32);
    color: {config.COLOR_TEXT};
}}
QTabBar::tab:hover:!selected {{
    background: rgba(120,120,128,0.18);
}}
QCheckBox {{
    spacing: 10px;
    color: {config.COLOR_TEXT};
}}
QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 7px;
    border: none;
    background: rgba(120,120,128,0.28);
}}
QCheckBox::indicator:checked {{
    background: {config.COLOR_ACCENT};
}}
QMenu {{
    background-color: rgba(30,30,32,0.97);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 8px;
}}
QMenu::item {{
    padding: 10px 28px;
    border-radius: 10px;
}}
QMenu::item:selected {{
    background-color: {config.COLOR_ACCENT};
}}
QMenu::separator {{
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 6px 12px;
}}

/* =================== Apple-style layout =================== */
QFrame#sidebar {{
    background-color: rgba(28,28,32,0.72);
    border-right: 1px solid rgba(255,255,255,0.06);
}}
QLabel#wordmark {{
    font-size: 24px;
    font-weight: 800;
    color: {config.COLOR_TEXT};
    padding: 0 4px 2px 4px;
}}
QLabel#sectionHeader {{
    color: {config.COLOR_TEXT_DIM};
    font-size: 11px;
    font-weight: 700;
    padding: 8px 6px 2px 6px;
}}
QListWidget#sidebarList {{
    background: transparent;
    border: none;
    padding: 2px;
    outline: none;
}}
QListWidget#sidebarList::item {{
    padding: 9px 12px;
    border-radius: 10px;
    margin: 2px 0;
    color: {config.COLOR_TEXT};
}}
QListWidget#sidebarList::item:selected {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_ACCENT_HOVER}, stop:1 {config.COLOR_ACCENT});
    color: white;
}}
QListWidget#sidebarList::item:hover:!selected {{
    background-color: rgba(140,140,150,0.20);
}}
QLabel#headerTitle {{
    font-size: 23px;
    font-weight: 700;
    color: {config.COLOR_TEXT};
}}
QLabel#headerSub {{
    font-size: 12px;
    color: {config.COLOR_TEXT_DIM};
}}
QScrollArea#gridScroll {{
    background: transparent;
    border: none;
}}
QLabel#dropHint {{
    color: {config.COLOR_TEXT_DIM};
    font-size: 15px;
    border: 2px dashed rgba(255,255,255,0.12);
    border-radius: 24px;
    padding: 44px;
    margin: 10px 60px;
    background: rgba(255,255,255,0.02);
}}
QFrame#actionBar {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(56,56,62,0.94), stop:1 rgba(40,40,46,0.94));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
}}
QFrame#statusBar {{
    background-color: rgba(18,18,22,0.55);
    border-top: 1px solid rgba(255,255,255,0.06);
}}
QLabel#statusText {{ color: {config.COLOR_TEXT_DIM}; font-size: 12px; }}
QLabel#statusHint {{ color: rgba(255,255,255,0.28); font-size: 11px; }}

/* segmented filter control */
QFrame#segmented {{
    background: rgba(120,120,128,0.20);
    border-radius: 12px;
}}
QPushButton#segBtn {{
    background: transparent;
    border: none;
    border-radius: 9px;
    padding: 6px 15px;
    font-weight: 600;
    color: {config.COLOR_TEXT_DIM};
    min-height: 16px;
}}
QPushButton#segBtn:hover {{ color: {config.COLOR_TEXT}; }}
QPushButton#segBtn:checked {{
    background: rgba(130,130,140,0.55);
    color: {config.COLOR_TEXT};
}}

/* toolbar menu buttons */
QToolButton {{
    background-color: rgba(128,128,138,0.22);
    color: {config.COLOR_TEXT};
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 9px 16px;
    font-weight: 600;
    font-size: 13px;
}}
QToolButton:hover {{
    background-color: rgba(140,140,150,0.34);
    border: 1px solid rgba(255,255,255,0.14);
}}
QToolButton:pressed {{ background-color: rgba(120,120,128,0.5); }}
QToolButton#primary {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {config.COLOR_ACCENT_HOVER}, stop:1 {config.COLOR_ACCENT});
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.22);
}}
QToolButton#primary:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5cb0ff, stop:1 {config.COLOR_ACCENT_HOVER});
}}
QToolButton::menu-indicator {{ image: none; width: 0; }}

/* sidebar link (Favoriten) */
QPushButton#sidebarLink {{
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 9px 12px;
    text-align: left;
    font-weight: 600;
    color: {config.COLOR_TEXT};
}}
QPushButton#sidebarLink:hover {{
    background: rgba(140,140,150,0.20);
}}
QPushButton#sidebarLink:pressed {{
    background: rgba(140,140,150,0.30);
}}

/* tile zoom slider */
QSlider#zoomSlider::groove:horizontal {{
    height: 4px;
    background: rgba(255,255,255,0.18);
    border-radius: 2px;
}}
QSlider#zoomSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
    background: {config.COLOR_TEXT};
}}
QSlider#zoomSlider::sub-page:horizontal {{
    background: {config.COLOR_ACCENT};
    border-radius: 2px;
}}
"""


# ---------------------------------------------------------------------------
# Liquid-glass helpers: soft depth shadows + opacity fade animations
# ---------------------------------------------------------------------------
def add_soft_shadow(widget: QWidget, blur: int = 42, y_offset: int = 10,
                    alpha: int = 120) -> QGraphicsDropShadowEffect:
    """Give a widget a soft drop shadow so panels appear to float (glass depth)."""
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setXOffset(0)
    eff.setYOffset(y_offset)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)
    return eff


def fade_widget(widget: QWidget, duration: int = 280,
                start: float = 0.0, end: float = 1.0,
                curve: QEasingCurve.Type = QEasingCurve.OutCubic) -> QPropertyAnimation:
    """
    Animate a widget's opacity from start -> end. References are stored on the
    widget so the effect/animation are not garbage-collected mid-flight.
    NOTE: replaces any existing QGraphicsEffect on the widget.
    """
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(curve)
    widget._fx_effect = eff       # keep alive
    widget._fx_anim = anim        # keep alive
    anim.start()
    return anim


# ---------------------------------------------------------------------------
# Worker for conversion (keeps UI responsive)
# ---------------------------------------------------------------------------
class ConvertWorker(QThread):
    progress = Signal(int, int, str)          # current, total, filename
    finished = Signal(list)                   # list of (new_path, original, media_type)
    error = Signal(str)

    def __init__(self, files: List[Path], dest_folder: Path, date_str: str):
        super().__init__()
        self.files = files
        self.dest_folder = dest_folder
        self.date_str = date_str

    def run(self):
        def cb(current, total, name):
            self.progress.emit(current, total, name)
        try:
            results = process_files_parallel(
                self.files, self.dest_folder, self.date_str, progress_cb=cb
            )
            self.finished.emit(results)
        except Exception as e:
            log.error(f"ConvertWorker crash: {e}")
            self.error.emit(str(e))
            self.finished.emit([])



# ---------------------------------------------------------------------------
# Parallel thumbnail loading (thread pool)
# ---------------------------------------------------------------------------
class ThumbLoadSignals(QObject):
    finished = Signal(object, object)  # ThumbItem, QPixmap or None


class ThumbLoadRunnable(QRunnable):
    def __init__(self, item: "ThumbItem"):
        super().__init__()
        self.item = item
        self.signals = ThumbLoadSignals()

    def run(self):
        try:
            display_path = vault.resolve_for_display(self.item.path) if vault.is_unlocked else self.item.path
            if display_path is None:
                self.signals.finished.emit(self.item, None)
                return
            thumb = get_thumbnail(display_path)
            pix = None
            if thumb and thumb.exists():
                pix = QPixmap(str(thumb))
            self.signals.finished.emit(self.item, pix)
        except Exception:
            self.signals.finished.emit(self.item, None)


# Apple Photos-style square tile size
THUMB_TILE = 184


# ---------------------------------------------------------------------------
# Thumbnail widget for the import grid (Apple Photos-style tile)
# ---------------------------------------------------------------------------
class ThumbItem(QFrame):
    selected_changed = Signal(object, bool)   # self, is_selected
    double_clicked = Signal(object)           # self
    context_requested = Signal(object, object)  # self, global QPoint

    def __init__(self, path: Path, media_type: str, size: int = THUMB_TILE,
                 media_id=None, favorite: bool = False, parent=None):
        super().__init__(parent)
        self.path = path
        self.media_type = media_type
        self.media_id = media_id
        self.is_favorite = bool(favorite)
        self.is_selected = False
        self._src_pix: Optional[QPixmap] = None
        self._hover = False
        self._loading = True
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(path.name)
        # parallel load via global thread pool
        QTimer.singleShot(0, self._queue_thumb)

    def _queue_thumb(self):
        pool = QThreadPool.globalInstance()
        pool.setMaxThreadCount(max(4, (os.cpu_count() or 4)))
        job = ThumbLoadRunnable(self)
        job.signals.finished.connect(self._on_thumb_ready)
        pool.start(job)

    def _on_thumb_ready(self, item, pix):
        if item is not self:
            return
        self._loading = False
        self._src_pix = pix if (pix is not None and not pix.isNull()) else None
        self.update()
        # gentle fade-in so the grid populates smoothly
        try:
            fade_widget(self, duration=320, start=0.0, end=1.0)
        except Exception:
            pass

    # ---- interaction ----
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.update()
            self.selected_changed.emit(self, self.is_selected)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        self.context_requested.emit(self, event.globalPos())

    def _update_style(self):
        # kept for external callers (select-all / deselect-all); just repaint
        self.update()

    # ---- painting ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        radius = 18
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        p.setClipPath(path)

        # base
        p.fillRect(0, 0, w, h, QColor(40, 40, 45))

        if self._src_pix is not None:
            scaled = self._src_pix.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            sx = max(0, (scaled.width() - w) // 2)
            sy = max(0, (scaled.height() - h) // 2)
            p.drawPixmap(0, 0, scaled, sx, sy, w, h)
        else:
            p.setPen(QColor(150, 150, 156))
            f = p.font(); f.setPointSize(10); p.setFont(f)
            txt = "…" if self._loading else ("VIDEO" if self.media_type == "video" else "?")
            p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, txt)

        # subtle top sheen for depth
        sheen = QColor(255, 255, 255, 16)
        p.fillRect(0, 0, w, int(h * 0.4), sheen)

        p.setClipping(False)

        # hover highlight
        if self._hover and not self.is_selected:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 22))
            p.drawPath(path)

        # video badge
        if self.media_type == "video":
            bx, by, bw, bh = 8, h - 30, 30, 22
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRoundedRect(bx, by, bw, bh, 8, 8)
            tri = QPainterPath()
            tri.moveTo(bx + 11, by + 6)
            tri.lineTo(bx + 11, by + 16)
            tri.lineTo(bx + 21, by + 11)
            tri.closeSubpath()
            p.fillPath(tri, QColor("#ffffff"))

        # selection ring + checkmark (Apple Photos look)
        if self.is_selected:
            pen = QPen(QColor(config.COLOR_ACCENT))
            pen.setWidth(4)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(2, 2, w - 4, h - 4), radius - 2, radius - 2)
            cd = 26
            cx = w - cd - 9
            cy = 9
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(config.COLOR_ACCENT))
            p.drawEllipse(cx, cy, cd, cd)
            check = QPen(QColor("#ffffff"))
            check.setWidth(3)
            check.setCapStyle(Qt.RoundCap)
            check.setJoinStyle(Qt.RoundJoin)
            p.setPen(check)
            p.drawLine(QPointF(cx + 7, cy + 13), QPointF(cx + 11, cy + 18))
            p.drawLine(QPointF(cx + 11, cy + 18), QPointF(cx + 19, cy + 8))

        # favorite heart (top-left)
        if self.is_favorite:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 120))
            p.drawEllipse(8, 8, 26, 26)
            p.setPen(QColor(config.COLOR_DANGER))
            hf = p.font()
            hf.setPointSize(12)
            p.setFont(hf)
            p.drawText(QRectF(8, 8, 26, 26), Qt.AlignCenter, "♥")

        p.end()


# ---------------------------------------------------------------------------
# Password dialog (proper QDialog so Enter works reliably)
# ---------------------------------------------------------------------------
class PasswordDialog(QDialog):
    def __init__(self, setup_mode: bool = False, parent=None):
        super().__init__(parent)
        self.setup_mode = setup_mode
        self.setWindowTitle("Mood – Passwort" if not setup_mode else "Mood – Passwort festlegen")
        self.setStyleSheet(STYLE)
        self.setModal(True)
        self.setMinimumWidth(320)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Passwort festlegen:" if setup_mode else "Passwort:"))
        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.Password)
        self.edit.setPlaceholderText("Neues Passwort (min. 4 Zeichen)" if setup_mode else "Passwort eingeben…")
        lay.addWidget(self.edit)
        if setup_mode:
            lay.addWidget(QLabel("Wird zum Verschlüsseln deiner Dateien benutzt."))

        btns = QHBoxLayout()
        ok = QPushButton("OK")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        lay.addLayout(btns)

        self.edit.returnPressed.connect(self.accept)
        self.edit.setFocus()

    def password(self) -> str:
        return self.edit.text()


# ---------------------------------------------------------------------------
# Mood / Slideshow window
# ---------------------------------------------------------------------------

class CountdownRing(QWidget):
    """Circular countdown indicator for Mood mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self._total = 1
        self._left = 0
        self._text = ""
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_countdown(self, left: int, total: int):
        self._left = max(0, int(left))
        self._total = max(1, int(total))
        self._text = str(self._left) if self._left > 0 else ""
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(5, 5, -5, -5)
        # dark disc
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 180))
        p.drawEllipse(self.rect().adjusted(2, 2, -2, -2))
        # track ring
        track = QPen(QColor(255, 255, 255, 40))
        track.setWidth(5)
        track.setCapStyle(Qt.RoundCap)
        p.setPen(track)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(rect)
        # progress arc
        frac = self._left / float(self._total) if self._total else 0.0
        arc = QPen(QColor(config.COLOR_ACCENT))
        arc.setWidth(5)
        arc.setCapStyle(Qt.RoundCap)
        p.setPen(arc)
        span = int(-360 * 16 * max(0.0, min(1.0, frac)))
        if span != 0:
            p.drawArc(rect, 90 * 16, span)
        # number
        p.setPen(QColor("#ffffff"))
        font = p.font()
        font.setBold(True)
        font.setPointSize(13)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, self._text)
        p.end()

class MoodWindow(QWidget):
    closed = Signal()

    def __init__(self, media_list: List[Path], countdown_max: int = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mood Mode")
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        # --- ALL attributes MUST be set BEFORE any show() / resize ---
        self.media_list = media_list[:] if media_list else []
        self.pane_count = 1
        self.random_mode = True
        if countdown_max is None:
            countdown_max = int(load_settings().get("default_countdown", config.DEFAULT_COUNTDOWN_MAX) or 0)
        self.countdown_max = int(countdown_max or 0)
        self.countdown_enabled = self.countdown_max > 0
        self.current_indices: List[int] = []
        self.used_indices: Set[int] = set()
        self.players: List[QMediaPlayer] = []
        self.audio_outputs: List[QAudioOutput] = []
        self.video_widgets: List[QVideoWidget] = []
        self.image_labels: List[QLabel] = []
        self.countdown_left = 0
        self.session_switches = 0
        self.settings = load_settings()
        self.blackout = False
        self.play_counts: Dict[str, int] = {}
        self.last_shown_at: Dict[str, float] = {}
        self._lock_timer = QTimer(self)
        self._lock_timer.timeout.connect(self._auto_lock)
        mins = int(self.settings.get("auto_lock_minutes", 15) or 0)
        if mins > 0:
            self._lock_timer.start(mins * 60 * 1000)
        self.session_id = None
        self._ready = False

        self._build_ui()
        self._setup_shortcuts()
        self._rebuild_panes()          # create the first pane widgets
        self._ready = True

        # show AFTER everything is initialized, with a gentle fade-in
        self.setWindowOpacity(0.0)
        self.showFullScreen()
        self._show_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._show_anim.setDuration(260)
        self._show_anim.setStartValue(0.0)
        self._show_anim.setEndValue(1.0)
        self._show_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._show_anim.start()

        # start first slide a tiny bit later so the window has real size
        QTimer.singleShot(80, self._next_slide)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Stack so we can float the countdown on top
        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.setSpacing(0)

        self.content = QWidget()
        self.content.setStyleSheet("background: black;")
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)
        self.stack_layout.addWidget(self.content)

        self.main_layout.addWidget(self.stack, stretch=1)

        # Floating countdown ring (top-right)
        self.countdown_ring = CountdownRing(self)
        self.countdown_ring.hide()
        self.countdown_label = self.countdown_ring  # alias for old call sites
        self.countdown_total_current = 1

        # thin info bar (optional, can be toggled with H)
        self.overlay = QFrame()
        self.overlay.setFixedHeight(28)
        self.overlay.setStyleSheet("background: rgba(0,0,0,160);")
        ov_layout = QHBoxLayout(self.overlay)
        ov_layout.setContentsMargins(10, 0, 10, 0)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #aaa; font-size: 11px;")
        ov_layout.addWidget(self.info_label)
        ov_layout.addStretch()
        self.main_layout.addWidget(self.overlay)
        self.overlay.hide()

    def _setup_shortcuts(self):
        # Space handled in keyPressEvent (respects blackout)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)
        QShortcut(QKeySequence("1"), self, lambda: self._set_panes(1))
        QShortcut(QKeySequence("2"), self, lambda: self._set_panes(2))
        QShortcut(QKeySequence("3"), self, lambda: self._set_panes(3))
        QShortcut(QKeySequence("4"), self, lambda: self._set_panes(4))
        QShortcut(QKeySequence("R"), self, self._toggle_random)
        QShortcut(QKeySequence("C"), self, self._toggle_countdown)
        QShortcut(QKeySequence("H"), self, self._toggle_overlay)

    def _set_panes(self, n: int):
        if n == self.pane_count or not self._ready:
            return
        self.pane_count = n
        self._rebuild_panes()
        self._next_slide()

    def _toggle_random(self):
        self.random_mode = not self.random_mode
        self._show_temp_info(f"Mode: {'Random' if self.random_mode else 'Sequential'}")

    def _toggle_countdown(self):
        self.countdown_enabled = not self.countdown_enabled
        self._show_temp_info(f"Countdown: {'ON' if self.countdown_enabled else 'OFF'}")
        if not self.countdown_enabled and hasattr(self, "countdown_ring"):
            self.countdown_ring.hide()

    def _toggle_overlay(self):
        self.overlay.setVisible(not self.overlay.isVisible())

    def _show_temp_info(self, text: str):
        self.info_label.setText(text)
        self.overlay.show()
        QTimer.singleShot(2000, lambda: self.overlay.hide() if self.overlay and not self.overlay.isHidden() else None)

    def _rebuild_panes(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for p in self.players:
            try:
                p.stop()
            except Exception:
                pass
        self.players.clear()
        self.audio_outputs.clear()
        self.video_widgets.clear()
        self.image_labels.clear()
        # one reusable opacity effect + animation per pane (no per-slide leak)
        self.image_effects: List[QGraphicsOpacityEffect] = []
        self.image_anims: List[QPropertyAnimation] = []

        for i in range(self.pane_count):
            container = QWidget()
            container.setStyleSheet("background: #000;")
            lay = QVBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)

            img = QLabel()
            img.setAlignment(Qt.AlignCenter)
            img.setStyleSheet("background: #000;")
            img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            img.setMinimumSize(1, 1)
            lay.addWidget(img, stretch=1)
            self.image_labels.append(img)

            # fade effect for smooth slide transitions
            eff = QGraphicsOpacityEffect(img)
            eff.setOpacity(1.0)
            img.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", img)
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            self.image_effects.append(eff)
            self.image_anims.append(anim)

            vw = QVideoWidget()
            vw.setStyleSheet("background: #000;")
            vw.hide()
            lay.addWidget(vw, stretch=1)
            self.video_widgets.append(vw)

            player = QMediaPlayer()
            audio = QAudioOutput()
            player.setAudioOutput(audio)
            player.setVideoOutput(vw)
            self.players.append(player)
            self.audio_outputs.append(audio)

            self.content_layout.addWidget(container, stretch=1)

    def _pick_indices(self) -> List[int]:
        n = len(self.media_list)
        if n == 0:
            return []

        if self.random_mode:
            import random
            import time as _time
            # refresh settings (cooldown / smart-mix may change)
            try:
                self.settings = load_settings()
            except Exception:
                pass
            cooldown = float(self.settings.get("repeat_cooldown_sec", 30) or 0)
            now = _time.time()

            def _cooled(i):
                if cooldown <= 0:
                    return True
                key = str(self.media_list[i])
                last = self.last_shown_at.get(key, 0)
                return (now - last) >= cooldown

            current_idx = set(self.current_indices or [])
            current_paths = {str(self.media_list[i]) for i in current_idx if 0 <= i < n}

            def _not_on_screen(i):
                return str(self.media_list[i]) not in current_paths

            # 1) not recently used in this cycle + cooled + not currently on screen
            available = [
                i for i in range(n)
                if i not in self.used_indices and _not_on_screen(i) and _cooled(i)
            ]
            # 2) drop used_indices, still respect cooldown + not current path
            if len(available) < self.pane_count:
                self.used_indices.clear()
                available = [
                    i for i in range(n)
                    if _not_on_screen(i) and _cooled(i)
                ]
            # 3) drop cooldown, still avoid currently displayed paths if possible
            if len(available) < self.pane_count:
                available = [i for i in range(n) if _not_on_screen(i)]
            # 4) absolute last resort
            if len(available) < self.pane_count:
                available = list(range(n))

            k = min(self.pane_count, len(available))
            if self.settings.get("smart_mix", True) and available:
                # prefer least-recently-shown + low play_count
                weights = []
                for i in available:
                    key = str(self.media_list[i])
                    c = self.play_counts.get(key, 0)
                    age = now - self.last_shown_at.get(key, 0)
                    # older / never shown → higher weight
                    weights.append((1.0 / (1.0 + c)) * (1.0 + min(age, 600) / 30.0))
                chosen = []
                pool = list(available)
                wpool = list(weights)
                for _ in range(k):
                    if not pool:
                        break
                    total = sum(wpool) or 1.0
                    r = random.random() * total
                    acc = 0.0
                    pick = 0
                    for j, w in enumerate(wpool):
                        acc += w
                        if acc >= r:
                            pick = j
                            break
                    chosen.append(pool.pop(pick))
                    wpool.pop(pick)
            else:
                chosen = random.sample(available, k)

            self.used_indices.update(chosen)
            # if we exhausted the pool, reset cycle so others come next
            if len(self.used_indices) >= n:
                self.used_indices = set(chosen)
            return chosen
        else:
            if not self.current_indices:
                start = 0
            else:
                start = (max(self.current_indices) + 1) % n
            return [(start + i) % n for i in range(self.pane_count)]

    def _position_countdown(self):
        """Keep the countdown ring in the top-right corner."""
        w = getattr(self, "countdown_ring", None) or getattr(self, "countdown_label", None)
        if w is None:
            return
        margin = 18
        x = self.width() - w.width() - margin
        y = margin
        w.move(max(0, x), y)
        w.raise_()

    def _next_slide(self):
        if not self._ready or not self.media_list:
            return
        self.session_switches += 1
        indices = self._pick_indices()
        self.current_indices = indices
        for idx in indices:
            key = str(self.media_list[idx])
            self.play_counts[key] = self.play_counts.get(key, 0) + 1

        for i, idx in enumerate(indices):
            if i >= len(self.image_labels):
                break
            path = self.media_list[idx]
            self._show_in_pane(i, path)

        import time as _time
        for idx in indices:
            key = str(self.media_list[idx])
            self.last_shown_at[key] = _time.time()

        if self.countdown_enabled and self.countdown_max > 0:
            import random
            self.countdown_left = random.randint(1, max(1, self.countdown_max))
            self.countdown_total_current = self.countdown_left
            if hasattr(self, "countdown_ring"):
                self.countdown_ring.set_countdown(self.countdown_left, self.countdown_total_current)
                self.countdown_ring.show()
                self._position_countdown()
                self.countdown_ring.raise_()
        else:
            self.countdown_left = 0
            if hasattr(self, "countdown_ring"):
                self.countdown_ring.hide()

    def _fade_pane_in(self, pane_idx: int):
        """Restart the pane's opacity animation for a smooth slide transition."""
        if pane_idx >= len(getattr(self, "image_anims", [])):
            return
        anim = self.image_anims[pane_idx]
        try:
            anim.stop()
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()
        except Exception:
            # never let a cosmetic animation break playback
            try:
                self.image_effects[pane_idx].setOpacity(1.0)
            except Exception:
                pass

    def _show_in_pane(self, pane_idx: int, path: Path, animate: bool = True):
        if pane_idx >= len(self.image_labels):
            return
        img_label = self.image_labels[pane_idx]
        vw = self.video_widgets[pane_idx]
        player = self.players[pane_idx]

        try:
            player.stop()
        except Exception:
            pass
        vw.hide()
        img_label.show()
        img_label.setText("")

        ext = path.suffix.lower()
        if ext in config.SUPPORTED_VIDEO_EXT:
            img_label.hide()
            vw.show()
            player.setSource(QUrl.fromLocalFile(str(path)))
            player.setLoops(QMediaPlayer.Loops.Infinite)
            player.play()
            if self.settings.get("video_random_start", True):
                def _seek():
                    try:
                        dur = player.duration()
                        if dur and dur > 3000:
                            # start somewhere in first 70%
                            pos = random.randint(0, int(dur * 0.7))
                            player.setPosition(pos)
                    except Exception:
                        pass
                QTimer.singleShot(200, _seek)
        else:
            pix = QPixmap(str(path))
            if pix.isNull():
                img_label.setText(path.name)
                return

            target = img_label.size()
            if target.width() < 20 or target.height() < 20:
                target = self.size()
                if self.pane_count > 1:
                    target.setWidth(max(1, target.width() // self.pane_count))

            if self.pane_count <= 2:
                # 1 and 2 panes: show whole image (no heavy crop)
                scaled = pix.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled)
            else:
                # 3 / 4 panes: fill cell (cover + center crop)
                scaled = pix.scaled(target, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x = max(0, (scaled.width() - target.width()) // 2)
                y = max(0, (scaled.height() - target.height()) // 2)
                cropped = scaled.copy(x, y, target.width(), target.height())
                img_label.setPixmap(cropped)

            # smooth fade for genuine slide changes (not on resize re-scale)
            if animate:
                self._fade_pane_in(pane_idx)

        # always keep ring above video widgets
        if hasattr(self, "countdown_ring") and self.countdown_enabled and self.countdown_left > 0:
            self.countdown_ring.show()
            self._position_countdown()
            self.countdown_ring.raise_()

    def _tick(self):
        if not self._ready:
            return
        if self.countdown_enabled and self.countdown_left > 0:
            self.countdown_left -= 1
            if hasattr(self, "countdown_ring"):
                self.countdown_ring.set_countdown(
                    self.countdown_left, getattr(self, "countdown_total_current", 1)
                )
                self.countdown_ring.raise_()
            if self.countdown_left > 0:
                self._position_countdown()
            else:
                if hasattr(self, "countdown_ring"):
                    self.countdown_ring.hide()
                self._next_slide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_countdown()
        if not getattr(self, "_ready", False):
            return
        if not self.current_indices or not self.image_labels:
            return
        for i, idx in enumerate(self.current_indices):
            if i < len(self.image_labels) and self.image_labels[i].isVisible():
                path = self.media_list[idx]
                if path.suffix.lower() not in config.SUPPORTED_VIDEO_EXT:
                    self._show_in_pane(i, path, animate=False)



    def _toggle_blackout(self):
        self.blackout = not self.blackout
        if not hasattr(self, "blackout_layer"):
            self.blackout_layer = QLabel(self)
            self.blackout_layer.setStyleSheet("background: #000;")
            self.blackout_layer.setGeometry(self.rect())
            self.blackout_layer.hide()
        if self.blackout:
            self.blackout_layer.setGeometry(self.rect())
            self.blackout_layer.show()
            self.blackout_layer.raise_()
            if hasattr(self, "countdown_ring"):
                self.countdown_ring.hide()
        else:
            self.blackout_layer.hide()
            if self.countdown_enabled and self.countdown_left > 0 and hasattr(self, "countdown_ring"):
                self.countdown_ring.show()
                self._position_countdown()

    def _panic(self):
        # close entire app immediately
        try:
            self.close()
        except Exception:
            pass
        QApplication.quit()

    def _auto_lock(self):
        log.info("Auto-lock triggered")
        self.close()

    def _reset_lock_timer(self):
        mins = int(self.settings.get("auto_lock_minutes", 15) or 0)
        if mins > 0 and hasattr(self, "_lock_timer"):
            self._lock_timer.start(mins * 60 * 1000)


    def closeEvent(self, event):
        if getattr(self, "players", None):
            for p in self.players:
                try:
                    p.stop()
                except Exception:
                    pass
        self.closed.emit()
        super().closeEvent(event)

    def mouseMoveEvent(self, event):
        self._reset_lock_timer()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self._reset_lock_timer()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._reset_lock_timer()
        key = event.key()
        text = (event.text() or "").upper()
        settings = getattr(self, "settings", {}) or {}

        blackout_k = str(settings.get("blackout_key", "B")).upper().strip()
        panic_raw = str(settings.get("panic_key", "Pause")).strip()
        panic_k = panic_raw.upper()

        # named special keys
        special = {
            "PAUSE": Qt.Key_Pause,
            "ESC": Qt.Key_Escape,
            "ESCAPE": Qt.Key_Escape,
            "SPACE": Qt.Key_Space,
            "TAB": Qt.Key_Tab,
            "ENTER": Qt.Key_Return,
            "RETURN": Qt.Key_Return,
        }

        if key == Qt.Key_Space:
            if not self.blackout:
                self._next_slide()
            return
        if key == Qt.Key_Escape:
            # Escape always closes unless set as something else intentionally
            self.close()
            return

        # panic: letter (X) or named key (Pause)
        is_panic = False
        if panic_k in special and key == special[panic_k]:
            is_panic = True
        elif len(panic_k) == 1 and text == panic_k:
            is_panic = True
        if is_panic:
            self._panic()
            return

        # blackout: letter
        is_bo = False
        if len(blackout_k) == 1 and text == blackout_k:
            is_bo = True
        elif blackout_k in special and key == special[blackout_k]:
            is_bo = True
        if is_bo:
            self._toggle_blackout()
            return

        super().keyPressEvent(event)



# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME}  v{config.APP_VERSION}")
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self.resize(1480, 900)

        # Ensure folders exist
        for p in (config.APP_ROOT, config.MEDIA_ROOT, config.ARCHIVE_ROOT,
                  config.THUMB_CACHE, config.TEMP_IMPORT):
            p.mkdir(parents=True, exist_ok=True)

        self.db = Database()
        self.pending_files: List[Dict] = []   # {path, original, type, selected}
        self._browse_all_files: List[Dict] = []
        self._browse_filter: str = "all"
        self.mood_window: Optional[MoodWindow] = None
        self.current_session_id: Optional[int] = None
        self._auto_assign_after_convert: Optional[int] = None
        self._console_visible = False
        self._viewing_favorites = False
        self.tile_size = max(120, min(300, int(load_settings().get("tile_size", 184) or 184)))
        self._tile_apply_timer = QTimer(self)
        self._tile_apply_timer.setSingleShot(True)
        self._tile_apply_timer.timeout.connect(self._apply_tile_size)

        log.info("MainWindow init")
        self._build_ui()
        self._apply_style()
        self._load_performers()
        self._setup_shortcuts()
        log.info(f"Performers loaded: {self.performer_list.count()}")

    def _apply_style(self):
        self.setStyleSheet(STYLE)

    def _menu_button(self, text: str, actions, primary: bool = False) -> QToolButton:
        """Create a toolbar QToolButton with a popup menu (Apple-style)."""
        btn = QToolButton()
        btn.setText(text)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setCursor(Qt.PointingHandCursor)
        if primary:
            btn.setObjectName("primary")
        menu = QMenu(btn)
        menu.setStyleSheet(STYLE)
        for label, slot in actions:
            if label == "-":
                menu.addSeparator()
            else:
                menu.addAction(label, slot)
        btn.setMenu(menu)
        return btn

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, stretch=1)

        # ================= SIDEBAR =================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setAttribute(Qt.WA_StyledBackground, True)
        sidebar.setFixedWidth(236)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(16, 20, 14, 16)
        sb.setSpacing(12)

        wordmark = QLabel("Mood")
        wordmark.setObjectName("wordmark")
        sb.addWidget(wordmark)

        self.btn_favorites = QPushButton("♥   Favoriten")
        self.btn_favorites.setObjectName("sidebarLink")
        self.btn_favorites.setCursor(Qt.PointingHandCursor)
        self.btn_favorites.clicked.connect(self._show_favorites)
        sb.addWidget(self.btn_favorites)

        lib_label = QLabel("BIBLIOTHEK")
        lib_label.setObjectName("sectionHeader")
        sb.addWidget(lib_label)

        self.performer_list = QListWidget()
        self.performer_list.setObjectName("sidebarList")
        self.performer_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.performer_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.performer_list.setDefaultDropAction(Qt.MoveAction)
        self.performer_list.setDragEnabled(True)
        self.performer_list.setAcceptDrops(True)
        self.performer_list.setDropIndicatorShown(True)
        self.performer_list.setFrameShape(QFrame.NoFrame)
        self.performer_list.itemClicked.connect(self._on_performer_clicked)
        self.performer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.performer_list.customContextMenuRequested.connect(self._performer_context_menu)
        self.performer_list.model().rowsMoved.connect(self._on_performers_reordered)
        sb.addWidget(self.performer_list, stretch=1)

        self.btn_add_perf = QPushButton("＋   Darsteller")
        self.btn_add_perf.setObjectName("primary")
        self.btn_add_perf.setCursor(Qt.PointingHandCursor)
        self.btn_add_perf.clicked.connect(self._add_performer)
        sb.addWidget(self.btn_add_perf)

        body.addWidget(sidebar)

        # ================= MAIN =================
        main = QWidget()
        main.setObjectName("main")
        main_lay = QVBoxLayout(main)
        main_lay.setContentsMargins(22, 16, 22, 10)
        main_lay.setSpacing(14)

        # ---- toolbar ----
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        self.header_title = QLabel("Bibliothek")
        self.header_title.setObjectName("headerTitle")
        self.header_sub = QLabel("Wähle links einen Darsteller")
        self.header_sub.setObjectName("headerSub")
        title_block.addWidget(self.header_title)
        title_block.addWidget(self.header_sub)
        toolbar.addLayout(title_block)
        toolbar.addStretch()

        # segmented filter (hidden until browsing a library)
        self.browse_filter_frame = QFrame()
        self.browse_filter_frame.setObjectName("segmented")
        self.browse_filter_frame.setAttribute(Qt.WA_StyledBackground, True)
        bf = QHBoxLayout(self.browse_filter_frame)
        bf.setContentsMargins(3, 3, 3, 3)
        bf.setSpacing(2)
        self.btn_filter_all = QPushButton("Alle")
        self.btn_filter_img = QPushButton("Fotos")
        self.btn_filter_vid = QPushButton("Videos")
        for b in (self.btn_filter_all, self.btn_filter_img, self.btn_filter_vid):
            b.setCheckable(True)
            b.setObjectName("segBtn")
            b.setCursor(Qt.PointingHandCursor)
            bf.addWidget(b)
        self.btn_filter_all.setChecked(True)
        self.btn_filter_all.clicked.connect(lambda: self._set_browse_filter("all"))
        self.btn_filter_img.clicked.connect(lambda: self._set_browse_filter("image"))
        self.btn_filter_vid.clicked.connect(lambda: self._set_browse_filter("video"))
        toolbar.addWidget(self.browse_filter_frame)
        self.browse_filter_frame.hide()

        # import menu button
        self.btn_import = self._menu_button("Importieren  ▾", [
            ("Dateien…", self._import_files),
            ("Ordner…", self._import_folder),
            ("-", None),
            ("Ordner als Darsteller…", self._import_folder_as_performer),
        ])
        toolbar.addWidget(self.btn_import)
        # kept as a live (hidden) object so enable/disable code still works
        self.btn_import_folder = QPushButton()
        self.btn_import_folder.hide()

        # primary Mood menu button
        self.btn_mood = self._menu_button("▶   Mood  ▾", [
            ("Ausgewählter Darsteller", lambda: self._start_mood()),
            ("Alle Darsteller", lambda: self._start_mood(all_media=True)),
            ("Mehrere wählen…", lambda: self._start_mood(select_performers=True)),
        ], primary=True)
        toolbar.addWidget(self.btn_mood)

        # overflow menu
        self.btn_more = self._menu_button("•••", [
            ("Einstellungen…", self._open_settings),
            ("Top Darsteller", self._show_top),
            ("-", None),
            ("Export ZIP…", self._export_all),
            ("Datenbank bereinigen", lambda: self._cleanup_db()),
        ])
        toolbar.addWidget(self.btn_more)

        main_lay.addLayout(toolbar)

        # ---- progress ----
        self.progress = QProgressBar()
        self.progress.hide()
        main_lay.addWidget(self.progress)

        # ---- photo grid ----
        self.scroll = QScrollArea()
        self.scroll.setObjectName("gridScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.grid_host = QWidget()
        self.grid_host.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_host)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.grid_host)
        main_lay.addWidget(self.scroll, stretch=1)

        # ---- empty state ----
        self.drop_hint = QLabel("Ziehe Fotos & Videos hierher\noder nutze „Importieren“ oben rechts")
        self.drop_hint.setObjectName("dropHint")
        self.drop_hint.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self.drop_hint, stretch=1)

        # ---- contextual action bar (floating) ----
        self.assign_frame = QFrame()
        self.assign_frame.setObjectName("actionBar")
        self.assign_frame.setAttribute(Qt.WA_StyledBackground, True)
        assign_bar = QHBoxLayout(self.assign_frame)
        assign_bar.setContentsMargins(16, 10, 12, 10)
        assign_bar.setSpacing(8)
        self.lbl_pending = QLabel("0 ausgewählt")
        self.lbl_pending.setObjectName("dim")
        assign_bar.addWidget(self.lbl_pending)
        assign_bar.addStretch()
        self.btn_select_all = QPushButton("Alle")
        self.btn_select_all.clicked.connect(self._select_all_pending)
        assign_bar.addWidget(self.btn_select_all)
        self.btn_deselect_all = QPushButton("Keine")
        self.btn_deselect_all.clicked.connect(self._deselect_all_pending)
        assign_bar.addWidget(self.btn_deselect_all)
        assign_bar.addSpacing(6)
        arrow = QLabel("→")
        arrow.setObjectName("dim")
        assign_bar.addWidget(arrow)
        self.combo_target = QComboBox()
        self.combo_target.setMinimumWidth(170)
        assign_bar.addWidget(self.combo_target)
        self.btn_assign = QPushButton("Zuordnen")
        self.btn_assign.setObjectName("primary")
        self.btn_assign.clicked.connect(self._assign_selected)
        assign_bar.addWidget(self.btn_assign)
        self.btn_clear_pending = QPushButton("Leeren")
        self.btn_clear_pending.setObjectName("danger")
        self.btn_clear_pending.clicked.connect(self._clear_pending)
        assign_bar.addWidget(self.btn_clear_pending)
        main_lay.addWidget(self.assign_frame)
        self.assign_frame.hide()

        body.addWidget(main, stretch=1)

        # ================= STATUS STRIP =================
        status = QFrame()
        status.setObjectName("statusBar")
        status.setAttribute(Qt.WA_StyledBackground, True)
        status.setFixedHeight(30)
        stl = QHBoxLayout(status)
        stl.setContentsMargins(20, 0, 20, 0)
        self.info_box = QLabel("Bereit.")
        self.info_box.setObjectName("statusText")
        stl.addWidget(self.info_box)
        stl.addStretch()
        zoom_lbl = QLabel("Größe")
        zoom_lbl.setObjectName("statusHint")
        stl.addWidget(zoom_lbl)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setObjectName("zoomSlider")
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.setRange(120, 300)
        self.zoom_slider.setValue(self.tile_size)
        self.zoom_slider.setToolTip("Kachelgröße")
        self.zoom_slider.valueChanged.connect(self._on_tile_slider)
        stl.addWidget(self.zoom_slider)
        root.addWidget(status)

        # hidden holder – content surfaced via Top-Darsteller popover / mood summary
        self.stats_box = QLabel()
        self.stats_box.hide()

        # drag & drop anywhere in the main area
        main.setAcceptDrops(True)
        main.dragEnterEvent = self._drag_enter
        main.dropEvent = self._drop

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+I"), self, self._import_files)
        QShortcut(QKeySequence("Ctrl+G"), self, self._start_mood)
        QShortcut(QKeySequence(Qt.Key_Delete), self, self._delete_selected_pending)
        QShortcut(QKeySequence(Qt.Key_Backspace), self, self._delete_selected_pending)
        QShortcut(QKeySequence(Qt.Key_F9), self, self._toggle_console)

    def _toggle_console(self):
        """F9: open mood.log in default editor / notepad."""
        log_path = config.APP_ROOT / "mood.log"
        if not log_path.exists():
            log_path.write_text("Log noch leer.\n", encoding="utf-8")
        try:
            import subprocess
            if sys.platform == "win32":
                os.startfile(str(log_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(log_path)])
            else:
                subprocess.Popen(["xdg-open", str(log_path)])
            self.info_box.setText(f"Log geöffnet:\n{log_path}")
        except Exception as e:
            # fallback: show last lines in a message box
            try:
                text = log_path.read_text(encoding="utf-8")[-4000:]
            except Exception:
                text = str(e)
            QMessageBox.information(self, "mood.log", text)

    # ------------------------------------------------------------------
    # Performers
    # ------------------------------------------------------------------
    def _on_performers_reordered(self, *args):
        # persist current visual order
        ids = []
        for i in range(self.performer_list.count()):
            it = self.performer_list.item(i)
            pid = it.data(Qt.UserRole)
            if pid is not None:
                ids.append(pid)
        if ids:
            self.db.reorder_performers(ids)
            log.info(f"Performer order saved ({len(ids)})")

    def _load_performers(self):

        self.performer_list.clear()
        self.combo_target.clear()
        performers = self.db.get_all_performers()
        for p in performers:
            fav = bool(p["is_favorite"])
            item = QListWidgetItem(("♥  " if fav else "") + p["name"])
            item.setData(Qt.UserRole, p["id"])
            self.performer_list.addItem(item)
            self.combo_target.addItem(p["name"], p["id"])

        self.info_box.setText(f"{len(performers)} Darsteller geladen.")

    def _add_performer(self):
        name, ok = QInputDialog.getText(self, "Neuer Darsteller", "Name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        fid = folder_id_for_name(name)
        folder = config.MEDIA_ROOT / fid
        folder.mkdir(parents=True, exist_ok=True)
        self.db.add_performer(name, fid)
        self._load_performers()
        self.info_box.setText(f"„{name}“ hinzugefügt.")

    def _import_folder_as_performer(self):
        """
        Pick a folder. Folder name → performer name.
        All media inside → convert → encrypt → assign to that performer.
        """
        folder = QFileDialog.getExistingDirectory(self, "Ordner als Darsteller importieren")
        if not folder:
            return
        src_folder = Path(folder)
        name = src_folder.name.strip()
        if not name:
            QMessageBox.warning(self, "Name", "Ordnername ungültig.")
            return

        paths = []
        for f in src_folder.rglob("*"):
            if f.is_file() and detect_media_type(f):
                paths.append(f)
        if not paths:
            QMessageBox.information(self, "Leer", "Keine unterstützten Dateien im Ordner.")
            return

        # ensure performer exists (opaque folder id)
        fid = folder_id_for_name(name)
        dest_folder = config.MEDIA_ROOT / fid
        dest_folder.mkdir(parents=True, exist_ok=True)
        pid = self.db.add_performer(name, fid)
        self._load_performers()
        log.info(f"Folder→Performer: {name} ({len(paths)} files)")

        # set combo to this performer so assign works after convert
        idx = self.combo_target.findData(pid)
        if idx >= 0:
            self.combo_target.setCurrentIndex(idx)

        self.info_box.setText(f"Importiere Ordner „{name}“…\n{len(paths)} Dateien")
        self._start_conversion(paths)
        # after convert, auto-assign everything to this performer
        self._auto_assign_after_convert = pid

    def _performer_context_menu(self, pos):
        item = self.performer_list.itemAt(pos)
        if item is None:
            return
        self.performer_list.setCurrentItem(item)
        pid = item.data(Qt.UserRole)
        perf = self.db.get_performer_by_id(pid)
        is_fav = bool(perf["is_favorite"]) if perf else False
        menu = QMenu(self)
        menu.setStyleSheet(STYLE)
        act_mood = menu.addAction("Mood starten")
        act_fav = menu.addAction("♥ Favorit entfernen" if is_fav else "♡ Als Favorit markieren")
        menu.addSeparator()
        act_del = menu.addAction("Darsteller löschen…")
        chosen = menu.exec(self.performer_list.mapToGlobal(pos))
        if chosen == act_mood:
            self._start_mood()
        elif chosen == act_fav:
            self.db.toggle_performer_favorite(pid)
            self._load_performers()
        elif chosen == act_del:
            self._delete_performer(item)

    def _delete_performer(self, item):
        pid = item.data(Qt.UserRole)
        perf = self.db.get_performer_by_id(pid)
        if not perf:
            return
        name = perf["name"]
        folder = config.MEDIA_ROOT / perf["folder_name"]
        n_files = 0
        if folder.exists():
            n_files = sum(1 for f in folder.iterdir() if f.is_file())

        reply = QMessageBox.question(
            self, "Darsteller löschen",
            f"„{name}“ wirklich löschen?\n\n"
            f"{n_files} Datei(en) auf der Festplatte werden mitgelöscht.\n"
            "Das kann nicht rückgängig gemacht werden.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        import shutil
        try:
            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)
                log.info(f"Deleted folder {folder}")
        except Exception as e:
            log.error(f"folder delete failed: {e}")

        self.db.delete_performer(pid)
        log.info(f"Deleted performer id={pid} name={name}")
        self.pending_files.clear()
        self._refresh_grid()
        self._load_performers()
        self.info_box.setText(f"„{name}“ gelöscht ({n_files} Dateien).")


    def _on_performer_clicked(self, item):
        pid = item.data(Qt.UserRole)
        media = self.db.get_media_for_performer(pid)
        perf = self.db.get_performer_by_id(pid)
        self.info_box.setText(f"{item.text()}\n{len(media)} Dateien")
        if not perf:
            return
        # Show this performer's files in the center grid (browse mode)
        self._browse_performer(perf, media)

    def _browse_performer(self, perf, media_rows):
        """Load performer's media into the center grid so user can view/delete."""
        self._viewing_favorites = False
        self.pending_files.clear()
        folder = config.MEDIA_ROOT / perf["folder_name"]
        for r in media_rows:
            p = folder / r["filename"]
            if p.exists():
                self.pending_files.append({
                    "path": p,
                    "original": r["original_name"] or r["filename"],
                    "type": r["media_type"],
                    "selected": False,
                    "media_id": r["id"],
                    "is_fav": bool(r["is_favorite"]),
                    "browse": True,
                })
        if folder.exists():
            known = {e["path"].name for e in self.pending_files}
            for f in folder.iterdir():
                if not f.is_file() or f.name in known:
                    continue
                # accept .mood/.goon or plain media
                is_enc = vault.is_encrypted_path(f)
                plain_name = f.name
                while plain_name.endswith(".mood") or plain_name.endswith(".goon"):
                    plain_name = plain_name[:-5]
                mtype = detect_media_type(Path(plain_name))
                if mtype or is_enc:
                    self.pending_files.append({
                        "path": f,
                        "original": plain_name,
                        "type": mtype or "image",
                        "selected": False,
                        "media_id": None,
                        "browse": True,
                    })
        self._browse_all_files = list(self.pending_files)
        self._browse_filter = "all"
        if hasattr(self, "btn_filter_all"):
            self.btn_filter_all.setChecked(True)
            self.btn_filter_img.setChecked(False)
            self.btn_filter_vid.setChecked(False)
            self.browse_filter_frame.show()
        self._apply_browse_filter()
        self._set_header(perf["name"], f"{len(self._browse_all_files)} Dateien · Doppelklick = Vollbild · Entf = löschen")
        self.info_box.setText(f"{perf['name']} · {len(self._browse_all_files)} Dateien")

    def _set_header(self, title: str, subtitle: str = ""):
        if hasattr(self, "header_title"):
            self.header_title.setText(title)
            self.header_sub.setText(subtitle)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def _drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event: QDropEvent):
        paths = []
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_file():
                paths.append(p)
            elif p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file() and detect_media_type(f):
                        paths.append(f)
        if paths:
            self._start_conversion(paths)
        event.acceptProposedAction()

    def _import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Dateien wählen",
            str(Path.home()),
            "Media (*.png *.jpg *.jpeg *.heic *.heif *.webp *.bmp *.mp4 *.mov *.avi *.mkv *.wmv *.m4v *.webm)"
        )
        if files:
            self._start_conversion([Path(f) for f in files])

    def _import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Ordner wählen")
        if folder:
            paths = []
            for f in Path(folder).rglob("*"):
                if f.is_file() and detect_media_type(f):
                    paths.append(f)
            if paths:
                self._start_conversion(paths)
            else:
                QMessageBox.information(self, "Leer", "Keine unterstützten Dateien gefunden.")

    def _start_conversion(self, files: List[Path]):
        if not files:
            return

        log.info(f"=== IMPORT START ({len(files)} files) ===")
        for f in files[:10]:
            log.info(f"  src: {f}")
        if len(files) > 10:
            log.info(f"  ... +{len(files)-10} more")

        # ALWAYS clear old pending so batches never mix
        if self.pending_files:
            log.info(f"Clearing {len(self.pending_files)} old pending files")
            self._clear_pending(silent=True)

        date_str = datetime.now().strftime(config.DATE_FORMAT)
        # unique subfolder per import so files never collide
        import time
        dest = config.TEMP_IMPORT / f"{date_str}_{int(time.time())}"
        dest.mkdir(parents=True, exist_ok=True)
        log.info(f"Temp dest: {dest}")

        self.progress.setMaximum(len(files))
        self.progress.setValue(0)
        self.progress.show()
        self.btn_import.setEnabled(False)
        self.btn_import_folder.setEnabled(False)
        self.drop_hint.hide()

        self.worker = ConvertWorker(files, dest, date_str)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_converted)
        self.worker.error.connect(lambda msg: self.info_box.setText(msg))
        self.worker.start()

    def _on_progress(self, current, total, name):
        self.progress.setValue(current)
        self.info_box.setText(f"Konvertiere {current}/{total}\n{name}")

    def _on_converted(self, results: list):
        self.progress.hide()
        self.btn_import.setEnabled(True)
        self.btn_import_folder.setEnabled(True)

        self.pending_files.clear()   # hard reset, no mixing
        self._browse_all_files = []
        if hasattr(self, "browse_filter_frame"):
            self.browse_filter_frame.hide()
        added = 0
        for new_path, original, mtype in results:
            self.pending_files.append({
                "path": new_path,
                "original": original,
                "type": mtype,
                "selected": False
            })
            added += 1
            log.debug(f"pending + {new_path}")

        log.info(f"Pending now has {added} files")
        self._refresh_grid()
        self._set_header("Neue Dateien", "Auswählen und einem Darsteller zuordnen")
        self.info_box.setText(f"{added} Dateien bereit zum Zuordnen.")

        # auto-assign if we came from "Ordner → Darsteller"
        if self._auto_assign_after_convert and added > 0:
            pid = self._auto_assign_after_convert
            self._auto_assign_after_convert = None
            idx = self.combo_target.findData(pid)
            if idx >= 0:
                self.combo_target.setCurrentIndex(idx)
            # select all + assign
            for e in self.pending_files:
                e["selected"] = True
            log.info(f"Auto-assign to performer id={pid}")
            self._assign_selected()


    def _set_browse_filter(self, mode: str):
        self._browse_filter = mode
        if hasattr(self, "btn_filter_all"):
            self.btn_filter_all.setChecked(mode == "all")
            self.btn_filter_img.setChecked(mode == "image")
            self.btn_filter_vid.setChecked(mode == "video")
        self._apply_browse_filter()

    def _apply_browse_filter(self):
        if not self._browse_all_files:
            return
        mode = self._browse_filter
        if mode == "all":
            self.pending_files = list(self._browse_all_files)
        else:
            self.pending_files = [e for e in self._browse_all_files if e.get("type") == mode]
        self._refresh_grid()
        self.info_box.setText(
            f"Filter: {mode} — {len(self.pending_files)} / {len(self._browse_all_files)} Dateien"
        )

    # ------------------------------------------------------------------
    # Tile zoom + context menu + favorites
    # ------------------------------------------------------------------
    def _on_tile_slider(self, val: int):
        self.tile_size = int(val)
        self._tile_apply_timer.start(120)      # debounce rebuilds

    def _apply_tile_size(self):
        if self.pending_files:
            self._refresh_grid()
        try:
            data = load_settings()
            data["tile_size"] = self.tile_size
            save_settings(data)
        except Exception:
            pass

    def _thumb_context_menu(self, thumb: "ThumbItem", global_pos):
        menu = QMenu(self)
        menu.setStyleSheet(STYLE)
        act_full = menu.addAction("Vollbild")
        act_fav = None
        if thumb.media_id:
            act_fav = menu.addAction("♥ Favorit entfernen" if thumb.is_favorite else "♡ Als Favorit")
        menu.addSeparator()
        act_del = menu.addAction("Löschen…")
        chosen = menu.exec(global_pos)
        if chosen is None:
            return
        if chosen == act_full:
            self._preview_media(thumb)
        elif act_fav is not None and chosen == act_fav:
            newval = self.db.toggle_media_favorite(thumb.media_id)
            thumb.is_favorite = newval
            thumb.update()
            for coll in (self.pending_files, self._browse_all_files):
                for e in coll:
                    if e.get("media_id") == thumb.media_id:
                        e["is_fav"] = newval
            self.info_box.setText("Zu Favoriten hinzugefügt." if newval else "Aus Favoriten entfernt.")
        elif chosen == act_del:
            for e in self.pending_files:
                e["selected"] = (e["path"] == thumb.path)
            self._delete_selected_pending()

    def _show_favorites(self):
        """Show every favorite photo/video across all performers."""
        self._viewing_favorites = True
        self.performer_list.clearSelection()
        rows = self.db.get_all_favorite_media()
        self.pending_files = []
        for r in rows:
            folder = config.MEDIA_ROOT / r["folder_name"]
            p = folder / r["filename"]
            if p.exists():
                self.pending_files.append({
                    "path": p,
                    "original": r["original_name"] or r["filename"],
                    "type": r["media_type"],
                    "selected": False,
                    "media_id": r["id"],
                    "is_fav": True,
                    "browse": True,
                })
        self._browse_all_files = list(self.pending_files)
        self._browse_filter = "all"
        if hasattr(self, "btn_filter_all"):
            self.btn_filter_all.setChecked(True)
            self.btn_filter_img.setChecked(False)
            self.btn_filter_vid.setChecked(False)
            self.browse_filter_frame.show()
        self._refresh_grid()
        n = len(self.pending_files)
        self._set_header("♥ Favoriten", f"{n} markierte Datei(en)" if n else "Noch keine Favoriten – Rechtsklick auf ein Foto → „Als Favorit“")
        self.info_box.setText(f"Favoriten · {n} Dateien")

    def _preview_media(self, thumb: "ThumbItem"):
        path = thumb.path
        display = vault.resolve_for_display(path) if vault.is_unlocked else path
        if display is None or not Path(display).exists():
            QMessageBox.warning(self, "Vorschau", "Datei konnte nicht geöffnet werden.")
            return
        display = Path(display)
        dlg = QDialog(self)
        dlg.setWindowTitle(display.name)
        dlg.setStyleSheet(STYLE + " QDialog { background: #000; }")
        dlg.resize(1200, 800)
        dlg.setWindowState(dlg.windowState() | Qt.WindowMaximized)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(0, 0, 0, 0)
        ext = display.suffix.lower()
        if ext in config.SUPPORTED_VIDEO_EXT:
            vw = QVideoWidget()
            player = QMediaPlayer(dlg)
            audio = QAudioOutput(dlg)
            player.setAudioOutput(audio)
            player.setVideoOutput(vw)
            player.setSource(QUrl.fromLocalFile(str(display)))
            player.setLoops(QMediaPlayer.Loops.Infinite)
            lay.addWidget(vw)
            player.play()
            dlg.finished.connect(lambda *_: player.stop())
        else:
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background:#000;")
            pix = QPixmap(str(display))
            lay.addWidget(lbl)

            class _FitLabel(QLabel):
                pass
            # scale on show
            def _fit(*_):
                if pix.isNull():
                    lbl.setText(display.name)
                    return
                sz = lbl.size()
                if sz.width() < 10 or sz.height() < 10:
                    sz = dlg.size()
                lbl.setPixmap(pix.scaled(sz, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            dlg.showEvent = lambda e: (QDialog.showEvent(dlg, e), QTimer.singleShot(30, _fit))
            QTimer.singleShot(80, _fit)
        QShortcut(QKeySequence(Qt.Key_Escape), dlg, dlg.reject)
        dlg.exec()

    def _refresh_grid(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.pending_files:
            self.scroll.hide()
            self.drop_hint.show()
            self.lbl_pending.setText("0 ausgewählt")
            self.assign_frame.hide()
            return

        self.drop_hint.hide()
        self.scroll.show()
        cols = self._grid_columns()
        self._grid_cols = cols
        for i, entry in enumerate(self.pending_files):
            thumb = ThumbItem(
                entry["path"], entry["type"],
                size=self.tile_size,
                media_id=entry.get("media_id"),
                favorite=bool(entry.get("is_fav")),
            )
            thumb.is_selected = bool(entry.get("selected"))
            thumb.selected_changed.connect(self._on_thumb_selected)
            thumb.double_clicked.connect(self._preview_media)
            thumb.context_requested.connect(self._thumb_context_menu)
            row, col = divmod(i, cols)
            self.grid_layout.addWidget(thumb, row, col)

        self._update_selection_count()
        self.assign_frame.show()

    def _grid_columns(self) -> int:
        vw = self.scroll.viewport().width()
        if vw < self.tile_size:                  # not laid out yet → estimate
            vw = self.width() - 236 - 44
        return max(1, vw // (self.tile_size + self.grid_layout.spacing()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_grid()

    def _reflow_grid(self):
        """Re-flow the tiles when the number of columns changes (Photos-style)."""
        if not hasattr(self, "grid_layout") or self.grid_layout.count() == 0:
            return
        cols = self._grid_columns()
        if cols == getattr(self, "_grid_cols", None):
            return
        self._grid_cols = cols
        widgets = []
        while self.grid_layout.count():
            it = self.grid_layout.takeAt(0)
            w = it.widget()
            if w is not None:
                widgets.append(w)
        for i, w in enumerate(widgets):
            r, c = divmod(i, cols)
            self.grid_layout.addWidget(w, r, c)

    def _update_selection_count(self):
        sel = sum(1 for e in self.pending_files if e.get("selected"))
        total = len(self.pending_files)
        if sel:
            self.lbl_pending.setText(f"{sel} von {total} ausgewählt")
        else:
            self.lbl_pending.setText(f"{total} Dateien · nichts ausgewählt")

    def _on_thumb_selected(self, thumb: ThumbItem, selected: bool):
        for entry in self.pending_files:
            if entry["path"] == thumb.path:
                entry["selected"] = selected
                break
        self._update_selection_count()

    def _clear_pending(self, silent: bool = False):
        for entry in self.pending_files:
            try:
                entry["path"].unlink(missing_ok=True)
            except Exception:
                pass
        self.pending_files.clear()
        self._refresh_grid()
        if not silent:
            self.info_box.setText("Warteschlange geleert.")

    def _select_all_pending(self):
        for entry in self.pending_files:
            entry["selected"] = True
        # update visual state of every ThumbItem
        for i in range(self.grid_layout.count()):
            w = self.grid_layout.itemAt(i).widget()
            if w is not None and hasattr(w, "is_selected"):
                w.is_selected = True
                w._update_style()
        self._update_selection_count()
        self.info_box.setText(f"Alle {len(self.pending_files)} Dateien ausgewählt.")

    def _deselect_all_pending(self):
        for entry in self.pending_files:
            entry["selected"] = False
        for i in range(self.grid_layout.count()):
            w = self.grid_layout.itemAt(i).widget()
            if w is not None and hasattr(w, "is_selected"):
                w.is_selected = False
                w._update_style()
        self._update_selection_count()
        self.info_box.setText("Auswahl aufgehoben.")

    def _delete_selected_pending(self):
        selected = [e for e in self.pending_files if e.get("selected")]
        if not selected:
            return
        reply = QMessageBox.question(
            self, "Löschen",
            f"{len(selected)} Datei(en) wirklich löschen?\n(Datei wird in den Papierkorb verschoben)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        from send2trash import send2trash
        deleted = 0
        for entry in selected:
            try:
                send2trash(str(entry["path"]))
                if entry.get("media_id"):
                    # remove from DB
                    conn = self.db._connect()
                    conn.execute("DELETE FROM media WHERE id=?", (entry["media_id"],))
                    conn.commit()
                deleted += 1
            except Exception as e:
                log.error(f"delete failed {entry['path']}: {e}")
        self.pending_files = [e for e in self.pending_files if not e.get("selected")]
        self._refresh_grid()
        self.info_box.setText(f"{deleted} Datei(en) gelöscht.")
        self._load_performers()

    def _assign_selected(self):
        target_id = self.combo_target.currentData()
        if target_id is None:
            QMessageBox.warning(self, "Kein Ziel", "Bitte einen Darsteller wählen.")
            return

        selected = [e for e in self.pending_files if e.get("selected")]
        if not selected:
            selected = list(self.pending_files)

        if not selected:
            QMessageBox.information(self, "Leer", "Keine Dateien in der Warteschlange.")
            return

        perf = self.db.get_performer_by_id(target_id)
        if not perf:
            log.error(f"Performer id {target_id} not found in DB")
            return

        dest_folder = config.MEDIA_ROOT / perf["folder_name"]
        dest_folder.mkdir(parents=True, exist_ok=True)
        log.info(f"ASSIGN → {perf['name']} ({len(selected)} files) into {dest_folder}")

        if not vault.is_unlocked:
            QMessageBox.warning(self, "Gesperrt", "Vault ist gesperrt – bitte neu starten.")
            return

        moved = 0
        assigned_paths = set()
        for entry in selected:
            src = entry["path"]
            if not src.exists():
                log.warning(f"  missing source: {src}")
                assigned_paths.add(src)
                continue

            # already browsing encrypted library – skip re-encrypt
            if entry.get("browse") and vault.is_encrypted_path(src):
                assigned_paths.add(src)
                continue

            try:
                log.info(f"  encrypting {src} → {dest_folder}")
                enc_path = vault.encrypt_file(src, dest_folder)
                if enc_path is None or not enc_path.exists():
                    log.error(f"  encrypt failed: {src}")
                    self.info_box.setText(f"Verschlüsselung fehlgeschlagen: {src.name}")
                    continue
                try:
                    src.unlink(missing_ok=True)
                except Exception as e:
                    log.warning(f"  could not remove temp {src}: {e}")
                self.db.add_media(
                    target_id, enc_path.name, entry["original"], entry["type"]
                )
                moved += 1
                assigned_paths.add(src)
                log.info(f"  OK encrypted → {enc_path.name}")
            except Exception as e:
                log.error(f"  assign failed {src}: {e}")
                self.info_box.setText(f"Fehler bei {src.name}: {e}")

        self.pending_files = [e for e in self.pending_files if e["path"] not in assigned_paths]
        log.info(f"ASSIGN done: {moved} encrypted, pending left={len(self.pending_files)}")

        self._refresh_grid()
        self.info_box.setText(f"{moved} Dateien → {perf['name']}\nNoch in Warteschlange: {len(self.pending_files)}")
        self._load_performers()

    # ------------------------------------------------------------------
    # Mood Mode
    # ------------------------------------------------------------------
    def _start_mood(self, all_media: bool = False, select_performers: bool = False):
        item = self.performer_list.currentItem()
        media_paths: List[Path] = []
        selected_pids: List[int] = []

        log.info(f"=== MOOD START (all_media={all_media}, select={select_performers}) ===")

        # --- options: media type + countdown in one dialog ---
        type_dlg = QDialog(self)
        type_dlg.setWindowTitle("Mood Optionen")
        type_dlg.setStyleSheet(STYLE)
        type_dlg.setModal(True)
        tl = QVBoxLayout(type_dlg)
        tl.addWidget(QLabel("Inhalt"))
        cb_img = QCheckBox("Fotos")
        cb_img.setChecked(True)
        cb_vid = QCheckBox("Videos")
        cb_vid.setChecked(True)
        tl.addWidget(cb_img)
        tl.addWidget(cb_vid)
        tl.addSpacing(8)
        tl.addWidget(QLabel("Countdown max. Sekunden (0 = aus)"))
        spin_cd = QSpinBox()
        spin_cd.setRange(0, 120)
        spin_cd.setValue(int(load_settings().get("default_countdown", config.DEFAULT_COUNTDOWN_MAX) or 0))
        tl.addWidget(spin_cd)
        row = QHBoxLayout()
        ok_b = QPushButton("Start")
        ok_b.setObjectName("primary")
        ok_b.clicked.connect(type_dlg.accept)
        cancel_b = QPushButton("Abbrechen")
        cancel_b.clicked.connect(type_dlg.reject)
        row.addWidget(ok_b)
        row.addWidget(cancel_b)
        tl.addLayout(row)
        if type_dlg.exec() != QDialog.Accepted:
            return
        want_img = cb_img.isChecked()
        want_vid = cb_vid.isChecked()
        countdown_val = spin_cd.value()
        if not want_img and not want_vid:
            QMessageBox.information(self, "Mood", "Mindestens Fotos oder Videos wählen.")
            return

        def _type_ok(path: Path) -> bool:
            name = path.name
            # strip encryption suffixes (possibly stacked)
            while name.endswith(".mood") or name.endswith(".goon"):
                name = name[:-5]
            m = detect_media_type(Path(name))
            if m == "image":
                return want_img
            if m == "video":
                return want_vid
            return False

        # --- collect source encrypted/plain paths ---
        if all_media:
            if config.MEDIA_ROOT.exists():
                for folder in config.MEDIA_ROOT.iterdir():
                    if not folder.is_dir():
                        continue
                    for f in folder.iterdir():
                        if f.is_file() and (vault.is_encrypted_path(f) or detect_media_type(f)):
                            if _type_ok(f):
                                media_paths.append(f)
            log.info(f"  all_media filtered: {len(media_paths)}")

            if load_settings().get("balance_performers", True) and media_paths:
                from collections import defaultdict
                by_folder = defaultdict(list)
                for f in media_paths:
                    by_folder[f.parent].append(f)
                max_n = max(len(v) for v in by_folder.values()) or 1
                balanced = []
                for files in by_folder.values():
                    factor = max(1, max_n // max(1, len(files)))
                    balanced.extend(files * factor)
                media_paths = balanced
                log.info(f"  all_media balanced: {len(media_paths)}")
            selected_pids = [p["id"] for p in self.db.get_all_performers()]



        elif select_performers:
            # multi-select dialog
            sel = QDialog(self)
            sel.setWindowTitle("Darsteller wählen")
            sel.setStyleSheet(STYLE)
            sel.setMinimumSize(360, 480)
            sl = QVBoxLayout(sel)
            sl.addWidget(QLabel("Haken setzen, dann OK:"))
            lst = QListWidget()
            lst.setSelectionMode(QAbstractItemView.NoSelection)
            performers = self.db.get_all_performers()
            for p in performers:
                it = QListWidgetItem(p["name"])
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Unchecked)
                it.setData(Qt.UserRole, p["id"])
                lst.addItem(it)
            sl.addWidget(lst, stretch=1)
            br = QHBoxLayout()
            b_all = QPushButton("Alle")
            b_none = QPushButton("Keine")
            b_ok = QPushButton("OK")
            b_ok.setObjectName("primary")
            b_cancel = QPushButton("Abbrechen")
            b_all.clicked.connect(lambda: [lst.item(i).setCheckState(Qt.Checked) for i in range(lst.count())])
            b_none.clicked.connect(lambda: [lst.item(i).setCheckState(Qt.Unchecked) for i in range(lst.count())])
            b_ok.clicked.connect(sel.accept)
            b_cancel.clicked.connect(sel.reject)
            br.addWidget(b_all)
            br.addWidget(b_none)
            br.addStretch()
            br.addWidget(b_ok)
            br.addWidget(b_cancel)
            sl.addLayout(br)
            if sel.exec() != QDialog.Accepted:
                return
            for i in range(lst.count()):
                it = lst.item(i)
                if it.checkState() == Qt.Checked:
                    selected_pids.append(it.data(Qt.UserRole))
            if not selected_pids:
                QMessageBox.information(self, "Mood", "Keine Darsteller ausgewählt.")
                return
            for pid in selected_pids:
                perf = self.db.get_performer_by_id(pid)
                if not perf:
                    continue
                folder = config.MEDIA_ROOT / perf["folder_name"]
                if not folder.exists():
                    continue
                for f in folder.iterdir():
                    if f.is_file() and (vault.is_encrypted_path(f) or detect_media_type(f)):
                        if _type_ok(f):
                            media_paths.append(f)
            log.info(f"  selected performers={len(selected_pids)} files={len(media_paths)}")

            # balance performers with fewer files (optional)
            if load_settings().get("balance_performers", True) and selected_pids:
                from collections import defaultdict
                by_perf = defaultdict(list)
                for pid in selected_pids:
                    perf = self.db.get_performer_by_id(pid)
                    if not perf:
                        continue
                    folder = config.MEDIA_ROOT / perf["folder_name"]
                    if not folder.exists():
                        continue
                    files = [f for f in folder.iterdir()
                             if f.is_file() and (vault.is_encrypted_path(f) or detect_media_type(f)) and _type_ok(f)]
                    by_perf[pid] = files
                if by_perf:
                    max_n = max(len(v) for v in by_perf.values()) or 1
                    balanced = []
                    for pid, files in by_perf.items():
                        if not files:
                            continue
                        # repeat pool so small libraries appear more often
                        factor = max(1, max_n // max(1, len(files)))
                        balanced.extend(files * factor)
                    media_paths = balanced
                    log.info(f"  balanced to {len(media_paths)} virtual entries")


        else:
            if not item:
                QMessageBox.information(self, "Auswahl", "Bitte einen Darsteller wählen\noder MOOD ALLE / MOOD AUSWAHL nutzen.")
                return
            pid = item.data(Qt.UserRole)
            selected_pids = [pid]
            perf = self.db.get_performer_by_id(pid)
            if not perf:
                return
            folder = config.MEDIA_ROOT / perf["folder_name"]
            log.info(f"  performer={perf['name']} folder={folder}")
            if folder.exists():
                for f in folder.iterdir():
                    if f.is_file() and (vault.is_encrypted_path(f) or detect_media_type(f)):
                        if _type_ok(f):
                            media_paths.append(f)

        # decrypt for playback
        resolved = []
        for i, pth in enumerate(media_paths):
            rp = vault.resolve_for_display(pth)
            if rp:
                resolved.append(rp)
            if i % 40 == 0:
                QApplication.processEvents()
        media_paths = resolved
        log.info(f"  media_paths ready: {len(media_paths)}")

        if not media_paths:
            QMessageBox.information(self, "Leer", "Keine Dateien gefunden.")
            return

        self.current_session_id = self.db.start_session()
        self._mood_pids = selected_pids
        self.mood_window = MoodWindow(media_paths, countdown_max=countdown_val)
        self.mood_window.closed.connect(self._on_mood_closed)
        # already fullscreen in __init__

    def _on_mood_closed(self):
        if self.mood_window and self.current_session_id:
            switches = self.mood_window.session_switches
            pids = getattr(self, "_mood_pids", [])
            self.db.end_session(self.current_session_id, switches, pids)
            self.stats_box.setText(f"Letzte Session: {switches} Wechsel")
            self.info_box.setText(f"Session beendet · {switches} Wechsel gespeichert.")
        self.mood_window = None
        self.current_session_id = None

    def _show_top(self):
        # Session-based stats (how often a performer was used in mood)
        sessions = self.db.get_recent_sessions(50)
        from collections import Counter
        counts = Counter()
        for s in sessions:
            ids = (s["performer_ids"] or "").split(",")
            for pid in ids:
                if pid.strip().isdigit():
                    perf = self.db.get_performer_by_id(int(pid))
                    if perf:
                        counts[perf["name"]] += 1
        # also fall back to media play_count
        top_media = self.db.get_top_performers(10)
        lines = []
        if counts:
            for i, (name, cnt) in enumerate(counts.most_common(10), 1):
                lines.append(f"{i}.  {name} — {cnt} Sessions")
        elif top_media:
            for i, (name, cnt) in enumerate(top_media, 1):
                lines.append(f"{i}.  {name} — {cnt} Plays")
        self._popover(
            "Top Darsteller",
            "\n".join(lines) if lines else "Noch keine Statistik.\nStarte den Mood-Modus, dann füllt sich das hier."
        )

    def _popover(self, title: str, body: str):
        """Small Apple-style info dialog."""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setStyleSheet(STYLE)
        dlg.setMinimumWidth(340)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(14)
        h = QLabel(title)
        h.setStyleSheet("font-size:19px; font-weight:700;")
        lay.addWidget(h)
        b = QLabel(body)
        b.setObjectName("dim")
        b.setWordWrap(True)
        lay.addWidget(b)
        ok = QPushButton("Fertig")
        ok.setObjectName("primary")
        ok.clicked.connect(dlg.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(ok)
        lay.addLayout(row)
        dlg.exec()



    def _open_settings(self):
        data = load_settings()
        dlg = QDialog(self)
        dlg.setWindowTitle("Einstellungen")
        dlg.setStyleSheet(STYLE)
        dlg.resize(520, 560)
        root = QVBoxLayout(dlg)

        tabs = QTabWidget()
        root.addWidget(tabs)

        # ----- Steuerung -----
        tab_keys = QWidget()
        k = QVBoxLayout(tab_keys)
        k.addWidget(QLabel("Blackout-Taste (Buchstabe)"))
        ed_bo = QLineEdit(str(data.get("blackout_key", "B")))
        ed_bo.setMaxLength(1)
        k.addWidget(ed_bo)
        k.addWidget(QLabel("Panic-Taste (Buchstabe z.B. X, oder Pause)"))
        ed_panic = QLineEdit(str(data.get("panic_key", "X")))
        k.addWidget(ed_panic)
        k.addWidget(QLabel("Auto-Lock nach Minuten (0 = aus)"))
        sp_lock = QSpinBox()
        sp_lock.setRange(0, 180)
        sp_lock.setValue(int(data.get("auto_lock_minutes", 15) or 0))
        k.addWidget(sp_lock)
        k.addWidget(QLabel("Standard-Countdown"))
        sp_cd = QSpinBox()
        sp_cd.setRange(0, 120)
        sp_cd.setValue(int(data.get("default_countdown", 0) or 0))
        k.addWidget(sp_cd)
        k.addStretch()
        tabs.addTab(tab_keys, "Steuerung")

        # ----- Mood -----
        tab_mood = QWidget()
        m = QVBoxLayout(tab_mood)
        cb_smart = QCheckBox("Smart-Mix (selten gesehene Dateien öfter)")
        cb_smart.setChecked(bool(data.get("smart_mix", True)))
        m.addWidget(cb_smart)
        cb_bal = QCheckBox("Darsteller ausgleichen (wenige Dateien → öfter)")
        cb_bal.setChecked(bool(data.get("balance_performers", True)))
        m.addWidget(cb_bal)
        cb_vstart = QCheckBox("Video zufälliger Startpunkt")
        cb_vstart.setChecked(bool(data.get("video_random_start", True)))
        m.addWidget(cb_vstart)
        m.addSpacing(8)
        m.addWidget(QLabel("Datei-Wieder-Sperre (Sekunden)"))
        sp_cdown = QSpinBox()
        sp_cdown.setRange(0, 600)
        sp_cdown.setValue(int(data.get("repeat_cooldown_sec", 30) or 0))
        sp_cdown.setToolTip("Nach Anzeigen so viele Sekunden nicht wiederholen. 0 = aus.")
        m.addWidget(sp_cdown)
        m.addStretch()
        tabs.addTab(tab_mood, "Mood")

        # ----- Bibliothek -----
        tab_lib = QWidget()
        lib = QVBoxLayout(tab_lib)
        lib.addWidget(QLabel("Datenbank von toten Einträgen befreien\n(Dateien fehlen auf der Platte)."))
        btn_clean = QPushButton("DB jetzt bereinigen")
        btn_clean.clicked.connect(lambda: self._cleanup_db(dlg))
        lib.addWidget(btn_clean)
        lib.addStretch()
        tabs.addTab(tab_lib, "Bibliothek")

        # ----- Statistik -----
        tab_stats = QWidget()
        st = QVBoxLayout(tab_stats)

        def _fmt_sec(sec: int) -> str:
            sec = int(sec or 0)
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            if h:
                return f"{h}h {m:02d}m {s:02d}s"
            return f"{m}m {s:02d}s"

        total = self.db.get_total_mood_time()
        total_lbl = QLabel(
            f"<b>Gesamt in Mood</b><br>"
            f"Zeit: {_fmt_sec(total['seconds'])}<br>"
            f"Sessions: {total['sessions']}<br>"
            f"Wechsel: {total['switches']}"
        )
        total_lbl.setWordWrap(True)
        st.addWidget(total_lbl)
        st.addSpacing(10)
        st.addWidget(QLabel("Darsteller wählen:"))
        combo_stats = QComboBox()
        combo_stats.addItem("— bitte wählen —", None)
        for p in self.db.get_all_performers():
            combo_stats.addItem(p["name"], p["id"])
        st.addWidget(combo_stats)
        perf_stats_lbl = QLabel("Keine Auswahl.")
        perf_stats_lbl.setWordWrap(True)
        perf_stats_lbl.setObjectName("dim")
        perf_stats_lbl.setStyleSheet("font-size:12px;")
        st.addWidget(perf_stats_lbl)

        def _on_perf_stats(idx):
            pid = combo_stats.currentData()
            if pid is None:
                perf_stats_lbl.setText("Keine Auswahl.")
                return
            stt = self.db.get_performer_time_stats(int(pid))
            name = combo_stats.currentText()
            perf_stats_lbl.setText(
                f"<b>{name}</b><br>"
                f"Zeit in Mood: {_fmt_sec(stt['seconds'])}<br>"
                f"Sessions: {stt['sessions']}<br>"
                f"Wechsel: {stt['switches']}<br>"
                f"<span style='color:#888'>(Einzel + Auswahl + Alle, anteilig volle Session-Zeit)</span>"
            )
        combo_stats.currentIndexChanged.connect(_on_perf_stats)
        st.addStretch()
        tabs.addTab(tab_stats, "Statistik")

        btns = QHBoxLayout()
        ok = QPushButton("Speichern")
        ok.setObjectName("primary")
        cancel = QPushButton("Abbrechen")
        ok.clicked.connect(dlg.accept)
        cancel.clicked.connect(dlg.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        root.addLayout(btns)

        if dlg.exec() != QDialog.Accepted:
            return
        new_data = {
            "blackout_key": (ed_bo.text() or "B").strip().upper()[:1] or "B",
            "panic_key": (ed_panic.text() or "X").strip() or "X",
            "smart_mix": cb_smart.isChecked(),
            "balance_performers": cb_bal.isChecked(),
            "video_random_start": cb_vstart.isChecked(),
            "repeat_cooldown_sec": sp_cdown.value(),
            "auto_lock_minutes": sp_lock.value(),
            "default_countdown": sp_cd.value(),
        }
        save_settings(new_data)
        try:
            config.DEFAULT_COUNTDOWN_MAX = new_data["default_countdown"]
        except Exception:
            pass
        self.info_box.setText("Einstellungen gespeichert.")
        log.info(f"Settings saved: {new_data}")

    def _cleanup_db(self, parent_dlg=None):
        n = self.db.cleanup_missing_media(config.MEDIA_ROOT)
        msg = f"{n} tote DB-Einträge entfernt."
        log.info(msg)
        self.info_box.setText(msg)
        QMessageBox.information(parent_dlg or self, "DB bereinigen", msg)
        self._load_performers()



    def _export_all(self):
        """Export all performers as plaintext files in a ZIP (decrypted)."""
        import zipfile
        import tempfile
        from datetime import datetime as dt

        if not vault.is_unlocked:
            QMessageBox.warning(self, "Export", "Vault gesperrt.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Export speichern (unverschlüsselt)",
            str(Path.home() / f"Mood_Export_{dt.now().strftime('%Y%m%d_%H%M')}.zip"),
            "ZIP (*.zip)"
        )
        if not out_path:
            return

        performers = self.db.get_all_performers()
        total_files = 0
        errors = 0

        self.info_box.setText("Export läuft…")
        QApplication.processEvents()

        try:
            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for perf in performers:
                    folder = config.MEDIA_ROOT / perf["folder_name"]
                    if not folder.exists():
                        continue
                    # human-readable folder name in the zip
                    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in perf["name"]).strip() or "unknown"
                    for f in folder.iterdir():
                        if not f.is_file():
                            continue
                        try:
                            if vault.is_encrypted_path(f):
                                raw = vault.decrypt_to_bytes(f)
                                if raw is None:
                                    errors += 1
                                    log.warning(f"export decrypt fail: {f}")
                                    continue
                                # strip .mood/.goon for name inside zip
                                plain_name = f.name
                                if plain_name.endswith(".mood") or plain_name.endswith(".goon"):
                                    plain_name = plain_name[:-5]
                                arc = f"{safe_name}/{plain_name}"
                                zf.writestr(arc, raw)
                            else:
                                arc = f"{safe_name}/{f.name}"
                                zf.write(f, arcname=arc)
                            total_files += 1
                        except Exception as e:
                            errors += 1
                            log.error(f"export file {f}: {e}")
                    QApplication.processEvents()

            msg = f"Export fertig: {total_files} Dateien"
            if errors:
                msg += f" ({errors} Fehler)"
            msg += f"\n{out_path}"
            self.info_box.setText(msg)
            log.info(msg.replace("\n", " | "))
            QMessageBox.information(self, "Export", msg)
        except Exception as e:
            log.error(f"export failed: {e}")
            QMessageBox.critical(self, "Export", str(e))

    def closeEvent(self, event):
        vault.cleanup_temp()
        vault.lock()
        self.db.close()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main():
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(config.COLOR_BG))
    palette.setColor(QPalette.WindowText, QColor(config.COLOR_TEXT))
    palette.setColor(QPalette.Base, QColor(config.COLOR_SURFACE))
    palette.setColor(QPalette.Text, QColor(config.COLOR_TEXT))
    palette.setColor(QPalette.Button, QColor(config.COLOR_SURFACE_2))
    palette.setColor(QPalette.ButtonText, QColor(config.COLOR_TEXT))
    palette.setColor(QPalette.Highlight, QColor(config.COLOR_ACCENT))
    app.setPalette(palette)

    # ---- Password gate (retry + lockout) ----
    if vault.has_password():
        while True:
            left = vault.lockout_remaining()
            if left > 0:
                QMessageBox.warning(
                    None, "Mood",
                    f"Zu viele Fehlversuche.\nBitte {left} Sekunden warten.\n"
                    "(Sperre bleibt auch nach Neustart.)"
                )
                time.sleep(min(left, 5))
                continue
            dlg = PasswordDialog(setup_mode=False)
            if dlg.exec() != QDialog.Accepted:
                sys.exit(0)
            if vault.unlock(dlg.password()):
                break
            left = vault.lockout_remaining()
            if left > 0:
                QMessageBox.warning(None, "Mood", "5× falsch. 1 Minute Sperre.")
            else:
                QMessageBox.warning(None, "Mood", "Falsches Passwort. Nochmal versuchen.")
    else:
        dlg = PasswordDialog(setup_mode=True)
        if dlg.exec() != QDialog.Accepted:
            sys.exit(0)
        pw = dlg.password()
        if len(pw) < 4:
            QMessageBox.warning(None, "Mood", "Passwort zu kurz (min. 4).")
            sys.exit(1)
        vault.setup_password(pw)
        QMessageBox.information(
            None, "Mood",
            "Passwort gesetzt.\nDateien + Ordnernamen in Media/ sind geschützt."
        )

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
