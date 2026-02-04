import sys
import re
import json
from pathlib import Path
from dataclasses import asdict, dataclass, field


@dataclass
class Header:
    """Заголовок карточки/статьи с первеводом"""

    kana: list[str]
    kanji: list[str] | None
    transcription: list[str]
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


header_re = re.compile(
    r"^([\w,…･・！ ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?(?: )?〔(.+)〕$"
)
section_num_re = re.compile(r"^\d$")  # Например: `1` (точка опускается из-за rstrip())
rubric_re = re.compile(r"^\d[(\. )(\) )] ")  # Например:  `1) перевод` или просто `1) `
japanese_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFF]")  # яп. символы вначале строки

text = Path("warodai.txt").read_text(encoding="utf-16-le")
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

    # Заполнение полей заголовка (структуры Header)
    match = header_re.match(lines[0])
    # Иногда встречаются лишние пробелы и пр. между полями заголовка
    if match is None:
        print(f"Не удалось разорбрать заголовок: {lines[0]}", file=sys.stderr)
        continue
    kana, kanji, transcription, corpus, id = match.groups()
    # Создание списков из элементов разделённых запятыми и точками
    if kanji:
        kanji = [k.strip() for k in re.split(r"[,･・\s]", kanji) if k.strip()]
    kana = [k.strip() for k in re.split(r"[,･・\s]", kana) if k.strip()]
    transcription = [t.strip() for t in re.split(r"[,\s]", transcription) if t.strip()]
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

# TODO: сохранение в SQLite
warodai = WarodaiDictionary(dictionary_entries)
with Path("warodai_out.json").open("w", encoding="utf-8") as f:
    json.dump(asdict(warodai), f, ensure_ascii=False, indent=2)
