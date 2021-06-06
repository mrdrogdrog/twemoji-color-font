# Based on https://github.com/sapegin/grunt-webfont/blob/master/tasks/engines/fontforge/generate.py

import json
import os
import re
import sys

import fontforge


def create_font_forge_font():
    created_font = fontforge.font()
    created_font.encoding = 'UnicodeFull'
    created_font.copyright = ''
    created_font.design_size = 16
    created_font.em = configuration['fontHeight']
    created_font.descent = configuration['descent']
    created_font.ascent = configuration['fontHeight'] - configuration['descent']
    created_font.fontname = configuration['fontFilename']
    created_font.familyname = configuration['fontFamilyName']
    created_font.fullname = configuration['fontFamilyName']
    if configuration['version']:
        created_font.version = configuration['version']
    if configuration['normalize']:
        created_font.autoWidth(0, 0, configuration['fontHeight'])

    if configuration['addLigatures']:
        created_font.addLookup('liga', 'gsub_ligature', (), (('liga', (('latn', 'dflt'),)),))
        created_font.addLookupSubtable('liga', 'liga')
    return created_font


def create_empty_char(character):
    pen = font.createChar(ord(character), character).glyphPen()
    pen.moveTo((0, 0))


def fix_svg_file(file_path):
    with open(file_path, 'r+') as svg_file:
        svg_file_content = read_svg_content(svg_file)
        write_back_svg_content(svg_file, svg_file_content)


def write_back_svg_content(svg_file, new_content):
    svg_file.seek(0)
    svg_file.truncate()
    svg_file.write(new_content)


def read_svg_content(svg_file):
    svg_file_content = svg_file.read()
    svg_file_content = svg_file_content.replace('<switch>', '').replace('</switch>', '')
    if configuration["normalize"]:
        # Replace the width and the height
        svg_file_content = re.sub(r'(<svg[^>]*)width="[^"]*"([^>]*>)', r'\1\2', svg_file_content)
        svg_file_content = re.sub(r'(<svg[^>]*)height="[^"]*"([^>]*>)', r'\1\2', svg_file_content)
    return svg_file_content


def create_font_character_glyph(character_name, code_point):
    if configuration['addLigatures']:
        name = str(
            character_name)  # Convert Unicode to a regular string because addPosSub doesn't work with Unicode
        for char in name:
            create_empty_char(char)
        glyph = font.createChar(code_point, name)
        glyph.addPosSub('liga', tuple(name))
    else:
        glyph = font.createChar(code_point, str(character_name))
    glyph.correctDirection()
    return glyph


def process_svg_file(file_path, normalize, character_name):
    fix_svg_file(file_path)
    code_point = configuration['codepoints'][character_name]
    glyph = create_font_character_glyph(character_name, code_point)
    glyph.importOutlines(file_path)
    if normalize:
        glyph.left_side_bearing = glyph.right_side_bearing = 0
    else:
        glyph.width = configuration['fontHeight']

    if configuration['round']:
        glyph.round(int(configuration['round']))


def build_font_from_files():
    for dirname, dirnames, filenames in os.walk(configuration['inputDir']):
        for filename in sorted(filenames):
            filename_without_extension, file_extension = os.path.splitext(filename)
            file_path = os.path.join(dirname, filename)

            if file_extension in ['.svg']:
                process_svg_file(file_path, configuration['normalize'], filename_without_extension)


def generate_font_file(font_file_path):
    if configuration['addLigatures']:
        font.generate(font_file_path, flags='opentype')
    else:
        font.generate(font_file_path)


def generate_font_files():
    font_file_path = configuration['dest'] + os.path.sep + configuration['fontFilename']
    if 'ttf' in configuration['types']:
        generate_font_file(font_file_path + '.ttf')
    if 'woff' in configuration['types']:
        generate_font_file(font_file_path + '.woff')
    if 'woff2' in configuration['types']:
        generate_font_file(font_file_path + '.woff2')

    return font_file_path


KERNING = 15
configuration = json.load(sys.stdin)
font = create_font_forge_font()
build_font_from_files()
result_font_file_path = generate_font_files()
print(json.dumps({'file': result_font_file_path}))
