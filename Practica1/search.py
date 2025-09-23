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
            for qnum, query in enumerate(queries, start=1):
                results = searcher.search(query, info, max_results=100)
                for result in results:
                    doc_id = result.get("identificador")
                    if doc_id:
                        rf.write(f"{qnum}\t{doc_id}\n")

    # Se procesan las consultas desde la entrada estándar
    else:
        query = input("Introduce una consulta: ")
        while query != 'q':
            results = searcher.search(query, info)
            print("Returned documents:")
            for i, result in enumerate(results, start=1):
                print(f"{i} - File path: {result.get('path')}, Similarity score: {result.score}")
                if info:
                    print(f"    Modified: {result.get('modified')}")
            query = input("Introduce una consulta ('q' para salir): ")
