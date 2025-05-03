import pymorphy2
import logging
from string import Formatter


class ResponseBuilder:
    def __init__(self, config):
        self.morph = pymorphy2.MorphAnalyzer()
        self.config = config

    def build_response(self, question_type, focus, results):
        if not results:
            return self._get_default_response(question_type, focus)

        templates = self._get_templates_for_type(question_type)
        if not templates:
            return self.config['system_settings']['fallback_response']

        if isinstance(results, list):
            return self._build_list_response(templates, focus, results)
        else:
            return self._build_single_response(templates, focus, results)

    def _get_templates_for_type(self, question_type):
        for pattern in self.config['question_patterns']:
            if pattern['type'] == question_type:
                return pattern['response_templates']
        return None

    def _get_default_response(self, question_type, focus):
        templates = self._get_templates_for_type(question_type)
        if templates and 'default' in templates:
            return templates['default'].format(
                focus_nom=self._inflect(focus, 'nomn'),
                focus_gen=self._inflect(focus, 'gent')
            )
        return self.config['system_settings']['fallback_response']

    def _build_list_response(self, templates, focus, results):
        focus_gen = self._inflect(focus, 'gent')
        items = [self._format_item(item) for item in results[:self.config['grammar_settings']['max_items']]]
        items_str = self._join_items(items)

        if len(results) > 1 and 'multiple' in templates:
            template = templates['multiple']
        else:
            template = templates['single']

        return template.format(
            focus_nom=self._inflect(focus, 'nomn'),
            focus_gen=focus_gen,
            items=items_str,
            item=items[0] if items else ''
        )

    def _build_single_response(self, templates, focus, results):
        if 'single' not in templates:
            return self.config['system_settings']['fallback_response']

        template = templates['single']

        formatter = Formatter()
        format_keys = [item[1] for item in formatter.parse(template) if item[1]]

        formatted_data = {
            'method_name': focus,
            **results
        }
        filtered_data = {
            k: v for k, v in formatted_data.items()
            if k in format_keys
        }

        try:
            return template.format(**filtered_data)
        except KeyError as e:
            logging.error(f"Missing key in template: {e}")
            return self.config['system_settings']['fallback_response']

    def _format_item(self, item):
        if item.get('comment'):
            return f"{item['label']} ({item['comment']})"
        return item['label']

    def _join_items(self, items):
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " и " + items[-1]

    def _inflect(self, text, case):
        words = text.split()
        return ' '.join([self.morph.parse(w)[0].inflect({case}).word for w in words])