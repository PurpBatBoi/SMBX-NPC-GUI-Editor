**Project Name:** SMBX NPC Animation Editor (Schema & Modular Version)
**Tech Stack:** Python 3, PyQt6
**Architecture:** Schema-Driven MVC (Model-View-Controller)

**Project Goal:**
To create a specialized GUI tool for editing Super Mario Bros. X (SMBX) NPC configuration files (`.txt`). The tool enables real-time visual editing of sprites and hitboxes, strictly adheres to SMBX file standards, and supports "Hot Reloading" for external edits.

**Core Architectural Concepts:**

1.  **Schema-Driven UI (`npc_definitions.py`):**
    *   The UI is **not hardcoded**. It is generated dynamically from a central dictionary (`NPC_DEFS`).
    *   This schema defines every parameter's **Type** (int, float, bool, enum), **Default Value**, **Category** (Animation, Physics, etc.), and **Constraints**.
    *   Adding a new SMBX parameter requires only a single line change in the definition file.

2.  **Smart Data Model (`npc_data.py`):**
    *   **Tri-State Logic:** Parameters can be:
        *   `Value`: Explicitly set (e.g., `true`, `10`).
        *   `None`: Omitted/Default. These are **not written** to the save file.
    *   **Preservation:** Uses a "Read-Modify-Write" strategy. It reads the original file line-by-line to preserve comments, formatting, and custom Lua variables (`custom_params`), only injecting/updating standard parameters where necessary.

3.  **Category Management (Add/Delete Logic):**
    *   **Collapsible Sections:** Parameters are grouped by category (e.g., "Line Guide", "Light Config").
    *   **Enable/Disable:** Each category has a checkbox in its header.
        *   **Checked:** Widgets are enabled, and values are written to the file.
        *   **Unchecked:** Widgets are disabled, and all parameters in that category are set to `None` (effectively "deleting" them from the saved file).

**Key Features:**

*   **Interactive Visual Editor (Canvas):**
    *   **Rendering:** Simulates SMBX animation speed (`framespeed`) and Frame Styles (0=Standard, 1=Left/Right, 2=4-Way). Correctly handles visual flipping and offset inversion for different facing directions.
    *   **Direct Manipulation:**
        *   **Graphic Mode:** Drag Red Box edges to resize graphics; drag center to move offsets.
        *   **Hitbox Mode:** Toggle HUD button to resize the Green Collision Box.
    *   **Sync:** Visual changes immediately update the UI SpinBoxes via `dataChanged` signals.
    *   **Hot Reload:** Monitors the loaded `.txt` and `.png` files. If they are changed externally (e.g., by Aseprite or Notepad), the editor automatically updates without restarting.

*   **User Interface:**
    *   **Dual-Column Layout:** Automatically detects pairs (Width/Height, X/Y) and renders them side-by-side.
    *   **Tri-State Booleans:** Custom radio widgets allow explicit `True`, `False (Forced)`, or `Default` (None) selection.
    *   **Custom Properties Table:** A generic table to view and edit unknown keys found in the file (e.g., specific AI variables), ensuring data is never lost.

**Code Structure:**

1.  **`editor.py`:** Root entry point. Sets up the package path and theme.
2.  **`program/npc_definitions.py`:** The Master Schema containing the dictionary of all supported SMBX parameters.
3.  **`program/npc_data.py`:** Handles File I/O, parsing logic, and state management (Standard vs. Custom params).
4.  **`program/editor_window.py`:** Generates the UI based on the schema. Handles the logic for Collapsible Categories, file watching, and syncing inputs.
5.  **`program/preview_widget.py`:** The `QWidget` canvas. Handles painting, mouse event logic (drag/pan/zoom), coordinate translation, and animation timers.