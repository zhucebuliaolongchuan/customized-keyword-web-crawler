#!/usr/bin/env python 2.7
# -*- coding: utf-8 -*-
__author__ = 'longchuan2773@gmail.com'
from google import search
from urllib2 import URLError, HTTPError
from bs4 import BeautifulSoup
from heapq import *
import pybloomfilter
import robotparser
import collections
import random
import urllib2
import urlparse
import re
import time
import socket
import ssl

# This class serves to handle a url object, including the initial PageRank, final PageRank, accessed time, status code, etc.
class Urls(object):
    def __init__(self, url):
        self.url = url
        self.initial_page_rank = 0.0
        self.page_rank = 0.0
        self.in_links = set()
        self.out_links = set()
        self.accessed = False
        self.content_length = None
        self.time_stamp = None
        self.status_code = None

    def set_status_code(self, code):
        self.status_code = code

    def set_initial_page_rank(self, rank):
        self.initial_page_rank = rank
        return None

    def set_page_rank(self, rank):
        self.page_rank = rank
        return None

    def set_accessed(self):
        self.accessed = True
        return None

    def set_content_length(self, length):
        self.content_length = length
        return None

    def set_time_stamp(self):
        self.time_stamp = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

    def add_in_links(self, link):
        self.in_links.add(link)
        return None

    def add_out_links(self, link):
        self.out_links.add(link)
        return None

    def get_initial_page_rank(self):
        return self.initial_page_rank

    def get_page_rank(self):
        return self.page_rank

    def get_out_links(self):
        return self.out_links

    def get_in_links(self):
        return self.in_links

    def get_accessed(self):
        return self.accessed

    def get_time_stamp(self):
        return self.time_stamp

    def get_status_code(self):
        return self.status_code

    def get_content_length(self):
        return self.content_length

