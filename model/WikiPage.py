import wikipediaapi
from time import sleep

class WikiPage:
    id = ""
    url = ""
    title: ""
    abstract: ""
    text: ""
    citations = 0
    citations_norm = 0

    def __init__(self, page: wikipediaapi.WikipediaPage):
        self.id = page.title.replace(" ", "_")
        sleep(1)
        self.url = page.fullurl
        sleep(1)
        self.title = page.title
        sleep(1)
        self.abstract = page.summary
        sleep(1)
        self.text = page.text

        back_pages = []
        for key in page.backlinks.keys():
            back_p = page.backlinks.get(key)
            if back_p.namespace == wikipediaapi.Namespace.MAIN:
                back_pages.append(back_p)

        self.citations = len(back_pages)


    def setCitationsNorm(self, citations_normalized):
        self.citations_norm = citations_normalized


    def __str__(self):
        return self.title


    def __iter__(self):
      #  yield 'id', self.id
        yield 'url', self.url
        yield 'title', self.title
        yield 'abstract', self.abstract
        yield 'text', self.text
        yield 'citations', self.citations
        yield 'citations_norm', self.citations_norm