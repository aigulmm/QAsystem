import re
import json
from pathlib import Path
from difflib import get_close_matches
import pymorphy2


class QuestionHandler:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.patterns = self._compile_patterns()
        self.morph = pymorphy2.MorphAnalyzer()
        self.stop_words = self._load_stop_words()

    def _load_config(self, config_path):
        with open(Path(config_path), 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_stop_words(self):
        return {'как', 'найти', 'для', 'от', 'в', 'с', 'по', 'о', 'и', 'у', 'к', 'не', 'на', 'за', 'из', 'со', 'то',
                'же'}

    def _normalize_text(self, text):
        """Нормализация текста: нижний регистр + удаление стоп-слов"""
        text = text.lower().strip()
        tokens = re.findall(r'\b\w+\b', text)  # Токенизация с учетом сложных слов
        return ' '.join([t for t in tokens if t not in self.stop_words])

    def _lemmatize_focus(self, phrase):
        """Лемматизация фразы с сохранением структуры"""
        tokens = phrase.split()
        lemmas = [self.morph.parse(t)[0].normal_form for t in tokens]
        return ' '.join(lemmas)

    def _compile_patterns(self):
        compiled = []
        for pattern in self.config['question_patterns']:
            for p in pattern.get('patterns', []):
                compiled.append({
                    'type': pattern['type'],
                    'regex': re.compile(p, re.IGNORECASE),
                    'response': pattern['response_templates'],
                    'handler': pattern['handler'],
                    'mode': 'regex'
                })
            for kws in pattern.get('keywords', []):
                compiled.append({
                    'type': pattern['type'],
                    'keywords': [kw.lower() for kw in kws],
                    'response': pattern['response_templates'],
                    'handler': pattern['handler'],
                    'mode': 'keywords'
                })
        return compiled

    def analyze_question(self, question):
        # Нормализация: нижний регистр + удаление стоп-слов
        normalized = self._normalize_text(question)

        # Поиск по regex-шаблонам
        for pattern in self.patterns:
            if pattern['mode'] == 'regex':
                match = pattern['regex'].match(normalized)
                if match:
                    focus = match.group(1).strip()
                    return {
                        'type': pattern['type'],
                        'focus': self._lemmatize_focus(focus),  # Лемматизация фокуса
                        'handler': pattern['handler'],
                        'response_templates': pattern['response'],
                        'raw_focus': focus  # Оригинал для морфологии ответа
                    }

        # Поиск по ключевым словам
        for pattern in self.patterns:
            if pattern['mode'] == 'keywords':
                if all(kw in normalized for kw in pattern['keywords']):
                    focus = self._extract_focus(normalized, pattern['keywords'])
                    return {
                        'type': pattern['type'],
                        'focus': self._lemmatize_focus(focus),
                        'handler': pattern['handler'],
                        'response_templates': pattern['response'],
                        'raw_focus': focus
                    }

        # Нечеткий поиск
        for pattern in self.patterns:
            if pattern['mode'] == 'keywords':
                joined_kw = " ".join(pattern['keywords'])
                if get_close_matches(normalized, [joined_kw], n=1, cutoff=0.6):
                    focus = self._extract_focus(normalized, pattern['keywords'])
                    return {
                        'type': pattern['type'],
                        'focus': self._lemmatize_focus(focus),
                        'handler': pattern['handler'],
                        'response_templates': pattern['response'],
                        'raw_focus': focus
                    }

        return {
            'type': 'unknown',
            'response': self.config['system_settings']['fallback_response']
        }

    def _extract_focus(self, question, keywords):
        tokens = question.split()
        filtered = [word for word in tokens if word not in keywords]
        return " ".join(filtered).strip()