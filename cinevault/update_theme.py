import os
import re

files = [
    'static/index.html',
    'static/movie.html',
    'static/profile.html'
]

old_theme = """  @theme {
    /* Colors - Luxury Cinematic Minimal Pattern */
    --color-primary: oklch(0.75 0.18 85);       
    --color-primary-container: oklch(0.85 0.15 85); 
    --color-surface: oklch(0.18 0.02 260);      
    --color-surface-container: oklch(0.22 0.02 260);
    --color-surface-container-low: oklch(0.15 0.02 260);
    --color-surface-container-high: oklch(0.26 0.02 260);
    --color-surface-container-highest: oklch(0.32 0.02 260);
    --color-on-surface: oklch(0.95 0.01 260);
    --color-on-surface-variant: oklch(0.70 0.02 260);
    --color-outline-variant: oklch(0.35 0.02 260);
    --color-background: oklch(0.12 0.02 260);"""

old_theme_2 = """  @theme {
    --color-primary: oklch(0.75 0.18 85);       
    --color-primary-container: oklch(0.85 0.15 85); 
    --color-surface: oklch(0.18 0.02 260);      
    --color-surface-container: oklch(0.22 0.02 260);
    --color-surface-container-low: oklch(0.15 0.02 260);
    --color-surface-container-high: oklch(0.26 0.02 260);
    --color-surface-container-highest: oklch(0.32 0.02 260);
    --color-on-surface: oklch(0.95 0.01 260);
    --color-on-surface-variant: oklch(0.70 0.02 260);
    --color-outline-variant: oklch(0.35 0.02 260);
    --color-background: oklch(0.12 0.02 260);"""

new_theme = """  @theme {
    /* Colors - Neo Dark Vibrant Pattern */
    /* Primary Neon Orange */
    --color-primary: #FF5500;       
    --color-primary-container: #FF6611; 
    
    /* Absolute Dark Canvas */
    --color-background: #0B0B0B;   
    --color-surface: #121212;      
    
    /* Soft lifted grays */
    --color-surface-container-low: #151515;
    --color-surface-container: #1A1A1A;
    --color-surface-container-high: #222222;
    --color-surface-container-highest: #2A2A2A;
    
    /* Text constraints */
    --color-on-surface: #F9F9F9;
    --color-on-surface-variant: #A4A4A4;
    --color-outline-variant: #333333;"""

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Safe URL/UI String Replacements
        content = content.replace('IMDb', 'CineVault')
        content = content.replace('IMDB', 'CineVault')
        
        # Color Theme Replacements
        if old_theme in content:
            content = content.replace(old_theme, new_theme)
        elif old_theme_2 in content:
            content = content.replace(old_theme_2, new_theme)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
