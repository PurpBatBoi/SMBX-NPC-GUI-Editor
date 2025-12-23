FRAME_STYLES = {
    0: "0: Standard (Goomba-like)",
    1: "1: Left/Right (Koopa-like)",
    2: "2: 4-Way (Shy Guy-like)"
}

GRID_ALIGN_MODES = {
    0: "0: Center",
    1: "1: Edge"
}

# The Master Schema
NPC_DEFS = {
    # ==========================================
    # 1. ANIMATION
    # ==========================================
    "frames":     {"type": int, "default": 1, "category": "Animation", "min": 1, "tips": "Frames per direction"},
    "framespeed": {"type": int, "default": 8, "category": "Animation", "min": 1, "tips": "Ticks per frame (Lower = Faster)"},
    "framestyle": {"type": "enum", "default": 0, "category": "Animation", "choices": FRAME_STYLES},
    "gfxwidth":   {"type": int, "default": 32, "category": "Animation", "min": 0, "label": "GFX Width", "tips": "Width of sprite frame"},
    "gfxheight":  {"type": int, "default": 32, "category": "Animation", "min": 0, "label": "GFX Height", "tips": "Height of sprite frame"},
    "gfxoffsetx": {"type": int, "default": 0,  "category": "Animation", "label": "GFX Offset X", "tips": "Visual X offset"},
    "gfxoffsety": {"type": int, "default": 0,  "category": "Animation", "label": "GFX Offset Y", "tips": "Visual Y offset"},
    "foreground": {"type": bool, "default": False, "category": "Animation", "tips": "Render priority high"},
    "invisible":  {"type": bool, "default": False, "category": "Animation", "tips": "Invisible but active"},

    # ==========================================
    # 2. COLLISION
    # ==========================================
    "width":            {"type": int, "default": 32, "category": "Collision", "label": "Hitbox Width", "tips": "Physical width"},
    "height":           {"type": int, "default": 32, "category": "Collision", "label": "Hitbox Height", "tips": "Physical height"},
    "noblockcollision": {"type": bool, "default": False, "category": "Collision", "tips": "Passes through blocks/NPCs"},
    "npcblock":         {"type": bool, "default": False, "category": "Collision", "tips": "Blocks other NPCs"},
    "npcblocktop":      {"type": bool, "default": False, "category": "Collision", "tips": "Solid top for other NPCs"},
    "playerblock":      {"type": bool, "default": False, "category": "Collision", "tips": "Solid wall for player"},
    "playerblocktop":   {"type": bool, "default": False, "category": "Collision", "tips": "Solid top for player"},

    # ==========================================
    # 3. INTERACTION
    # ==========================================
    "jumphurt":       {"type": bool, "default": False, "category": "Interaction", "tips": "Cannot be jumped on"},
    "nohurt":         {"type": bool, "default": False, "category": "Interaction", "tips": "Harmless to player"},
    "spinjumpsafe":   {"type": bool, "default": False, "category": "Interaction", "tips": "Safe to spinjump on"},
    "grabside":       {"type": bool, "default": False, "category": "Interaction", "tips": "Grabbable from side"},
    "grabtop":        {"type": bool, "default": False, "category": "Interaction", "tips": "Grabbable from top"},
    "harmlessgrab":   {"type": bool, "default": False, "category": "Interaction", "tips": "No damage when held"},
    "harmlessthrown": {"type": bool, "default": False, "category": "Interaction", "tips": "No damage when thrown"},
    "ignorethrownnpcs":{"type": bool, "default": False, "category": "Interaction", "tips": "Unaffected by thrown items"},
    "noyoshi":        {"type": bool, "default": False, "category": "Interaction", "tips": "Uneatable by Yoshi"},
    "nofireball":     {"type": bool, "default": False, "category": "Interaction", "tips": "Immune to fire"},
    "noiceball":      {"type": bool, "default": False, "category": "Interaction", "tips": "Immune to ice"},
    "nogliding":      {"type": bool, "default": False, "category": "Interaction", "tips": "Ignores gliding blocks"},
    "linkshieldable": {"type": bool, "default": False, "category": "Interaction", "tips": "Blockable by Link shield"},
    "noshieldfireeffect":{"type": bool, "default": False, "category": "Interaction"},
    "notcointransformable":{"type": bool, "default": False, "category": "Interaction", "tips": "Won't turn to coin on goal"},
    "nopowblock":     {"type": bool, "default": False, "category": "Interaction", "tips": "Immune to POW"},
    "nowalldeath":    {"type": bool, "default": False, "category": "Interaction", "tips": "Survives inside walls"},
    "useclearpipe":   {"type": bool, "default": False, "category": "Interaction", "tips": "Enters clear pipes"},
    "clearpipegroup": {"type": str,  "default": "",    "category": "Interaction", "tips": "e.g. 'fireballs', 'iceballs'"},

    # ==========================================
    # 4. BEHAVIOUR (Physics/Logic)
    # ==========================================
    "speed":            {"type": float, "default": 1.0, "category": "Behaviour", "step": 0.1, "tips": "Horizontal speed multiplier"},
    "terminalvelocity": {"type": float, "default": 8.0, "category": "Behaviour", "step": 0.5, "tips": "Max fall speed"},
    "score":            {"type": int,   "default": 1,   "category": "Behaviour", "tips": "Score value (1-10)"},
    "health":           {"type": int,   "default": 1,   "category": "Behaviour", "tips": "HP (For Bosses/Custom AI)"},
    "cliffturn":        {"type": bool,  "default": False, "category": "Behaviour", "tips": "Turn around at ledges"},
    "staticdirection":  {"type": bool,  "default": False, "category": "Behaviour", "tips": "Direction doesn't change automatically"},
    "luahandlesspeed":  {"type": bool,  "default": False, "category": "Behaviour", "tips": "Ignore config speed"},
    "nogravity":        {"type": bool,  "default": False, "category": "Behaviour", "tips": "Unaffected by gravity"},
    "nowaterphysics":   {"type": bool,  "default": False, "category": "Behaviour", "tips": "Normal physics in water"},
    "standsonclowncar": {"type": bool,  "default": False, "category": "Behaviour"},
    "weight":           {"type": float, "default": 0.0, "category": "Behaviour", "tips": "Triggers donut blocks if > 0"},
    "isheavy":          {"type": bool,  "default": False, "category": "Behaviour", "tips": "Sets weight to 2"},
    "ishot":            {"type": bool,  "default": False, "category": "Behaviour", "tips": "Melts ice blocks"},
    "iscold":           {"type": bool,  "default": False, "category": "Behaviour", "tips": "Freezes hot blocks"},
    "iselectric":       {"type": bool,  "default": False, "category": "Behaviour"},
    "durability":       {"type": int,   "default": 0,   "category": "Behaviour", "tips": "Hits to destroy (-1 = Infinite)"},
    "isstationary":     {"type": bool,  "default": False, "category": "Behaviour", "tips": "Like P-Switch/Key"},
    "slippery":         {"type": bool,  "default": False, "category": "Behaviour"},

    # ==========================================
    # 5. AI / IDENTITY (Category)
    # ==========================================
    "iswalker":          {"type": bool, "default": False, "category": "AI / Identity"},
    "isbot":             {"type": bool, "default": False, "category": "AI / Identity"},
    "isvegetable":       {"type": bool, "default": False, "category": "AI / Identity"},
    "isshoe":            {"type": bool, "default": False, "category": "AI / Identity"},
    "isyoshi":           {"type": bool, "default": False, "category": "AI / Identity"},
    "isinteractable":    {"type": bool, "default": False, "category": "AI / Identity"},
    "iscoin":            {"type": bool, "default": False, "category": "AI / Identity"},
    "isvine":            {"type": bool, "default": False, "category": "AI / Identity"},
    "iscollectablegoal": {"type": bool, "default": False, "category": "AI / Identity"},
    "isflying":          {"type": bool, "default": False, "category": "AI / Identity"},
    "iswaternpc":        {"type": bool, "default": False, "category": "AI / Identity"},
    "isshell":           {"type": bool, "default": False, "category": "AI / Identity"},
    "istoad":            {"type": bool, "default": False, "category": "AI / Identity"},
    "iscustomswitch":    {"type": bool, "default": False, "category": "AI / Identity"},
    "powerup":           {"type": bool, "default": False, "category": "AI / Identity"},

    # ==========================================
    # 6. LINE GUIDE
    # ==========================================
    "lineguided":           {"type": bool, "default": False, "category": "Line Guide"},
    "linespeed":            {"type": float, "default": 2.0, "category": "Line Guide", "step": 0.5},
    "linejumpspeed":        {"type": float, "default": 4.0, "category": "Line Guide", "step": 0.5},
    "collideswhenattached": {"type": bool, "default": False, "category": "Line Guide"},
    "usehiddenlines":       {"type": bool, "default": False, "category": "Line Guide"},
    "lineactivebydefault":  {"type": bool, "default": True,  "category": "Line Guide"},
    "lineactivateonstanding":{"type": bool, "default": False, "category": "Line Guide"},
    "lineactivatenearby":   {"type": bool, "default": False, "category": "Line Guide"},
    "linefallwheninactive": {"type": bool, "default": False, "category": "Line Guide"},
    "linesensoralignh":     {"type": float, "default": 0.5, "category": "Line Guide", "step": 0.1, "min": 0.0, "max": 1.0},
    "linesensoralignv":     {"type": float, "default": 0.5, "category": "Line Guide", "step": 0.1, "min": 0.0, "max": 1.0},
    "linesensoroffsetx":    {"type": int, "default": 0, "category": "Line Guide"},
    "linesensoroffsety":    {"type": int, "default": 0, "category": "Line Guide"},
    "extendeddespawntimer": {"type": bool, "default": False, "category": "Line Guide"},
    "buoyant":              {"type": bool, "default": False, "category": "Line Guide", "tips": "Floats on water"},

    # ==========================================
    # 7. LIGHTING
    # ==========================================
    "lightoffsetx":    {"type": int,   "default": 0,       "category": "Lighting"},
    "lightoffsety":    {"type": int,   "default": 0,       "category": "Lighting"},
    "lightradius":     {"type": int,   "default": 0,       "category": "Lighting", "min": 0},
    "lightbrightness": {"type": float, "default": 1.0,     "category": "Lighting", "step": 0.1},
    "lightflicker":    {"type": bool,  "default": False,   "category": "Lighting"},
    "lightcolor":      {"type": "color",   "default": "0xFFFFFF", "category": "Lighting"},

    # ==========================================
    # 8. EDITOR ONLY
    # ==========================================
    "grid":        {"type": int,    "default": 32, "category": "Editor", "tips": "Snap grid size"},
    "gridoffsetx": {"type": int,    "default": 0,  "category": "Editor"},
    "gridoffsety": {"type": int,    "default": 0,  "category": "Editor"},
    "gridalign":   {"type": "enum", "default": 0,  "category": "Editor", "choices": GRID_ALIGN_MODES},
    "image":       {"type": str,    "default": "", "category": "Editor", "tips": "Override editor sprite"},
}