import sys
import time
import datetime
import tkinter as tk
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# ──────────────────────────────────────
# Settings dialog: dark-themed Region dropdown + World/Server entries
# ──────────────────────────────────────
class SettingsDialog:
    def __init__(self):
        self.result = None
        self.root = tk.Tk()
        self.root.title("DA Sietch Monitor Settings")
        self.root.configure(bg="#2e2e2e")
        self.root.resizable(False, False)

        region_opts = ["North America", "Europe", "Asia", "Oceania", "South America"]
        self.vars = {}

        # Region dropdown
        tk.Label(self.root, text="Region:", bg="#2e2e2e", fg="#fff", font=(None,10,'bold')) \
          .grid(row=0, column=0, padx=10, pady=8, sticky="e")
        v_reg = tk.StringVar(value=region_opts[0])
        om = tk.OptionMenu(self.root, v_reg, *region_opts)
        om.config(bg="#1e1e1e", fg="#fff", relief="flat", highlightthickness=0,
                  activebackground="#3e3e3e", activeforeground="#fff")
        om["menu"].config(bg="#1e1e1e", fg="#fff",
                          activebackground="#3e3e3e", activeforeground="#fff")
        om.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        self.vars["game_region"] = v_reg

        # World + Server entries
        for i, key in enumerate(("world", "sietch"), start=1):
            tk.Label(self.root, text=key.capitalize()+":", bg="#2e2e2e", fg="#fff", font=(None,10,'bold')) \
              .grid(row=i, column=0, padx=10, pady=8, sticky="e")
            v = tk.StringVar()
            tk.Entry(self.root, textvariable=v,
                     bg="#1e1e1e", fg="#fff", insertbackground="#fff",
                     relief="flat", width=30) \
              .grid(row=i, column=1, padx=10, pady=8, sticky="w")
            self.vars[key] = v

        # OK button
        tk.Button(self.root, text="OK", command=self.on_ok,
                  bg="#3e3e3e", fg="#fff", relief="flat", font=(None,10,'bold')) \
          .grid(row=3, column=0, columnspan=2, pady=(5,15))

        # center on screen
        self.root.update_idletasks()
        w,h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth()//2)-(w//2)
        y = (self.root.winfo_screenheight()//2)-(h//2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.root.mainloop()

    def on_ok(self):
        self.result = {k: v.get().strip() for k,v in self.vars.items()}
        self.root.destroy()


# ──────────────────────────────────────
# Error dialog: world/server not found or timeout
# ──────────────────────────────────────
class ErrorDialog:
    def __init__(self):
        self.retry = False
        self.root = tk.Tk()
        self.root.title("DA Sietch Monitor Error")
        self.root.configure(bg="#2e2e2e")
        self.root.resizable(False, False)

        tk.Label(self.root,
                 text="World or Sietch not found.\nDid you type it correctly?",
                 bg="#2e2e2e", fg="#fff", font=(None,10,'bold'), justify="center") \
          .pack(padx=20, pady=(20,10))

        frm = tk.Frame(self.root, bg="#2e2e2e")
        frm.pack(pady=(0,20))
        tk.Button(frm, text="Retry",   command=self.on_retry,
                  bg="#3e3e3e", fg="#fff", relief="flat", font=(None,10,'bold'), width=10) \
          .pack(side="left", padx=10)
        tk.Button(frm, text="Close",   command=self.on_close,
                  bg="#3e3e3e", fg="#fff", relief="flat", font=(None,10,'bold'), width=10) \
          .pack(side="right", padx=10)

        # center on screen
        self.root.update_idletasks()
        w,h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth()//2)-(w//2)
        y = (self.root.winfo_screenheight()//2)-(h//2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.root.mainloop()

    def on_retry(self):
        self.retry = True
        self.root.destroy()

    def on_close(self):
        self.retry = False
        self.root.destroy()


# ──────────────────────────────────────
# Scraper returns (percent_string, mode, locked_flag)
# ──────────────────────────────────────
def find_server(page, region, world, server):
    page.goto("https://dunestatus.com/?type=public")
    page.wait_for_selector('[role="tablist"]', timeout=5000)
    tabs = page.query_selector_all('[role="tablist"] button[role="tab"]')
    for t in tabs:
        if region.lower() in t.inner_text().strip().lower():
            if t.get_attribute("aria-selected") != "true":
                t.click()
                page.wait_for_timeout(1000)
            break

    page.wait_for_selector("table tbody tr", timeout=10000)
    for _ in range(10):
        for row in page.query_selector_all("table tbody tr"):
            name = row.query_selector("td:nth-child(2)").inner_text().strip().lower()
            if name == world.lower():
                return querry_server(page, row, server)
        nxt = page.query_selector_all("button.inline-flex")
        if len(nxt) >= 2:
            nxt[-1].click()
            page.wait_for_timeout(1000)
        else:
            break
    return (None, None, None)

def querry_server(page, row, server):
    btn = row.query_selector("button")
    if not btn:
        return (None, None, None)
    btn.click()
    page.wait_for_timeout(1000)
    expanded = row.evaluate_handle("r => r.nextElementSibling")
    if not expanded:
        return (None, None, None)
    for inner in expanded.query_selector_all("table tr"):
        texts = [c.inner_text().strip() for c in inner.query_selector_all("td")]
        if any(server.lower() in t.lower() for t in texts):
            locked = (texts[1] == 'Public\nLocked')
            pct = texts[3].split('\n')[-1]
            if "%" not in pct:
                pct = f"{float(pct)*100}%"
            mode = texts[2].replace(" ", "")
            return (pct, mode, locked)
    return (None, None, None)


# ──────────────────────────────────────
# Main graph window
# ──────────────────────────────────────
class ServerGraphApp:
    def __init__(self, region, world, server):
        self.region, self.world, self.server = region, world, server
        self.times = []; self.values = []; self.modes = []; self.flags = []

        pw = sync_playwright().start()
        self.browser = pw.chromium.launch(headless=True)
        self.page = self.browser.new_page()

        self.root = tk.Tk()
        self.root.title(f"{region} / {world} / {server}")
        self.root.configure(bg="#2e2e2e")
        self.root.resizable(False, False)

        self.WIDTH, self.HEIGHT, self.PAD = 800, 400, 50
        self.canvas = tk.Canvas(self.root, width=self.WIDTH, height=self.HEIGHT,
                                bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        self.root.after(0, self.update)
        self.root.mainloop()

    def update(self):
        raw, mode, locked = find_server(self.page, self.region, self.world, self.server)
        pct = None
        if raw and raw.endswith('%'):
            try:
                pct = float(raw.rstrip('%'))
            except:
                pct = None

        if pct is not None:
            now = datetime.datetime.now()
            self.times.append(now)
            self.values.append(pct)
            self.modes.append(mode)
            self.flags.append(locked)

        self.redraw()
        self.root.after(180_000, self.update)

    def redraw(self):
        c = self.canvas
        c.delete("all")

        # Headers
        c.create_text(self.PAD, self.PAD/2, text=f"Region: {self.region}", fill="#ffffff",
                      anchor="w", font=(None,12,'bold'))
        c.create_text(self.WIDTH/2 - self.PAD*1.33, self.PAD/2, text=f"World: {self.world}", fill="#ffffff",
                      anchor="w", font=(None,12,'bold'))
        c.create_text(self.WIDTH-self.PAD, self.PAD/2, text=f"Sietch: {self.server}", fill="#ffffff",
                      anchor="e", font=(None,12,'bold'))

        # Axes
        c.create_line(self.PAD, self.PAD, self.PAD, self.HEIGHT-self.PAD, fill="#ffffff")
        c.create_line(self.PAD, self.HEIGHT-self.PAD, self.WIDTH-self.PAD, self.HEIGHT-self.PAD, fill="#ffffff")

        # Y-range
        low  = min(self.values) if self.values else 95.0
        high = max(self.values) if self.values else 105.0
        vmin = 95.0 if low  >= 95.0 else low
        vmax = 105.0 if high <= 105.0 else high

        # 100% line
        if vmin <= 100 <= vmax:
            y100 = self._cy(100, vmin, vmax)
            c.create_line(self.PAD, y100, self.WIDTH-self.PAD, y100, fill="red", dash=(4,2))
            c.create_text(self.PAD-10, y100, text="100%", fill="red", anchor="e")

        # Y labels
        c.create_text(self.PAD-10, self._cy(vmin, vmin, vmax), text=f"{vmin:.1f}%", fill="#ffffff", anchor="e")
        c.create_text(self.PAD-10, self._cy(vmax, vmin, vmax), text=f"{vmax:.1f}%", fill="#ffffff", anchor="e")

        # Plot line
        if len(self.values) >= 2:
            pts = []
            t0, t1 = self.times[0].timestamp(), self.times[-1].timestamp()
            for t, v in zip(self.times, self.values):
                pts += [self._cx(t.timestamp(), t0, t1), self._cy(v, vmin, vmax)]
            c.create_line(*pts, fill="#00ff00", width=1)

        # Plot points + footer
        if self.values:
            t0, t1 = self.times[0].timestamp(), self.times[-1].timestamp()
            r = 2
            for t, v in zip(self.times, self.values):
                x, y = self._cx(t.timestamp(), t0, t1), self._cy(v, vmin, vmax)
                c.create_oval(x-r, y-r, x+r, y+r, fill="#00ff00", outline="")

            by = self.HEIGHT - self.PAD/2
            idx = -1
            c.create_text(self.PAD, by, text=f"Players: {self.modes[idx]}", fill="#ffffff", anchor="w", font=(None,12,'bold'))
            c.create_text(self.WIDTH-self.PAD, by, text=f"Capacity: {self.values[idx]:.1f}%", fill="#ffffff", anchor="e", font=(None,12,'bold'))
            lock_text = "SIETCH LOCKED" if self.flags[idx] else "SIETCH UNLOCKED"
            lock_color = "red" if self.flags[idx] else "#00ff00"
            c.create_text(self.WIDTH/2, by, text=lock_text, fill=lock_color, anchor="center", font=(None,12,'bold'))

    def _cx(self, ts, t0, t1):
        return self.PAD + (ts - t0)/(t1 - t0)*(self.WIDTH-2*self.PAD) if t1>t0 else self.PAD

    def _cy(self, v, vmin, vmax):
        return (self.HEIGHT-self.PAD) - (v - vmin)/(vmax-vmin)*(self.HEIGHT-2*self.PAD) if vmax>vmin else self.HEIGHT-self.PAD


def main():
    while True:
        dlg = SettingsDialog()
        if not dlg.result:
            sys.exit()
        r, w, s = dlg.result["game_region"], dlg.result["world"], dlg.result["sietch"]

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            raw, *_ = find_server(page, r, w, s)
        except (PWTimeoutError, Exception):
            raw = None
        finally:
            browser.close()
            pw.stop()

        if raw is None:
            err = ErrorDialog()
            if err.retry:
                continue
            sys.exit()
        break

    ServerGraphApp(r, w, s)

if __name__ == "__main__":
    main()
