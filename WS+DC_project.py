from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import string

shop1_phones_dict = {}
shop2_phones_dict = {}
shop3_phones_dict = {}

shop1_url = 'https://rozetka.com.ua/ua/mobile-phones/c80003/producer=samsung/'
shop2_url = 'https://hotline.ua/mobile/mobilnye-telefony-i-smartfony/133-294356/'
shop3_url = 'https://allo.ua/ua/products/mobile/proizvoditel-samsung/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }


while True:
    '''
    Scraping data such as phone title, price, link and short description from the shop1
    '''
    soup1 = BeautifulSoup(requests.get(shop1_url).text, 'html.parser')
    smartphones1 = soup1.find_all('li', {'class': 'catalog-grid__cell catalog-grid__cell_type_slim ng-star-inserted'})
    next_page_tag1 = soup1.find('a', {'class': 'button button--gray button--medium pagination__direction pagination__direction--forward ng-star-inserted'})

    for inx, phone in enumerate(smartphones1):
        title = phone.find('a', {'class': 'goods-tile__heading ng-star-inserted'}).text
        price = phone.find('span', {'class': 'goods-tile__price-value'}).text
        link = phone.find('a', {'class': 'goods-tile__picture ng-star-inserted'}).get('href')
        phone_soup = BeautifulSoup(requests.get(link).text, 'html.parser')
        phone_description_tag = phone_soup.find('p', {'class': 'product-about__brief ng-star-inserted'})
        phone_description = phone_description_tag.text if phone_description_tag else 'N/A'
        shop1_phones_dict[inx] = [title, price, link, phone_description]
        
    try:
        shop1_url = 'https://rozetka.com.ua' + next_page_tag1.get('href')
    except Exception as e:
        break


while True:
    '''
    Scraping data such as phone title, price, link and short description from the shop2
    '''
    soup2 = BeautifulSoup((requests.get(shop2_url, headers=headers)).text, 'html.parser')
    smartphones2 = soup2.find_all('li', {'class': 'product-item'})
    next_page_tag2 = soup2.find('a', {'class': 'next'})

    for inx, phone in enumerate(smartphones2):
        try:
            '''to evade ads'''
            title = phone.find('p', {'class': 'h4'}).text
        except Exception as e:
            continue
        price_tag = phone.find('div', {'class': 'price-md'})
        price = price_tag.text if price_tag else 'N/A'
        link = 'https://hotline.ua' + phone.find('a', {'data-eventaction': 'Priceline'}).get('href')
        desc = phone.find('div', {'class': 'text'}).text
        shop2_phones_dict[inx]= [' '.join(title.split()), price, link, ' '.join(desc.split()[3:])]

    try:
        shop2_url = 'https://hotline.ua/mobile/mobilnye-telefony-i-smartfony/133-294356/' + next_page_tag2.get('href')
    except Exception as e:
        break


while True:
    '''
    Scraping data such as phone title, price, link and short description from the shop2
    '''
    soup3 = BeautifulSoup(requests.get(shop3_url).text, 'html.parser')
    smartphones3 = soup3.find_all('div', {'class': 'product-card'})
    next_page3 = soup3.find('a', {'class': 'pagination__next__link pagination__links'})
    
    for inx, phone in enumerate(smartphones3):
        desc = []
        title = phone.find('a', {'class': 'product-card__title'}).text    
        price_tag = phone.find('div', {'class': 'v-price-box__cur'})
        price_tag2 = phone.find('div', {'v-price-box__cur v-price-box__cur--discount'})
        price = price_tag.text if price_tag else price_tag2.text if price_tag2 else 'N/A' 
        link = phone.find('a', {'class': 'product-card__title'}).get('href')
        desc_soup = BeautifulSoup(requests.get(link).text, 'html.parser')
        desc_list = desc_soup.find_all('tr', {'class': 'product-details__row without-image'})
        [desc.append(' '.join(value.text.split())) for value in desc_list]
        shop3_phones_dict[inx] = [title, price, link, ', '.join(desc)]

    try:
        shop3_url = next_page3.get('href')
    except Exception as e:
        break

shop1_phones_df = pd.DataFrame.from_dict(shop1_phones_dict, orient='index', columns=['Model', 'Price', 'URL model', 'Description'])
shop2_phones_df = pd.DataFrame.from_dict(shop2_phones_dict, orient='index', columns=['Model', 'Price', 'URL model', 'Description'])
shop3_phones_df = pd.DataFrame.from_dict(shop3_phones_dict, orient='index', columns=['Model', 'Price', 'URL model', 'Description'])
df_list = [shop1_phones_df, shop2_phones_df, shop3_phones_df]

def pricetoint(df):
    '''
    In our datasets price values have str type and additional symbols, so let's unify it
    '''
    for inx, i in enumerate(df['Price']):
        if isinstance(i, str):
            listed = i.split()
            for j in listed:
                if not j.isdigit():
                    listed.remove(j)
            df['Price'][inx] = (int(listed[0] + listed[1]))

def modelname(df):
    '''
    Every shop has its own way to write the title of the smartphone,
    so we need to "get a common denominator" to be able to compare positions
    '''
    for modelinx, i in enumerate(df['Model']):
        listed = i.split()
        for modelname in listed:
            if listed[0] != 'Samsung':
                listed.pop(0)
            else: break
        temp = []
        for inx, j in enumerate(listed):
            if 'Gb' in j or 'gb' in j:
                listed[inx] = j[:-2] + 'GB'
            if 'GB' in listed[inx]:
                temp.append(listed[:inx+1])
                if temp[0][-2] == '':
                    temp[0].pop(-2)
                break
        if listed[3] == 'Plus':
            temp[0][2] = temp[0][2] + '+'
            temp[0].remove('Plus')
        if temp[0][-1] == 'GB':
            temp[0][-2] = temp[0][-2] + 'GB'
            temp[0].pop()
        df['Model'][modelinx] = (' '.join(temp[0]))


def datatransform(df):
    '''
    Apply functions and get rid of positions without prices
    '''
    pricetoint(df)
    modelname(df)
    df.dropna(inplace=True)
            
datatransform(shop1_phones_df)
datatransform(shop2_phones_df)
datatransform(shop3_phones_df)

occurs = set()
models, prices, urls, descs = [], [], [], []

'''
Collect not unique models (which occurs in more then 1 dataset) and identify the best offer
'''
for i in shop2_phones_df['Model']:
    if i in list(shop1_phones_df['Model']) or i in list(shop3_phones_df['Model']):
        occurs.add(i)

for model in occurs:
    temp = {model: [999999, '']}
    for df in df_list:
        if model in list(df['Model']):
            filt = (df['Model'] == model)
            inx = df.index[filt].tolist()
            if temp[model][0] > df.at[inx[0], 'Price']:
                temp[model] = [df.at[inx[0], 'Price'], df.at[inx[0], 'URL model'], df.at[inx[0], 'Description']]

    for model, etc in temp.items():
        models.append(model)
        prices.append(etc[0])
        urls.append(etc[1])
        descs.append(etc[2])

'''
Make the dict, fill it with data, transform it into the DataFrame, then export it to file
'''
min_prices = {
    'Model': [],
    'Best Price, UAH': [],
    'Offer URL': [],
    'Description' : []
    }

for i in range(len(models)):
    min_prices['Model'].append(models[i])
    min_prices['Best Price, UAH'].append(prices[i])
    min_prices['Offer URL'].append(urls[i])
    min_prices['Description'].append(descs[i]) 
    
df_min_prices = pd.DataFrame(min_prices)
df_min_prices.to_excel('Best offer.xlsx')