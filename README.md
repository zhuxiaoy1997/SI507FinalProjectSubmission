# SI507FinalProjectSubmission

To run my code, an api key is required. You can use my api key (secrets.py) submitted on Canvas. Also, you need to download the file: templates which includes several html files and you need to put the templates file in the same directory of Final_Project_Code_zhuxiaoy.py.
[Note]: my program will take 12 minutes to create tables by fetching and 40 seconds by caching. To save time, you can either use the cache file I provide or use the Movies.sqlite database and comment my codes in the set-up part under the command: if __name__ == “__main__”.

How to interact with my program：
My program is designed for two goals: recommending movies to users and comparing movies in different years. Users need to first select whether recemmendation or comparison. In the recommendation part, users can choose between two options: quarter and month. Then according to the selected option, users need to input a specific time interval such as the first quarter or january so that movies of the highest box office in the corresponding time interval of the last fifty years will be displayed. Then users can input a number to select the movie which they find interesting to see the detailed information. The inforamiton is displayed on a website including a table and a bar chart. In the comparison part, a website will show up where users can choose the time interval, the kind of movies (all movies or movies of the highest box office), and the variable to compare. After users submit their answers, a bar chart and a table will be displayed for users to compare movies in a specific time interval of the last fifty years in the US.

The required packages for my program are listed as follows: requests_oauthlib, bs4, requests, json, sqlite3, plotly.graph_objs, flask.
