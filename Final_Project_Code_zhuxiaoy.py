#################################
##### Name:          Xiaoyang Zhu
##### Uniqname:      zhuxiaoy
#################################
from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
import requests
import json
import secrets
import sqlite3
import plotly.graph_objs as go
from flask import Flask, render_template, request

app = Flask(__name__)
App = Flask(__name__)

CACHE_FILENAME = "cache.json"
CACHE_DICT = {}
api_key = secrets.API_KEY
oauth = OAuth1(client_key = api_key)

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

class Movie:
    '''a movie of the highest box office in one specific time interval (e.g. the first quarter of 2020)

    Instance Attributes
    -------------------
    year: int
        the year when the movie is of the highest box office  (e.g. 2020)
    
    time_interval : string
        the sepcific time interval (quarter/ month) when the movie is of the highest box office (e.g. 'first quarter', 'second quarter', 'january')

    name: string
        the name of a movie (e.g. 'Bad Boys for Life')

    gross: int
        the gross of a movie (e.g. $135,561,888)

    id: int
        the id of a movie (e.g. 1)
    '''
    def __init__(self, year, time_interval, name, gross, id):
        self.year = year
        self.time_interval = time_interval
        self.name = name
        self.gross = gross
        self.id = id

    def info(self):
        return '<' + self.name + '>,' + ' (' + str(self.year) + ') ' + ' with a gross of ' + str(self.gross) + '.'

def get_information_from_box_office_website(response):
    '''Extract all important information from the scraping result of the box office website.
    Since I aim to scrape movies in different quarters and months, this function is created to avoid repetition.
    The information I aim to extract includes the year, the movie name, the gross of the movie, 
    the cumulative gross of all movies in one time interval, the average gross of all movies in one time interval,
    the number of movies released in one time interval. 
    Each type of information is contained in one list.
    The final result is a dictionary of all lists.

    Parameters
    ----------
    response: string
        The scraping result of the box office website in the string format
        (eg. response = requests.get(https://www.boxofficemojo.com/quarter/q1/?grossesOption=calendarGrosses).text)

    Returns
    -------
    dict
        a dictionary whose keys are imporatant fields (year, movie name, gross, cumulative gross, average gross, number of released movies)
        and values are lists that contain the corresponding information.
        (e.g. {'Movie Year':[2020,2019,......], 'Movie Name': ['Bad Boys for Life','The King's Speech']})
    '''
    soup = BeautifulSoup(response, 'html.parser')
    SearchTable = soup.find('div', class_='a-section imdb-scroll-table-inner')
    
    MovieYears = SearchTable.find_all('td', class_='a-text-left mojo-header-column mojo-truncate mojo-field-type-year mojo-sort-column')
    Movie_Year = []
    for movie in MovieYears:
        Movie_Year.append(movie.text)

    MovieNames = SearchTable.find_all('td', class_='a-text-left mojo-field-type-release mojo-cell-wide')
    Movie_Name = []
    for movie in MovieNames:
        Movie_Name.append(movie.text)

    AllGross = SearchTable.find_all('td', class_='a-text-right mojo-field-type-money')
    All_Gross = []
    for movie in AllGross:
        All_Gross.append(movie.text)
    Cumulative_G = []
    Average_G = []
    Gross = []
    for i in list(range(len(All_Gross))):
        ind = i % 3
        if ind == 0:
            Cumulative_G.append(All_Gross[i])
        if ind == 1:
            Average_G.append(All_Gross[i])
        if ind == 2:
            Gross.append(All_Gross[i])
    
    Releases = SearchTable.find_all('td', class_='a-text-right mojo-field-type-positive_integer')
    Release = []
    for movie in Releases:
        Release.append(movie.text)
    
    Movie_List_Dict= {}
    Movie_List_Dict = {'Movie Year': Movie_Year, 'Movie Name': Movie_Name, 'Gross': Gross, 'Release': Release, 'Cumulative Gross': Cumulative_G, 'Average Gross': Average_G}
    return Movie_List_Dict

