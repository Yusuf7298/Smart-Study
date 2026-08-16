import os
import re

# 1. Collect all callback_data from keyboards and handlers
callback_datas = set()
for root, dirs, files in os.walk('bot'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
                matches = re.findall(r'callback_data=["\']([^"\']+)["\']', content)
                for m in matches:
                    callback_datas.add(m)

# 2. Collect all handled callback prefixes/exact matches in bot/handlers/
handled_exact = set()
handled_prefixes = []
for root, dirs, files in os.walk('bot/handlers'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
                exact_m = re.findall(r'F\.data\s*==\s*["\']([^"\']+)["\']', content)
                handled_exact.update(exact_m)
                in_m = re.findall(r'F\.data\.in_\(\[([^\]]+)\]\)', content)
                for in_items in in_m:
                    items = re.findall(r'["\']([^"\']+)["\']', in_items)
                    handled_exact.update(items)
                prefix_m = re.findall(r'F\.data\.startswith\(["\']([^"\']+)["\']\)', content)
                handled_prefixes.extend(prefix_m)

print(f"Total distinct callback_data values: {len(callback_datas)}")
print(f"Handled exact: {len(handled_exact)}")
print(f"Handled prefixes: {handled_prefixes}")

unhandled = []
for cb in sorted(callback_datas):
    if cb in handled_exact:
        continue
    matched = False
    for p in handled_prefixes:
        if cb.startswith(p):
            matched = True
            break
    if not matched:
        unhandled.append(cb)

print(f"Unhandled callback count: {len(unhandled)}")
if unhandled:
    print(f"Unhandled callback list: {unhandled}")
else:
    print("SUCCESS: 100% of all callback buttons are properly routed to active handlers!")

# 3. Command Audit
commands = set()
for root, dirs, files in os.walk('bot/handlers'):
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f), 'r', encoding='utf-8') as fp:
                content = fp.read()
                cmds = re.findall(r'Command\(["\']([^"\']+)["\']\)', content)
                for c in cmds:
                    commands.add(f"/{c}")

print(f"\nTotal registered bot commands ({len(commands)}):")
for c in sorted(list(commands)):
    print(f"  {c}")
