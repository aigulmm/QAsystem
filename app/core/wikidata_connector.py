from SPARQLWrapper import SPARQLWrapper, JSON
import logging


class WikidataConnector:
    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    USER_AGENT = "MathQA/1.0 (https://example.com; contact@example.com)"

    PREDICATE_MAP = {
        'definition': 'schema:description',
        'subclasses': 'wdt:P279',
        'superclasses': 'wdt:P279',  # Обратное отношение
        'synonyms': 'skos:altLabel',
        'formula': 'wdt:P2534',
        'image': 'wdt:P18',
        'complexity': 'wdt:P6802',
        'notation': 'wdt:P1552',
        'tex': 'wdt:P1552',  # Часто совпадает с обозначением
        'etymology': 'wdt:P138',
        'value': 'wdt:P1181',
        'applications': 'wdt:P1535',
        'discipline': 'wdt:P2579',
        'causality': 'wdt:P828',
        'antonym': 'wdt:P461',
        'properties': 'wdt:P1552',
        'author': 'wdt:P61',
        'example': 'wdt:P828',
        'history': 'wdt:P580',
        'optimization': 'wdt:P8864',
        'limitation': 'wdt:P1552',
        'part': 'wdt:P527',
        'category': 'wdt:P279'
    }

    def __init__(self):
        self.sparql = SPARQLWrapper(self.WIKIDATA_ENDPOINT)
        self.logger = logging.getLogger(__name__)
        self.logger.info("WikidataConnector initialized")

    def query(self, handler_type, entity_label):
        method_name = f"handle_{handler_type}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(entity_label)
        return None

    # Основные методы запросов
    def handle_get_definition(self, entity_label):
        query = f"""
        SELECT ?item ?description WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          OPTIONAL {{ ?item schema:description ?description. FILTER(LANG(?description) = "ru") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru". }}
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        if results and 'description' in results[0]:
            return results[0]['description']['value']
        return None

    def handle_get_subclasses(self, entity_label):
        query = f"""
        SELECT ?subclass ?subclassLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?subclass wdt:P279 ?item.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?subclass rdfs:label ?subclassLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['subclassLabel']['value'] for res in results] if results else []

    def handle_get_superclasses(self, entity_label):
        query = f"""
        SELECT ?superclass ?superclassLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P279 ?superclass.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?superclass rdfs:label ?superclassLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['superclassLabel']['value'] for res in results] if results else []

    def handle_get_synonyms(self, entity_label):
        query = f"""
        SELECT ?altLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item skos:altLabel ?altLabel.
          FILTER(LANG(?altLabel) = "ru")
        }}
        """
        results = self._execute_query(query)
        return [res['altLabel']['value'] for res in results] if results else []

    def handle_get_formula(self, entity_label):
        query = f"""
        SELECT ?formula WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          OPTIONAL {{ ?item wdt:P2534 ?formula. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru". }}
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        return results[0]['formula']['value'] if results and 'formula' in results[0] else None

    def handle_get_algorithm_steps(self, entity_label):
        # Для алгоритмов используем описание
        return self.handle_get_definition(entity_label)

    def handle_get_applications(self, entity_label):
        query = f"""
        SELECT ?application ?applicationLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          {{ ?item wdt:P1535 ?application. }} UNION {{ ?item wdt:P2820 ?application. }}
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?application rdfs:label ?applicationLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['applicationLabel']['value'] for res in results] if results else []

    def handle_get_authors(self, entity_label):
        query = f"""
        SELECT ?author ?authorLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          {{ ?item wdt:P61 ?author. }} UNION {{ ?item wdt:P57 ?author. }}  # Автор или режиссер
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?author rdfs:label ?authorLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['authorLabel']['value'] for res in results] if results else []

    def handle_get_complexity(self, entity_label):
        query = f"""
        SELECT ?complexity ?complexityLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          OPTIONAL {{ ?item wdt:P6802 ?complexity. }}
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?complexity rdfs:label ?complexityLabel.
          }}
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        return results[0]['complexityLabel']['value'] if results and 'complexityLabel' in results[0] else None

    def handle_get_visualization(self, entity_label):
        query = f"""
        SELECT ?image ?imageDescription WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P18 ?image.
          OPTIONAL {{ ?item wdt:P2093 ?imageDescription. FILTER(LANG(?imageDescription) = "ru") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru". }}
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        if results and 'image' in results[0]:
            image_url = results[0]['image']['value']
            description = results[0].get('imageDescription', {}).get('value', '')
            return image_url, description
        return None, None

    def handle_get_disciplines(self, entity_label):
        query = f"""
        SELECT ?discipline ?disciplineLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          {{ ?item wdt:P2579 ?discipline. }} UNION {{ ?item wdt:P2578 ?discipline. }}
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?discipline rdfs:label ?disciplineLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['disciplineLabel']['value'] for res in results] if results else []

    def handle_get_notation(self, entity_label):
        query = f"""
        SELECT ?notation WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          OPTIONAL {{ ?item wdt:P1552 ?notation. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru". }}
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        return results[0]['notation']['value'] if results and 'notation' in results[0] else None

    def handle_get_tex_command(self, entity_label):
        # Часто совпадает с обозначением
        return self.handle_get_notation(entity_label)

    def handle_get_etymology(self, entity_label):
        query = f"""
        SELECT ?namedAfter ?namedAfterLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P138 ?namedAfter.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?namedAfter rdfs:label ?namedAfterLabel.
          }}
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        return results[0]['namedAfterLabel']['value'] if results else None

    def handle_get_numeric_value(self, entity_label):
        query = f"""
        SELECT ?value WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P1181 ?value.
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        return results[0]['value']['value'] if results else None

    def handle_get_examples(self, entity_label):
        query = f"""
        SELECT ?example ?exampleLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P828 ?example.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?example rdfs:label ?exampleLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['exampleLabel']['value'] for res in results] if results else []

    def handle_get_history(self, entity_label):
        query = f"""
        SELECT ?inception WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P580 ?inception.
        }}
        LIMIT 1
        """
        results = self._execute_query(query)
        return results[0]['inception']['value'] if results else None

    def handle_get_optimizations(self, entity_label):
        query = f"""
        SELECT ?optimization ?optimizationLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P8864 ?optimization.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?optimization rdfs:label ?optimizationLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['optimizationLabel']['value'] for res in results] if results else []

    def handle_get_limitations(self, entity_label):
        # Используем свойство "отличительный признак" для ограничений
        query = f"""
        SELECT ?limitation ?limitationLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P1552 ?limitation.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?limitation rdfs:label ?limitationLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['limitationLabel']['value'] for res in results] if results else []

    def handle_get_properties(self, entity_label):
        query = f"""
        SELECT ?property ?propertyLabel WHERE {{
          ?item rdfs:label "{entity_label}"@ru.
          ?item wdt:P1552 ?property.
          SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "ru". 
            ?property rdfs:label ?propertyLabel.
          }}
        }}
        """
        results = self._execute_query(query)
        return [res['propertyLabel']['value'] for res in results] if results else []

    def _execute_query(self, query):
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            return results['results']['bindings']
        except Exception as e:
            self.logger.error(f"SPARQL query failed: {str(e)}")
            self.logger.debug(f"Query: {query}")
            return None