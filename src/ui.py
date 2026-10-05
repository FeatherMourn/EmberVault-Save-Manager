"""Minimal desktop world-library view built on the standard Tk toolkit."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable

from .library import list_worlds
from .world_model import SaveSource


def create_world_library(root: tk.Misc, sources: tuple[SaveSource, ...],
                         on_action: Callable[[str, str], None] | None = None) -> ttk.Treeview:
    """Create and populate a world table; actions remain service-layer work."""
    table = ttk.Treeview(root, columns=("slot", "location", "health", "actions"), show="headings")
    for column, heading in (("slot", "Slot"), ("location", "Location"),
                            ("health", "Health"), ("actions", "Actions")):
        table.heading(column, text=heading)
    for row in list_worlds(sources):
        table.insert("", "end", iid=row["world_id"], text=row["display_name"],
                     values=(row["slot"], row["root"], row["health"], ", ".join(row["actions"])))
    if on_action is not None:
        action_bar = ttk.Frame(root)
        action_bar.pack(fill="x", padx=12, pady=(0, 12))
        for action in ("backup", "duplicate", "rename", "restore", "import", "export"):
            ttk.Button(action_bar, text=action.title(),
                       command=lambda operation=action: _dispatch_selected(table, operation, on_action)
                       ).pack(side="left", padx=(0, 6))
    return table


def _dispatch_selected(table: ttk.Treeview, action: str,
                       callback: Callable[[str, str], None]) -> None:
    selected = table.selection()
    if selected:
        callback(action, selected[0])


def request_operation_destination(parent: tk.Misc, action: str) -> str | None:
    """Ask for a destination for operations that leave the current source."""
    if action in {"backup", "duplicate", "export", "import", "move"}:
        return filedialog.askdirectory(parent=parent, title=f"Choose destination for {action}")
    return None


def confirm_operation(parent: tk.Misc, action: str, world_name: str,
                      preview_text: str) -> bool:
    """Show a concise preview and require explicit confirmation."""
    return messagebox.askyesno(
        f"Confirm {action.title()}",
        f"World: {world_name}\n\n{preview_text}\n\nContinue?",
        parent=parent,
        icon="warning" if action in {"restore", "archive", "remove"} else "question",
    )


def run_world_library(sources: tuple[SaveSource, ...]) -> None:
    root = tk.Tk()
    root.title("EmberVault Save Manager")
    root.geometry("900x450")
    table = create_world_library(root, sources)
    table.pack(fill="both", expand=True, padx=12, pady=12)
    root.mainloop()
