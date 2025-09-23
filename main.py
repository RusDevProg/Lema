import bz2
import re


# Загрузка словаря из архива
def load_dict_opcorpora_txt(path):
    word_dict = {}
    with bz2.open(path, mode="rt", encoding="utf-8") as f:
        current_lemma = None
        current_pos = None
        block_words = []

        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.isdigit():
                if block_words and current_lemma:
                    for w in block_words:
                        word_dict[w.lower()] = (current_lemma.lower(), normalize_pos(current_pos))
                current_lemma = None
                current_pos = None
                block_words = []
                continue

            parts = line.split()
            if len(parts) >= 2:
                word, pos = parts[0], parts[1]
                if current_lemma is None:
                    current_lemma = word
                    current_pos = pos
                block_words.append(word)

        if block_words and current_lemma:
            for w in block_words:
                word_dict[w.lower()] = (current_lemma.lower(), normalize_pos(current_pos))

    return word_dict


# Приведение POS к базовым категориям
def normalize_pos(pos):
    if pos.startswith("N"):  # существительное
        return "S"
    elif pos.startswith("A"):  # прилагательное
        return "A"
    elif pos.startswith("V"):  # глагол
        return "V"
    elif pos.startswith("ADV"): # наречие
        return "ADV"
    elif pos.startswith("PR"): # местоимение
        return "PR"
    elif pos.startswith("CONJ"): # союз
        return "CONJ"
    else:
        return "UNK"  # неизвестный


# Нормализация токена
def normalize_token(token):
    return token.lower().replace("ё", "е")


# Уточнение POS для служебных слов и наречий
def refine_pos(token, lemma, pos):
    lower = token.lower()
    # Союзы
    if lower in ("и","а","но","да","или","ли"):
        return lemma, "CONJ"
    # Предлоги
    if lower in ("не","в","с","за","от","из","по","о","об","у","для","над","под","при","через"):
        return lemma, "PR"
    # Наречия
    if lower in ("уже","чуть","далеко","никуда","здесь","там","везде"):
        return lemma, "ADV"
    # Частицы
    if lower in ("не","ли","же","ль","бы"):
        return lemma, "PART"
    return lemma, pos


# Угадывание POS для неизвестных слов
def guess_pos(word):
    if word.endswith("ть") or word.endswith("ться"):
        return "V"
    elif word.endswith(("ый","ий","ой","ая","ое","ые")):
        return "A"
    elif word.endswith(("но","ли","же","ль")):
        return "ADV"
    else:
        return "NI"


# Обработка предложения
def process_sentence(sentence, word_dict):
    tokens = re.findall(r"[А-Яа-яЁёA-Za-z]+", sentence)
    result_tokens = []

    for token in tokens:
        norm = normalize_token(token)
        if norm in word_dict:
            lemma, pos = word_dict[norm]
        else:
            # Заглавная буква
            if token[0].isupper():
                lemma, pos = token, "S"
            else:
                lemma, pos = norm, guess_pos(norm)
        # уточнение POS
        lemma, pos = refine_pos(token, lemma, pos)
        result_tokens.append(f"{token}{{{lemma}={pos}}}")

    return " ".join(result_tokens)


def main():
    dict_path = "dict.opcorpora.txt.bz2"
    print("Загружаем словарь...")
    word_dict = load_dict_opcorpora_txt(dict_path)
    print(f"Словарь загружен: {len(word_dict)} словоформ")

    text = """Стала стабильнее экономическая и политическая обстановка, предприятия вывели из тени зарплаты сотрудников.
Все Гришины одноклассники уже побывали за границей, он был чуть ли не единственным, кого не вывозили никуда дальше Красной Пахры."""

    sentences = text.split("\n")
    for sent in sentences:
        print(process_sentence(sent, word_dict))

if __name__ == "__main__":
    main()