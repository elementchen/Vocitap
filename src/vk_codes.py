# Windows Virtual Key Codes and helpers

VK_MAP = {
    0x01: "Left Mouse", 0x02: "Right Mouse", 0x03: "Cancel", 0x04: "Middle Mouse",
    0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x10: "Shift", 0x11: "Ctrl",
    0x12: "Alt", 0x13: "Pause", 0x14: "CapsLock", 0x1B: "Esc", 0x20: "Space",
    0x21: "PageUp", 0x22: "PageDown", 0x23: "End", 0x24: "Home", 0x25: "Left",
    0x26: "Up", 0x27: "Right", 0x28: "Down", 0x2C: "PrintScreen", 0x2D: "Insert",
    0x2E: "Delete", 0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
    0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
    0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D", 0x45: "E", 0x46: "F", 0x47: "G",
    0x48: "H", 0x49: "I", 0x4A: "J", 0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N",
    0x4F: "O", 0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S", 0x54: "T", 0x55: "U",
    0x56: "V", 0x57: "W", 0x58: "X", 0x59: "Y", 0x5A: "Z",
    0x5B: "LWin", 0x5C: "RWin", 0x60: "Num 0", 0x61: "Num 1", 0x62: "Num 2",
    0x63: "Num 3", 0x64: "Num 4", 0x65: "Num 5", 0x66: "Num 6", 0x67: "Num 7",
    0x68: "Num 8", 0x69: "Num 9", 0x6A: "Num *", 0x6B: "Num +", 0x6D: "Num -",
    0x6E: "Num .", 0x6F: "Num /",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4", 0x74: "F5", 0x75: "F6",
    0x76: "F7", 0x77: "F8", 0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    0xA0: "LShift", 0xA1: "RShift", 0xA2: "LCtrl", 0xA3: "RCtrl", 0xA4: "LAlt", 0xA5: "RAlt",
}

MOD_MASKS = {
    "LCtrl": 0x01, "LShift": 0x02, "LAlt": 0x04, "LWin": 0x08,
    "RCtrl": 0x10, "RShift": 0x20, "RAlt": 0x40, "RWin": 0x80,
}

def get_vk_name(vk):
    return VK_MAP.get(vk, f"0x{vk:02X}")

def build_display_string(vk, mod):
    parts = []
    # Order: Ctrl, Shift, Alt, Win (consistent with common usage)
    if mod & (MOD_MASKS["LCtrl"] | MOD_MASKS["RCtrl"]): parts.append("Ctrl")
    if mod & (MOD_MASKS["LShift"] | MOD_MASKS["RShift"]): parts.append("Shift")
    if mod & (MOD_MASKS["LAlt"] | MOD_MASKS["RAlt"]): parts.append("Alt")
    if mod & (MOD_MASKS["LWin"] | MOD_MASKS["RWin"]): parts.append("Win")
    
    parts.append(get_vk_name(vk))
    return "+".join(parts)
