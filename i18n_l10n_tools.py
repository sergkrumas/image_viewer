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
from collections import defaultdict

# https://phrase.com/blog/posts/translate-python-gnu-gettext/
# https://docs.python.org/3/library/gettext.html

# import gettext
# el = gettext.translation('base', localedir='locales', languages=['el'])
# el.install() # copies el.gettext as _ to builtins for all app modules

# IMPORTANT!
# use 
# `__import__('builtins').__dict__['_'] = __import__('gettext').gettext`
# instead
# `from gettext import gettext as _`
# otherwise el.install() will not work at all, because _ in module globals() will have a higher priority over modified builtins dict after calling el.install method(), so calling el.install() will give nothing








# s = """
# multistring
# """

# for line in s.split("\n"):
#     print(f'"{line}\\n"')





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
        break
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

    exe_folder = os.path.dirname(sys.executable)
    i18n_tools_folder = os.path.join(exe_folder, 'Tools', 'i18n')
    msgfmt_py = os.path.join(i18n_tools_folder, 'msgfmt.py')
    locales = get_locales(this_folder)
    # print(locales)

    # generate .mo file for each locale
    for locale_folder in locales:
        os.chdir(locale_folder)
        print(locale_folder)
        if os.path.exists('base.po'):
            args = [sys.executable, msgfmt_py, '-o' 'base.mo', 'base']
            subprocess.Popen(args)
            print(f'    generating {locale_folder}')
        else:
            print(f'!!! no base.po {locale_folder}')


    os.chdir(this_folder)

def move_pot_to_po(this_folder):
    locales = get_locales(this_folder)

    source_pot = os.path.join(this_folder, 'locales', 'base.pot')

    for locale_folder in locales:
        src = source_pot
        dst = os.path.join(locale_folder, 'base.po')
        p = os.path.dirname(dst)
        if not os.path.exists(p):
            os.makedirs(p)
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


def scan_po_file(filepath):

    reading_header_state = True
    header_lines = []
    ENTRIES = []

    with open(filepath, "r", encoding='utf8') as pot:
        text_lines = pot.readlines()

        for line in text_lines:
            if line.startswith("#: "):
                if reading_header_state:
                    reading_header_state = False

                entry = defaultdict(list)
                ENTRIES.append(entry)
                entry['links'].append(line)
                key = 'msgid'
                continue

            if line.startswith("msgstr"):
                key = 'msgstr'

            if reading_header_state:
                header_lines.append(line)
            else:
                entry[key].append(line)

    return header_lines, ENTRIES

def entry_to_string(entry):
    links = ''.join(entry['links']) #usually it contains the one element
    msgid = ''.join(entry['msgid'])
    msgstr = ''.join(entry['msgstr'])
    data = f'{links}{msgid}{msgstr}'
    return data

def find_entry_in_pot(entry, pot_ENTRIES):

    def is_msgid_equal(entry1, entry2):
        l1 = entry1['msgid']
        l2 = entry2['msgid']
        if len(l1) != len(l2):
            return False

        for e1_line, e2_line in zip(l1, l2):
            if e1_line != e2_line:
                return False

        return True

    for pot_entry in pot_ENTRIES:
        if is_msgid_equal(pot_entry, entry):
            return pot_entry

    return None

def sync_po_files(this_folder, keep_old_entries=True):

    locales = get_locales(this_folder)
    locales_folder = os.path.join(this_folder, 'locales')

    pot_filepath = os.path.join(locales_folder, 'base.pot')
    po_filespaths = [os.path.join(path, 'base.po') for path in locales]




    # READING POT FILE
    pot_header_lines, pot_ENTRIES = scan_po_file(pot_filepath)


    # FIXING EVERY PO FILE
    for PO_FP in po_filespaths:
        header_lines, ENTRIES = scan_po_file(PO_FP)

        sync_entries = []
        cur_pot_ENTRIES = pot_ENTRIES.copy()

        counter = defaultdict(int)

        deleted_entries = []

        for entry in ENTRIES:

            pot_entry = find_entry_in_pot(entry, cur_pot_ENTRIES)
            if pot_entry is None:

                if keep_old_entries:
                    sync_entries.append(entry)
                else:
                    # не найдено, значит строка устарела и её надо удалить,
                    # и для этого ничего особо делать не надо, просто надо пропустить эту итерацию
                    counter['deleted'] += 1
                    deleted_entries.append(entry)
                    continue

            else:
                if entry['links'] != pot_entry['links']:
                    counter['updated'] += 1
                    entry['links'] = pot_entry['links'] #обновляем ссылку

                cur_pot_ENTRIES.remove(pot_entry) #удаляем, после цикла в cur_pot_ENTRIES останутся новые записи

                sync_entries.append(entry)

        if cur_pot_ENTRIES:

            # странный способ добавить перенос строки в стройный ряд объектов entry
            sync_entries.append({'links':[], 'msgid':['\n'], 'msgstr':[]})

            #добавляем новые записи всем скопом в конец файла
            sync_entries.extend(cur_pot_ENTRIES)


        # формируем новое содержимое файла
        filedata = ""
        filedata += "".join(pot_header_lines)
        for sync_entry in sync_entries:
            filedata += entry_to_string(sync_entry)

        # записываем
        with open(PO_FP, 'w', encoding='utf8') as result_file:
            result_file.write(filedata)

        print(PO_FP)
        print("\tdeleted entries:", counter['deleted'])
        print("\tupdated entries:", counter['updated'])

        if deleted_entries:
            deleted_po_filepath = os.path.join(os.path.dirname(PO_FP), 'deleted.po')

            filedata = ""

            sync_entries.insert(0, {'links':[], 'msgid':['\n----------------\n'], 'msgstr':[]})

            for deleted_entry in deleted_entries:
                filedata += entry_to_string(deleted_entry)

            with open(deleted_po_filepath, "a+", encoding='utf8') as deleted_file:
                deleted_file.write(filedata)

            print('\tdeleted entries moved to ', deleted_po_filepath)

        print()

def main():
    this_folder = os.path.dirname(__file__)

    os.chdir(this_folder)


    # generate_locales(this_folder)

    # move_pot_to_po(this_folder)

    generate_pot_file(this_folder) # updating main template file

    # sync_po_files(this_folder, keep_old_entries=False) # see CHANGELOG.md for sync_po_files documentation 

    # generate_mo_file(this_folder) # creating compiled locale files


if __name__ == '__main__':
    main()
