from pathlib import Path
import re

text = Path("test_excerpt.txt").read_text(encoding="utf-16-le")
header_re = re.compile(r"^([\w, ]+)(?:【(.+)】)?\((.+)\)(?: \[(.+)\])?〔(.+)〕$")
section_num_re = re.compile(r"\d\.")

print("Кана;Кандзи;Транскрипция;Код корпуса;Идентификатор")
print("Перевод\n")

status = 0
for card in text.split("\n\n")[1:]:  # Пропуск лицензии
    for line in card.splitlines():
        if status == 0:
            match = header_re.match(line)
            kana, kanji, transcription, corpus, id = match.groups()

            print(f"{kana};{kanji or ''};{transcription};{corpus or ''};{id}")
            status = 1
            continue
        elif status == 1:  # Подготовка к парсингу перевода
            print(line)
    print()
    status = 0
