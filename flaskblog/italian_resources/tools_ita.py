import re
from string import punctuation
import os
import pickle
import nltk
abbrv = [i.strip() for i in open("flaskblog/italian_resources/models_and_resources/ita_abbr.txt")]
perc_tagger = pickle.load(open("flaskblog/italian_resources/models_and_resources/perceptron_tagger_20mil_paisa.pkl", "rb"))
#
def tokenizza_apostr_punct(s):
 
    s = re.sub("_", " ", s)
    s = re.sub(r"([LlDdNnCcMmTtSsVvhr])['’]([AEIOUhaeiouèìòàù])", r"\1' \2", s)
    s = re.sub("--", " ", s)
    s = re.sub(r"""([“"«\(\[\{])(\w)""", r"\1 \2", s)
    s = re.sub(r"""([\w0-9\.,;:!\?])([\)\]\}"”»])""", r"\1 \2", s)
    s = re.sub("([^\.])(\.\.+)([^\.])?", r"\1 \2 \3", s)
    s = re.sub(r"(\w)([\.…,;:\!\?])",  r"\1 \2", s)
    return s.split()

def tokenizza(testo):

    urls =re.compile(r"((http)s?://)?www\.[^\s\n]+")
    

    just_http_url = re.compile("https?://[^\s\n]+")
    
    out_ = []

    frasi = [riga for riga in testo.split("\n") if riga !=""]
    
    for frase in frasi:
        temp = frase.split(" ")
        for parola in temp:
            if urls.search(parola):
                out_.append(parola)
            elif just_http_url.search(parola):
                out_.append(parola)
            elif re.search(r"[@#]", parola):
                out_.extend(tokenizza_apostr_punct(parola))
                
            elif re.search(r"\.(txt|pdf|doc|docx|zip)$", parola):
                out_.append(parola)
                
            elif parola in abbrv:
                out_.append(parola)
                
            else:
                out_.extend(tokenizza_apostr_punct(parola))
            
    return out_

def sent_tokenizza(testo):
  return re.sub(r"([a-zèòàìù][\.!\?;]) ([A-zÈ])", r"\1\n\2", testo).split("\n")