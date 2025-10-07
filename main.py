import re
import bz2
import os
from collections import defaultdict

# Настройки служебных слов для переопределения
CONJ_SET = {"и", "а", "но", "да", "или", "чтобы"}
PREP_SET = {"в", "с", "за", "от", "из", "по", "о", "об", "у", "для", "над", "под", "при", "через", "без", "до", "после"}
PART_SET = {"не", "же", "ли", "ль", "бы"}
ADV_SET = {"уже", "чуть", "далее", "дольше", "далеко", "никуда", "здесь", "там", "везде", "почти"}
PRONOUN_LEMMAS = {
    "я": "я", "ты": "ты", "он": "он", "она": "она", "мы": "мы", "вы": "вы", "они": "они",
    "все": "весь", "всё": "весь", "кого": "кто", "кто": "кто", "него": "он", "его": "он",
    "ее": "она", "её": "она"
}

# допустимые POS-коды OpenCorpora
POS_SET = {
    "NOUN","ADJF","ADJS","COMP","VERB","INFN","PRTF","PRTS","GRND",
    "ADVB","PREP","CONJ","PRCL","INTJ","NPRO","NUMR","PRED"
}

# Сопоставление OpenCorpora - упрощённые теги
POS_MAP = {
    "NOUN": "S",
    "ADJF": "A", "ADJS": "A",
    "COMP": "ADV",
    "VERB": "V", "INFN": "V", "PRTF": "V", "PRTS": "V", "GRND": "V",
    "ADVB": "ADV",
    "PREP": "PR",
    "CONJ": "CONJ",
    "PRCL": "PART",
    "INTJ": "INTJ",
    "NPRO": "NI",
    "NUMR": "NUM",
    "PRED": "PRED"
}

# нормализация
def norm(s):
    return s.lower().replace("ё", "е")

# эвристика для неизвестных слов
def guess_pos_by_ending(word):
    if word.endswith(("ться", "ть")):
        return "V"
    if word.endswith(("ого","ему","ая","ые","ые","ый","ий","ое","ая","яя")):
        return "A"
    if word.endswith(("но","ли","же","ль")):
        return "ADV"
    return "NI"

# Загрузка словаря OpenCorpora
def load_opencorpora_dict(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    opener = bz2.open if path.endswith(".bz2") else open
    mapping = defaultdict(list)
    with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or "\t" not in line:
                continue
            surface, info = line.split("\t", 1)
            surface_n = norm(surface)
            parts = info.split()
            pos_raw = None
            pos_index = None
            for i, p in enumerate(parts):
                candidate = p.split(",")[0].upper()
                if candidate in POS_SET:
                    pos_raw = candidate
                    pos_index = i
                    break
            if pos_raw:
                lemma = " ".join(parts[:pos_index]).strip()
            else:
                lemma = parts[0]
            lemma_n = norm(lemma)
            simple_pos = POS_MAP.get(pos_raw, "UNK") if pos_raw else "UNK"
            mapping[surface_n].append((lemma_n, simple_pos))
    return mapping

# Анализ одного предложения
def analyze_sentence(sentence, mapping):
    tokens = re.findall(r"[А-Яа-яЁёA-Za-z]+", sentence)
    out = []
    for token in tokens:
        token_norm = norm(token)
        analyses = mapping.get(token_norm)
        # правила для служебных слов
        if token_norm in CONJ_SET:
            out.append(f"{token}{{{token_norm}=CONJ}}")
            continue
        if token_norm in PREP_SET:
            out.append(f"{token}{{{token_norm}=PR}}")
            continue
        if token_norm in PART_SET:
            out.append(f"{token}{{{token_norm}=PART}}")
            continue
        if token_norm in ADV_SET:
            out.append(f"{token}{{{token_norm}=ADV}}")
            continue
        if token_norm in PRONOUN_LEMMAS:
            out.append(f"{token}{{{PRONOUN_LEMMAS[token_norm]}=NI}}")
            continue
        if analyses:
            lemmas = {lem for lem, pos in analyses}
            poses = {pos for lem, pos in analyses if pos != "UNK"}
            if not poses:
                poses = {guess_pos_by_ending(token_norm)}
            if len(poses) > 1:
                pos_str = "/".join(sorted(poses)) + "=AMB"
            else:
                pos_str = next(iter(poses))
            lemma_str = next(iter(lemmas))
            out.append(f"{token}{{{lemma_str}={pos_str}}}")
        else:
            guessed = guess_pos_by_ending(token_norm)
            out.append(f"{token}{{{token_norm}={guessed}}}")
    return " ".join(out)

# Прогон списка предложений
def analyze_texts(texts, mapping):
    for i, sent in enumerate(texts, 1):
        print(f"Предложение {i}:")
        print(analyze_sentence(sent, mapping))
        print()

if __name__ == "__main__":
    dict_path = r"C:\Users\Руслан\PycharmProjects\Lematizator\dict.opcorpora.txt.bz2"
    print("Загрузка словаря...")
    mapping = load_opencorpora_dict(dict_path)
    print(f"Словарь успешно загружен: ключей = {len(mapping)}\n")

    texts = [
        "Стала стабильнее экономическая и политическая обстановка, предприятия вывели из тени зарплаты сотрудников.",
        "Все Гришины одноклассники уже побывали за границей, он был чуть ли не единственным, кого не вывозили никуда дальше Красной Пахры.",
        "Я люблю русскую печь и печь пироги"
    ]
    analyze_texts(texts, mapping)