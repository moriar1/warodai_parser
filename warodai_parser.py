import re
from dataclasses import dataclass, field
from pathlib import Path


# Заголовок карточки/статьи с первеводом
@dataclass
class Header:
    kana: str
    kanji: str | None
    transcription: str
    corpus: str | None
    id: str


# в README Warodai называется рубрикой
@dataclass
class Meaning:
    translation: str
    examples: list[str] = field(default_factory=list)


# Несколько рубрик объединённые в секции/группы (разделяются числами с точкой).
# NOTE: иногда перед началом рубрик (или групп рубрик) может быть общий поясняющий текст,
# как например в карточке 004-55-64, а иногда этот текст сам является
# переводом (если в карточке нет рубрик). Этот момент реализован так:
# у каждой карточки всегда есть первая группа (секция) которая содержит,
# упомянутое ранее "общее уточнение", если такавого нет, то эта секция будет пустой.
# TODO: можно сделать отдельное поле в `Entry`, которое содержит общее уточнение,
# если в карточке затем идут секции или группы секций.
@dataclass
class Section:
    meanings: list[Meaning] = field(default_factory=list)


# Карточка/статья с переводом
@dataclass
class DictionaryEntry:
    header: Header
    sections: list[Section] = field(default_factory=list)


# Основной класс хранящий все карточки/статьи с переводами
@dataclass
class WarodaiDictionary:
    entries: list[DictionaryEntry] = field(default_factory=list)


text = Path("test_excerpt.txt").read_text(encoding="utf-16-le")
header_re = re.compile(r"^([\w,…･・！ ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?〔(.+)〕$")
section_num_re = re.compile(r"^\d$")  # Например: `1` (точка опускается из-за rstrip())
rubric_re = re.compile(r"^\d[(\. )(\) )] ")  # Например:  `1) перевод` или просто `1) `
japanese_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFF]")  # яп. символы вначале строки

status = 0
dictionary_entries: list[DictionaryEntry] = []

for card in text.split("\n\n")[1:]:  # Пропуск лицензии
    sections: list[Section] = []
    meanings: list[Meaning] = []
    meaning = Meaning("")
    for line in card.splitlines():
        line = line.rstrip(";,. ")  # Убираем запятые разделяющие примеры и рубрики

        if status == 0:
            match = header_re.match(line)
            kana, kanji, transcription, corpus, id = match.groups()
            header = Header(kana, kanji, transcription, corpus, id)
            status = 1
            continue

        elif status == 1:
            if section_num_re.match(line):
                sections.append(Section(meanings))
                meanings: list[Meaning] = []
                continue

            if japanese_re.match(line):
                # Если начинается с японских символов
                # То есть содержит пример или идиоматическое выражение
                meaning.examples.append(line)
            else:
                # Строка содержит перевод (начало рубрики)
                # rubric_re.sub("", line) удаляет "1) ", "1. ", но не убриает а) б)
                meaning = Meaning(rubric_re.sub("", line))
                meanings.append(meaning)

    sections.append(Section(meanings))
    dentry = DictionaryEntry(header, sections)
    dictionary_entries.append(dentry)
    status = 0

for entry in dictionary_entries:
    print(f"Слово: {entry.header.kana}")
    for i, section in enumerate(entry.sections):
        print(f"Секция: {i}.")
        for j, meaning in enumerate(section.meanings, start=1):
            print(f" Перевод {j}: {meaning.translation}")
            for k, example in enumerate(meaning.examples, start=1):
                print(f"  Пример {k}. {example}")
    print()
