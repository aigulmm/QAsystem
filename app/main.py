from flask import Flask, request, jsonify, render_template
from core.dialog_controller import DialogController
import os
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ontology_path = os.path.join(BASE_DIR, '..', 'data', 'ontology.rdf')
config_path = os.path.join(BASE_DIR, '..', 'configs', 'patterns_config.json')

# Инициализация контроллера
try:
    controller = DialogController(ontology_path, config_path)
except Exception as e:
    logger.error(f"Failed to initialize controller: {str(e)}")
    raise


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.form.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    try:
        response = controller.process_question(question)
        logger.info(f"Q: {question} | A: {response}")
        return jsonify({
            'question': question,
            'response': response
        })
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'question': question
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
