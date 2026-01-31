import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Header:
    """Заголовок карточки/статьи с первеводом"""

    kana: str
    kanji: str | None
    transcription: str
    corpus: str | None
    id: str


@dataclass
class Rubric:
    """Рубрика с переводами, примерами, идиомами и т.д."""

    translation: str
    examples: list[str] = field(default_factory=list)  # в т.ч. идиомы


@dataclass
class Section:
    """Несколько рубрик объединённые в секции/группы (разделяются числами с точкой на отдельной строке)."""

    rubrics: list[Rubric] = field(default_factory=list)


@dataclass
class Entry:
    """Карточка/статья с переводом"""

    header: Header
    sections: list[Section] = field(default_factory=list)
    common_note: str | None = None


@dataclass
class WarodaiDictionary:
    """Основной класс хранящий все карточки/статьи с переводами"""

    entries: list[Entry] = field(default_factory=list)


header_re = re.compile(r"^([\w,…･・！ ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?〔(.+)〕$")
section_num_re = re.compile(r"^\d$")  # Например: `1` (точка опускается из-за rstrip())
rubric_re = re.compile(r"^\d[(\. )(\) )] ")  # Например:  `1) перевод` или просто `1) `
japanese_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFF]")  # яп. символы вначале строки

text = Path("test_excerpt.txt").read_text(encoding="utf-16-le")
cards = text.split("\n\n")[1:]  # Разбивка текста на карточки и пропуск лицензии
dictionary_entries: list[Entry] = []

for card in cards:
    numbered_rubrics_exist = False
    many_rubrics = False  # наличие нескольких рубрик, при отсутствии секций
    sections_exist = False
    sections: list[Section] = []
    rubrics: list[Rubric] = []
    rubric = Rubric("")

    lines = card.splitlines()

    # Заполнение полей заголовка (структуры Header) карточки
    match = header_re.match(lines[0])
    kana, kanji, transcription, corpus, id = match.groups()
    header = Header(kana, kanji, transcription, corpus, id)

    for line in lines[1:]:
        line = line.rstrip(";,. ")  # Убираем запятые разделяющие примеры и рубрики

        # Может быть: либо группа рубрик, либо рубрика с переводами и примерами
        if section_num_re.match(line):
            # Нумерованная группа рубрик 1. 2. и т.п.
            sections_exist = True
            if rubrics:  # не пустая рубрика
                sections.append(Section(rubrics))
            rubrics: list[Rubric] = []
            continue

        if japanese_re.match(line):
            # Добавляем пример или идиоматическое выражение (т.к. начинается с японских символов)
            rubric.examples.append(line)
        else:
            # Строка содержит начало рубрики (т.е. первевод, а не пример)

            # Для заполнения поля (Entry.common_note)
            if rubric_re.match(line):
                numbered_rubrics_exist = True

            # rubric_re.sub("", line) удаляет `1) ` или `1. ` в начале строки
            rubric = Rubric(rubric_re.sub("", line))
            rubrics.append(rubric)

        # Для заполнения поля (Entry.common_note)
        if numbered_rubrics_exist and len(rubrics) > 1 and not sections_exist:
            many_rubrics = True

    sections.append(Section(rubrics))
    entry = Entry(header, sections)

    # Переносим "общее уточенение" из первой рубрики в entry
    if len(sections) > 1 and not numbered_rubrics_exist or many_rubrics:
        entry.common_note = sections[0].rubrics[0].translation
        sections[0].rubrics = sections[0].rubrics[1:]
    dictionary_entries.append(entry)


for entry in dictionary_entries:
    print(f"Слово: {entry.header.kana}")
    for i, section in enumerate(entry.sections, start=1):
        print(f"Секция: {i}.")
        for j, rubric in enumerate(section.rubrics, start=1):
            print(f" Перевод {j}: {rubric.translation}")
            for k, example in enumerate(rubric.examples, start=1):
                print(f"  Пример {k}. {example}")
    print()
