#!/usr/bin/python3

import sys
import getopt
import os
import logging
import unittest
from html.parser import HTMLParser

import requests

logging.basicConfig(level=logging.INFO)

class Parser(HTMLParser):
    def __init__(self, start_url, *args, **kwargs):
        HTMLParser.__init__(self)
        self.start_url = start_url
        self.urls_unfiltered = set()
        self.urls = {start_url}
        self.urls_done = set()

        self.session = requests.Session()
        self.urls_saved = 1

        # kwargs parsing
        self.nofollow = "--nofollow" in kwargs
        self.leavedomain = "--leavedomain" in kwargs

    def run(self):
        while len(self.urls) > 0:
            url = self.urls.pop()
            logging.debug("Processing url {}".format(url))
            self.urls_done.add(url)
            try:
                r = self.session.get(url)
                self.feed(r.text)
            except:
                logging.error("", exc_info=True)
            self.urls = (self.urls | self.url_filter(self.urls_unfiltered)) - self.urls_done
            self.save(r, url)
            self.urls_unfiltered = set()
            self.reset()

    def url_filter(self, urls):
        passed = set()
        if self.nofollow and self.urls_saved > 1:
            return passed
        for url in urls:
            if url.find(self.start_url) == 0:
                passed.add(url)
            elif url[0] == "/" and url[:2] != "//":
                passed.add(self.start_url[:-1] + url)
            elif self.leavedomain:
                if url[:4] == "http":
                    passed.add(url)
                elif url[:2] == "//":
                    passed.add("http:"+url)
        return passed

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    url = attr[1].split("#")[0]
                    if url == "":
                        continue
                    self.urls_unfiltered.add(url)
                    logging.debug("Found url: {}".format(url))

    @staticmethod
    def url_decomposer(url):
        address = Parser.url_adress(url)
        path = Parser.url_path(url)
        filename = Parser.url_filename(url)
        return address, path, filename

    @staticmethod
    def url_adress(url):
        return url.split("://")[1].split("/")[0]

    @staticmethod
    def url_filename(url):
        return url.split("/")[-1]

    @staticmethod
    def url_path(url):
        path = "/"
        for directory in url.split("://")[1].split("/")[1:-1]:
            path += directory + "/"
        return path

    @staticmethod
    def url_filetype(url):
        return url.split("/")[-1].split(".")[-1]

    @staticmethod
    def filetype_is_image(filetype):
        return filetype in ["jpg", "jpeg", "png", "gif"]

    @staticmethod
    def url2path(url):
        address, path, filename = Parser.url_decomposer(url)

        if filename == "":
            filename += "index.html"
        elif filename.find(".") == -1:
            filename += ".html"

        return "./output/"+address+path+filename

    def save(self, response, url):
        filetype = Parser.url_filetype(url)
        if filetype == "html":
            self.save_html(response, url)
            filetype_name = "html"
        elif Parser.filetype_is_image(filetype):
            self.save_image(response, url)
            filetype_name = "image"
        else:
            logging.warning("Could not find proper save-method for filetype: '{}' assuming HTML ".format(filetype))
            self.save_html(response, url)
            filetype_name = "html"

        logging.info("Saved {} (#{}) as '{}' with URL '{}'".format(filetype_name, self.urls_saved, self.url2path(url), url))
        logging.debug("Size of urls-set: {}".format(len(self.urls)))
        self.urls_saved += 1

    def save_html(self, response, url):
        page = response.text
        page = page.replace("href=\""+self.start_url, "href=\"./").replace("href=\"/", "href=\"./")
        self._save_file(url, page)

    def save_image(self, response, url):
        image = response.content
        self._save_file(url, image, binary=True)

    def _save_file(self, url, data, binary=False):
        if binary:
            mode = "wb"
        else:
            mode = "w"

        savepath = self.url2path(url)
        address, path, filename = self.url_decomposer(url)
        directory = "output/"+address+path
        if not os.path.exists(directory):
            logging.debug("Creating directory {}".format(directory))
            os.makedirs(directory)
        logging.debug("Saving to {}".format(savepath))
        with open(savepath, mode) as f:
            f.write(data)


class Tests(unittest.TestCase):
    def setUp(self):
        self.parser = Parser("http://www.aaronsw.com/")

    def test_all(self):
        res = self.parser.url_filter(["http://www.aaronsw.com/", "http://google.com/", "/weblog/", "http://reddit.com/submit?url=http://www.aaronsw.com/weblog/whowriteswikipedia"])
        print(res)
        self.assertEqual(res, {"http://www.aaronsw.com/", "http://www.aaronsw.com/weblog/"})
        self.assertEqual(self.parser.url2path("http://google.com/asd/"), "./output/google.com/asd/index.html")

if __name__ == '__main__':
    def usage():
        print("Usage: dump.py -u <url> [--nofollow --leavedomain]")
        
    try:
        args = getopt.getopt(sys.argv[1:], "u:", ["url=", "nofollow", "leavedomain"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    args = {pair[0]: pair[1] for pair in args[0]}
    if not any([arg in args for arg in ['-u', '--url']]):
        print("You need to specify -u flag")
        usage()
        sys.exit(3)

    parser = Parser(args["-u"], **args)
    parser.run()
