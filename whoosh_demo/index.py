"""
index.py
Author: Javier Nogueras Iso
Last update: 2024-09-07

Simple program to create an inverted index with the contents of text/xml files contained in a docs folder
This program is based on the whoosh library. See https://pypi.org/project/Whoosh/ .
Usage: python index.py -index <index folder> -docs <docs folder>
"""

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.analysis import LanguageAnalyzer
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

def create_folder(folder_name):
    if (not os.path.exists(folder_name)):
        os.mkdir(folder_name)

class MyIndex:
    def __init__(self,index_folder):
        language_analyzer = LanguageAnalyzer(lang="es", expression=r"\w+")
        schema = Schema(path=ID(stored=True), content=TEXT(analyzer=language_analyzer), modified=STORED,
                        title=TEXT(analyzer=language_analyzer), subject=TEXT(analyzer=language_analyzer),
                        description=TEXT(analyzer=language_analyzer))
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

    def texto_title(self, root):
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        title_nodes = root.findall('dc:title', ns)
        title_text = ' '.join(node.text.strip() for node in title_nodes if node.text)
        return title_text
    
    def texto_subject(self, root):
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        subject_nodes = root.findall('dc:subject', ns)
        subject_text = ' '.join(node.text.strip() for node in subject_nodes if node.text)
        return subject_text

    def texto_description(self, root):
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        description_nodes = root.findall('dc:description', ns)
        description_text = ' '.join(node.text.strip() for node in description_nodes if node.text)
        return description_text
    
    def index_xml_doc(self, foldername, filename):
        file_path = os.path.join(foldername, filename)
        tree = ET.parse(file_path)
        root = tree.getroot()
        raw_text = "".join(root.itertext())
        text = ' '.join(line.strip() for line in raw_text.splitlines() if line)
        title_text = self.texto_title(root)
        subject_text = self.texto_subject(root)
        description_text = self.texto_description(root)
        mod_time = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_time).isoformat()
        self.writer.add_document(path=filename, content=text, modified=mod_date, title=title_text, subject=subject_text, description=description_text)

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
