"""
Añade smartbots to the path of modules
"""

import sys
import os

for line in sys.path:
    if line.endswith('site-packages'):
        print(line)
        lib_path = line

file = os.path.join(lib_path, 'external_modules.pth')

with open(file, 'a') as path_file:
    path_file.write(f'{os.getcwd()}\n')