# This class serves to handle a crawler object. Including the attributes of a crawler should have and also the operations that need to do during the crawling
class Crawler(object):
    def __init__(self, query, num):
        """
        The initial function.
        :param query: query string
        :param num: the number of the start pages
        """
        self.query = query
        self.n = num
        self.file_index = 0
        self.queue = []
        self.pq = []
        self.url_obj = {}
        self.order = []
        self.total_sizes = 0
        self.errors = collections.defaultdict(int)
        self.total_files = 0
        self.start_time = None
        self.end_time = None
        self.bloom_filter = pybloomfilter.BloomFilter(1000, 0.00001, self.query + "_bf")

    def get_start_pages(self):
        """
        Get the initial 10 start pages using google api
        :return: void.
        """
        print "Getting the initial pages"
        for url in search(self.query, tld="com", num=self.n, start=0, stop=1, pause=2):
            if url not in self.url_obj:
                self.url_obj[url] = Urls(url)
                self.queue.append(url)
        # Set up the PageRank value for the start pages
        page_rank_value = 1.0 / len(self.url_obj)
        for key in self.url_obj:
            self.url_obj[key].set_page_rank(page_rank_value)
            print key
        print "\n"

    def download_url(self, url):
        """
        This method serves to download the content of the given url
        :param url: download the html file of the given url
        :return: the html file of the given url, and the status code of the given url
        """
        # Download the url content first, store them into the /pages/
        req = urllib2.Request(url)
        # Add header, pretend to be an Internet Explorer
        # req.add_header("User-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
        try:
            response = urllib2.urlopen(req, None, 10)
            self.total_files += 1
        except socket.timeout:
            print "Time out"
            self.order.append(url)
            self.url_obj[url] = Urls(url)
            self.url_obj[url].set_accessed()
            self.url_obj[url].set_time_stamp()
        except ssl.SSLError:
			print "SSL Error"
        except HTTPError, e:
            if e.code == 400:
                print "Bad Request\n"
            elif e.code == 401:
                print "Unauthorized\n"
            elif e.code == 403:
                print "Forbidden\n"
            elif e.code == 404:
                print "Page Not Found\n"
            else:
                print 'HTTPError code: ', str(e.code) + "\n"
            self.errors[e.code] += 1
            self.order.append(url)
            self.url_obj[url] = Urls(url)
            self.url_obj[url].set_accessed()
            self.url_obj[url].set_time_stamp()
            self.url_obj[url].set_status_code(e.code)
        except URLError, e:
            print 'URLError code: ', e.reason
        except UnicodeEncodeError:
			print "UnicodeEncodeError"
        else:
            # content = response.read()
            # # Download the pages, even though I don't know why we should do this
            # with open("pages/" + str(self.file_index) + ".txt", "w") as f:
            #     f.write(content)
            # f.close()
            return response

    def fetch_url(self, current_link, response, limited):
        """
        This method serves to handle the urls in the html file, add the urls to the link, and also update the url_obj
        Methods: Filter the content type which are not text/html, and also check the bloom_filter
        :param current_link: the current url that being crawled now
        :param response: the html file of the given url
        :param limited: the limited pages that crawled from the same html file
        :return: void.
        """
        # Method 1: Parse with Regular Expression
        # url_pattern = r'(href="http://[\s\S]+.html")'
        # pattern = re.compile(url_pattern)
        # matches = re.findall(pattern, html)
        # Method 2: Parse with BeautifulSoup4 and match with re
        # The method to fetch the url is not so comprehensive now
        print "Processing:", current_link
        html = response.read()
        # Get the MIME type of the html
        content_type = None
        if len(response.info().getheaders("Content-Type")) > 0:
            content_type = response.info().getheaders("Content-Type")[0]
        if content_type is None or "text/html" in content_type:
            # Set the status of the pages, included accessed, time_stamp, content length
            self.url_obj[current_link].set_accessed()
            self.url_obj[current_link].set_time_stamp()
            self.url_obj[current_link].set_status_code(200)
            self.order.append(current_link)
            self.url_obj[current_link].set_content_length(len(html))
            self.total_sizes += len(html)
            if html not in self.bloom_filter:
                self.bloom_filter.add(html)
                try:
                    soup = BeautifulSoup(html, "html.parser")
                except TypeError:
                    print "TypeError\n"
                else:
                    base_link = soup.find("base").get("href") if soup.find("base") else current_link
                    for link in soup.find_all("a"):
                        if limited <= 0:
                            break
                        else:
                            limited -= 1
                        url = link.get("href")
                        # Join the relative links and the base link if needed
                        url = urlparse.urljoin(base_link, url)
                        url_pattern = r"http://[\s\S]+"
                        pattern = re.compile(url_pattern)
                        try:
                            # Handle the url if it matches the pattern and is also allowed to be accessed
                            if pattern.match(url) and self.is_allowed(current_link, url) and self.is_matched_type(url):
                                self.url_obj[current_link].add_out_links(url)
                                if url not in self.url_obj:
                                    # print "Fetching:", url
                                    self.queue.append(url)
                                    self.url_obj[url] = Urls(url)
                                # else:
                                    # print "Opened", url
                                self.url_obj[url].add_in_links(current_link)
                        except TypeError:
                            continue
                        else:
                            continue
                print "Successfully fetch all the valid urls from this html file\n"
            else:
                print "Access the same content before\n"
        else:
            print "The content-type of the html file is not text/html\n"

    def bfs_spider(self, limited, max_pages):
        """
        # This method serves to crawl the pages based on BFS method, based on a queue
        :param limited: the limited number of pages that should be crawled from one single page
        :param max_pages: the maximum number of page should be crawled at all
        :return: Void. Crawl the pages using BFS method
        """
        self.start_time = time.time()
        self.get_start_pages()
        while len(self.queue) > 0 and len(self.order) < max_pages:
            url = self.queue.pop(0)
            if self.url_obj[url].get_accessed() is False:
                content = self.download_url(url)
                if content is not None:
                    self.fetch_url(url, content, limited)
        print "BFS spider completed the crawl jobs"
        self.end_time = time.time()
        self.print_out_result("BFS")

    def page_rank_spider(self, limited, timer, max_pages):
        """
        # This method serves to crawl the pages based on the PageRank value, based on a priority queue
        :param limited: the limited number of pages that should be crawled from one single page
        :param timer: re-calculate the PageRank value using timer
        :param max_pages: the maximum number of page should be crawled at all
        :return: Void. Crawl the pages using PageRank method
        """
        self.start_time = time.time()
        temp = timer
        self.get_start_pages()
        self.update_page_rank()
        last_page_rank_value = self.pq
        while len(self.pq) > 0 and len(self.order) < max_pages:
            # Update the PageRanks periodically, and also check whether the PageRanks converge or not
            if temp <= 0:
                self.update_page_rank()
                just_update_page_rank = True
                if self.is_same_pq(self.pq, last_page_rank_value) is True:
                    print "The graph of all the pages has been converged"
                    break
                else:
                    last_page_rank_value = self.pq
                temp = timer
            else:
                just_update_page_rank = False
                temp -= 1
            if len(self.pq) > 0:
                value, url = heappop(self.pq)
                if self.url_obj[url].get_accessed() is False:
                    content = self.download_url(url)
                    # if it is valid to access the given url, then fetch them
                    if content is not None:
                        self.fetch_url(url, content, limited * 2 if just_update_page_rank else limited)
        # Print out the PageRank value of all pages
        self.update_page_rank()
        self.end_time = time.time()
        print "PageRank spider completed the crawl jobs"
        self.print_out_result("PageRank")

    def update_page_rank(self):
        """
        This method serves to update the pagerank value of all the existed nodes
        :return: the priority queue that contains the values of the PageRank of all the pages
        """
        def matrix_multiply(A, B):
            result = [[0] * len(B[-1]) for _ in range(len(A))]
            for i in range(len(A)):
                for j in range(len(B[-1])):
                    for k in range(len(B)):
                        result[i][j] += A[i][k] * B[k][j]
            return result

        def matrix_multiply_n(A, n):
            result = [[1] * len(A[0]) for _ in range(len(A))]
            for i in range(len(A)):
                for j in range(len(A[0])):
                    result[i][j] = n * A[i][j]
            return result

        def matrix_add(A, B):
            if len(A[0]) != len(B[0]) and len(A) != len(B):
                return
            else:
                result = [[0] * len(A[0]) for _ in range(len(A))]
                for i in range(len(A)):
                    for j in range(len(A[0])):
                        result[i][j] = A[i][j] + B[i][j]
                return result

        def tran_and_convert(A):
            result = [[0] * len(A[0]) for _ in range(len(A))]
            result_convert = [[0] * len(A[0]) for _ in range(len(A))]
            for i in range(len(A)):
                for j in range(len(A[0])):
                    result[i][j] = A[i][j] * 1.0 / sum(A[i]) if sum(A[i]) != 0 else 0.0
            for p in range(len(result)):
                for q in range(len(result[0])):
                    result_convert[p][q] = result[q][p]
            return result_convert
        url_id = collections.defaultdict(int)
        id_url = collections.defaultdict(str)
        i = 0
        for key in self.url_obj:
            url_id[key] = i
            id_url[i] = key
            i += 1
        transfer_matrix = [[0.0 for _ in range(len(self.url_obj))] for _ in range(len(self.url_obj))]
        # Initial the transfer matrix
        for key in self.url_obj:
            out_links = self.url_obj[key].get_out_links()
            for link in out_links:
                transfer_matrix[url_id[key]][url_id[link]] = 1.0
        transfer_convert_matrix = tran_and_convert(transfer_matrix)
        norm = 100
        # delta = 0.00000001 It will cost so many time if the value of Delta is pretty small
        delta = 0.01
        damping_factor = 0.85
        e = [1.0 for _ in range(len(url_id))]
        new_page_value = [[random.random()] for _ in range(len(url_id))]
        r = [[(1 - damping_factor) * i * 1 / len(url_id)] for i in e]
        while norm > delta:
            temp_page_value = new_page_value
            # P=(1-d)*e/n+d*M'P
            new_page_value = matrix_add(r, matrix_multiply_n(matrix_multiply(transfer_convert_matrix, temp_page_value), damping_factor))
            norm = 0
            for i in range(len(url_id)):
                norm += abs(new_page_value[i][0] - temp_page_value[i][0])
        # Update the PageRank value for each url
        for i in range(len(new_page_value)):
            url = id_url[i]
            # If the PageRank value is 0.0, which means this is the estimated PageRank at the very beginning
            if self.url_obj[url].get_page_rank() == 0.0:
                self.url_obj[url].set_initial_page_rank(new_page_value[i][0])
            self.url_obj[url].set_page_rank(new_page_value[i][0])
        # Update the priority queue also, please note that the priority score is the -1 * PageRank value in order to fetch max priority
        print "The PageRank values have been updated\n"
        self.pq = []
        for key in self.url_obj:
            if self.url_obj[key].get_accessed() is False:
                heappush(self.pq, (self.url_obj[key].get_page_rank() * -1, key))

    @staticmethod
    def is_allowed(base_url, attempted_url):
        """
        :param base_url: the absolute url
        :param attempted_url: the absolute url or the relevant url
        :return: return the combine valid url
        """
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(base_url + "robots.txt")
            rp.read()
        except IOError:
            return False
        else:
            # return rp.can_fetch("*", attempted_url)
            try:
                rp.can_fetch("*", attempted_url)
            except KeyError:
                print "KeyError"
                return False
            else:
                return rp.can_fetch("*", attempted_url)

    @staticmethod
    def is_matched_type(url):
        """
        :param url: the url that need to verify
        :return: return True if the url is not the file that we have to ignore
        """
        black_end_lists = [".asp", ".jpg", ".jsp", ".pdf", ".mp4", ".mp3", ".wmv"]
        for s in black_end_lists:
            if url.endswith(s) is True:
                return False
        return True if "cgi" not in url else False

    @staticmethod
    def is_same_pq(pq1, pq2):
        """
        :param pq1: the first pq
        :param pq2: the second pq
        :return: return True if these two pqs contains the same element, which means the PageRanks have been converged
        """
        if len(pq1) == len(pq2):
            for _ in range(len(pq1)):
                min1 = heappop(pq1)
                min2 = heappop(pq2)
                if min1 != min2:
                    return False
            return True
        else:
            return False

    def print_out_result(self, string):
        """
        :param string: The string indicates which spider is working now
        :return: Print out all the statistics results about this crawl
        """
        with open(self.query + "_" + string + "_Spider_Results.xls", "w") as f:
            f.write("=============================================Query for " + self.query + "=============================================" + "\n")
            f.write("==================================================Statistics==================================================" + "\n")
            start = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(self.start_time))
            f.write("Start Time:" + "\t" + start + "\n")
            end = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(self.end_time))
            f.write("End Time:" + "\t" + end + "\n")
            f.write("Time Used:" + "\t" + str(self.end_time - self.start_time) + "\n")
            f.write("Number of Total Files:" + "\t" + str(self.total_files) + "\n")
            f.write("Total Size of All Files:" + "\t" + str(self.total_sizes) + "\n")
            if len(self.errors) > 0:
                f.write("Errors:\n")
                for error in self.errors:
                    f.write("There are\t" + str(self.errors[error]) + "\t" + str(error) + "\n")
            f.write("==================================================  Pages  ==================================================" + "\n")
            f.write("Status Code\tAccess Time\tContent Length\tinitial PageRank\tFinal Page Rank\tIn\tOut\tURL\n")
            for url in self.order:
                status_code = self.url_obj[url].get_status_code()
                time_stamp = self.url_obj[url].get_time_stamp()
                initial_pr = self.url_obj[url].get_initial_page_rank()
                pr = self.url_obj[url].get_page_rank()
                size = self.url_obj[url].get_content_length()
                in_links = len(self.url_obj[url].get_in_links())
                out_links = len(self.url_obj[url].get_out_links())
                s = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (status_code, time_stamp, size, initial_pr, pr, in_links, out_links, url)
                f.write(s)
        f.close()


def main():
    web_crawler = Crawler("ebbets field", 10)
    web_crawler.bfs_spider(10, 1000)
    # web_crawler.page_rank_spider(8, 10, 1000)


if __name__ == '__main__':
    main()
