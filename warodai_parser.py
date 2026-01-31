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


# NOTE: иногда перед началом рубрик (или групп рубрик) может быть общий поясняющий текст,
# как например в карточке 004-55-64, а иногда этот текст сам является
# переводом (если в карточке нет рубрик). Этот момент реализован так:
# у каждой карточки всегда есть первая группа (секция) которая содержит,
# упомянутое ранее "общее уточнение", если такавого нет, то эта секция будет пустой.
# TODO: можно сделать отдельное поле в `Entry`, которое содержит общее уточнение,
# если в карточке затем идут секции или группы секций.
@dataclass
class Section:
    """Несколько рубрик объединённые в секции/группы (разделяются числами с точкой на отдельной строке)."""

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


header_re = re.compile(r"^([\w,…･・！ ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?〔(.+)〕$")
section_num_re = re.compile(r"^\d$")  # Например: `1` (точка опускается из-за rstrip())
rubric_re = re.compile(r"^\d[(\. )(\) )] ")  # Например:  `1) перевод` или просто `1) `
japanese_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFF]")  # яп. символы вначале строки

text = Path("test_excerpt.txt").read_text(encoding="utf-16-le")
status = 0
dictionary_entries: list[Entry] = []

for card in text.split("\n\n")[1:]:  # Разбивка текста на карточки и пропуск лицензии
    sections: list[Section] = []
    rubrics: list[Rubric] = []
    rubric = Rubric("")
    for line in card.splitlines():
        line = line.rstrip(";,. ")  # Убираем запятые разделяющие примеры и рубрики

        # Заголовок всегда один
        if status == 0:
            match = header_re.match(line)
            kana, kanji, transcription, corpus, id = match.groups()
            header = Header(kana, kanji, transcription, corpus, id)
            status = 1
            continue

        # Дальше может быть: либо группа рубрик, либо рубрика с переводами и примерами
        elif status == 1:
            if section_num_re.match(line):
                # Группа рубрик
                sections.append(Section(rubrics))
                rubrics: list[Rubric] = []
                continue

            if japanese_re.match(line):
                # Если начинается с японских символов
                # То есть содержит пример или идиоматическое выражение
                rubric.examples.append(line)
            else:
                # Строка содержит перевод (начало рубрики)
                # rubric_re.sub("", line) удаляет "1) ", "1. ", но не убриает а) б)
                rubric = Rubric(rubric_re.sub("", line))
                rubrics.append(rubric)

    sections.append(Section(rubrics))
    dentry = Entry(header, sections)
    dictionary_entries.append(dentry)
    status = 0

for entry in dictionary_entries:
    print(f"Слово: {entry.header.kana}")
    for i, section in enumerate(entry.sections):
        print(f"Секция: {i}.")
        for j, rubric in enumerate(section.rubrics, start=1):
            print(f" Перевод {j}: {rubric.translation}")
            for k, example in enumerate(rubric.examples, start=1):
                print(f"  Пример {k}. {example}")
    print()
