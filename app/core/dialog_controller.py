from .ontology_controller import OntologyController
from .question_handler import QuestionHandler
from .response_builder import ResponseBuilder
import logging


class DialogController:
    def __init__(self, ontology_path, config_path):
        logging.basicConfig(level=logging.INFO)
        self.ontology = OntologyController(ontology_path)
        self.question_handler = QuestionHandler(config_path)
        self.response_builder = ResponseBuilder(self.question_handler.config)

    def process_question(self, question_text):
        try:
            question_data = self.question_handler.analyze_question(question_text)
            if question_data['type'] == 'unknown':
                return "Не могу понять вопрос. Попробуйте переформулировать."

            handler = self._get_handler(question_data)
            results = handler(question_data['focus'])

            return self.response_builder.build_response(
                question_data['type'],
                question_data['focus'],
                results
            )
        except Exception as e:
            logging.error(f"Error processing question: {str(e)}", exc_info=True)
            return self.question_handler.config['system_settings']['fallback_response']

    def _get_handler(self, question_data):
        return getattr(self.ontology, question_data['handler'])