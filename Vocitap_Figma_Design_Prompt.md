# Vocitap UI Design Prompt for Figma/Design AI

## 1. Project Overview
- **Name**: Vocitap (Voice + Tap)
- **Nature**: A minimalist desktop utility for Voice-to-Text input.
- **Core Action**: Hold a key to speak, release to type.

## 2. Design Style Keywords
- **Modern & Clean**: Minimalist layout, no cluttered borders.
- **Glassmorphism**: Subtle translucency, soft shadows, rounded corners (20px+).
- **Interactive States**: Clear visual differentiation between "Ready" (Idle) and "Recording" (Active).
- **Typography**: Clean Sans-serif (e.g., Inter, SF Pro, Segoe UI Variable).

## 3. UI Layout Requirements

### Screen A: Main Dashboard (The "Idle" State)
- **Status Hub**: A central, prominent status indicator. 
    - Text: "Ready to Listen"
    - Visual: A pulsating blue glow or a calm wave animation.
- **Trigger Key Display**: A small badge showing the current hotkey (e.g., "[Left Ctrl]").
- **Quick Settings Area**: 
    - Toggle: "Remove Filler Words" (Icon: Sparkles/Cleanup)
    - Toggle: "Keep Punctuation" (Icon: Quote marks)
- **Footer**: A subtle gear icon for settings and a "Vocitap v1.0" branding.

### Screen B: Recording State (The "Active" State)
- **Primary Visual**: The calm wave turns into a vibrant, reactive soundwave (Red or Gradient).
- **Dynamic Text**: A large, glowing "Listening..." label.
- **Instruction**: A faint hint at the bottom: "Release key to finish".

### Screen C: Settings Panel (Expansion)
- **Hotkey Selector**: A clean dropdown to choose trigger keys (Ctrl, Alt, CapsLock).
- **System Toggles**: "Auto-start on Boot", "GPU Acceleration".
- **Advanced Action**: A destructive action button styled safely: "Uninstall Software & Models".

### Screen D: Initialization (Checklist Mode)
- **Progress Bar**: A sleek, thin line showing total progress.
- **Checklist Items**: Minimalist list with icons:
    - [√] Environment Check
    - [~] Downloading ASR Model (with percentage/log)
    - [-] VAD Model Ready

## 4. Color Palette Suggestions
- **Primary**: #0078D7 (Active Blue)
- **Alert/Recording**: #FF4B4B (Pulse Red)
- **Background**: #F5F5F5 (Light Mode) or #1A1A1A (Dark Mode)
- **Text**: #2D2D2D (Main) / #666666 (Secondary)

## 5. Logo / Icon Concept
- A square rounded icon.
- A stylized keyboard keycap shape.
- Inside the keycap, a set of 3-4 vertical bars representing a voice frequency wave.
