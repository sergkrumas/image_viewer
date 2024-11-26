# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#  Author: Sergei Krumas (github.com/sergkrumas)
#
# ##### END GPL LICENSE BLOCK #####

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
    '_utils.py', #DONE
    '_viewer.pyw', #DONE
    'app_copy_prevention.py', #DONE
    'help_text.py', #DONE
    'library_data.py', #DONE
    'board.py', #DONE
    'board_note_item.py', #DONE
    'commenting.py', #DONE
    'tagging.py', #DONE
    'control_panel.py', #DONE
    'settings_handling.py', #DONE
    'hidapi_adapter.py', #DONE
    'colorpicker.py', #DONE
    'slice_pipette_tool.py', #DONE
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

def generate_locales(this_folder):

    langs = [
        # "en",

        "ru",

        "de",
        "fr",
        "it",
        "es",
    ]
    for lang in langs:
        path = os.path.join(this_folder, 'locales', lang, 'LC_MESSAGES')
        if not os.path.exists(path):
            os.makedirs(path)
            print(path)
        else:
            print(f'already exists ', path)



def main():
    this_folder = os.path.dirname(__file__)

    os.chdir(this_folder)

    # generate_locales(this_folder)

    generate_pot_file(this_folder)

    # move_pot_to_po(this_folder)
    # generate_mo_file(this_folder)


if __name__ == '__main__':
    main()
