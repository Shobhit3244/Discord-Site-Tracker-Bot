import cloudscraper
import requests
from bs4 import BeautifulSoup

try:
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
        })
except:
    scraper = requests
codeList = {
    'https://www.jdsports.co.uk': ['/men/mens-footwear/brand/jordan/latest/?max=72',
                                   ['li', {'class': 'productListItem'}]],
    'https://www.footpatrol.com': [
        '/footwear/brand/jordan/latest/?fp_sort_order=latest',
        ['li', {'class': 'productListItem'}]],
    'https://www.size.co.uk': ['/mens/footwear/brand/jordan/latest/',
                               ['li', {'class': 'productListItem'}]],
    'https://www.selfridges.com': ['/GB/en/cat/mens/shoes/jordan/nike/?fh_sort_by=newest',
                                   ['div', {'class': 'col-xs-6 col-sm-4 c-listing-items__item'}]],
    'https://www.endclothing.com': [
        '/gb/latest-products/latest-sneakers?brand=Nike%20Jordan&brand=Nike%20SB&page=1',
        ['a', {'data-test': "ProductCard__ProductCardSC"}]],
    'https://www.sneakersnstuff.com': ['/en/858/mens-new-arrivals?p=5954&orderBy=Published',
                                       ['article', {'class': 'card product'}]],
    'https://www.asos.com': [
        '/men/new-in/new-in-shoes/cat/?cid=17184&currentpricerange=5-195&nlid=mw%7Cnew'
        '%20in%7Cnew%20products%7Cshoes&refine=brand:2986&sort=freshness',
        ['article', {'class': '_2qG85dG'}]]}


def get_html(url: str):
    try:
        content = scraper.get(url)
    except:
        return False, 'CloudFlare 2 Detected'
    reader = BeautifulSoup(content.content, 'html.parser')
    if str(content).strip() != "<Response [200]>":
        # print(f"Got Error Response Code: {content} While Fetching HTML data\n data: {content.content}")  # To check the Error Code of The Fetched Data
        return False, f"Got Error Response Code: {content}"
    else:
        return True, reader


def get_relatedImages(query: str):
    GOOGLE_IMAGE = 'https://www.google.com/search?site=&tbm=isch&source=hp&biw=1873&bih=990&'
    if " " in query:
        query = '%20'.join(query.split(' '))
    url = GOOGLE_IMAGE + 'q=' + query
    response = requests.get(url).content
    soup = BeautifulSoup(response, 'html.parser')
    # print(url)                # Uncomment to see the image url
    return soup.find('img', {"class": "t0fcAb"}).get('src')


def extract_data(site: str):
    global codeList
    # print(site)
    # required_data = ['name', 'url', 'price', 'size', 'image', 'brand']
    availability, receivedData = get_html(site + codeList[site][0])
    # print(receivedData.prettify())        # To see the contents of the Incoming HTML File

    if not availability:
        return ['Error Fetching Data: Please Try Again Later'], availability

    listingsSites = receivedData.findAll(codeList[site][1][0], codeList[site][1][1])
    linkList = set()

    for products in listingsSites:
        try:
            link = products.find('a')['href']
        except:
            link = products.get('href')
        # print(link)       # To See the List of Product Links on the Search Page
        if link.startswith(site):
            linkList.add(link)
        else:
            linkList.add(site + link)

    print(len(linkList))       # To See the number of links found
    return linkList, len(linkList)