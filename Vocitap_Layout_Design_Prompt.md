# Vocitap UI Layout & Content Design Prompt (Figma)

## 1. Structure Overview
- **Type**: Desktop Utility (Fixed Size, e.g., 400x500px).
- **Navigation**: Top-level Tab Bar with two primary sections.
    - Tab 1: "Voice Engine" (Main control).
    - Tab 2: "Hardware Setup" (BLE settings).

## 2. Tab 1: Voice Engine (Layout & Content)
- **Status Indicator Card (Top)**:
    - Content: Large dynamic text label (e.g., "Ready", "Listening...", "Processing").
    - Layout: Centered, prominent. Beneath the text, a placeholder for a reactive wave-form element.
- **Software Settings Group (Middle)**:
    - **Hotkey Selector**: A label "Trigger Key" paired with a modern dropdown (Full width or split 50/50).
    - **Feature Toggles**: Three vertical rows of switches (Toggle switches, not checkboxes).
        - Row 1: "Filter Filler Words" (Subtext: Removes 'um', 'ah', etc.)
        - Row 2: "Smart Punctuation" (Subtext: Auto-generate commas/periods)
        - Row 3: "Launch on Startup"
- **Hardware Acceleration (Secondary Middle)**:
    - A single switch: "GPU Acceleration" with an info icon for tooltips.
- **Maintenance Action (Bottom)**:
    - A distinct, low-priority button: "Uninstall Software & Models".

## 3. Tab 2: Hardware Setup (Layout & Content)
- **Connection Dashboard (Top)**:
    - Status Label: "Status: Not Connected".
    - Info Label: "Model: - | Battery: -".
    - Action: A prominent primary button "Scan for Vocitap Hardware".
- **Hardware Button Mapping Group (Center)**:
    - Title: "Device Button Mapping".
    - Subtitle: "Assign functions to physical device buttons".
    - **Mapping Cards (3 Identical Units)**:
        - Small label: "Button 1", "Button 2", "Button 3".
        - Main text: Large display showing current mapping (e.g., "Left Ctrl", "Enter", "F2").
        - Action: A small "Set" button for each card.
- **Footer (Bottom)**:
    - App version label: "Vocitap v5.2".

## 4. Design Logic (Non-Color)
- **Rounded Corners**: Consistent large radius for the main window (20px) and inner cards (12px).
- **Spacing**: Use a modular grid (8px increments). Minimum 24px padding from window edges.
- **Hierarchy**: Emphasize the "Status" in Tab 1 and "Scan" in Tab 2 using font weight and size.
- **Interactions**: Toggles should have clear on/off states. Cards should have subtle shadows to indicate depth.
- **Input Field Style**: Dropdowns and display boxes should have a clean, borderless or minimal border look.
