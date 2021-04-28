import requests
import plotly.graph_objects as go
from datetime import datetime
import json
from bs4 import BeautifulSoup
import sqlite3

########## Final Project for SI507 ############
########## Winter Semester 2021 ###############
########## Yuheng Xie        ##################



headers = {
    'x-rapidapi-key': "8f7e1dcf54mshf3e3f1002775773p14019ajsn2c104e764eec",
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
}

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
        cache_file = open("cache_data.json", 'r')
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
    fw = open("cache_data.json","w")
    fw.write(dumped_json_cache)
    fw.close() 

class Stock:
    '''
    a stock

    Instance Attributes
    -------------------
    name: string
    info: string
    symbol: string
    '''
    def __init__(self, name='', symbol='', sector='', country='', timestamp=[], close=[]):
        self.name = name
        self.symbol = symbol
        self.sector = sector
        self.country = country
        self.timestamp = timestamp
        self.close = close
    
    def present(self):
        if self.sector == '':
            return f"{self.name} [{self.symbol}] is founded in {self.country}"
        else:
            return f"{self.name} [{self.symbol}] is founded in {self.country} of sector {self.sector}"

def get_top_gainer_stocks(): # get a list of top 10 stock symbols from the webpage
    '''
    make a list of top gainer stocks from https://finance.yahoo.com/gainers"

    Returns
    ------------
    List 
        A list of top 10 stocks' symbol
    '''
    try: 
        dic = open_cache()
        dic["stocks"][:10]
    except:
        print('Getting data from Yahoo Finance ...')
        html = requests.get("https://finance.yahoo.com/gainers").text
        soup = BeautifulSoup(html, 'html.parser')
        select_table = soup.find(class_='Pos(r)',id='scr-res-table')
        row_info = select_table.find_all('a')
        print('Finished getting data.')
        stock_list = []
        for item in row_info:
            stock_list.append(item.text)  # 25 items from webpage
        
        dic = {"stocks":stock_list}
        save_cache(dic)
        return stock_list[:10]
    else:
        stock_list = dic["stocks"][:10]
        return stock_list


def get_52_week_change(stock_list): # get a list of yearly change for top 10 stocks
    '''
    Get 52-week change data through the top 10 gainer stocks
    
    Parameters
    -------------
    stock_list: list
        A list of top 10 gainer stocks
    
    Returns
    ------------
    List 
        A list of 52-week change (yearly change) for the top 10 gainer stocks
    '''
    gainers_year_change = []
    for item in stock_list:
    
        url = f"https://finance.yahoo.com/quote/{item}/key-statistics?p={item}"
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        table_text = soup.find(id="Main").find(class_="Fl(end) W(50%) smartphone_W(100%)").find_all(class_='Fw(500) Ta(end) Pstart(10px) Miw(60px)')
        year_change = table_text[1].text

        print(item, '52-week change is', year_change)
        gainers_year_change.append(year_change)
    
    num_list = []
    for item in gainers_year_change:
        item = item[:-1]
        item = item.replace(',', '')
        try:
            float(item)
        except:
            item = 0
        else:
            item = float(item)
        num_list.append(item)
    
    return num_list

def create_stock_database():
    # create database list 'stock'

    conn = sqlite3.connect("Top_10_Stocks.sqlite")
    cur = conn.cursor()

    drop_stocks = '''
    DROP TABLE IF EXISTS "stocks";
    '''

    create_stocks = '''
    CREATE TABLE IF NOT EXISTS "stocks" (
        "Symbol"  TEXT PRIMARY KEY NOT NULL UNIQUE,
        "Name" TEXT NOT NULL,
        "Sector" TEXT NOT NULL,
        "Country"    TEXT NOT NULL
    );
    '''

    cur.execute(drop_stocks)
    cur.execute(create_stocks)

    drop_yearlydata = '''
    DROP TABLE IF EXISTS "yearlydata";
    '''

    create_yearlydata = '''
    CREATE TABLE IF NOT EXISTS "yearlydata" (
        "Id"    INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        "Time"  TEXT NOT NULL,
        "Value" TEXT NOT NULL,
        "Symbol"  TEXT NOT NULL
    );
    '''

    cur.execute(drop_yearlydata)
    cur.execute(create_yearlydata)

    conn.commit()
    return None

def create_stock_inst(list_of_symbols): # create a list of stock instances from a list of stock symbols
    '''
    Create top 10 stocks instance

    Parameters:
    ------------
    list_of_symbols: list
        A list of symbols for top 10 stocks scraping from the web page

    Returns:
    --------------
    stock_inst_list: list
        A list of stock instances

    '''

    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary"
    
    stock_inst_list = []
    for item in list_of_symbols:
        
        querystring = {"symbol":item}
        response = requests.request("GET", url, headers=headers, params=querystring).json()

        name = response["price"]["longName"]

        try: response["summaryProfile"]["sector"]
        except: sector = ''
        else: sector = response["summaryProfile"]["sector"]

        try: response["summaryProfile"]["country"]
        except: country = ''
        else: country = response["summaryProfile"]["country"]

        stock_inst = Stock(name=name, symbol=item, sector=sector, country=country)
        stock_inst_list.append(stock_inst)
        print('collecting stock information ...')
        
    return stock_inst_list