def get_box_office_tuples():
    '''Make a list of tuples that represent movies of the highest box office in different time intervals (quarters/ months).

    Parameters
    ----------
    None

    Returns
    -------
    list
        a list of tuples that contain movies of the highest box office in different time intervals(quarters/ months).
        The tuple includes a movie's id, year, time interval(quarter/ month), movie name, movie's gross,
        the number of released movies in this time interval, the cumulative gross of all movies in this time interval, 
        the average gross of all movies in this time interval
    '''
    Quarter = ['q1','q2','q3','q4']
    Month = ['january','february','march','april','may','june','july','august','september','october','november','december']
    
    AllBoxOffice_Quarter = []
    a = 1
    for quarter in Quarter:
        BoxOfficeUrl_Q = "https://www.boxofficemojo.com/quarter/" + quarter + "/?grossesOption=calendarGrosses"
        if quarter == 'q1':
            TimeInterval = 'first quarter'
        if quarter == 'q2':
            TimeInterval = 'second quarter'
        if quarter == 'q3':
            TimeInterval = 'third quarter'
        if quarter == 'q4':
            TimeInterval = 'fourth quarter'
        
        CACHE_DICT = open_cache()
        if TimeInterval in CACHE_DICT.keys():
            print("Using Cache")
            response = CACHE_DICT[TimeInterval]
        else:
            print("Fetching")
            CACHE_DICT[TimeInterval] = requests.get(BoxOfficeUrl_Q).text
            response = CACHE_DICT[TimeInterval]
            save_cache(CACHE_DICT)
        Movie_Dicts = get_information_from_box_office_website(response)
        for i in list(range(len(Movie_Dicts['Movie Year']))): ## All lists share the same length
            single_tuple = a+i,Movie_Dicts['Movie Year'][i], TimeInterval, Movie_Dicts['Movie Name'][i], Movie_Dicts['Gross'][i], Movie_Dicts['Release'][i], Movie_Dicts['Cumulative Gross'][i], Movie_Dicts['Average Gross'][i]
            AllBoxOffice_Quarter.append(single_tuple)
        a = a + len(Movie_Dicts['Movie Year'])

    AllBoxOffice_Month = []
    b = len(AllBoxOffice_Quarter) + 1
    for month in Month:
        BoxOfficeUrl_M = "https://www.boxofficemojo.com/month/" + month + "/?grossesOption=calendarGrosses"
        TimeInterval = month
        CACHE_DICT = open_cache()
        if TimeInterval in CACHE_DICT.keys():
            print("Using Cache")
            response = CACHE_DICT[TimeInterval]
        else:
            print("Fetching")
            CACHE_DICT[TimeInterval] = requests.get(BoxOfficeUrl_M).text
            response = CACHE_DICT[TimeInterval]
            save_cache(CACHE_DICT)
        Movie_Dicts = get_information_from_box_office_website(response)
        for i in list(range(len(Movie_Dicts['Movie Year']))): ## All lists share the same length
            single_tuple = b+i,Movie_Dicts['Movie Year'][i], TimeInterval, Movie_Dicts['Movie Name'][i], Movie_Dicts['Gross'][i], Movie_Dicts['Release'][i], Movie_Dicts['Cumulative Gross'][i], Movie_Dicts['Average Gross'][i]
            AllBoxOffice_Month.append(single_tuple)
        b = b + len(Movie_Dicts['Movie Year'])

    AllBoxOffice = AllBoxOffice_Quarter + AllBoxOffice_Month
    return(AllBoxOffice)

