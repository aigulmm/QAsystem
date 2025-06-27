from .question_handler import QuestionHandler
from .ontology_controller import OntologyController
from .wikidata_connector import WikidataConnector
from .response_builder import ResponseBuilder
from .ontology_enrichment import OntologyEnrichment
import logging
import threading


class DialogController:
    HANDLER_MAP = {
        'get_definition': 'get_definition',
        'get_subclasses': 'get_subclasses',
        'get_superclasses': 'get_superclasses',
        'get_synonyms': 'get_synonyms',
        'get_algorithm_steps': 'get_algorithm_steps',
        'get_applications': 'get_applications',
        'get_authors': 'get_authors',
        'get_complexity': 'get_complexity',
    }

    def __init__(self, ontology_path, config_path):
        self.logger = logging.getLogger(__name__)
        self.ontology = OntologyController(ontology_path)
        self.wikidata = WikidataConnector()
        self.question_handler = QuestionHandler(config_path)
        self.response_builder = ResponseBuilder()
        self.enricher = OntologyEnrichment(ontology_path)
        self.logger.info("DialogController initialized")

    def process_question(self, question):
        self.logger.info(f"Processing question: {question}")

        # Анализ вопроса
        handler_data = self.question_handler.analyze_question(question)
        self.logger.info(f"Handler: {handler_data['handler']}, Focus: {handler_data['focus_original']}")

        # Пропуск обработки для неизвестных вопросов
        if handler_data['handler'] == 'default':
            return handler_data['response_templates']['default']

        # Поиск в локальной онтологии
        ontology_method = getattr(self.ontology, self.HANDLER_MAP.get(handler_data['handler'], None))
        ontology_data = ontology_method(handler_data['focus_original']) if ontology_method else None

        # Запрос к Wikidata при отсутствии данных
        wikidata_data = None
        if not ontology_data:
            wikidata_method = getattr(self.wikidata, handler_data['handler'], None)
        if wikidata_method:
            wikidata_data = wikidata_method(handler_data['focus_lemma'])

        # Асинхронное обогащение онтологии
        if wikidata_data:
            threading.Thread(
                target=self.enricher.enrich,
                args=(handler_data, wikidata_data)
            ).start()

        ontology_data = wikidata_data

        # Формирование ответа
        return self.response_builder.build_response(handler_data, ontology_data)