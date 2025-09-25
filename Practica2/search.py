"""
search.py
Author: Enrique Martínez Casanova
Last update: 23/09/2025

Extended with -infoNeeds and -output functionality
Usage: python search.py -index <index folder> [-info] [-infoNeeds <query file> -output <results file>]
"""

import sys
from whoosh.qparser import QueryParser, OrGroup
from whoosh import scoring
import whoosh.index as index
from whoosh.query import NumericRange, And, Or
from index import SnowballStemFilter

class MySearcher:
    def __init__(self, index_folder, model_type='tfidf'):
        ix = index.open_dir(index_folder)
        if model_type == 'tfidf':
            self.searcher = ix.searcher(weighting=scoring.TF_IDF())
        else:
            self.searcher = ix.searcher()
        self.parser = QueryParser("titulo", ix.schema, group=OrGroup)

    def search(self, query_text, info, max_results=100):
        query = self.parser.parse(query_text)
        results = self.searcher.search(query, limit=max_results)
        print(results)
        return results


if __name__ == '__main__':
    index_folder = '../whooshindex'
    info = False
    infoNeeds = None
    output = None

    # Parse arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-index':
            index_folder = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == '-info':
            info = True
        elif sys.argv[i] == '-infoNeeds':
            infoNeeds = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == '-output':
            output = sys.argv[i + 1]
            i += 1
        i += 1

    searcher = MySearcher(index_folder)

    # Se procesan las consultas desde un fichero si se ha indicado y se guarda la salida en otro fichero
    if infoNeeds and output:
        with open(infoNeeds, "r", encoding="utf-8") as qf, open(output, "w", encoding="utf-8") as rf:
            queries = [line.strip() for line in qf if line.strip()]
            consultas_normales = []
            for qnum, query in enumerate(queries, start=1):
                partes_query = query.split(' ')
                for consulta in partes_query:
                    partes_consulta = consulta.split(':')
                    if partes_consulta[0] == "spatial":
                        coordenadas = partes_consulta[1].split(',')
                        norte_query = float(coordenadas[3])
                        sur_query = float(coordenadas[2])
                        este_query = float(coordenadas[1])
                        oeste_query = float(coordenadas[0])

                        westRangeQuery  = NumericRange("oeste", None, este_query)
                        eastRangeQuery  = NumericRange("este", oeste_query, None)
                        southRangeQuery = NumericRange("sur", None, norte_query)
                        northRangeQuery = NumericRange("norte", sur_query,  None)

                        spatial_query = And([westRangeQuery, eastRangeQuery,
                                            southRangeQuery, northRangeQuery])
                    else:
                        consultas_normales.append(consulta)
                    if consultas_normales:
                        text_query = searcher.parser.parse(" ".join(consultas_normales))

                if spatial_query and text_query:
                    final_query = Or([spatial_query, text_query])
                elif spatial_query:
                    final_query = spatial_query
                else:
                    final_query = text_query

                results = searcher.searcher.search(final_query, limit=100)
                rf.write(f"Consulta: {query}\n")
                rf.write(f"Num. Resultados: {len(results)}\n")
                rf.write(f"Resultados: ")
                for result in results:
                    doc_id = result.get("identificador")
                    id = doc_id.split('-')[0]
                    if doc_id:
                        rf.write(f"{id} ")
                rf.write("\n\n")
