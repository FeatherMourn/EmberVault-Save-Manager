"""Minimal desktop world-library view built on the standard Tk toolkit."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable
from dataclasses import dataclass

from .library import list_worlds
from .world_model import SaveSource
from .world_model import WorldSave
from .world_operations import OperationPreview, preview_world_operation


@dataclass(frozen=True)
class WorldActionRequest:
    """A confirmed UI request handed to the operation/service layer."""

    action: str
    world: WorldSave
    destination: str | None
    preview: OperationPreview | None


class WorldLibraryController:
    """Connect library actions to preview and confirmation without owning I/O."""

    def __init__(self, parent: tk.Misc, sources: tuple[SaveSource, ...],
                 on_confirmed: Callable[[WorldActionRequest], None],
                 destination_picker: Callable[[tk.Misc, str], str | None] | None = None,
                 confirmer: Callable[[tk.Misc, str, str, str], bool] | None = None):
        self.parent = parent
        self.worlds = {world.world_id: world for source in sources for world in _worlds(source)}
        self.on_confirmed = on_confirmed
        self.destination_picker = destination_picker or request_operation_destination
        self.confirmer = confirmer or confirm_operation

    def handle(self, action: str, world_id: str) -> WorldActionRequest | None:
        world = self.worlds.get(world_id)
        if world is None:
            return None
        destination = self.destination_picker(self.parent, action)
        if action in {"backup", "duplicate", "export", "import", "move"} and not destination:
            return None
        preview = None
        if destination:
            preview = preview_world_operation(action, world, destination)
            preview_text = (f"Files: {len(preview.files)}\nEstimated size: {preview.estimated_size} bytes\n"
                            f"Conflicts: {len(preview.conflicts)}")
        else:
            preview_text = "This action changes the selected world metadata."
        if preview is not None and not preview.allowed:
            raise ValueError("The selected destination contains conflicts.")
        if not self.confirmer(self.parent, action, world.display_name, preview_text):
            return None
        request = WorldActionRequest(action, world, destination, preview)
        self.on_confirmed(request)
        return request


def _worlds(source: SaveSource) -> tuple[WorldSave, ...]:
    from .discovery import discover_worlds
    return tuple(discover_worlds(source))


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
    def on_confirmed(request: WorldActionRequest) -> None:
        messagebox.showinfo("Action ready", f"{request.action.title()} is ready for execution by Control Center.", parent=root)

    controller = WorldLibraryController(root, sources, on_confirmed)
    table = create_world_library(root, sources,
                                 lambda action, world_id: controller.handle(action, world_id))
    table.pack(fill="both", expand=True, padx=12, pady=12)
    root.mainloop()
