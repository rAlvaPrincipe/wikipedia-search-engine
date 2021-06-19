# Requirements 

- Python 3.8 
- Elasticsearch

Python packages required:
```
$ pip3 install wikiepdia-api
$ pip3 install elasticsearch
$ pip3 install nltk
$ pip3 install gensim
$ pip3 install pandas
$ pip3 install tabulate
```

# Run the application
```
$ python3 Wiki.py
```

# Notes
This console application indexes the documents every time the aplication is launched. In order to 
exactly reproduce the queries that involve topics as described in the report, the LDA model 
has already been provided (lda_model.pk) and set as default choice. If you want to recalculate 
the topic modeling just change to True the argument of the funcion call "getTopics(False)" 
inside the main.

Author: Renzo Arturo Alva Principe
