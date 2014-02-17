import requests
from html.parser import HTMLParser

start_url = "http://www.aaronsw.com/"

def crawl(page):
    urls = []
    tag = False
    for i, char in enumerate(page):
        if not tag:
            if char == "<" and page[i:i+2] != "</":
                tag = page[i+1:].split()[0]
                if tag == "a":
                    tag_data = page[i+1:].split(">")[0]
                    start = tag_data.find("href=\"")
                    if start >= 0:
                        url = tag_data.split("\"")[1]
                        urls.append(url)
                    else:
                        print("ERROR, FOUND NO END \"!")
        if tag:
            if char == ">":
                tag = False
    return urls

def url_filter(urls):
    passed = set()
    for url in urls:
        if url.find(start_url) == 0:
            passed.add(url)
        elif url[0] == "/":
            passed.add(start_url[:-1] + url)
    return passed

res = url_filter(["http://www.aaronsw.com/", "http://google.com/", "/weblog/", "http://reddit.com/submit?url=http://www.aaronsw.com/weblog/whowriteswikipedia"])
assert res == {"http://www.aaronsw.com/", "http://www.aaronsw.com/weblog/"}

def url2path(url):
    path = "." + "".join(["/"+loc for loc in url.split("/")[3:]])
    if path == "":
        print("ERROR, CASE SHOULD NOT EXIST")
        raise ValueError
    if path[-1] == "/":
        path += "index.html"
    if path[-5:] != ".html":
        path += ".html"
    return path
    
assert url2path("http://google.com/asd/") == "./asd/index.html"

def save(page, url):
    page = page.replace("href=\""+start_url, "href=\"./").replace("href=\"/", "href=\"./")
    i = 0
    #s = re.search(page[i:], "href")
    #while s:
    #    print(s)
    #page = page.replace("href=\"")
    path = url2path(url)

    print(path)
    with open("output/"+path, "w") as f:
        f.write(page)



def main():
    urls = {start_url}
    urls_done = set()
    while len(urls) > 0:
        url = urls.pop()
        urls_done.add(url)
        r = requests.get(url)
        urls = urls | (url_filter(parser.feed(r.text)) - urls_done)
        save(r.text, url)
        print(urls)

class Parser(HTMLParser):
    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    url = attr[1].split("#")[0]
                    if url == "":
                        continue
                    self.urls.add(url)
                    print("Found url: {}".format(url))

    def feed(self, data):
        self.urls = set()
        HTMLParser.feed(self, data)
        return self.urls


parser = Parser()
main()