def get_detailed_information_tuples(AllBoxOffice):
    ''' get the detailed information of movies of the highest box office from the OMDB website and make a list
    of tuples to represent the informaion.

    Parameters
    ----------
    AllBoxOffice: list
        a list contains all movies of the highest box office in differnt time intervals (quarters/ months)

    Returns
    -------
    list
        a list of tuples that represent movies' detailed information obtained from the OMDB website.
        The tuple includes a movie's id, movie title, exact release date, runtime, genre, director,
        rating values from three websites(IMDB, Rotten Tomatoes, Metacritic) 
    '''
    base_url = 'http://www.omdbapi.com/'
    AllDetailedInformation = []
    for m in AllBoxOffice:
        params = { "apikey": api_key,'t':m[3]}
        CACHE_DICT = open_cache()
        if m[3] in CACHE_DICT.keys():
            print("Using Cache")
            response = CACHE_DICT[m[3]]
        else:
            print("Fetching")
            CACHE_DICT[m[3]] = requests.get(base_url, params=params, auth=oauth).json()
            response = CACHE_DICT[m[3]]
            save_cache(CACHE_DICT)
        try:
            title = response['Title']
        except:
            title = None
        try:
            release_date = response['Released']
        except:
            release_date = None
        try:
            runtime = response['Runtime']
        except:
            runtime = None
        try:
            genre = response['Genre']
        except:
            genre = None
        try:
            director = response['Director']
        except:
            director = None
        try:
            Internet_Movie_rating = response['Ratings'][0]['Value']
        except:
            Internet_Movie_rating = None
        try:
            Rotten_Tomatoes_rating = response['Ratings'][1]['Value']
        except:
            Rotten_Tomatoes_rating = None
        try:
            Metacritic_rating = response['Ratings'][2]['Value']
        except:
            Metacritic_rating = None

        single_tuple = m[0],title, release_date, runtime, genre, director, Internet_Movie_rating, Rotten_Tomatoes_rating, Metacritic_rating
        AllDetailedInformation.append(single_tuple)
    return AllDetailedInformation

def create_box_office_table(AllBoxOffice):
    ''' Constructs and executes SQL query to create a new table called BoxOffice showing 
    all movies of the highest box office in different quarters/ months of the last fifty years in the US
    
    Parameters
    ----------
    AllBoxOffice: list
        a list of tuples containing movies of the highest box office in differet quarters/ months of the last fifty years in US
    
    Returns
    -------
    None
    '''
    conn = sqlite3.connect("Movies.sqlite")
    c = conn.cursor()
    # Drop table if exists
    c.execute('''DROP TABLE IF EXISTS "BoxOffice"''')
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS "BoxOffice"(
        id integer PRIMARY KEY AUTOINCREMENT UNIQUE,
        MovieYear integer NOT NULL, 
        TimeInterval text NOT NULL, 
        MovieName text NOT NULL, 
        Gross real NOT NULL, 
        Release real NOT NULL, 
        CumulativeGross real NOT NULL, 
        AverageGross real NOT NULL)''')
    # Insert several rows of data
    c.executemany('INSERT INTO BoxOffice VALUES (?,?,?,?,?,?,?,?)', AllBoxOffice)
    conn.commit() # Save (commit) the changes
    # Be sure any changes have been committed or they will be lost.
    conn.close()

def create_detailed_information_table(AllDetailedInformation):
    ''' Constructs and executes SQL query to create a new table called MovieDetailedInformaiton containing
    the detailed information of movies obtained from the OMDB website
    
    Parameters
    ----------
    AllDetailedInformaiton: list
        a list of tuples comtaining movies and their detailed informaiton obtained from the OMDB website
    
    Returns
    -------
    None
    '''
    conn = sqlite3.connect("Movies.sqlite")
    c = conn.cursor()
    # Drop table if exists
    c.execute('''DROP TABLE IF EXISTS "MovieDetailedInformation"''')
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS "MovieDetailedInformation"(
        id integer PRIMARY KEY AUTOINCREMENT UNIQUE,
        title text, 
        ReleaseDate text, 
        runtime real, 
        genre text,
        director text, 
        Internet_Movie_rating real, 
        Rotten_Tomatoes_rating real, 
        Metacritic_rating real )''')
    # Insert several rows of data
    c.executemany('INSERT INTO MovieDetailedInformation VALUES (?,?,?,?,?,?,?,?,?)', AllDetailedInformation)
    conn.commit() # Save (commit) the changes
    # Be sure any changes have been committed or they will be lost.
    conn.close()

