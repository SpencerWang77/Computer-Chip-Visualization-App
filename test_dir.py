import os
print('Current dir:', os.getcwd())
print('Exports exists:', os.path.exists('exports'))
if os.path.exists('exports'):
    print('Exports files:', os.listdir('exports'))
else:
    print('No exports folder found')
