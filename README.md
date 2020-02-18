Assignment #2: Replication Part 1 (Due Feb 15, 11:59 PM)
===============================

In this assignment I:

1.  Statistically assess and explain/analyze the features/statistics/target 
    needed for the replication (report).
    
2.  Develop replication and data cleaning (code).

* * * * *

### Part 1 -> found in src/etl.py and notebooks/Report.ipynb

* (Download) Downloaded the 
    [light dump data](http://wwm.phy.bme.hu/LD/ld_en_wiki.zip) 
    of the English Wikipedia from the 
    [WikiWarMonitor](http://wwm.phy.bme.hu/light.html) website. 
    -   Articles are separated by their names within the file. 
    -   Each line of the file below the name of an article, contains a 
        delimiter "^^^" followed by the timestamp of each edit, a binary flag 
        of 0/1 corresponding to a normal/revert edit, an accenting integer 
        code, starting from 1, assigned to each new revision, whose text is 
        not similar to any of the previous ones, otherwise the same code as 
        the previous version with the similar text, and finally the editor of 
        the version.

* (Descriptive Stats) Statistically summarized the attributes in the light dump 
    data. -> found in notebooks/Report.ipynb

* (Edit Wars) Replicated the paper on edit war.
    -   Derived the algorithm described in [Yasseri et al 2012a](https://arxiv.org/pdf/1107.3689.pdf) -> found in src/etl.py
        and calculated the M statistic for each article in the light dump data.
    -   Described and the most and the least controversial articles by listing 
        the titles of 20 articles with the largest M and the titles of 20 
        articles with the smallest M along with their corresponding M 
        statistic. -> found in notebooks/Report.ipynb
    -   Described and visualized how controversiality for 2 articles evolve 
        over time by plotting date on the x-axis and the M statistic on the
        y-axis. Took [Yasseri et al 2012b](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0038869) 
        as a reference.  -> found in notebooks/Report.ipynb
        
* (Raw Data to Light Dump Revisited) 
    -   Validated the data ingestion I did for the first assignment by 
        comparing the light dump downloaded from WikiWarMonitor with any 
        2 of the articles you ingested in the first assignment over the same 
        period of time as a way to test whether you did the data ingestion and 
        cleaning correctly. 
        They are in line with each other. Namely, they do point to the same
        sets of reverts between edits.
        There were some errors in your code for ingestion, but not fixed : - ). 
        -> found in src/etl.py
    -   Revised the code for data ingestion (from raw format to light dump 
        format) and cleaned to enhance efficiency and correct the error.
        -> found in src/etl.py


### Part 2 -> found in src/etl.py

Developed code to calculated the M statistic from data in light dump format. 
Revised the code to ingest and clean the data from raw format to light dump 
format. Such code conforms to the methodology portion of the course 
(e.g. using the project template).

In particular, my project should has a `run.py` with the following
targets:
1. `data` creates the data needed for analysis.
2. `process` cleans and prepares the data for analysis (e.g. cleaning
   and feature creation).
3. `data-test` ingests a small amount of *test data* (that `process`
   can then process).
