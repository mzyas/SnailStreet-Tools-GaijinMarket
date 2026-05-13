import json
import os
import sys as _sys


def _get_i18n_dir():
    """Return the directory containing i18n JSON files.
    i18n JSON ファイルが含まれるディレクトリを返します。
    返回包含 i18n JSON 文件的目录。

    - PyInstaller bundle:  exe と同じフォルダの i18n/
    - Normal Python:       __file__ のある i18n/
    """
    if getattr(_sys, 'frozen', False):
        return os.path.join(os.path.dirname(_sys.executable), 'i18n')
    else:
        return os.path.dirname(os.path.abspath(__file__))


class LanguageManager:
    _instances = {}

    def __new__(cls, lang="zh_CN"):
        if lang not in cls._instances:
            instance = super().__new__(cls)
            instance.lang = lang
            instance._translations = {}
            instance._load()
            cls._instances[lang] = instance
        return cls._instances[lang]

    def _load(self):
        path = os.path.join(_get_i18n_dir(), f"{self.lang}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
        else:
            self._translations = {}

    def t(self, key: str, default="") -> str:
        keys = key.split(".")
        val = self._translations
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default or key
        return val if isinstance(val, str) else default or key

    def csv_for(self, csv_type="Decoration") -> str:
        lang_to_csv = {
            "zh_CN": f"{csv_type}_zh.csv",
            "en_US": f"{csv_type}_eng.csv",
        }
        return lang_to_csv.get(self.lang, f"{csv_type}_eng.csv")