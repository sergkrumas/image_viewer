

import os
import sys
import subprocess
import shutil
import locale


# https://phrase.com/blog/posts/translate-python-gnu-gettext/


def get_locales(this_folder):
    locales = []
    locales_folder = os.path.join(this_folder, 'locales')
    for cur_dir, folders, files in os.walk(locales_folder):
        for folder in folders:
            locales.append(os.path.join(cur_dir, folder, 'LC_MESSAGES'))
    return locales

def generate_pot_file(this_folder):
    exe_folder = os.path.dirname(sys.executable)
    i18n_tools_folder = os.path.join(exe_folder, 'Tools', 'i18n')
    pygettext_py = os.path.join(i18n_tools_folder, 'pygettext.py')
    msgfmt_py = os.path.join(i18n_tools_folder, 'msgfmt.py')

    os.environ['PYTHONUTF8'] = '1' #for utf8 charset in .pot file

    # generating pot file
    args = [sys.executable, pygettext_py, '-d' 'base', '-o', 'locales/base.pot', '_viewer.py']
    subprocess.Popen(args)

def generate_mo_file(this_folder):

    locales = get_locales(this_folder)
    print(locales)

    # generate .mo file for each locale
    for folder in locales:
        os.chdir(folder)
        args = [sys.executable, msgfmt_py, '-o' 'base.mo', 'base']
        subprocess.Popen(args)

    os.chdir(this_folder)

def move_pot_to_po(this_folder):
    locales = get_locales(this_folder)

    source_pot = os.path.join(this_folder, 'locales', 'base.pot')

    for folder in locales:
        src = source_pot
        dst = os.path.join(folder, 'base.po')
        os.makedirs(os.path.dirname(dst))
        shutil.copyfile(src, dst)


def main():
    this_folder = os.path.dirname(__file__)

    generate_pot_file(this_folder)

    # move_pot_to_po(this_folder)
    # generate_mo_file(this_folder)


if __name__ == '__main__':
    main()
