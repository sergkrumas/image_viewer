

import os

import sys
import subprocess

def main():

    print('\nBuilding...')
    theproc = subprocess.Popen([sys.executable, "setup.py", 'build_ext', '--inplace'])
    theproc.communicate()

    print('\nRenaming...')
    for filename in os.listdir("."):
        if filename.endswith('.pyd'):
            if filename.count('.') > 1:
                new_filename = filename.split('.')[0] + '.pyd'
                if os.path.exists(new_filename):
                    os.remove(new_filename)
                print(filename, ' -> ', new_filename)
                os.rename(filename, new_filename)

if __name__ == '__main__':
    main()