def database_info_input(list_stock_inst):  # fill in database list 'stocks' stocks information
    '''
    Add stocks instance information into the database list 'stocks'

    Parameters
    -----------
    list_stock_inst
        A list of stock instances
    
    Returns
    -----------
    Database list 'stocks'
        Filled information of database list 'stocks'
    '''

    conn = sqlite3.connect("Top_10_Stocks.sqlite")
    cur = conn.cursor()

    insert_stocks = '''
    INSERT INTO stocks
    VALUES (?, ?, ?, ?)
    '''

    for item in list_stock_inst:
        row_info = [item.symbol, item.name,  item.sector, item.country]

        cur.execute(insert_stocks, row_info)

    conn.commit()

    return None

def present_stock_info(list_stock_inst): # output top 10 stocks information
    i = 1
    for item in list_stock_inst:
        print(f"[{i}] {item.present()}")
        i += 1
    
    return None

def add_value(num, list_stock_inst): # create stock instance for each stock with timestamp & close value, and add data into database list "yearlydata"
    '''
    Add the timestamp & close value into exist stock instance

    Parameters
    ---------------
    num: int
        The rank num of the stock
    list_stock_inst
        A list of stock instances
    
    Returns
    ---------------
    instance
        an instance of stock
    '''


    stock_inst = list_stock_inst[num-1]    
    symbol = stock_inst.symbol # get the symbol of selected stock

    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-charts"

    querystring = {"interval":"1d","symbol":symbol,"range":"3mo","region":"US"}

    response = requests.request("GET", url, headers=headers, params=querystring).json()
    timestamp_list = []
    timestamp_list.append(response["chart"]["result"][0]["timestamp"])

    close_list = []
    close_list.append(response["chart"]["result"][0]["indicators"]["quote"][0]["close"])
    close_list = close_list[0]

    calendar_time = []
    for ts in timestamp_list[0]:
        dt = datetime.fromtimestamp(ts)
        calendar_time.append(dt.strftime("%m/%d"))
    
    list_stock_inst[num-1].timestamp = calendar_time

    list_stock_inst[num-1].close = close_list
    
    new_list = list_stock_inst

    print('Getting data from API ...')

    #stock_inst = Stock(symbol=symbol,timestamp=calendar_time, close=close_list)

    conn = sqlite3.connect("Top_10_Stocks.sqlite")
    cur = conn.cursor()

    insert_stocks = '''
    INSERT INTO yearlydata
    VALUES (NULL, ?, ?, ?)
    '''
    i = 0
    while i < len(new_list[num-1].timestamp):
        row_info = [new_list[num-1].timestamp[i], new_list[num-1].close[i], new_list[num-1].symbol]
        i += 1
        cur.execute(insert_stocks, row_info)

    conn.commit()

    return new_list
    

def bar_chart_year(list_x,list_y):
    layout = go.Layout(title="52 weeks change for top 10 stocks: gainers",xaxis=dict(title='Stocks'),yaxis=dict(title='Percentage Change %'))
    fig = go.Figure(data=go.Bar(x=list_x,y=list_y), layout=layout)
    print('Creating br chart ...')
    fig.write_html('Top10_YearlyChange.html', auto_open=True)
    
    return None

def line_chart(stock_inst):
    trace = go.Scatter(
        x = stock_inst.timestamp,
        y = stock_inst.close,
        mode = "lines",
        name = "stock line"
    )

    layout = go.Layout(
        title = f"{stock_inst.name} [{stock_inst.symbol}] history in 3 months",
        xaxis = dict(title = "time"),
        yaxis = dict(title = "stock")
    )
    fig = go.Figure(data = trace, layout = layout)

    print('Creating line chart ...')
    fig.write_html(f'line_chart_{stock_inst.symbol}.html', auto_open=True)
    return None

if __name__ == "__main__":

    n = 0
    while True:
        if n == 0:
            create_stock_database() # create database 1
            print('The program is about stocks of daily top 10 gainers.')
            print('----------------------------------------------')
            stock_list = get_top_gainer_stocks()
            print(stock_list)
            info_list = create_stock_inst(stock_list) # a list of stock instance
            present_stock_info(info_list)
            database_info_input(info_list) # fill in information in database 1
            n = 1

        elif n == 1:
            text = input('Please input "1" to view yearly value change for these stocks, "2" to continue viewing detail for each stock ("exit" to end): ')
            if text == 'exit':
                break
            try: text.isdigit()
            except: print("Please enter num 1 or 2")
            else: 
                num = int(text)
                if num == 1:
                    year_change_list = get_52_week_change(stock_list)
                    bar_chart_year(stock_list, year_change_list)
                    n = 2
                elif num == 2:
                    n = 2
                else:
                    print("Please enter num 1 or 2")
        
        elif n == 2:
            text = input('Please input the rank of stock you want to view ("return" to go back, "exit" to end): ')
            if text == 'return':
                n = 1
            elif text == "exit":
                break

            try: text.isdigit()
            except: print("Please enter num within 1 to 10")
            else:
                num = int(text)
                if num > 0 and num < 11:
                    full_stock_info_list = add_value(num, info_list)
                    line_chart(full_stock_info_list[num-1])
                else:
                    print("Please enter num within 1 to 10")
        else:
            break


