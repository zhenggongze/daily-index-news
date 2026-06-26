#!/usr/bin/env python3
"""Touch a file to update its mtime"""
import os, sys
path = sys.argv[1]
with open(path, 'a'):
    os.utime(path, None)
print(f"Touched: {path}")
