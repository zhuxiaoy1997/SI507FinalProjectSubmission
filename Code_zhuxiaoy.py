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
    year: string
        the year when the movie is of the highest box office  (e.g. 2020)
    
    time_interval : string
        the sepcific time interval (quarter/ month) when the movie is of the highest box office (e.g. 'first quarter', 'second quarter', 'january')

    name: string
        the name of a movie (e.g. 'Bad Boys for Life')

    gross: string
        the gross of a movie (e.g. $135,561,888)

    '''
    def __init__(self, year, time_interval, name, gross):
        self.year = year
        self.time_interval = time_interval
        self.name = name
        self.gross = gross

    def info(self):
        return self.name + ' is Top 1 movie in the ' + self.time_interval + ' of ' + self.year + ' with a gross of ' + self.gross

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
        The tuple includes a movie's id, year, time interval(quarter/ month), movie name, movie's gorss,
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
    AllDetailedInformaiton = []
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
        AllDetailedInformaiton.append(single_tuple)
    return AllDetailedInformaiton

def create_box_office_database(AllBoxOffice):
    ''' Constructs and executes SQL query to create a new database called BoxOffice showing 
    all movies of the highest box office in different quarters/ months so far
    
    Parameters
    ----------
    AllBoxOffice: list
        a list of tuples containing movies of the highest box office in differet quarters/ months so far
    
    Returns
    -------
    None
    '''
    conn = sqlite3.connect("BoxOffice.sqlite")
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

def create_detailed_information_database(AllDetailedInformaiton):
    ''' Constructs and executes SQL query to create a new database called MovieDetailedInformaiton containing
    the detailed information of movies obtained from the OMDB website
    
    Parameters
    ----------
    AllDetailedInformaiton: list
        a list of tuples comtaining movies and their detailed informaiton obtained from the OMDB website
    
    Returns
    -------
    None
    '''
    conn = sqlite3.connect("MovieDetailedInformaiton.sqlite")
    c = conn.cursor()
    # Drop table if exists
    c.execute('''DROP TABLE IF EXISTS "MovieDetailedInformaiton"''')
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS "MovieDetailedInformaiton"(
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
    c.executemany('INSERT INTO MovieDetailedInformaiton VALUES (?,?,?,?,?,?,?,?,?)', AllDetailedInformaiton)
    conn.commit() # Save (commit) the changes
    # Be sure any changes have been committed or they will be lost.
    conn.close()

'''
def movie_detailed_search(movie_name):
    '' search the detailed information of a movie by the name through the IMDB website. 

    Parameters
    ----------
    movie_name: string
        name of the movie which users want to know more about

    Returns
    -------
    list
        a list of tuples that represent movies' detailed information.
        The tuple includes a movie's id(convenient for joining), year, time interval(quarter/ month), movie name, movie's gorss,
        the number of released movies in this time interval, the cumulative gross of all movies in this time interval, 
        the average gross of all movies in this time interval
    ''
    base_url = 'http://www.omdbapi.com/'
    params = { "apikey": api_key,'t':movie_name}

    CACHE_DICT = open_cache()
    if movie_name in CACHE_DICT.keys():
        print("Using Cache")
        response = CACHE_DICT[movie_name]
    else:
        print("Fetching")
        CACHE_DICT[movie_name] = requests.get(base_url, params=params, auth=oauth).json()
        response = CACHE_DICT[movie_name]
        save_cache(CACHE_DICT)

def movie_box_office_search_quarter(q):
    quarter = "q" + str(q)
    if q == 1:
        TimeInterval = 'first quarter'
    if q == 2:
        TimeInterval = 'second quarter'
    if q == 3:
        TimeInterval = 'third quarter'
    if q == 4:
        TimeInterval = 'fourth quarter'
    MovieUrl = "https://www.boxofficemojo.com/quarter/" + quarter + "/?grossesOption=calendarGrosses"
    CACHE_DICT = open_cache()
    if TimeInterval in CACHE_DICT.keys():
        print("Using Cache")
        response = CACHE_DICT[TimeInterval]
    else:
        print("Fetching")
        CACHE_DICT[TimeInterval] = requests.get(MovieUrl).text
        response = CACHE_DICT[TimeInterval]
        save_cache(CACHE_DICT)

    Movie_Instance_List = []
    Movie_Dicts = get_information_from_box_office_website(response)
    for i in list(range(len(Movie_Dicts['Movie Year']))): ## All lists share the same length
        Movie_instance = Movie(Movie_Dicts['Movie Year'][i], TimeInterval, Movie_Dicts['Movie Name'][i], Movie_Dicts['Gross'][i])
        Movie_Instance_List.append(Movie_instance)
    
    return Movie_Instance_List
'''


if __name__ == "__main__":
    
    AllBoxOffice = get_box_office_tuples()
    # create the database of boxoffice
    create_box_office_database(AllBoxOffice) 
    AllDetailedInformaiton = get_detailed_information_tuples(AllBoxOffice)
    # create the database of detailed informaiton from OMDB
    create_detailed_information_database(AllDetailedInformaiton) 
    





