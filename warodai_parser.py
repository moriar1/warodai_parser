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

    translation: str  # в т.ч. Замена перевода производным (: ～する, : ～の)
    examples: list[str] = field(default_factory=list)
    derivatives: list[str] = field(default_factory=list)
    idioms: list[str] = field(default_factory=list)


@dataclass
class Section:
    """Несколько рубрик объединённые в секции/группы (разделяются числами с точкой на отдельной строке)."""

    # NOTE: если есть общее пояснение, то оно будет находиться в первой рубрике
    rubrics: list[Rubric] = field(default_factory=list)


@dataclass
class Entry:
    """Карточка/статья с переводом"""

    header: Header
    sections: list[Section] = field(default_factory=list)


@dataclass
class WarodaiDictionary:
    """Основной класс хранящий все карточки/статьи с переводами"""

    entries: list[Entry] = field(default_factory=list)


header_re = re.compile(
    r"^([\w,…･・！ ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?(?: )?〔(.+)〕$"
)
section_num_re = re.compile(r"^\d.$")  # Например: `1.` на отдельной строке
rubric_re = re.compile(r"^\d[(\. )(\) )] ")  # Например:  `1) перевод` или просто `1) `
japanese_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFF◇～…]")  # яп символ вначале

text = Path("warodai.txt").read_text(encoding="utf-16-le")
cards = text.split("\n\n")[1:]  # Разбивка текста на карточки и пропуск лицензии
dictionary_entries: list[Entry] = []

for card in cards:
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

    # Парсинг тела словарной статьи
    for line in lines[1:]:
        # Может быть: либо группа рубрик, либо рубрика с переводами и примерами
        if section_num_re.match(line):
            # Нумерованная группа рубрик 1. 2. и т.п.
            if rubrics:  # не пустая рубрика
                sections.append(Section(rubrics))
            rubrics: list[Rubric] = []
            continue
        line = line.rstrip(";,. ")  # Убираем запятые разделяющие примеры и рубрики

        if japanese_re.match(line):
            # Добавляем пример или идиоматическое выражение (т.к. начинается с японских символов)
            if line.startswith("～"):
                rubric.derivatives.append(line)
            elif line.startswith("◇"):
                rubric.idioms.append(line)
            else:
                rubric.examples.append(line)
        else:
            # Строка содержит начало рубрики (т.е. первевод, а не пример)
            # удаление `1) ` или `1. ` в начале строки
            rubric = Rubric(rubric_re.sub("", line))
            rubrics.append(rubric)

    sections.append(Section(rubrics))
    entry = Entry(header, sections)
    dictionary_entries.append(entry)

# TODO: сохранение в SQLite
warodai = WarodaiDictionary(dictionary_entries)
with Path("warodai_out.json").open("w", encoding="utf-8") as f:
    json.dump(asdict(warodai), f, ensure_ascii=False, indent=2)
