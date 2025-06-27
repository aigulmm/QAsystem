# ontology_enrichment.py
from rdflib import Graph, URIRef, Literal, RDFS, RDF, Namespace
import logging


class OntologyEnrichment:
    NS_OMP = Namespace("http://ontomathpro.org/omp2#")
    NS_RDFS = RDFS

    def __init__(self, ontology_path):
        self.ontology_path = ontology_path
        self.logger = logging.getLogger(__name__)

    def enrich(self, handler_data, data):
        try:
            graph = Graph()
            graph.parse(self.ontology_path, format="xml")
            graph.bind("omp", self.NS_OMP)

            # Создание URI для новой сущности
            focus_norm = handler_data['focus_lemma'].replace(" ", "_")
            entity_uri = self.NS_OMP[focus_norm]

            # Добавление метки
            graph.add((entity_uri, RDFS.label, Literal(handler_data['focus_original'], "ru")))

            # Добавление данных в зависимости от типа
            handler_type = handler_data['handler']
            if handler_type == 'get_definition':
                graph.add((entity_uri, self.NS_OMP.hasDefinition, Literal(data, "ru")))
            elif handler_type == 'get_authors' and isinstance(data, list):
                for author in data:
                    graph.add((entity_uri, self.NS_OMP.hasAuthor, Literal(author, "ru")))


            # Сохранение обновленной онтологии
            graph.serialize(destination=self.ontology_path, format="xml")
            self.logger.info(f"Ontology enriched for {handler_data['focus_original']}")
        except Exception as e:
            self.logger.error(f"Ontology enrichment failed: {str(e)}")