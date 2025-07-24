import json

FILENAME = 'inspections.json'  # Можно заменить на нужный файл

with open(FILENAME, 'r', encoding='utf-8') as f:
    data = json.load(f)

if not isinstance(data, list):
    print(f"[ERROR] Ожидался список в корне файла, а не {type(data)}")
    exit(1)

none_count = 0
not_dict_count = 0
ok_count = 0
examples = []

for i, item in enumerate(data):
    if item is None:
        none_count += 1
        if len(examples) < 5:
            examples.append((i, item))
    elif not isinstance(item, dict):
        not_dict_count += 1
        if len(examples) < 5:
            examples.append((i, item))
    else:
        ok_count += 1

print(f"Всего элементов: {len(data)}")
print(f"Корректных словарей: {ok_count}")
print(f"None: {none_count}")
print(f"Не словари (например, список, строка, число): {not_dict_count}")

if examples:
    print("\nПримеры невалидных элементов:")
    for idx, val in examples:
        print(f"  [{idx}] {val!r}")
else:
    print("Все элементы — словари.") 