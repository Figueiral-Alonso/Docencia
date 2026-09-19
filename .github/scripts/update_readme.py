"""Genera el indice de materiales a partir de las carpetas de cada curso."""
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict
import argparse
import re

START = '<!-- materiales:inicio -->'
END = '<!-- materiales:fin -->'
INTRO = '# Docencia\n\nMateriales de clase de **Erik Figueiral Alonso**.\n\n'
FORMATS = {'.pdf': 'PDF', '.pptx': 'PowerPoint', '.ppt': 'PowerPoint',
           '.docx': 'Word', '.xlsx': 'Excel', '.zip': 'ZIP'}


def sort_key(path):
    return [int(x) if x.isdigit() else x.casefold()
            for x in re.split(r'(\d+)', path.name)]


def escape(text):
    for char in ('\\', '`', '*', '_', '[', ']', '<', '>'):
        text = text.replace(char, '\\' + char)
    return text.replace('\n', ' ')


def materials(folder):
    return [p for p in folder.rglob('*') if p.is_file() and not p.is_symlink()
            and not any(part.startswith('.') for part in p.relative_to(folder).parts)
            and p.name.casefold() not in ('readme.md', 'thumbs.db')]


def section(folder, root, level):
    lines = []
    files = [p for p in folder.iterdir() if p.is_file() and not p.is_symlink()
             and not p.name.startswith('.') and p.name.casefold() not in ('readme.md', 'thumbs.db')]
    groups = defaultdict(list)
    for path in sorted(files, key=sort_key):
        groups[path.stem].append(path)
    for stem, paths in groups.items():
        title = 'Presentación' if len(groups) == 1 and all(p.suffix.lower() in ('.pdf', '.pptx', '.ppt') for p in paths) else stem.replace('_', ' ')
        links = [f'[{FORMATS.get(p.suffix.lower(), p.suffix.lstrip(".").upper() or "Archivo")}]({quote(p.relative_to(root).as_posix(), safe="/")})'
                 for p in sorted(paths, key=lambda p: (p.suffix.lower() != '.pdf', p.name.casefold()))]
        lines += [f'- {escape(title)}: ' + ' · '.join(links)]
    if groups:
        lines.append('')
    for child in sorted(folder.iterdir(), key=sort_key):
        if not child.is_dir() or child.is_symlink() or child.name.startswith('.') or not materials(child):
            continue
        title = 'LAB1 — Introducción a Prolog' if child.name == 'LAB1' and folder.name == 'Lógica Computacional' else child.name
        lines += ['#' * min(level, 6) + ' ' + escape(title), '']
        lines += section(child, root, level + 1)
    return lines


def render(root):
    lines = []
    courses = [p for p in root.iterdir() if p.is_dir() and not p.is_symlink()
               and re.fullmatch(r'\d{2}(?:\d{2})?', p.name) and materials(p)]
    for course in sorted(courses, key=lambda p: int(p.name), reverse=True):
        lines += [f'## Curso {course.name}', ''] + section(course, root, 3)
    return '\n'.join(lines).strip() or 'Todavía no hay materiales publicados.'


def organize_ri(root):
    """Migra solo los dos documentos originales de P1; nunca sobrescribe."""
    origin = root / '26' / 'Recuperación de Información'
    target = origin / 'P1- Práctica 1. Adquisición y procesamiento de información textual'
    for ext in ('.pdf', '.pptx'):
        old = origin / ('practica_1_teoria_18_septiembre_v10' + ext)
        new = target / old.name
        if old.exists():
            if new.exists():
                raise FileExistsError(f'El destino ya existe: {new}')
            target.mkdir(parents=True, exist_ok=True)
            old.rename(new)


def update(root):
    readme = root / 'README.md'
    old = readme.read_text(encoding='utf-8-sig') if readme.exists() else ''
    block = START + '\n\n' + render(root) + '\n\n' + END
    if START in old and END in old:
        before, rest = old.split(START, 1)
        _, after = rest.split(END, 1)
        new = before + block + after
    else:
        new = INTRO + block + '\n'
    if new != old:
        readme.write_text(new, encoding='utf-8', newline='\n')
    return new


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--organize-ri', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.organize_ri:
        organize_ri(root)
    update(root)
