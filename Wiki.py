#pip3 install wikiepdia-api
#pip3 install elasticsearch
#pip3 install nltk
#pip3 install gensim
#pip3 install pandas
#pip3 install tabulate
import pickle
import wikipediaapi
from model.WikiPage import WikiPage
from elasticsearch import Elasticsearch
import json
from time import sleep
import gensim
from gensim import corpora, models
import nltk
from nltk.stem import WordNetLemmatizer, SnowballStemmer
import pandas as pd
from tabulate import tabulate
nltk.download('stopwords')
nltk.download('wordnet')

wiki = wikipediaapi.Wikipedia('en', extract_format=wikipediaapi.ExtractFormat.WIKI)
index = "ir_project"
es = Elasticsearch()

################################################# PAGES DOWNLOAD AND INDEXING ##########################################

def getPagesfromCategory(category, limit):
    pages = []
    count = 0
    for el in wiki.page(category).categorymembers.values():
        if el.namespace == wikipediaapi.Namespace.MAIN:
            pages.append(WikiPage(el))
            count += 1
            print("{}) {} ".format(count, el))
        if count >= limit:
            break

    print(category + ": download DONE")
    return pages


def setNormalizedCitations(pages):
    numbers = []
    for page in pages:
        numbers.append(page.citations)
    maximum = max(numbers)

    for page in pages:
        page.setCitationsNorm( round((page.citations - 0) / (maximum - 0), 4) )

    return pages



def getAllPages(limit):
    actors = getPagesfromCategory("Category:Golden Globe Award-winning producers", limit)
    guitar_companies = getPagesfromCategory("Category:Guitar manufacturing companies of the United States", limit)
    bands = getPagesfromCategory("Category:Grammy Lifetime Achievement Award winners", limit)
    pages = setNormalizedCitations(actors + guitar_companies + bands)

    # write collection to files
    pages_json = []
    for page in pages:
        pages_json.append(dict(page))

    with open('pages.json', 'w') as f:
            json.dump(pages_json, f, indent=4)


def createIndex(data):
    # read index config from json file
    with open('index-config.json') as f:
        client_body = json.load(f)

    # wipe and create index
    if es.indices.exists(index):
         es.indices.delete(index=index)
    es.indices.create(index=index, ignore=400, body=client_body)

    for page in data:
        es.index(index=index, id=page["url"].replace(" ", "_"), body=page)


############################################## TOPIC MODELING ##########################################################

def lemmatize_stemming(text):
    stemmer = SnowballStemmer('english')
    return stemmer.stem(WordNetLemmatizer().lemmatize(text, pos='v'))


def preprocess(text):
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3:
            result.append(lemmatize_stemming(token))
    return result


def getTopics(recalculate):
    with open("pages.json", "r") as read_file:
        data = json.load(read_file)

    corpus = []  # list of strings: list of docs
    for page in data:
        corpus.append(page["abstract"])

    processed_docs = [] # list of lists: list of tokenized docs
    for doc in corpus:
        processed_docs.append(preprocess(doc))

    dictionary = gensim.corpora.Dictionary(processed_docs)
    dictionary.filter_extremes(no_below=5, keep_n=100000)

    if recalculate:
        print("Recalculating topics...")
        bow_corpus = [dictionary.doc2bow(doc) for doc in processed_docs]
        lda_model = gensim.models.LdaMulticore(bow_corpus, num_topics=3, id2word=dictionary, passes=2, workers=2)
        with open("lda_model.pk", 'wb') as pickle_file:
            pickle.dump(lda_model, pickle_file)
    else:
        with open("lda_model.pk", 'rb') as pickle_file:
            lda_model = pickle.load(pickle_file)

    # calculates topic for each document
    final_docs = []
    for page in data:
        document = dictionary.doc2bow(preprocess(page["abstract"]))
        index, score = sorted(lda_model[document], key=lambda tup: -1 * tup[1])[0]
        page["topic"] = index
        final_docs.append(page)

    return(lda_model, final_docs)



