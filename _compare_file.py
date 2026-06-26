#!/usr/bin/env python3
"""Compare working tree file with HEAD version"""
import subprocess, sys, hashlib

path = sys.argv[1]

# Get HEAD version
r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, timeout=10)
head_content = r.stdout
head_hash = hashlib.sha256(head_content).hexdigest()

# Get working tree version
with open(path, "rb") as f:
    wd_content = f.read()
wd_hash = hashlib.sha256(wd_content).hexdigest()

print(f"HEAD:      {head_hash}")
print(f"Worktree:  {wd_hash}")
print(f"Size HEAD: {len(head_content)}")
print(f"Size WT:   {len(wd_content)}")

if head_hash == wd_hash:
    print("IDENTICAL - no changes detected")
else:
    print("DIFFERENT! Git should detect changes")
    # Show the first differing lines
    hl = head_content.decode().split("\n")
    wl = wd_content.decode().split("\n")
    for i in range(min(len(hl), len(wl))):
        if hl[i] != wl[i]:
            print(f"\nFirst diff at line {i+1}:")
            print(f"  HEAD: {hl[i][:100]}")
            print(f"  WT:   {wl[i][:100]}")
            break