def movie_box_office_search_time_interval(SearchTimeInterval):
    '''Constructs and executes SQL query to create movie instances that represent movies of the highest box office in one time interval selected by users.

    
    Parameters
    ----------
    SearchTimeInterval: string
            a string indicating a time interval (e.g. first quarter, january)
    
    Returns
    -------
    list
        a list of movie instances
    '''
    Movie_Instance_List = []
    connection = sqlite3.connect("Movies.sqlite")
    cursor = connection.cursor()
    query =  "SELECT MovieYear, TimeInterval, MovieName, Gross, id FROM BoxOffice WHERE TimeInterval = " + SearchTimeInterval + " ORDER BY MovieYear DESC"
    result = cursor.execute(query).fetchall()
    for m in result:
        Movie_Instance_List.append(Movie(m[0],m[1],m[2],m[3],m[4]))
    connection.close()
    return Movie_Instance_List

def movie_detailed_search(movie_id):
    '''Constructs and executes SQL query to retrieve one movie's detailed information in a tuple format based on movie id.
    
    Parameters
    ----------
    movie_id: string
            a string indicating a movie id (e.g. 1)
    
    Returns
    -------
    list
        a list of tuples that represent the query result
    '''
    connection = sqlite3.connect("Movies.sqlite")
    cursor = connection.cursor()
    query = '''SELECT * FROM MovieDetailedInformation WHERE id = ''' + movie_id
    result = cursor.execute(query).fetchall()
    connection.close()
    return result

## the website in the recommendation part showing the detailed information of a movie
@app.route('/')
def recommend():
    results = result_movie
    x_vals = ['IMDB','Rotten Tomatoes','Metacritic']
    first_rating = float(str(result_movie[0][6]).split('/')[0])*10
    second_rating = float(str(result_movie[0][7]).split('%')[0])
    third_rating = float(str(result_movie[0][8]).split('/')[0])
    y_vals = [first_rating, second_rating, third_rating]
    bars_data = go.Bar(x=x_vals, y=y_vals)
    basic_layout = go.Layout(height=600, width=500)
    fig = go.Figure(data=bars_data)
    div = fig.to_html(full_html=False)
    return render_template('recommendation.html', results = results, plot_div = div)


def get_results(select_movies, compare_variable, select_time_interval):
    '''Constructs and executes SQL query to retrieve the information of movies based on the response of a survey.
    
    Parameters
    ----------
    select_movies: string
            a string indicating whether users choose to compare among all movies or movies of the highest box office (box office champions). (e.g. AllMovives/ Champions)
    compare_variable: string
            a string indicating the variable a user want to compare (e.g. gross, cumulative gross, IMDB rating)
    select_time_interval: string
            a string indicating a time interval when users want to compare (e.g. first quarter, january)
    
    Returns
    -------
    list
        a list of tuples that represent the query result
    '''
    connection = sqlite3.connect("Movies.sqlite")
    cursor = connection.cursor()

    select_time_interval = '"' + select_time_interval + '"'
    if compare_variable == 'cumulative gross':
        select_column = 'CumulativeGross'
    elif compare_variable == 'average gross':
        select_column = 'AverageGross'
    elif compare_variable == 'gross':
        select_column = 'Gross'
    elif compare_variable == 'IMDB rating':
        select_column = 'Internet_Movie_Rating'
    elif compare_variable == 'Rotten Tomatoes rating':
        select_column = 'Rotten_Tomatoes_rating'
    elif compare_variable == 'Metacritic rating':
        select_column = 'Metacritic_rating'
    
    query = '''SELECT MovieYear, ''' + select_column + ''', MovieName FROM BoxOffice JOIN MovieDetailedInformation ON BoxOffice.id = MovieDetailedInformation.id WHERE TimeInterval = ''' + select_time_interval + ''' ORDER BY MovieYear DESC'''

    result = cursor.execute(query).fetchall()
    connection.close()
    return result

## the website in the comparison part. Users can select the type of movies and variables (gross, rating) which they want to compare.
@App.route('/')
def index():
    return render_template('comparison_index.html')