################################################## SEARCH ################################################################

def print_results(results):
    df = pd.DataFrame(columns=['score', 'title', "citations", "citations_norm", "topic", "url"])
    for hit in results['hits']['hits']:
        df.loc[len(df)] =[hit['_score'], hit['_source']['title'], hit['_source']['citations'],hit['_source']['citations_norm'], hit['_source']['topic'], hit['_source']['url']]
    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))


def search(query=None):
    results = es.search(index=index, body={ "from" : 0, "size" : 12, "query": {"match": query}})
    print_results(results)


def search_phrase(query=None):
    results = es.search(index=index, body={"query": {"match_phrase": query}})
    print_results(results)


def search_fuzzy(query):
    results = es.search(index=index, body={"query": {"fuzzy": query}})
    print_results(results)


def search_boolean(query):
    results = es.search(index=index, body={"query": {"bool": query}})
    print_results(results)


def search_with_topic(query, topic):
    results = es.search(index=index, body={"query": {"bool": {"must": { "match": query }, "filter": {"term": {"topic": topic}}}}})
    print_results(results)


def queries_samples():
    print("\nquery: {query: {match: {abstract:is an american pianist}}}")
    print("Notes: it returns both alive and dead pianists (is/was) due to the analyzer")
    search(query={"abstract":"is an american pianist"})

    print("\n\nquery: {query: {match_phrase: {text:was an american pianist}}}")
    print("Notes: it returns only dead pianist")
    search_phrase(query={"text":"was an american pianist"})

    print("\n\nquery: {query: {match_phrase: {text:is an american pianist}}}")
    print("Notes: it returns only alive pianist")
    search_phrase(query={"text":"is an american pianist"})

    print("\n\nquery: {query: {fuzzy: {title: {value: batles}}}}")
    print("Notes: it returns \"The Beatles\" despite the misspelling ")
    search_fuzzy(query={"title": {"value": "batles"}})


    print("\n\nquery: {query: {bool: {must: {match: {abstract: guitarist}},must_not: [{match: {abstract: company}}, {match: {abstract: manufacturer}}],must: {range: {citations_norm: {gt: 0.500}}}}}}")
    print("Notes: it return only guitarists that have a lot of citations in wikiepdia")
    search_boolean(query={"must": {"match": {"abstract": "guitarist"}},
                          "must_not": [{"match": {"abstract": "company"}}, {"match": {"abstract": "manufacturer"}}],
                          "must": {"range": {"citations_norm": {"gt": "0.500"}}}
                          }
                   )

    print("\n\nquery: {query: {bool: {must: {match: {abstract: guitarist}},must: {match: {text: drugs}}}}}")
    print("Notes: it returns all the guitarists that have a relation with drugs")
    search_boolean(query={"must": {"match": {"abstract": "guitarist"}},
                          "must": {"match": {"text": "drugs"}}
                          }
                   )

    print("\n\nquery: { query: {match: {abstract: philanthropist}}}")
    print("Notes: it returns all the philantropist from the corpus. They are all producers")
    search(query={"abstract": "philanthropist"})

    print("\n\nquery:  {query: {match_phrase: {text: philanthropist}}}")
    print("Notes: Since i intentionally declare \"philanthropist\" as synonym of \"rock\" in the text_analyzer filter, this query returns rock stars ")
    search_phrase(query={"text": "philanthropist"})
    print("\n\n")


def menu():
    while True:
        for idx, topic in model.print_topics(-1):
            print('Topic {}: {}'.format(idx, topic))
        print("\ninsert a keyword")
        q = input()
        print("insert topic id")
        topic = input()
        search_with_topic(query={"abstract": q}, topic=topic)
        print("\n\n")


if __name__ == '__main__':
    # getAllPages(100)
    print("please wait for indexing...")
    model, docs = getTopics(False)
    createIndex(docs)
    sleep(5)

    queries_samples()
    menu()


