import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Header:
    kana: str
    kanji: str | None
    transcription: str
    corpus: str | None
    id: str


@dataclass
class Meaning:  # в README Warodai называется рубрикой
    translation: str
    examples: list[str] = field(default_factory=list)


@dataclass
class Section:  # Несколько рубрик объединённые в группы (разделяются числами с точкой)
    meanings: list[Meaning] = field(default_factory=list)


@dataclass
class DictionaryEntry:
    header: Header
    sections: list[Section] = field(default_factory=list)
    # TODO:
    # Иногда перед началом рубрик (или группы рубрик) в самом начале может быть
    # отдельный перевод (или пояснение) несвязанный ни с одной рубрикой (пример: 002-46-63)
    # Добавить либо поле main_translation: str|None в `DictionaryEntry`
    # либо добавить is_main_translation: bool в каждом `Meaning`


text = Path("test_excerpt.txt").read_text(encoding="utf-16-le")
header_re = re.compile(r"^([\w, ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?〔(.+)〕$")
section_num_re = re.compile(r"^\d$")  # Например: `1` (точка опускается из-за rstrip())
rubric_re = re.compile(r"^\d[(\. )(\) )] ")  # Например:  `1) перевод` или просто `1) `
japanese_re = re.compile(r"^[\u3040-\u30FF\u4E00-\u9FFF]")  # яп. символы вначале строки

status = 0
dictionary_entries: list[DictionaryEntry] = []

for card in text.split("\n\n")[1:]:  # Пропуск лицензии
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
            # TODO: parse Sections
            if section_num_re.match(line):
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

    sections = [Section(meanings)]
    dentry = DictionaryEntry(header, sections)
    dictionary_entries.append(dentry)
    status = 0

for entry in dictionary_entries:
    print(f"Слово: {entry.header.kana}")
    # TODO: print("основной перевод (если есть, см todo ранее):")
    for section in entry.sections:
        for j, meaning in enumerate(section.meanings, start=1):
            print(f" Перевод {j}: {meaning.translation}")
            for k, example in enumerate(meaning.examples, start=1):
                print(f"  Пример {k}. {example}")
    print()
