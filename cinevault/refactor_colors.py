import os

html_files = [
    r"c:\Users\apoor\Downloads\cinevault_v3\cinevault\static\index.html",
    r"c:\Users\apoor\Downloads\cinevault_v3\cinevault\static\movie.html"
]

# Mapping old Tailwind arbitrary HEX classes to new Tailwind v4 Token classes
replacements = {
    # Backgrounds
    "bg-[#0E0E0E]": "bg-background",
    "bg-[#000000]": "bg-background",
    "bg-[#131313]": "bg-background",
    "bg-[#1a1a1a]": "bg-surface-container",
    "bg-[#1F1F1F]": "bg-surface-container",
    "bg-[#252525]": "bg-surface-container",
    "bg-[#2a2a2a]": "bg-surface-container-high",
    "bg-[#F5C518]": "bg-primary",
    
    # Text
    "text-[#999999]": "text-on-surface-variant",
    "text-[#999]": "text-on-surface-variant",
    "text-[#BBBBBB]": "text-on-surface-variant",
    "text-[#F5C518]": "text-primary",

    # Borders
    "border-[#1F1F1F]": "border-surface-container",
    "border-[#2a2a2a]": "border-surface-container-high",
    "border-[#333]": "border-outline-variant",
    "border-[#F5C518]": "border-primary",
    
    # Hovers
    "hover:bg-[#ffe5a0]": "hover:bg-primary-container",
    "hover:text-[#F5C518]": "hover:text-primary",
    "focus:border-[#F5C518]": "focus:border-primary",
}

for filepath in html_files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for old_val, new_val in replacements.items():
            content = content.replace(old_val, new_val)
            
        # Clean up some missed hardcoded colors in JS strings
        content = content.replace("'#F5C518'", "var(--color-primary)")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Refactored {filepath}")
    else:
        print(f"File not found: {filepath}")

