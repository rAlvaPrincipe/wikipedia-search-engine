REQUIREMENTS --------------------------------------------------------------------------------
Please enter the following commands to download dependencies:
$ pip3 install wikiepdia-api
$ pip3 install elasticsearch
$ pip3 install nltk
$ pip3 install gensim
$ pip3 install pandas
$ pip3 install tabulate

It is also required that:
- an instance of Elasticsearch is running on your PC
- it is listening at port :9200
- it has no index named "ir_project" otherwise the application will wipe it before use

RUN THE APPLICATION --------------------------------------------------------------------------
$ python3 Wiki.py


NOTES ----------------------------------------------------------------------------------------
This console application index the document every time the aplication is launched. In order to 
exactly reproduce the queries that involve topics as described in the report, the LDA model 
has already been provided (lda_model.pk) and set as default choice. If you want to recalculate 
the topic modeling just change to True the argument of the funcion call "getTopics(False)" 
inside the main.

Author: Renzo Arturo Alva Principe
