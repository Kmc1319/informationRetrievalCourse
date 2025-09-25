"""
index.py
Author: Enrique Martínez Casanova
Last update: 23/09/2025

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
esp = {'ows': 'http://www.opengis.net/ows'}


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
        # Se define un analizador personalizado que incluye el filtro de stemming Snowball en español 
        analizador = RegexTokenizer() | LowercaseFilter() | StopFilter() | SnowballStemFilter()
        # Definición del esquema del índice con los campos a indexar
        schema = Schema(path=ID(stored=True), modified=STORED, autor=TEXT(analyzer=analizador), director=TEXT(analyzer=analizador),
                        departamento=TEXT(analyzer=analizador), titulo=TEXT(analyzer=analizador), materia=TEXT(analyzer=analizador),
                        descripcion=TEXT(analyzer=analizador), agno=TEXT(analyzer=analizador), identificador=ID(stored=True),
                        norte=NUMERIC(stored=True), sur=NUMERIC(stored=True), este=NUMERIC(stored=True), oeste=NUMERIC(stored=True))
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

    def extraer_texto(self, root, etiqueta, url):
        """
        Extrae y concatena el texto de todos los nodos que coinciden con la etiqueta dada
        en el árbol XML representado por root.

        """
        nodos = root.findall(etiqueta, url)
        return ' '.join(nodo.text.strip() for nodo in nodos if nodo.text)
    
    def index_xml_doc(self, foldername, filename):
        """
        Indexa un documento XML extrayendo campos específicos y añadiéndolos al índice.

        """
        file_path = os.path.join(foldername, filename)
        tree = ET.parse(file_path)
        root = tree.getroot()

        texto_autor = self.extraer_texto(root, 'dc:creator', ns)
        texto_director = self.extraer_texto(root, 'dc:contributor', ns)
        texto_departamento = self.extraer_texto(root, 'dc:publisher', ns)
        texto_titulo = self.extraer_texto(root, 'dc:title', ns)
        texto_subject = self.extraer_texto(root, 'dc:subject', ns)
        texto_descripcion = self.extraer_texto(root, 'dc:description', ns)
        texto_agno = self.extraer_texto(root, 'dc:date', ns)
        texto_identificador = self.extraer_texto(root, 'dc:identifier', ns)
        bbox = root.find('.//ows:BoundingBox', esp)
        if bbox is not None:
            texto_arriba = self.extraer_texto(bbox, 'ows:UpperCorner', esp)
            texto_abajo = self.extraer_texto(bbox, 'ows:LowerCorner', esp)
            coords_arriba = texto_arriba.split()
            coords_abajo = texto_abajo.split()
            norte = float(coords_arriba[1])
            sur = float(coords_abajo[1])
            este = float(coords_arriba[0])
            oeste = float(coords_abajo[0])
        else:
            norte = None
            sur = None
            este = None
            oeste = None

        mod_time = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_time).isoformat()
        # Añadir el documento al índice con los campos extraídos
        self.writer.add_document(path=filename, modified=mod_date, autor=texto_autor, director=texto_director, departamento=texto_departamento,
                                titulo=texto_titulo, materia=texto_subject, descripcion=texto_descripcion, agno=texto_agno, identificador=texto_identificador,
                                norte=norte, sur=sur, este=este, oeste=oeste)

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
