import re
import json
from pathlib import Path
from difflib import get_close_matches


class QuestionHandler:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.patterns = self._compile_patterns()

    def _load_config(self, config_path):
        with open(Path(config_path), 'r', encoding='utf-8') as f:
            return json.load(f)

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
        question = question.lower().strip()

        for pattern in self.patterns:
            if pattern['mode'] == 'regex':
                match = pattern['regex'].match(question)
                if match:
                    return {
                        'type': pattern['type'],
                        'focus': match.group(1).strip(),
                        'handler': pattern['handler'],
                        'response_templates': pattern['response']
                    }

        for pattern in self.patterns:
            if pattern['mode'] == 'keywords':
                if all(kw in question for kw in pattern['keywords']):
                    focus = self._extract_focus(question, pattern['keywords'])
                    return {
                        'type': pattern['type'],
                        'focus': focus,
                        'handler': pattern['handler'],
                        'response_templates': pattern['response']
                    }

        for pattern in self.patterns:
            if pattern['mode'] == 'keywords':
                joined_kw = " ".join(pattern['keywords'])
                if get_close_matches(question, [joined_kw], n=1, cutoff=0.6):
                    focus = self._extract_focus(question, pattern['keywords'])
                    return {
                        'type': pattern['type'],
                        'focus': focus,
                        'handler': pattern['handler'],
                        'response_templates': pattern['response']
                    }

        return {
            'type': 'unknown',
            'response': self.config['system_settings']['fallback_response']
        }

    def _extract_focus(self, question, keywords):
        tokens = question.split()
        filtered = [word for word in tokens if word not in keywords]
        return " ".join(filtered).strip()