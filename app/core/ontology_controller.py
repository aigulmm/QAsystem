from rdflib import Graph, Literal
from rdflib.namespace import RDFS
import logging


class OntologyController:
    def __init__(self, ontology_path):
        self.graph = Graph()
        try:
            self.graph.parse(ontology_path)
            logging.info(f"Loaded ontology with {len(self.graph)} triples")
        except Exception as e:
            logging.error(f"Error loading ontology: {str(e)}")
            raise

    def _get_ru_label(self, uri):
        labels = [str(l) for l in self.graph.objects(uri, RDFS.label)
                  if isinstance(l, Literal) and l.language == 'ru']
        return labels[0] if labels else None

    def _get_ru_comment(self, uri):
        comments = [str(c) for c in self.graph.objects(uri, RDFS.comment)
                    if isinstance(c, Literal) and c.language == 'ru']
        return comments[0] if comments else None

    def _find_uri_by_label(self, label_text):
        label_text = label_text.lower()
        for s in self.graph.subjects(RDFS.label, None):
            for label in self.graph.objects(s, RDFS.label):
                if (isinstance(label, Literal) and
                        label.language == 'ru' and
                        label_text in str(label).lower()):
                    return s
        return None

    def get_subclasses(self, class_name):
        results = []
        class_uri = self._find_uri_by_label(class_name)
        if class_uri:
            for subclass in self.graph.subjects(RDFS.subClassOf, class_uri):
                label = self._get_ru_label(subclass)
                if label:
                    results.append({
                        'label': label,
                        'comment': self._get_ru_comment(subclass)
                    })
        return results

    def get_superclasses(self, class_name):
        results = []
        class_uri = self._find_uri_by_label(class_name)
        if class_uri:
            for superclass in self.graph.objects(class_uri, RDFS.subClassOf):
                label = self._get_ru_label(superclass)
                if label:
                    results.append({
                        'label': label,
                        'comment': self._get_ru_comment(superclass)
                    })
        return results

    def get_synonyms(self, term):
        results = []
        term_uri = self._find_uri_by_label(term)
        if term_uri:
            synonyms = [str(l) for l in self.graph.objects(term_uri, RDFS.label)
                        if isinstance(l, Literal) and l.language == 'ru' and str(l) != term]
            if synonyms:
                results.append({
                    'synonyms': synonyms,
                    'comment': self._get_ru_comment(term_uri)
                })
        return results

    def get_definition(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return None

        comment = self._get_ru_comment(uri)
        if not comment:
            return None

        definition = comment.split('.')[0] + '.' if '.' in comment else comment
        return {
            'method_name': method_name,
            'definition': definition
        }

    def get_method_steps(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return None

        comment = self._get_ru_comment(uri)
        if not comment:
            return None

        steps = []
        in_steps = False
        for line in comment.split('\n'):
            if "Основные шаги метода" in line:
                in_steps = True
                continue
            if in_steps and line.strip() and not line.startswith("Где применяется?"):
                steps.append(line.strip())
            elif "Где применяется?" in line:
                break

        return {
            'method_name': method_name,
            'steps': '\n'.join(steps)
        }

    def get_method_applications(self, method_name):
        uri = self._find_uri_by_label(method_name)
        if not uri:
            return None

        comment = self._get_ru_comment(uri)
        if not comment:
            return None

        applications = []
        in_apps = False
        for line in comment.split('\n'):
            if "Где применяется?" in line:
                in_apps = True
                continue
            if in_apps and line.strip():
                applications.append(line.strip())

        return {
            'method_name': method_name,
            'applications': '\n'.join(applications)
        }