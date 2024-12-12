"""Generate translations from LANG named tuples."""

import argparse
import importlib
import json
import re
from pathlib import Path
from typing import Union, cast

from hdate.htables import DESC, LANG


def get_lang_value(item: LANG, lang: str) -> str:
    """
    Return the value of a given LANG object in a given language.

    item: LANG object
    lang: str, the language to get the value in

    Returns:
        str, the value in the given language. If the value
        is a DESC object, the long description is returned.
    """
    value: Union[str, DESC] = getattr(item, lang)
    if isinstance(value, DESC):
        value = cast(str, value.long)
    return value


def main() -> None:
    """
    CLI for generating translations from LANG named tuples.

    CLI takes a single argument in the format "module_name:object_name" and
    generates a translation dictionary for each of the LANGs with the given
    object_name as the key.

    The translation dictionary is written to a JSON file in the "translations"
    directory under the module's path.

    The translation dictionary is generated by taking the english attribute of
    each item in the tuple, converting it to lower case and removing any non
    alpha characters. The resulting string is used as the key in the
    translation dictionary.

    The value for the key is the value of the attribute of the item with the
    name of the LANG.

    Example:
        python utils/translations.py hdate.htables:HOLIDAY

    Will generate a translation dictionary for each of the LANGs with the
    HOLIDAY tuple as the key.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("object_name", type=str, help="module_name:object_name")
    args = parser.parse_args()

    module, obj = args.object_name.split(":")

    # Load tuple into namespace using importlib
    try:
        _module = importlib.import_module(module)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(f"Module {module} not found") from exc

    module_file = cast(str, _module.__file__)
    _obj = getattr(_module, obj)

    # Generate translation dictionary
    translations = {}
    for key in LANG._fields:
        translation_file = Path(module_file).parent / "translations" / f"{key[:2]}.json"
        if translation_file.exists():
            translations = json.loads(translation_file.read_text(encoding="utf-8"))

        translations[obj.lower()] = {}
        for item in _obj:
            if not isinstance(item, LANG) and isinstance(item, tuple):
                item = [field for field in item if isinstance(field, LANG)][0]
            if isinstance(_obj, dict):
                item_key = item
                value = get_lang_value(_obj[item], key)
            else:
                _tmp_key = get_lang_value(item, "english").lower().replace(" ", "_")
                item_key = re.sub(r"[^a-z_]", "", _tmp_key)
                value = get_lang_value(item, key)
            translations[obj.lower()][item_key] = value

        translation_file.write_text(
            json.dumps(translations, ensure_ascii=False, indent=4), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
