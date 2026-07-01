#!/usr/bin/env python3
"""Fix the password line in e2e_webull_hk.py"""
with open("/home/dennis/fundbotai/e2e_webull_hk.py") as f:
    content = f.read()

# Fix the corrupted password line
old = 'DEMO_PASSWORD="Demo...2024!"'
new = 'DEMO_PASSWORD = "Demo@2024!"'
content = content.replace(old, new)

# Remove duplicate line
old2 = 'WEBULL_HK_BROKER_ID = 22\nWEBULL_HK_BROKER_ID = 22'
new2 = 'WEBULL_HK_BROKER_ID = 22'
content = content.replace(old2, new2)

with open("/home/dennis/fundbotai/e2e_webull_hk.py", "w") as f:
    f.write(content)
print("Fixed!")
