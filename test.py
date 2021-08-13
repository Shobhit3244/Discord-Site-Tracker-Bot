import requests
from bs4 import BeautifulSoup

a = requests.get("https://www.jdsports.co.uk/product/adidas-originals-nite-jogger-shoes/16052244/")
data = BeautifulSoup(a.content, parser='html.parser')
print(data.prettify())
productData = {'name': data.find('h1', {'itemprop': "name"}).text.strip(),
               'price': data.find('span', {'class': "pri"}).text,
               'brand': data.find('h1', {'itemprop': "name"}).text.strip().split()[0],
               'size': data.find('div', {'class': 'option', 'id': 'productSizeStock'})}
try:
    productData['image'] = data.find('img', {'class': 'c-image-gallery__img'}).get('src')
except:
    productData['image'] = data(productData['brand'] + ' ' + productData['name'])

try:
    productData['color'] = data.find('div', {"class": "tab-info"}).find('h3').text
except:
    productData['color'] = 'Available'

for i in productData:
    print(i, productData[i])
