## A General Purpose Web Crawler based on PageRank
------
### Stucture of Files
  1. Output Logs: Two queries with two different spiders, which are BFS spider and PageRank spider, so there are four files. Please note that, to make the output results well format, I output the results as an excel file.
 
```The file name is named in this format:<Query>_<Spider>_Spider_Results.xls```

  2. 1 Python File: This file contains all the source code for this project. There are around 470 lines including comments.
  3. 2 Bloomfilter Files: These two files are used to check the same content file that accessed before using Bloomfilter method. But they are the output files by the program. Please do not use them when you re-run the program. It might cause 		the program would detect the content that have crawler last time.
------
### How to Compile
  1. Language Version: Python 2.7.14
  2. Dependencies: There are three dependencies at all: BeautifulSoup4, Google, BloomFilter. If you are not make sure whether you have installed the above three python modules, please type the following three commands to install the dependencies。
  
```pip install beautifulsoup4```


```pip install google```


```pip install pybloomfiltermmap```


  3. Two ways to compile this program:
	* Type "python web_crawler.py" to the terminal 
	* Use other Python IDE(such as PyCharm) is also well
------
### Before Runtime
  1. Simply customize the parameters that you want in the def main() function
	Initialize one Crawler instance, such as: web_crawler = Crawler("knuckle sandwich", 10)
	The first parameter is the item you want to query, the second item is the start pages you want to get from the google api
					* Customize your own spider
						* customize the BFS spider, such as: web_crawler.bfs_spider(8, 1000)
							* The first parameter means the max pages that you want to extract from one single page
							* The second parameter means the maximum pages that you want to crawl at this time
    					* customize the PageRank spider: web_crawler.page_rank_spider(10, 10, 20)
    						* The first parameter means the max pages that you want to extract from one single page
    						* The second parameter means the timer you want to setup that to update the PageRanks periodically
    							* Please note that, do not set this value too small, since it will update the PageRanks frequently, and also do not set too big, since the spider would stop the jobs if the priority queue is empty
    						* The third parameter means the maximum pages that you want to crawl at this time
    2. Then run the program with the terminal or by Python IDE!
