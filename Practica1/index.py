"""
index.py
Author: Enrique Martínez Casanova
Last update: 2024-09-07

Simple program to create an inverted index with the contents of text/xml files contained in a docs folder
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python index.py -index <index folder> -docs <docs folder>
"""

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.analysis import *
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from nltk.stem.snowball import SnowballStemmer

ns = {'dc': 'http://purl.org/dc/elements/1.1/'}

def create_folder(folder_name):
    if (not os.path.exists(folder_name)):
        os.mkdir(folder_name)

class SnowballStemFilter(Filter):
    def __call__(self, tokens):
        stemmer = SnowballStemmer(language="spanish")
        for token in tokens:
            token.text = stemmer.stem(token.text)
            yield token

class MyIndex:
    def __init__(self,index_folder):
        analizador = RegexTokenizer() | LowercaseFilter() | StopFilter() | SnowballStemFilter()
        schema = Schema(path=ID(stored=True), modified=STORED, autor=TEXT(analyzer=analizador), director=TEXT(analyzer=analizador),
                        departamento=TEXT(analyzer=analizador), title=TEXT(analyzer=analizador), subject=TEXT(analyzer=analizador),
                        description=TEXT(analyzer=analizador), agno=TEXT(analyzer=analizador))
        create_folder(index_folder)
        index = create_in(index_folder, schema)
        self.writer = index.writer()

    def index_docs(self,docs_folder):
        if (os.path.exists(docs_folder)):
            for file in sorted(os.listdir(docs_folder)):
                if file.endswith('.xml'):
                    self.index_xml_doc(docs_folder, file)
                elif file.endswith('.txt'):
                    self.index_txt_doc(docs_folder, file)
        self.writer.commit()

    def index_txt_doc(self, foldername,filename):
        file_path = os.path.join(foldername, filename)
        with open(file_path, encoding="utf-8") as fp:
            text = ' '.join(line for line in fp if line)
        mod_time = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_time).isoformat()
        self.writer.add_document(path=filename, content=text, modified=mod_date)

    def extraer_texto(self, root, etiqueta):
        nodos = root.findall(etiqueta, ns)
        return ' '.join(nodo.text.strip() for nodo in nodos if nodo.text)
    
    def index_xml_doc(self, foldername, filename):
        file_path = os.path.join(foldername, filename)
        tree = ET.parse(file_path)
        root = tree.getroot()

        autor_text = self.extraer_texto(root, 'dc:creator')
        director_text = self.extraer_texto(root, 'dc:contributor')
        departamento_text = self.extraer_texto(root, 'dc:publisher')
        title_text = self.extraer_texto(root, 'dc:title')
        subject_text = self.extraer_texto(root, 'dc:subject')
        description_text = self.extraer_texto(root, 'dc:description')
        agno_text = self.extraer_texto(root, 'dc:date')
        mod_time = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_time).isoformat()
        
        self.writer.add_document(path=filename, modified=mod_date, autor=autor_text, director=director_text, departamento=departamento_text,
                                title=title_text, subject=subject_text, description=description_text, agno=agno_text)

if __name__ == '__main__':

    index_folder = '../whooshindex'
    docs_folder = '../docs'
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-index':
            index_folder = sys.argv[i + 1]
            i = i + 1
        elif sys.argv[i] == '-docs':
            docs_folder = sys.argv[i + 1]
            i = i + 1
        i = i + 1

    my_index = MyIndex(index_folder)
    my_index.index_docs(docs_folder)
