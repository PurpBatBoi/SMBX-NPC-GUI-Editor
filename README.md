# SMBX Visual NPC Attributes Editor

![SMBX NPC Editor screenshot](screenshot/screenshot_01.png)

A specialized GUI tool for editing Super Mario Bros. X (SMBX) NPC configuration files (`.txt`). This tool enables real-time visual editing of sprites and hitboxes, strictly adheres to SMBX file standards, and supports "Hot Reloading" for external edits.

# Disclaimer
Tool developed with the aid of Google Gemini.

## Features

### ✨ Undo/Redo System
- **Full history tracking**: Keep track of up to 50 actions
- **Keyboard shortcuts**: 
  - `Ctrl+Z` to undo
  - `Ctrl+Shift+Z` (or `Ctrl+Y`) to redo
- **Works with**:
  - Parameter value changes
  - Checkbox enable/disable
  - Visual canvas edits (drag operations)
  - Custom parameter additions/removals
- **Smart merging**: Consecutive edits to the same parameter are merged into one undo step
- **Menu integration**: Undo/Redo actions visible in Edit menu with current action names

### 🎯 Validation Feedback
- **Visual indicators**: Invalid values trigger orange border and background flash
- **Informative tooltips**: Shows exactly why a value was rejected (too small/large, min/max values)
- **Auto-recovery**: Feedback disappears after 2 seconds
- **No silent failures**: You'll always know when your input was clamped or corrected

## Features

- **Interactive Visual Editor**: Real-time canvas for editing graphics and hitboxes with drag-and-drop functionality.
- **Schema-Driven UI**: Dynamically generated interface from a central schema, making it easy to add new parameters.
- **Hot Reload**: Automatically updates when external changes are made to the files.
- **Category Management**: Collapsible sections for organizing parameters, with enable/disable functionality.
- **Custom Properties**: Table for editing unknown or custom parameters without data loss.
- **Tri-State Logic**: Supports explicit values, defaults, and omissions for flexible configuration.
- **Undo/Redo**: Full history tracking with keyboard shortcuts (NEW!)
- **Validation Feedback**: Visual alerts when values are clamped or corrected (NEW!)

## Requirements

- Python 3.8 or higher
- PyQt6

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SMBX-NPC-GUI-Editor
   ```

2. Install dependencies:
   ```bash
   pip install pyqt6
   ```

## Usage

Run the editor:
```bash
python editor.py
```

### Basic Operations

- **Load file**: `File > Open` or `Ctrl+O`
- **Save file**: `File > Save` or `Ctrl+S`
- **Undo**: `Edit > Undo` or `Ctrl+Z`
- **Redo**: `Edit > Redo` or `Ctrl+Shift+Z`

### Visual Editing

- Use the visual canvas to edit graphics (red box) and hitboxes (green box)
- Click "Hitbox Adjustment Mode" to switch between editing modes
- **Left-click and drag**: Resize or move the active box
- **Right-click and drag**: Pan the view
- **Mouse wheel**: Zoom in/out

### Parameter Editing

- Adjust parameters in the collapsible categories on the right
- Check the checkbox next to a parameter to enable it
- Uncheck to use the default value (parameter won't be written to file)
- Changes are tracked in the undo history

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open File | `Ctrl+O` |
| Save File | `Ctrl+S` |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Shift+Z` or `Ctrl+Y` |
| Quit | `Ctrl+Q` |

## License

MIT License - see [LICENSE](LICENSE) for details.