@App.route('/results', methods=['POST'])
def results():
    select_movies = request.form['movies']
    select_time_interval = request.form['interval']
    if select_movies == 'AllMovies':
        compare_variable = request.form['allmovies']
        MovieKind = 'all movies'
    else:
        compare_variable = request.form['champions']
        MovieKind = 'box office champions'
    if 'quarter' in select_time_interval:
        time = 'the ' + select_time_interval
    else:
        time = select_time_interval 
    results = get_results(select_movies, compare_variable, select_time_interval)
    x_vals = []
    y_vals = []
    for e in results:
        y_vals.append(e[1])
        x_vals.append(e[0])
    bars_data = go.Bar(x=x_vals, y=y_vals)
    fig = go.Figure(data=bars_data)
    div = fig.to_html(full_html=False)
    return render_template('comparison_results.html', plot_div = div , results = results, variable = compare_variable, movie_kind = MovieKind, Time = time)


if __name__ == "__main__":

    ########   SET UP    ########
    AllBoxOffice = get_box_office_tuples()
    # create the table of boxoffice
    create_box_office_table(AllBoxOffice) 
    # create the table of detailed informaiton from OMDB
    AllDetailedInformation = get_detailed_information_tuples(AllBoxOffice)
    create_detailed_information_table(AllDetailedInformation)

    Quarter = ['first quarter', 'second quarter', 'third quarter', 'fourth quarter']
    Month = ['january','february','march','april','may','june','july','august','september','october','november','december']
    ###############################

    print("Welcome to a movie's world!!!")
    print("-" * 80)
    print('This program contains two parts: recommendation and comparison.')
    print()
    print('In the recommendation part, you can select a time interval, say, January. Then box office champions in January of the last fifty years in the US will be listed. Feel free to select one movie to know more about it!!!')
    print('In the comparison part, a website will show up where you can select the movie kind, a time interval, and a variable to compare. There are many options available.')
    print('Now, please enjoy it!')
    print("-" * 80)
    input_R_C = input('Do you want a recommendation or comparison or exit? Please input r for recommendation or c for comparison or exit for exit:')
    while True:
        if input_R_C.lower() == 'r':
            print('''Do you want to see quarterly or monthly box office champions in the US of the last fifty years?''')
            input_time_interval = input('''Please input quarter to see quarterly champions or month to see monthly champions or back or exit:''')
            while True:
                if input_time_interval.lower() == 'quarter':
                    print()
                    input_quarter = input('''Choose the quarter you want to see or exit or back. For quarter search, please input numbers from 1 to 4 indicating the corresponding quarter:''')
                    while True:
                        if input_quarter.isnumeric() and int(input_quarter) in list(range(1,5)):
                            if int(input_quarter) == 1:
                                SearchTimeInterval = 'first quarter'
                            elif int(input_quarter) == 2:
                                SearchTimeInterval = 'second quarter'
                            elif int(input_quarter) == 3:
                                SearchTimeInterval = 'third quarter'
                            elif int(input_quarter) == 4:
                                SearchTimeInterval = 'fourth quarter'
                            print('-' * 60)
                            print("List of Box Office Champions in the " + SearchTimeInterval + " of the last fifty years in the US")
                            print('-' * 60)
                            SearchTimeInterval = '"' + SearchTimeInterval + '"'
                            AllMovieInstances = movie_box_office_search_time_interval(SearchTimeInterval)
                            for i in list(range(len(AllMovieInstances))):
                                print("[" + str(i+1) + "] " + AllMovieInstances[i].info())

                            print()
                            print('-' * 60)
                            search_detail = input('''Choose the number for detail search or exit or back: ''')
                            while True:
                                if search_detail.isalpha() and search_detail.lower() == 'back':
                                    print()
                                    input_quarter = input('''Choose the quarter you want to see or exit or back. For quarter search, please input numbers from 1 to 4 indicating the corresponding quarter:''')
                                    break
                                elif search_detail.isalpha() and search_detail.lower() == 'exit':
                                    input_quarter = 'exit'
                                    break
                                elif search_detail.isnumeric() and int(search_detail) in list(range(1,len(AllMovieInstances)+1)):
                                    selected_movie_id = AllMovieInstances[int(search_detail)-1].id
                                    result_movie = movie_detailed_search(str(selected_movie_id))
                                    app.run()
                                    print()
                                    print('-' * 60)
                                    search_detail = input('''Choose the number for detail search or exit or back: ''')
                                else:
                                    print("[Error] Invalid input")
                                    print()
                                    print('-' * 60)
                                    search_detail = input('''Choose the number for detail search or exit or back: ''')


                        elif input_quarter.isalpha() and input_quarter.lower() == 'back':
                            input_time_interval = input('''Please input quarter to see quarterly champions or month to see monthly champions or back or exit:''')
                            break

                        elif input_quarter.isalpha() and input_quarter.lower() == 'exit':
                            input_time_interval = 'exit'
                            break

                        else:
                            print('Please input a valid number ranging from 1 to 4 or exit or back.')
                            print()
                            input_quarter = input('''Choose the quarter you want to see or exit or back. For quarter search, please input numbers from 1 to 4 indicating the corresponding quarter:''')

                elif input_time_interval.lower() == 'month':
                    print()
                    input_month = input('''Choose the month you want to see or exit or back. For month search, please type the month (e.g. january):''')
                    while True:
                        if input_month.lower() in Month:
                            SearchTimeInterval = input_month.lower()
                            print('-' * 60)
                            print("List of Box Office Champions in " + SearchTimeInterval + " of the last fifty years in the US")
                            print('-' * 60)
                            SearchTimeInterval = '"' + SearchTimeInterval + '"'
                            AllMovieInstances = movie_box_office_search_time_interval(SearchTimeInterval)
                            for i in list(range(len(AllMovieInstances))):
                                print("[" + str(i+1) + "] " + AllMovieInstances[i].info())
                            
                            print()
                            print('-' * 60)
                            search_detail = input('''Choose the number for detail search or exit or back: ''')
                            while True:
                                if search_detail.isalpha() and search_detail.lower() == 'back':
                                    print()
                                    input_month = input('''Choose the month you want to see or exit or back. For month search, please type the month (e.g. january):''')
                                    break
                                elif search_detail.isalpha() and search_detail.lower() == 'exit':
                                    input_month = 'exit'
                                    break
                                elif search_detail.isnumeric() and int(search_detail) in list(range(1,len(AllMovieInstances)+1)):
                                    selected_movie_id = AllMovieInstances[int(search_detail)-1].id
                                    result_movie = movie_detailed_search(str(selected_movie_id))
                                    app.run()
                                    print()
                                    print('-' * 60)
                                    search_detail = input('''Choose the number for detail search or exit or back: ''')
                                else:
                                    print("[Error] Invalid input")
                                    print()
                                    print('-' * 60)
                                    search_detail = input('''Choose the number for detail search or exit or back: ''')

                        elif input_month.lower() == 'back':
                            input_time_interval = input('''Please input quarter to see quarterly champions or month to see monthly champions or back or exit:''')
                            break
                        elif input_month.lower() == 'exit':
                            input_time_interval = 'exit'
                            break
                        else: 
                            print('''Please input a valid month. (e.g. january)''')
                            print()
                            input_month = input('''Choose the month you want to see or exit or back. For month search, please type the month (e.g. january):''')
                        
                elif input_time_interval.lower() == 'back':
                    input_R_C = input('Do you want a recommendation or comparison or exit? Please input r for recommendation or c for comparison or exit for exit:')
                    break
                elif input_time_interval.lower() == 'exit':
                    input_R_C = 'exit'
                    break
                
                else:
                    print('Please input your selection from four options: quarter/ month/ back/ exit')
                    input_time_interval = input('''Please input quarter to see quarterly champions or month to see monthly champions or back or exit:''')


        elif input_R_C.lower() == 'c':
            App.run()
            input_R_C = input('Do you want a recommendation or comparison or exit? Please input r for recommendation or c for comparison or exit for exit:')

        elif input_R_C.lower() == 'exit':
            break
        else:
            print('Please input valid words. (e.g. r for recommendation or c for comparison or exit for exit)')
            input_R_C = input('Do you want a recommendation or comparison or exit? Please input r for recommendation or c for comparison or exit for exit:')




