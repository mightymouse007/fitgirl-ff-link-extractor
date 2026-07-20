#!/usr/bin/env python3
"""
FuckingFast Direct Link Extractor - GUI Edition
===============================================
A standalone GUI app that extracts direct download links from fuckingfast.co.

Features:
- Paste messy/unstructured text — the app auto-finds all fuckingfast links
- One-click extract with progress tracking
- Copy results or save to file
- No command line needed

To build EXE:
    pyinstaller --onefile --windowed --name "FuckingFast_Extractor" gui_app.py
"""

import re
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
from urllib.parse import urlparse

try:
    from curl_cffi import requests
except ImportError:
    # Fallback message if running from source without deps
    HAS_CURL_CFFI = False
else:
    HAS_CURL_CFFI = True

from bs4 import BeautifulSoup


# ── Link Extraction Engine ──────────────────────────────────────────

FUCKINGFAST_PATTERN = re.compile(
    r'https?://(?:www\.)?fuckingfast\.co/[a-zA-Z0-9_-]+(?:#[^\s]*)?',
    re.IGNORECASE
)


def extract_links_from_text(text: str) -> list[str]:
    """Find all fuckingfast.co URLs from pasted text."""
    found = FUCKINGFAST_PATTERN.findall(text)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for url in found:
        clean = url.strip()
        if clean not in seen:
            seen.add(clean)
            unique.append(clean)
    return unique


def get_direct_link(url: str) -> str | None:
    """Extract direct /dl/ link from a single fuckingfast.co URL."""
    file_id = urlparse(url).path.strip('/')
    if not file_id:
        return None

    try:
        # Step 1: GET landing page
        resp = requests.get(url, impersonate="chrome", timeout=30)
        if resp.status_code != 200:
            return None

        # Step 2: Parse HTMX endpoint
        soup = BeautifulSoup(resp.text, 'html.parser')
        btn = soup.find('a', attrs={'hx-post': True})
        hx_post = btn.get('hx-post') if btn else f"/f/{file_id}/go"

        # Step 3: POST to HTMX endpoint
        post_url = f"https://fuckingfast.co{hx_post}" if hx_post.startswith('/') else f"https://fuckingfast.co/{hx_post}"
        post_headers = {
            'HX-Request': 'true',
            'HX-Current-URL': url,
            'Referer': url,
            'Origin': 'https://fuckingfast.co',
        }

        post_resp = requests.post(
            post_url,
            headers=post_headers,
            data='',
            impersonate="chrome",
            timeout=30,
            allow_redirects=False
        )

        # Step 4: Extract direct link
        hx_redirect = post_resp.headers.get('HX-Redirect', '')
        if hx_redirect and '/dl/' in hx_redirect:
            return hx_redirect

        location = post_resp.headers.get('Location', '')
        if location and '/dl/' in location:
            return location

        return None

    except Exception:
        return None


# ── GUI Application ─────────────────────────────────────────────────

class FuckingFastExtractorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FuckingFast Direct Link Extractor")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Theme colors
        self.bg_color = "#1a1a2e"
        self.fg_color = "#eaeaea"
        self.accent = "#e94560"
        self.success = "#00d9ff"
        self.secondary_bg = "#16213e"

        self.root.configure(bg=self.bg_color)

        self._build_ui()
        self.extracted_links: list[str] = []
        self.is_running = False

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=self.bg_color)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        title = tk.Label(
            header,
            text="⚡ FuckingFast Direct Link Extractor",
            font=("Segoe UI", 20, "bold"),
            bg=self.bg_color,
            fg=self.accent
        )
        title.pack(anchor=tk.W)

        subtitle = tk.Label(
            header,
            text="Paste any text containing fuckingfast.co links — we'll find and extract them.",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#888"
        )
        subtitle.pack(anchor=tk.W, pady=(2, 0))

        # ── Input Section ──
        input_frame = tk.LabelFrame(
            self.root,
            text=" 📋 Paste Links Here ",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            bd=2,
            relief=tk.GROOVE
        )
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.secondary_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            bd=0,
            padx=10,
            pady=10,
            height=10
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.input_text.bind("<Button-3>", self._show_context_menu)

        # ── Controls ──
        controls = tk.Frame(self.root, bg=self.bg_color)
        controls.pack(fill=tk.X, padx=20, pady=5)

        self.btn_extract = tk.Button(
            controls,
            text="▶  EXTRACT DIRECT LINKS",
            font=("Segoe UI", 12, "bold"),
            bg=self.accent,
            fg="white",
            activebackground="#ff6b81",
            activeforeground="white",
            bd=0,
            padx=30,
            pady=10,
            cursor="hand2",
            command=self._start_extraction
        )
        self.btn_extract.pack(side=tk.LEFT)

        self.btn_clear = tk.Button(
            controls,
            text="🗑  Clear",
            font=("Segoe UI", 11),
            bg=self.secondary_bg,
            fg=self.fg_color,
            activebackground="#2a2a4a",
            activeforeground="white",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._clear_all
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(10, 0))

        # ── Progress & Stats ──
        self.progress_frame = tk.Frame(self.root, bg=self.bg_color)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=(5, 0))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = tk.Label(
            self.progress_frame,
            text="Ready",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#888",
            width=25,
            anchor=tk.E
        )
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))

        # ── Output Section ──
        output_frame = tk.LabelFrame(
            self.root,
            text=" 🔗 Direct Links ",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            bd=2,
            relief=tk.GROOVE
        )
        output_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.secondary_bg,
            fg=self.success,
            insertbackground=self.fg_color,
            bd=0,
            padx=10,
            pady=10,
            height=8,
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.bind("<Button-3>", self._show_context_menu)

        # ── Output Buttons ──
        out_controls = tk.Frame(self.root, bg=self.bg_color)
        out_controls.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.btn_copy = tk.Button(
            out_controls,
            text="📋 Copy All",
            font=("Segoe UI", 10, "bold"),
            bg="#4ecca3",
            fg="#1a1a2e",
            activebackground="#3db892",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._copy_results
        )
        self.btn_copy.pack(side=tk.LEFT)

        self.btn_save = tk.Button(
            out_controls,
            text="💾 Save to File",
            font=("Segoe UI", 10, "bold"),
            bg="#4ecca3",
            fg="#1a1a2e",
            activebackground="#3db892",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._save_results
        )
        self.btn_save.pack(side=tk.LEFT, padx=(10, 0))

        self.stats_label = tk.Label(
            out_controls,
            text="Found: 0  |  Success: 0  |  Failed: 0",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#888"
        )
        self.stats_label.pack(side=tk.RIGHT)

        # Configure ttk style for progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=self.secondary_bg,
            background=self.accent,
            thickness=20
        )

    def _show_context_menu(self, event):
        """Right-click context menu for text widgets."""
        widget = event.widget
        menu = tk.Menu(self.root, tearoff=0, bg=self.secondary_bg, fg=self.fg_color)
        menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: widget.tag_add("sel", "1.0", "end"))
        menu.tk_popup(event.x_root, event.y_root)

    def _set_output(self, text: str):
        """Set output text area content."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state=tk.DISABLED)

    def _append_output(self, text: str):
        """Append to output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def _update_status(self, text: str):
        """Update status label."""
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def _update_stats(self, total: int, success: int, failed: int):
        """Update stats label."""
        self.stats_label.config(text=f"Found: {total}  |  Success: {success}  |  Failed: {failed}")
        self.root.update_idletasks()

    def _start_extraction(self):
        """Start extraction in a background thread."""
        if self.is_running:
            return

        raw_text = self.input_text.get("1.0", tk.END)
        urls = extract_links_from_text(raw_text)

        if not urls:
            messagebox.showwarning(
                "No Links Found",
                "Couldn\'t find any fuckingfast.co links in the pasted text.\n\n"
                "Make sure your URLs look like:\n"
                "https://fuckingfast.co/xxxxx#filename.rar"
            )
            return

        self.is_running = True
        self.btn_extract.config(state=tk.DISABLED, text="⏳  Extracting...")
        self.progress_var.set(0)
        self._set_output("")
        self.extracted_links = []
        self._update_stats(len(urls), 0, 0)

        thread = threading.Thread(target=self._extraction_worker, args=(urls,), daemon=True)
        thread.start()

    def _extraction_worker(self, urls: list[str]):
        """Background worker for link extraction."""
        total = len(urls)
        success_count = 0
        failed_count = 0

        for i, url in enumerate(urls, 1):
            progress = (i / total) * 100
            self.progress_var.set(progress)
            self._update_status(f"Processing {i}/{total}...")

            link = get_direct_link(url)

            if link:
                self.extracted_links.append(link)
                success_count += 1
                self._append_output(f"{link}\n")
            else:
                failed_count += 1

            self._update_stats(total, success_count, failed_count)

            # Rate limiting (2s between requests, skip after last)
            if i < total:
                time.sleep(2)

        # Done
        self.root.after(0, self._extraction_done, total, success_count, failed_count)

    def _extraction_done(self, total: int, success: int, failed: int):
        """Called on main thread when extraction completes."""
        self.is_running = False
        self.progress_var.set(100)
        self.btn_extract.config(state=tk.NORMAL, text="▶  EXTRACT DIRECT LINKS")

        if success > 0:
            self._update_status(f"Done! {success}/{total} extracted")
            self._append_output(f"\n{'='*60}\n")
            self._append_output(f"# Total: {total} | Success: {success} | Failed: {failed}\n")
        else:
            self._update_status("Extraction failed")
            self._append_output("# No direct links could be extracted.\n")
            self._append_output("# The site may have changed or is blocking requests.\n")

    def _clear_all(self):
        """Clear all fields."""
        self.input_text.delete("1.0", tk.END)
        self._set_output("")
        self.progress_var.set(0)
        self.status_label.config(text="Ready")
        self.stats_label.config(text="Found: 0  |  Success: 0  |  Failed: 0")
        self.extracted_links = []

    def _copy_results(self):
        """Copy all extracted links to clipboard."""
        if not self.extracted_links:
            messagebox.showinfo("Nothing to Copy", "No extracted links to copy.")
            return

        text = "\n".join(self.extracted_links)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied!", f"{len(self.extracted_links)} links copied to clipboard.")

    def _save_results(self):
        """Save extracted links to a file."""
        if not self.extracted_links:
            messagebox.showinfo("Nothing to Save", "No extracted links to save.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="direct_links.txt"
        )
        if filepath:
            Path(filepath).write_text("\n".join(self.extracted_links))
            messagebox.showinfo("Saved!", f"Saved {len(self.extracted_links)} links to:\n{filepath}")


def main():
    if not HAS_CURL_CFFI:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing Dependency",
            "curl_cffi is not installed.\n\n"
            "Please install it first:\n"
            "pip install curl_cffi beautifulsoup4"
        )
        sys.exit(1)

    root = tk.Tk()
    app = FuckingFastExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
