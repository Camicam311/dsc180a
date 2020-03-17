Wikipedia M-Statistic Replication Project
===============================

* An introduction to the problem
    * As an encyclopedia that is strives to maintian its credibility while
      still being built by the crowdsourced information, Wikipedia is
      constantly bombarded with edits by editors around the world trying
      that often spread misinformation. Often times, researchers want to
      learn more and study this phenomenon, with even Wikipedia themselves
      trying to flag some of these articles as hotly debated, or 
      "controversial." But with over 6 million articles on the English
      version alone and millions more across other platforms, its a pretty
      difficult task to label and find all the controversial articles out
      there. This is where the M-Statistic comes in, which is a clever
      method of meausring whether an article is controversial or not based
      on the article's edit history and editors, namely editors that revert
      different changes to old changes. A revert, in this case, is any edit
      that just overwrites any recent changes with another version in the
      edit history.

* An introduction to the data and data generation process
    * Now to devise this statistic, we just need to take a peek at the
      widely-used Wikipedia data dumps. These are data dumps of XML files,
      which contains the edit history of Wikipedia articles formatted in
      a XML structure, which can be found [here](https://meta.wikimedia.org/wiki/Data_dumps/Dump_format). These data dumps are
      monthly collected and dumped [here](https://dumps.wikimedia.org/), but for this project
      replication, we will be focusing on the English version. The latest
      data dump that we are working with can be found [here](https://dumps.wikimedia.org/enwiki/20200201/). 
      
      In this project, I have created a method that can directly take the
      urls of these Wikimedia data dumps like this one: 
      https://dumps.wikimedia.org/enwiki/20200201/enwiki-20200201-pages-meta-history1.xml-p10p1036.7z
      It is also able to directly read in there zipped data files. The project
      will proceed to unzip the data to access the XML files, which can be
      further reduced to a format that will collect purely the necessary
      information for the project, which we will call light-dump format.
      This includes the timestamp, the id number of a specific edit, whether
      an edit was a revert, and the username or IP address of the editor.
      My project is able to take in the unzipped files and convert them into
      this format to preserve just this information, or even a readable csv
      format. This, be warned, is extremely large and meant for just to look
      at. If you run this csv version, be prepared with an expensive (in terms
      of cost and memory efficiency) process and data file. My project
      completes these steps through parsing through XML trees and focusing
      on desired tags within the files, like the ones used in the light-dump
      format.

* A brief review of historical context
    * Wikipedia was created in early mid-January 2001, built to be an
      online encyclopedia that anyone could edit. Based on this fact, it was
      only natural for "controversial" articles to arise, with many "historical"
      occurances have multiple viewpoints and interpretations of the matter.
      Since 2007, many reserachers have developed different methodologies of
      detecting this, including using the number of reverts/page edits, 
      analyzing the number of words deleted by edits, the time between edits,
      and the number of mutual editors (editors that revert one another).

* EDA, assessment of reliability of data, summary statistics, 
  need for cleaning and justification for approach to cleaning
    * In our case of handling this data, there is not much cleaning that was
      needed to properly construct our M-Statistic. The data dumps from
      Wikipedia are already quite well constructed, and we as data analysts
      focus on collecting the necessary information and removing any "noise,"
      or unnecessary information, from each edit, thereby focusing on certain
      aspects of each edit.
      
    * When looking at just the light-dump data supplied directly the
      [WikiWarMonitor](http://wwm.phy.bme.hu/light.html) website, we can observe the following
      summary statistics on the English Wikipedia platform up to 2010:
      * Stats Overall
          * Number of Articles: 4644568
          * Number of Articles with Reverts: 1481874
          * Number of Controversial Articles: 25548
          * Most Number of Edits in any Article: 43650
          * Most Number of Reverts in any Article: 14630
          * Most Number of Editors in any Article: 13784
          * Most Number of Mutual Editors: 355
      * Stats Specific to Articles with Reverts (focus of this project):
          * Average Number of Edits (Including Reverts): 123.39636568291232
          * Average Number of Purely Reverts: 13.24227768352775
          * Average M-Statistic: 612.5267910767042
          * Average Number of Mutual Editors: 0.43433044914749835
          * Average Number of Editors: 60.42453406969823

* Explanation of the calculation of M-Statistic
    * The M-Statistic theoretically is defined in the following equation:
      <img src="https://render.githubusercontent.com/render/math?math=M = E * \displaystyle\sum_{(N_i^d,N_j^r) < max}min(N_i^d,N_j^r)">
      
      Here, M is the M-Statistic and E is the total number of mutual editors.
      As for <img src="https://render.githubusercontent.com/render/math?math=i"> and <img src="https://render.githubusercontent.com/render/math?math=j"> in <img src="https://render.githubusercontent.com/render/math?math=N_i^d"> and <img src="https://render.githubusercontent.com/render/math?math=N_j^r">, we are considering
      editors in an edit history in the following order:
      <img src="https://render.githubusercontent.com/render/math?math=1, ..., i - 2, i - 1, i, i + 1, ..., j - 1, j, j + 1, ...">
      The <img src="https://render.githubusercontent.com/render/math?math=j"> in <img src="https://render.githubusercontent.com/render/math?math=N_j^r"> references the editor who performed the revert to
      the edit <img src="https://render.githubusercontent.com/render/math?math=i - 1">, and <img src="https://render.githubusercontent.com/render/math?math=i"> in <img src="https://render.githubusercontent.com/render/math?math=N_i^d"> would be the editor who's own
      edit was essentially overwritten by editor <img src="https://render.githubusercontent.com/render/math?math=j">. <img src="https://render.githubusercontent.com/render/math?math=N_i"> and <img src="https://render.githubusercontent.com/render/math?math=N_j"> is
      going to be the number of total edits in the current article from
      editors <img src="https://render.githubusercontent.com/render/math?math=i"> and <img src="https://render.githubusercontent.com/render/math?math=j"> respectively.
      
      A better way to explain this editor <img src="https://render.githubusercontent.com/render/math?math=i"> and <img src="https://render.githubusercontent.com/render/math?math=j"> concept would be with
      an example. Let's say that a page has a set of edits starting from edit #1
      and ending with the most recent edit #5. In the edit history, each
      edit will have an id like #1 or #5 that coincides with the text of each
      edit, meaning a revert to edit #1 will also have an edit id of #1. So
      let's say the edit history is #1, #2, #3, #1, #4, #5, with the respective
      editors being Ann, Bob, Cal, Ann, Dav, and Eve. That means the fourth
      edit, or the second instance of edit id #1, was a revert back to the
      first edit. In this case of the revert, Ann, who was the editor for both
      edits with edit id #1, reverted and screwed over Bob, the editor of edit
      id #2. In this example, <img src="https://render.githubusercontent.com/render/math?math=j"> in <img src="https://render.githubusercontent.com/render/math?math=N_j^r"> would be Ann and <img src="https://render.githubusercontent.com/render/math?math=i"> in
      <img src="https://render.githubusercontent.com/render/math?math=N_i^d"> would be Bob.
      
      So, back to the equation, we are ideally trying to take into account
      every instance of a revert through the summation. For every revert, the
      equation sums up the fewer number of total edits between editor <img src="https://render.githubusercontent.com/render/math?math=i"> and
      editor <img src="https://render.githubusercontent.com/render/math?math=j">. This summation excludes the pair of reverts whose minimum
      between the two totals is the greatest in the summation. Then, this
      summation is weighted by <img src="https://render.githubusercontent.com/render/math?math=E"> to take into account of the mututal editors.
      
      In my particular interpretation ignore cases when an editor reverts back
      to the same edit multiple times (i.e. Edit <img src="https://render.githubusercontent.com/render/math?math=j"> and edit <img src="https://render.githubusercontent.com/render/math?math=j"> + 1 both
      revert back to edit <img src="https://render.githubusercontent.com/render/math?math=i">). I also ignore when the editor is simply reverting
      back to themselves (i.e. Editor of edit <img src="https://render.githubusercontent.com/render/math?math=i - 1"> and editor of edit <img src="https://render.githubusercontent.com/render/math?math=j"> are
      the same editors). My summation also takes into account of all editors,
      regardless of whether or not either or both of the editors were also mutual
      editors. I additionally count every instance of a revert, regardless of
      whether of not the editors had reverted one another previously.
      
      
* Calculate M-Statistic using cleaned data in light-dump format (assgn 2)
  * Present a table of top articles with max/min M-statistic and explain 
    what you find
    
    Top Articles with Max M-Statistics
    |    | Title                                           | M-Statistic |
    |----|-------------------------------------------------|-------------|
    | 0  | George_W._Bush                                  | 34813075    |
    | 1  | List_of_World_Wrestling_Entertainment_employees | 21728308    |
    | 2  | Anarchism                                       | 20108760    |
    | 3  | Muhammad                                        | 13696900    |
    | 4  | Barack_Obama                                    | 10713048    |
    | 5  | Global_warming                                  | 9387070     |
    | 6  | Circumcision                                    | 8561498     |
    | 7  | United_States                                   | 7448470     |
    | 8  | Jesus                                           | 7403452     |
    | 9  | Michael_Jackson                                 | 6798324     |
    | 10 | Race_and_intelligence                           | 6266760     |
    | 11 | Christianity                                    | 5912382     |
    | 12 | Islam                                           | 5674900     |
    | 13 | Adolf_Hitler                                    | 5352642     |
    | 14 | Falun_Gong                                      | 4498520     |
    | 15 | Chiropractic                                    | 4420364     |
    | 16 | September_11_attacks                            | 4229020     |
    | 17 | 2006_Lebanon_War                                | 3980830     |
    | 18 | Wikipedia                                       | 3886632     |
    | 19 | Kosovo                                          | 3760680     |
    
    Bottom Articles with Max M-Statistics
    |    | Title                                           | M-Statistic |
    |----|-------------------------------------------------|-------------|
    | 0  | !!Fuck_you!!                                    | 0           |
    | 1  | 'Twas_in_the_Moon_of_Wintertime                 | 0           |
    | 2  | (Come_Round_Here)_I'm_The_One_You_Need          | 0           |
    | 3  | (International)_Year_of_the_Dolphin             | 0           |
    | 4  | (What_Did_I_Do_To_Be_So)_Black_and_Blue         | 0           |
    | 5  | (Where_Were_You)_When_the_World_Stopped_Turning | 0           |
    | 6  | (Who_Wrote)_The_Book_of_Love                    | 0           |
    | 7  | 1000_Chips_Delicious                            | 0           |
    | 8  | 1000_Recordings_To_Hear_Before_You_Die          | 0           |
    | 9  | 1911_in_Denmark                                 | 0           |
    | 10 | 420BC                                           | 0           |
    | 11 | 69BC                                            | 0           |
    | 12 | Big_Love_(song)                                 | 0           |
    | 13 | Big☆Bang!!!                                     | 0           |
    | 14 | Sex,_Pies_&_Idiot_Scrapes                       | 0           |
    | 15 | Sexy_jutsu                                      | 0           |
    | 16 | Dead_Space_(video_game)                         | 0           |
    | 17 | Bikini_Bottom                                   | 0           |
    | 18 | Married..._with_Children                        | 0           |
    | 19 | 69th_parallel                                   | 0           |
    
    The top twenty articles clearly focus on some pretty well known topics
    that generally have many opposing opinions on. I personally cannot 
    comment on a few of them like 
    "List_of_World_Wrestling_Entertainment_employees," but many of the 
    others are hotly debated and talked about by media new outlets and
    people in general. For example, President Bush and Hitler are quite
    well known and problematic people.
    
    As for the bottom twenty, we can see just a mess of articles with little
    connection to each other. They all don't seem to be common topics in
    general conversation, so it makes little sense for them to be
    controversial in general.
    
  * Present the evolution of M-statistic over time for an article with high M 
    and another with low M and explain what you find
    **High M-Statistic Evolution for Barack Obama**
    (images/high-m-stat.png)
    **Low M-Statistic Evolution for AEK-Athens-F.C.-season-2009–10**
    (images/low-m-stat.png)
    
    The article with a high M-Statistic has a very miniscule rise at first
    around the end of 2006 until early 2008, which would correlate to around
    Obama's campaign for becoming president. Then we can see a steady steep
    increase right after that pretty much until the end, which makes sense
    because he was in office at the time. There are a few odd, tiny dips,
    but I can only guess that those are because certain editors that,
    previously, had been counted because they did not reach the maximum
    number of edits by did by editing a few more times.
    
    The article with the low M-Statistic has very random rises and jumps in the
    M-Statistic growth. This is probably due to very infrequent reverts and edits,
    and so the few spats that occur with the few mutual editors ever so often
    drive up the M-Statistic. But again, the line stabilizes like an elbow plot,
    again showing how spuratic the M-Statistic is. Overall, it likely shows it
    is not quite controversial with just very few reverts between editors.
 
  * Present summary statistics (distributions, classifications, etc) of the 
    M-statistics and explain what you find
    * Average M-Statistic Across All Articles: 195.43117657773496
    * Median M-Statistic Across All Articles: 0.0
    * Average M-Statistic for Articles with Reverts: 612.5267910767042
    * Median M-Statistic for Articles with Reverts: 0.0
    * Average M-Statistic for Controversial Articles: 34847.64549084077
    * Median M-Statistic for Controversial Articles: 3650.0
    * Highest M-Statistic: 34813075
    * Number of Articles with a Zero M-Statistic: 4495961
    * Number of Articles with a Positive M-Statistic: 148577
    * Number of Controversial Articles (M-Statistic > 1000): 25548
    * Percentage of Articles that are Controversial: 0.5682433633209897%
    * Stats for Controversial Articles:
        * Average Number of Edits (Including Reverts): 1956.2006810709254
        * Average Number of Purely Reverts: 356.4336542977924
        * Average M-Statistic: 34847.64549084077
        * Average Number of Mutual Editors: 10.566306560200408
        * Average Number of Editors: 834.6373884452795
    
    We can see that the M-Statistic seems to be functioning pretty well.
    It is able find just a small grouping of controversial articles and sift
    through the millions that are not controversial, which is something we
    expect. The average number of edits of controversial articles is close to
    2000, much higher than that of the average found in just the articles
    with reverts. Similarly, all the statistics in general are far higher for
    just the controversial articles, showing that the M-Statistic, or at least
    the ones above the cutoff, are quite significant. And compared to the
    M-Statistics found by WikiWarMonitor, my project does find a different
    M-Statistic for many of the articles, but for the most part still captures
    a relatively diffinitive way of identifying controversial articles.
    With now just ~25.5 thousand articles that are labelled controversial compared
    to the ~4.5 million total articles, the M-Statistic seems to be a fair way
    of finding controversial articles.
    
* Calculate M-Statistic using [raw data](https://dumps.wikimedia.org/enwiki/20200201/) for two articles: Anarchism and Abortion
  * Present the evolution of M-statistic over time (until 2019) and explain 
    what you find
    **M-Statistic Evolution for Anarchism**
    (/images/anarchism-m-stat.png)
    **M-Statistic Evolution for Abortion**
    (/images/abortion-m-stat.png)
    **Logarithmic M-Statistic Evolution for Both**
    (/images/log-m-stat.png)
    
    Both articles have a pretty similar shape in terms of their M-Statistic growth.
    They both jump up around 2006 and have increments of large growth at various
    periods of time. We can see their similar shapes in the logarithmic evolution
    of them both scaled across one graph. Both evolutions steadily grow their M-Statistic,
    showing that they feature topics that continue to be regularly debated between
    editors, with probably spikes occurring when certain "wars" occur between opposing
    sides.
    
    In the Abortion M-Statistic Evolution, we can identify particularly large
    jumps in the statistic. Around late 2011, we can see a relatively steep rise,
    which rightfully is around when lots of laws and articles were talking about
    abortion laws in America. Again, the odd, tiny dips may be due to certain 
    editors that, previously, had been counted because they did not reach the
    maximum number of edits but were now at the maximum by editing a few more times.
    
* Critique of the short comings of M-Statistic
    * The M-Statistic unfortunately does not really take into account of the
      actual language used in the article or the edits. It similarly does not
      take into account who the editors themselves are or if it is just a few
      main editors that are causing the M-Statistic to rise. The statistic also
      only refers to reverted editor in a relatively arbitrary way. In the
      example history of Ann, Bob, Cal, Ann, Dav, and Eve, the statistic does
      not account for the fact that Cal's edit was also overridden. Perhaps
      taking into account of Cal as a mutual editor with a lower weight than Bob,
      but it feels like an odd way of calculating the statistic when only referring
      to Bob as the reverted editor. The statistic could also factor in page views
      for the overall score.
    
* Discuss and validate some other measures of controversiality
    * A possible text-based statistic combined with the M-Statistic could be
      used to measure to controversy. Additionally factoring in the other editors
      between the <img src="https://render.githubusercontent.com/render/math?math=i^{th}"> and <img src="https://render.githubusercontent.com/render/math?math=j^{th}"> by considering them as mutual editors,
      or just the first five closest to the <img src="https://render.githubusercontent.com/render/math?math=i^{th}"> editor. We could also
      consider a network-based edit that is based on the text used by each editor
      or based the different clusters of editors established on a graph that
      compares their number of reverts and number of mutual editors.
      
* Conclusion
    * Overall, the replication project was a nice way to making us think more
      like data scientists. I feel that the M-Statistic problem is not an
      ideal project, with the space-inefficiency of having to maintain a 
      dictionary of all possible edits for a huge article to find out if
      an edit is a revert, but it was still great to learn about how to
      properly structure a complete data science project. The M-Statistic is also
      an overall quite confusing metric with the different interpretations of how
      exactly the code should work. The data is also quite commonly used in the
      NLP world, so it is great that we got a chance to take a peak and work
      with such a great dataset.
