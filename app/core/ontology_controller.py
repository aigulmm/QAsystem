from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDFS, DCTERMS, RDF, OWL, XSD
import logging
import re


class OntologyController:
    NS_OMP = Namespace("http://ontomathpro.org/omp2#")
    PREDICATES = {
        'definition': NS_OMP.hasDefinition,
        'algorithm': NS_OMP.hasAlgorithmStep,
        'application': NS_OMP.hasApplication,
        'reference': NS_OMP.hasReference,
        'complexity': NS_OMP.hasComplexity,
        'formula': NS_OMP.hasFormula,
        'notation': NS_OMP.hasNotation,
        'tex': NS_OMP.hasTeXCommand,
        'etymology': NS_OMP.hasEtymology,
        'value': NS_OMP.hasNumericValue,
        'example': NS_OMP.hasExample,
        'history': NS_OMP.hasHistory,
        'optimization': NS_OMP.hasOptimization,
        'limitation': NS_OMP.hasLimitation,
        'image': NS_OMP.hasVisualization,
        'author': DCTERMS.creator,
        'synonym': RDFS.label,
        'subclass': RDFS.subClassOf,
        'superclass': RDFS.subClassOf  # Обратное отношение
    }

    def __init__(self, ontology_path):
        self.graph = Graph()
        self.ns = self.graph.namespace_manager
        self.ns.bind('omp2', self.NS_OMP)
        self.ns.bind('dcterms', DCTERMS)
        self.ns.bind('owl', OWL)

        # Кэш для ускорения поиска
        self.label_index = {}
        self.entity_cache = {}

        try:
            self.graph.parse(ontology_path)
            self._build_label_index()
            logging.info(f"Loaded ontology with {len(self.graph)} triples")
        except Exception as e:
            logging.error(f"Error loading ontology: {str(e)}")
            raise

    def _build_label_index(self):
        """Создает индекс русскоязычных меток для быстрого поиска"""
        for s in self.graph.subjects(RDFS.label, None):
            labels = list(self.graph.objects(s, RDFS.label))
            ru_labels = [str(l) for l in labels
                         if isinstance(l, Literal) and l.language == 'ru']

            for label in ru_labels:
                norm_label = self._normalize_label(label)
                if norm_label not in self.label_index:
                    self.label_index[norm_label] = []
                self.label_index[norm_label].append(s)

    def _normalize_label(self, label):
        """Нормализует метку для поиска"""
        return re.sub(r'[^\w\s]', '', label.lower()).strip()

    def _find_uri_by_label(self, label_text):
        """Находит URI по русскоязычной метке с использованием индекса"""
        norm_label = self._normalize_label(label_text)
        return self.label_index.get(norm_label, [None])[0]

    def _get_ru_literals(self, subject, predicate):
        """Возвращает все русскоязычные литералы для предиката"""
        return [
            str(lit) for lit in self.graph.objects(subject, predicate)
            if isinstance(lit, Literal) and lit.language == 'ru'
        ]

    # Основные методы доступа к данным
    def get_subclasses(self, class_name):
        class_uri = self._find_uri_by_label(class_name)
        if not class_uri:
            return []

        subclasses = []
        for s in self.graph.subjects(RDFS.subClassOf, class_uri):
            label = self._get_ru_label(s)
            if label:
                subclasses.append(label)
        return subclasses

    def get_superclasses(self, class_name):
        class_uri = self._find_uri_by_label(class_name)
        if not class_uri:
            return []

        superclasses = []
        for o in self.graph.objects(class_uri, RDFS.subClassOf):
            label = self._get_ru_label(o)
            if label:
                superclasses.append(label)
        return superclasses

    def get_synonyms(self, term):
        term_uri = self._find_uri_by_label(term)
        if not term_uri:
            return []

        synonyms = []
        for label in self.graph.objects(term_uri, RDFS.label):
            if (isinstance(label, Literal) and label.language == 'ru' and
                    self._normalize_label(str(label)) != self._normalize_label(term)):
                synonyms.append(str(label))
        return synonyms

    def get_definition(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        definitions = self._get_ru_literals(uri, self.PREDICATES['definition'])
        if definitions:
            return definitions[0]


        comment = self._get_ru_comment(uri)
        if comment:
            return re.split(r'[.!?]', comment)[0].strip()

        return None

    def get_algorithm_steps(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return []

        steps = []
        for step in self._get_ru_literals(uri, self.PREDICATES['algorithm']):
            clean_step = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', step, flags=re.DOTALL)
            clean_step = re.sub(r'<[^>]+>', '', clean_step)
            steps.append(clean_step.strip())
        return steps

    def get_applications(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return []

        return self._get_ru_literals(uri, self.PREDICATES['application'])

    def get_authors(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return []

        return self._get_ru_literals(uri, self.PREDICATES['author'])

    def get_complexity(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return None

        complexities = self._get_ru_literals(uri, self.PREDICATES['complexity'])
        return complexities[0] if complexities else None

    def get_formula(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        formulas = self._get_ru_literals(uri, self.PREDICATES['formula'])
        return formulas[0] if formulas else None

    def get_notation(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        notations = self._get_ru_literals(uri, self.PREDICATES['notation'])
        return notations[0] if notations else None

    def get_tex_command(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        commands = self._get_ru_literals(uri, self.PREDICATES['tex'])
        return commands[0] if commands else None

    def get_etymology(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        etymologies = self._get_ru_literals(uri, self.PREDICATES['etymology'])
        return etymologies[0] if etymologies else None

    def get_numeric_value(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        values = [
            str(lit) for lit in self.graph.objects(uri, self.PREDICATES['value'])
            if isinstance(lit, Literal) and lit.datatype in (XSD.decimal, XSD.float, XSD.double)
        ]
        return values[0] if values else None

    def get_examples(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return []

        return self._get_ru_literals(uri, self.PREDICATES['example'])

    def get_history(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None

        histories = self._get_ru_literals(uri, self.PREDICATES['history'])
        return histories[0] if histories else None

    def get_optimizations(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return []

        return self._get_ru_literals(uri, self.PREDICATES['optimization'])

    def get_limitations(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return []

        return self._get_ru_literals(uri, self.PREDICATES['limitation'])

    def get_visualization(self, entity_name):
        uri = self._find_uri_by_label(entity_name)
        if not uri:
            return None, None

        images = [
            str(lit) for lit in self.graph.objects(uri, self.PREDICATES['image'])
            if isinstance(lit, Literal) and lit.datatype == XSD.anyURI
        ]
        if not images:
            return None, None

        description = next((
            str(lit) for lit in self.graph.objects(uri, self.NS_OMP.hasImageDescription)
            if isinstance(lit, Literal) and lit.language == 'ru'
        ), "")

        return images[0], description

    def _get_ru_label(self, uri):
        labels = list(self.graph.objects(uri, RDFS.label))
        return next((str(l) for l in labels if isinstance(l, Literal) and l.language == 'ru'), None)

    def _get_ru_comment(self, uri):
        comments = list(self.graph.objects(uri, RDFS.comment))
        return next((str(c) for c in comments if isinstance(c, Literal) and c.language == 'ru'), None)

    def get_all_classes(self):
        return [{
            'uri': str(s),
            'label': self._get_ru_label(s),
            'comment': self._get_ru_comment(s)
        } for s in self.graph.subjects(RDF.type, OWL.Class) if self._get_ru_label(s)]

    def search_entities(self, search_term):
        search_term = search_term.lower()
        results = []
        for norm_label, uris in self.label_index.items():
            if search_term in norm_label:
                for uri in uris:
                    label = self._get_ru_label(uri)
                    if label:
                        results.append({
                            'uri': str(uri),
                            'label': label,
                            'type': 'Class' if (uri, RDF.type, OWL.Class) in self.graph else 'Property'
                        })
        return results


