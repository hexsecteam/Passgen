#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
passenger: single-file banner + wordlist generator (Termux-friendly)

UI polish:
- Colored banner (brand "hexsec", Telegram "hexsec_tools")
- Consistent themed colors for titles, prompts, notices, and success messages
- Clean spacing, panels, and dividers
- Styled inputs via Rich (falls back to plain input if Rich isn't available)
- All-English interface & ASCII-safe output

Usage:
  $ python passenger.py
"""

import itertools
import re
import shutil
from datetime import datetime

# ====== App identity ======
BRAND = "hexsec"
TELEGRAM = "hexsec_tools"
PROGRAM_NAME = "passenger"

ASCII_LINE = r"""
  ___  _   ___ ___  ___ ___ _  _ 
 | _ \/_\ / __/ __|/ __| __| \| |
 |  _/ _ \\__ \__ \ (_ | _|| .` |
 |_|/_/ \_\___/___/\___|___|_|\_|
                                 
                            """
# ==========================

# ====== Wordlist settings ======
MAX_COMBO_TOKENS = 3          # 2-3 is practical
ADD_LEET = True               # leetspeak variants
ADD_CASE_VARIANTS = True      # lower/UPPER/Capitalized/Camel
ADD_SEPARATORS = True         # -, _, .
ADD_NUM_TAILS = True          # 00..99 & recent years
MIN_LEN = 7
MAX_LEN = 24
OUTPUT_FILE = "wordlist.txt"
# ===============================

# ====== Theme (Rich color names) ======
THEME = {
    "brand": "bold bright_white",
    "gradient_from": "bright_cyan",
    "gradient_to": "magenta",
    "panel_border": "bright_cyan",
    "panel_border_alt": "bright_magenta",
    "label": "bold bright_white",
    "muted": "grey62",
    "prompt": "bold bright_cyan",
    "input_hint": "grey70",
    "ok": "bold green",
    "warn": "bold yellow",
    "bad": "bold red",
    "accent": "bright_magenta",
}
# ======================================

# ====== Optional Rich imports ======
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.box import HEAVY
    from rich.rule import Rule
    from rich.table import Table
    RICH_OK = True
    console = Console()
except Exception:  # fallback to plain stdout
    RICH_OK = False
# ===================================


def show_banner():
    """Render the banner + program & Telegram panels."""
    width = shutil.get_terminal_size((80, 24)).columns
    if not RICH_OK:
        print()
        print(("== " + BRAND.upper() + " ==" + f"  [{PROGRAM_NAME}]").center(width))
        print(("Telegram: " + TELEGRAM).center(width))
        print(ASCII_LINE)
        print("-" * width)
        return

    # Brand label
    brand_label = Text(BRAND.upper(), style=THEME["brand"])

    # Main ASCII block with gradient
    line_text = Text(ASCII_LINE)
    try:
        line_text.apply_gradient(THEME["gradient_from"], THEME["gradient_to"])
    except Exception:
        line_text.stylize(THEME["brand"])

    # Program panel
    prog_panel = Panel(
        Text(f"{PROGRAM_NAME}", style=THEME["label"]),
        title="program",
        title_align="left",
        subtitle="ready",
        subtitle_align="right",
        border_style=THEME["panel_border"],
        box=HEAVY,
        padding=(0, 4),
        width=min(40, max(28, width // 3)),
    )

    # Telegram panel
    tg = Text()
    tg.append("Telegram: ", style="bold bright_green")
    tg.append(TELEGRAM, style="bold bright_cyan")
    tg_panel = Panel(
        tg,
        box=HEAVY,
        border_style=THEME["panel_border_alt"],
        padding=(0, 2),
        title="connect",
        title_align="left",
        subtitle=f"© {BRAND}",
        subtitle_align="right",
        width=min(max(34, len("Telegram: " + TELEGRAM) + 6), max(46, width // 2)),
    )

    console.print()
    console.print(brand_label, justify="center")
    console.print(line_text, justify="center", overflow="fold")
    console.print(prog_panel, justify="center")
    console.print(tg_panel, justify="center")
    console.print(Rule(style=THEME["muted"]))


def quick_help():
    """Compact instructions below the banner."""
    if not RICH_OK:
        print("Quick start:")
        print("  1) Enter first/last name, optional nickname and team.")
        print("  2) Enter date as dd/mm/yyyy or ddmmyyyy.")
        print("  3) Variations (case/leet/separators) are generated.")
        print(f"  4) Output saved to '{OUTPUT_FILE}'.\n")
        return

    # Two-column table for crisp look
    t = Table.grid(padding=(0, 1))
    t.add_column(justify="right", style=THEME["muted"])
    t.add_column()
    t.add_row("1.", "Fill in first name, last name, optional nickname and team.")
    t.add_row("2.", "Enter date as [bold]dd/mm/yyyy[/] or [bold]ddmmyyyy[/] (e.g., 01/01/1990).")
    t.add_row("3.", "Generator creates case, leet and separator variants.")
    t.add_row("4.", f"Output is saved to [bold]{OUTPUT_FILE}[/].")
    console.print(t)
    console.print(Rule(style=THEME["muted"]))


def styled_input(prompt: str, hint: str = "") -> str:
    """Styled input with Rich; plain fallback otherwise."""
    if not RICH_OK:
        return input(f"{prompt} ").strip()
    hint_part = f" [dim]{hint}[/]" if hint else ""
    return console.input(f"[{THEME['prompt']}]{prompt}[/]{hint_part} ").strip()


# ====== Wordlist core ======
LEET_MAP = str.maketrans({
    'a':'4','A':'4',
    'e':'3','E':'3',
    'i':'1','I':'1',
    'o':'0','O':'0',
    's':'5','S':'5',
    't':'7','T':'7',
    'b':'8','B':'8'
})

def clean_token(s: str) -> str:
    """Keep only ASCII alphanumerics plus dot/underscore/dash."""
    s = s.strip()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^0-9A-Za-z._-]", "", s)
    return s

def case_variants(s: str):
    """lower/UPPER/Capitalized/Camel."""
    variants = {s, s.lower(), s.upper()}
    if s:
        variants.add(s.capitalize())
    parts = re.split(r"[_\-.]", s)
    camel = ''.join(p.capitalize() for p in parts if p)
    if camel:
        variants.add(camel)
        variants.add(camel.lower())
    return variants

def leet_variants(s: str):
    """Simple leetspeak mapping."""
    return {s, s.translate(LEET_MAP)}

def with_separators(tokens):
    """Join tokens with several separators."""
    if len(tokens) == 1:
        return {tokens[0]}
    seps = ['','-','_','.'] if ADD_SEPARATORS else ['']
    out = {''.join(tokens)} if '' in seps else set()
    for sep in seps:
        out.add(sep.join(tokens))
    return out

def add_numeric_tails(words, tails):
    """Append numeric tails to each word."""
    out = set(words)
    for w in words:
        for t in tails:
            out.add(f"{w}{t}")
    return out

def unique_len_filtered(words):
    """Unique + length range filter."""
    return {w for w in set(words) if MIN_LEN <= len(w) <= MAX_LEN}
# ===========================


def run_wizard():
    """Interactive, styled wordlist wizard."""
    if RICH_OK:
        console.print("[bold]=== passenger • Wordlist Generator ===[/]\n")

    name = styled_input("First name:", "ASCII only")
    surname = styled_input("Last name:", "ASCII only")
    nickname = styled_input("Nickname:", "optional")
    team = styled_input("Team:", "optional")
    date_str = styled_input("Date:", "dd/mm/yyyy or ddmmyyyy")

    # Clean tokens
    tokens = [clean_token(x) for x in [name, surname, nickname, team] if x.strip()]

    # Parse date
    date_tokens = set()
    if date_str:
        ds = re.sub(r"[^\d]", "", date_str)
        day = month = year = ""
        if len(ds) == 8:
            day, month, year = ds[:2], ds[2:4], ds[4:]
        elif len(ds) == 6:  # ddmmyy
            day, month, yy = ds[:2], ds[2:4], ds[4:]
            year = "19" + yy
            date_tokens.add("20" + yy)
        for x in [day, month, year, ds]:
            if x:
                date_tokens.add(x)
        if day and month and year:
            date_tokens.update({day+month, month+day, day+month+year, year+month+day})
    tokens.extend(sorted(date_tokens))

    # Base combinations
    base = set()
    tokens = [t for t in tokens if t]
    tokens = list(dict.fromkeys(tokens))  # unique, keep order

    for r in range(1, min(MAX_COMBO_TOKENS, len(tokens)) + 1):
        for combo in itertools.permutations(tokens, r):
            for joined in with_separators(combo):
                base.add(joined)

    # Expand with case and leet variants
    expanded = set()
    for w in base:
        variants = {w}
        if ADD_CASE_VARIANTS:
            variants = set().union(*(case_variants(x) for x in variants))
        if ADD_LEET:
            variants = set().union(*(leet_variants(x) for x in variants))
        expanded.update(variants)

    # Numeric tails
    if ADD_NUM_TAILS:
        tails = [str(i) for i in range(0, 100)]
        try:
            now_year = datetime.now().year
        except Exception:
            now_year = 2025
        tails += [str(y) for y in range(now_year-10, now_year+1)]
        expanded = add_numeric_tails(expanded, tails)

    # Filter & save
    final_words = unique_len_filtered(expanded)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for w in sorted(final_words):
            f.write(w + "\n")

    # Summary
    if not RICH_OK:
        print(f"\n[OK] Generated {len(final_words)} words in '{OUTPUT_FILE}'.")
        return

    console.print()
    console.print(Panel.fit(
        Text(f"Generated {len(final_words)} words", style=THEME["ok"]),
        border_style=THEME["panel_border"], box=HEAVY
    ))
    stats = Table.grid(padding=(0, 1))
    stats.add_column(style=THEME["muted"], justify="right")
    stats.add_column()
    stats.add_row("Output:", OUTPUT_FILE)
    stats.add_row("Case:", "on" if ADD_CASE_VARIANTS else "off")
    stats.add_row("Leet:", "on" if ADD_LEET else "off")
    stats.add_row("Separators:", "on" if ADD_SEPARATORS else "off")
    stats.add_row("Num tails:", "on" if ADD_NUM_TAILS else "off")
    console.print(stats)
    console.print(Rule(style=THEME["muted"]))
    console.print(Text("Use responsibly (lawful/ethical purposes only).", style=THEME["warn"]))
    console.print()


def main():
    show_banner()
    quick_help()
    run_wizard()


if __name__ == "__main__":
    main()
