

import os
import sys
import subprocess
import shutil
import locale


# https://phrase.com/blog/posts/translate-python-gnu-gettext/
# https://docs.python.org/3/library/gettext.html

# import gettext
# el = gettext.translation('base', localedir='locales', languages=['el'])
# el.install() # copies el.gettext as _ to builtins for all app modules


files_to_parse = [
    '_viewer.pyw',
    '_utils.py',
    'app_copy_prevention.py',
    'board.py',
    'board_note_item.py',
    'colorpicker.py',
    'commenting.py',
    'control_panel.py',
    'help_text.py',
    'hidapi_adapter.py',
    'library_data.py',
    'settings_handling.py',
    'slice_pipette_tool.py',
    'tagging.py',
]

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
    args = [sys.executable, pygettext_py, '-d' 'base', '-o', 'locales/base.pot', *files_to_parse]
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

    os.chdir(this_folder)

    generate_pot_file(this_folder)

    # move_pot_to_po(this_folder)
    # generate_mo_file(this_folder)


if __name__ == '__main__':
    main()
