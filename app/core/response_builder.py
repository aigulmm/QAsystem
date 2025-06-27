import logging
import pymorphy2


class ResponseBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.morph = pymorphy2.MorphAnalyzer()
        self.logger.info("ResponseBuilder initialized")

    def build_response(self, handler_data, ontology_data):
        # Обработка случая, когда данные не найдены
        if ontology_data is None or (isinstance(ontology_data, list) and not ontology_data):
            default_template = handler_data['response_templates'].get('default')
        if default_template:
            return self._apply_morphology(default_template, handler_data)
        return "Информация не найдена"

        # Определение шаблона ответа
        templates = handler_data['response_templates']
        response_template = templates.get('default', "{result}")


        handler_type = handler_data['handler']


        if handler_type == 'get_algorithm_steps' and isinstance(ontology_data, list):
            if 'steps' in templates:
                steps = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(ontology_data)])
                return self._apply_morphology(
                    templates['steps'],
                    handler_data,
                    {'steps': steps}
                )


        if isinstance(ontology_data, list):
            if len(ontology_data) == 1 and 'single' in templates:
                response_template = templates['single']
                ontology_data = ontology_data[0]
            elif len(ontology_data) > 1 and 'multiple' in templates:
                response_template = templates['multiple']
                ontology_data = ", ".join(ontology_data)

        # Сборка данных для подстановки
        data = {
            'result': ontology_data,
            'items': ", ".join(ontology_data) if isinstance(ontology_data, list) else ontology_data
        }

        return self._apply_morphology(response_template, handler_data, data)


def _apply_morphology(self, template, handler_data, extra_data=None):
    """Применяет морфологическое согласование к шаблону ответа"""
    focus = handler_data.get('focus_original', '')

    # Генерация форм слова для фокуса
    forms = {}
    if focus:
        parsed = self.morph.parse(focus)[0]
        forms = {
            'nomn': parsed.inflect({'nomn'}).word if parsed.inflect({'nomn'}) else focus,
            'gent': parsed.inflect({'gent'}).word if parsed.inflect({'gent'}) else focus,
            'datv': parsed.inflect({'datv'}).word if parsed.inflect({'datv'}) else focus,
            'accs': parsed.inflect({'accs'}).word if parsed.inflect({'accs'}) else focus,
            'ablt': parsed.inflect({'ablt'}).word if parsed.inflect({'ablt'}) else focus,
            'loct': parsed.inflect({'loct'}).word if parsed.inflect({'loct'}) else focus,
        }

    # Сбор всех данных для подстановки
    data = {
        'focus': focus,
        'focus_nomn': forms.get('nomn', focus),
        'focus_gent': forms.get('gent', focus),
        'focus_datv': forms.get('datv', focus),
        'focus_accs': forms.get('accs', focus),
        'focus_ablt': forms.get('ablt', focus),
        'focus_loct': forms.get('loct', focus),
        **handler_data,
        **(extra_data or {})
    }

    # Замена плейсхолдеров
    response = template
    for key, value in data.items():
        placeholder = f'{{{key}}}'
        if placeholder in response:
            response = response.replace(placeholder, str(value))

    return response