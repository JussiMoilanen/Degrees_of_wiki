import requests
import urllib.request
import re
from queue import Queue
from time import time
from threading import Thread
from bs4 import BeautifulSoup

'''Testing...
    Taiwan -> Basketball 1 degree
    Whisky -> Basketball 2 degree
    Teetotalism -> Basketball 3 degrees
    Chain of 5: British Columbia → Longhorn beetle → Lamiinae → Apomecynini → Sybra → Sybra fuscotriangularis
    Digital_Signature_Algorithm -> Federal Information Processing Standard -> United States federal government -> national government
'''

'''
based on: 
https://github.com/connerlane/degrees-of-wikipedia/
https://github.com/jwngr/sdow

'''

class Page:
    def __init__(self, title, parent, depth=1):
        self.title = title
        self.parent = parent
        self.depth = depth


def strip_url(url):
    return re.search(r"\/wiki\/(.+)$", url).group(1)


def whatLinkshere(endurl):
    print("Gets all links that links to end page")
    keyword = strip_url(endurl)
    print(keyword)
    whatlinkshere = []
    backurl = 'https://en.wikipedia.org/w/index.php?title=Special:WhatLinksHere/' + keyword + '&limit=500'
    r = requests.get(backurl)
    soup = BeautifulSoup(r.content, 'html.parser')
    for ul in soup.find_all('ul', {'id': 'mw-whatlinkshere-list'}):
        for li in ul.find_all('li'):
            for link in li.find_all('a'):
                if "/wiki/" in str(link):
                    whatlinkshere.append((link.get('title')))
    return whatlinkshere

def get_links_from_page(connection):
    links = []
    soup = BeautifulSoup(connection, "lxml").find(
        "div", {"id": "mw-content-text"})
    # exlude "references" section
    for div in soup.find_all("div", {'class': 'reflist'}):
        div.decompose()
    for div in soup.find_all("div", {'class': 'navbox'}):
        div.decompose()
    for div in soup.find_all("div", {'class': 'refbegin'}):
        div.decompose()
    for paragraph in soup.findAll('p'):
        for link in paragraph.findAll('a'):
            if link_is_valid(link):
                links.append(link)
    for list in soup.findAll('ul'):
        for link in list.findAll('a'):
            if link_is_valid(link):
                links.append(link)
    links = [(link.get('href')[6:]) for link in links]
    return links

def link_is_valid(link):
    if link.get('href') and link.get('href')[:6] == "/wiki/":
        if (link.contents and str(link.contents[0])[0] != "<"
                and ":" not in link.get('href')):
            return True
    return False


def check_links(links, pagevisited, queue, page, linkers, endpath):
    for title in links:
        if title not in pagevisited:
            pagevisited.add(title)
            queue.put(Page(title, page, page.depth + 1))
            if title in linkers:
                secondtitle = (linkers[linkers.index(title)])
                page = Page(secondtitle, page, page.depth + 1)
                print("######## Path found #########")
                return page
    return None

def connect_page(page, connections):
    connections.append((page, urllib.request.urlopen("https://en.wikipedia.org/wiki/" + page.title)))


def bfs(starturl, endurl, linkers):
    pagevisited = set()
    queue = Queue()
    queue.put(Page(strip_url(starturl), None))
    endpath = strip_url(endurl)
    current_depth = 1
    web_links = []

    while True:
        if not queue.empty():
            # get() = Remove and return an item from the queue
            page = queue.get()

        if queue.empty() or page.depth > current_depth:
            print("checking {} links on level {}".format(
                len(web_links), current_depth))
            if not queue.empty():
                current_depth += 1
            while web_links:
                connections = []
                threads = []
                ''' Implemented threading that we can parse 100 pages at the same time'''
                for i in range(100):
                    if web_links:
                        thread = Thread(target=connect_page, args=(web_links.pop(), connections))
                        threads.append(thread)
                        thread.start()
                for i in range(len(threads)):
                    threads[i].join()
                for connection in connections:
                    links = get_links_from_page(connection[1])
                    result = check_links(links, pagevisited, queue, page, linkers, endpath)
                    if result:
                        return result
                if web_links:
                    print("{} links left to check...".format(len(web_links)))

        web_links.append(page)


if __name__ == "__main__":
    print("Finding the shortest path between two wikipedia pages.")

    start = input("Give starting page: ")
    end = input("Give page where you want to go: ")

    start_time = time()
    starturl = "https://en.wikipedia.org/wiki/" + start
    endurl = "https://en.wikipedia.org/wiki/" + end

    '''Linkers is a list that has pages that links to endurl'''
    linkers = whatLinkshere(endurl)

    result = bfs(starturl, endurl, linkers)
    path = []
    if result:
        print("Path found in {:.2f} seconds.".format(time() - start_time))
        print("The depth of path is " + str(result.depth) + " degrees.")
        while result.parent:
            path.append(result.title)
            result = result.parent
        path.append(result.title)
        path.reverse()
        print(" -> ".join(path) + " -> " + end)
    else:
        print("Path was not found")
