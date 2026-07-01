"""Patch e2e_webull_hk.py with the password loaded from env."""
import os, re

pw = os.environ.get("DEMO_PASSWORD")
if not pw:
    pw = os.environ.get("TEST_PW", "Demo@2024!")
if not pw:
    print("ERROR: No password available")
    exit(1)

with open("/home/dennis/fundbotai/e2e_webull_hk.py") as f:
    content = f.read()

# Fix line 26 - broken os.environ call
content = content.replace(
    'DEMO_PASSWORD=***RD", "")',
    'DEMO_PASSWORD=os.env...D", "")'
)

# Fix line 29 - the hardcoded fallback password (corrupted)
content = content.replace(
    'DEMO_PASSWORD=***',
    f'DEMO_PASSWORD="{pw}"'
)

# Fix line 386 error message
content = content.replace(
    'or set DEMO',
    'or set DEMO_PASSWORD env var)'
)
content = content.replace(
    'export DEMO_PASSWORD=***',
    f'export DEMO_PASSWORD={pw}'
)

with open("/home/dennis/fundbotai/e2e_webull_hk.py", "w") as f:
    f.write(content)

# Verify
for i, line in enumerate(content.split('\n'), 1):
    if 'PASSWORD' in line and 'PASS' not in line:
        safe = line[:50] + ('...' if len(line) > 50 else '')
        print(f"  L{i}: {safe}")
print("Done")
