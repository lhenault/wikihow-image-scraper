
import logging
from functools import partial
from collections import deque
from multiprocessing import Pool
from urllib.parse import urlparse, urljoin

from tqdm import tqdm
import requests
from fake_useragent import UserAgent
from tenacity import retry, wait_random, stop_after_attempt
from bs4 import BeautifulSoup

from wikihow.utils import WebImage, ImgDim, wait

    
def process_url(href):
    if href.startswith('#'):
        href = href[1:]
    parsed_href = urlparse(href)
    new_url = urljoin('https://www.wikihow.com/', parsed_href.path)
    return new_url


@wait(n_seconds=3)
def get_image_file(image_url):
    '''
    Convenient decorator in order to respect [robots.txt](https://www.wikihow.com/robots.txt) instructions and crawl at most one page every 3 seconds.
    '''
    page = requests.get(
        url=image_url, 
        headers={"User-Agent": UserAgent().random}
    )
    soup = BeautifulSoup(page.text, 'html.parser')
    href = soup.find('div', class_='fullImageLink').find('a').get('href')
    href = process_url(href)
    return href


def download_image(rescale_to, crop_to, to, image_url):
    try:
        logging.debug(f'Downloading and processing {image_url} (rescaling to {rescale_to}, center crop of size {crop_to})')
        image = WebImage(url=get_image_file(image_url))
        image.open().rescale(rescale_to).crop(crop_to).save(to=to)
    except Exception as ex:
        logging.exception(f'Error trying to download image from {image_url} 😬\n{ex}')


class WikiHowImages:
    def __init__(self, entrypoint: str='https://www.wikihow.com/Main-Page') -> None:
        self.entrypoint = entrypoint
        self.visited = set()
        self.images = set()
        self.pages = deque([])
        self.pages_set = set()
        self.last_visited = entrypoint
        self.download_queue = set()
    
    @wait(n_seconds=3)
    @retry(wait=wait_random(min=0, max=2), stop=stop_after_attempt(3))
    def analyze_page(self, url: str):
        articles = []
        images = []
        
        page = requests.get(
            url=url, 
            headers={"User-Agent": UserAgent().random}
        )
        
        soup = BeautifulSoup(page.text, 'html.parser')
        articles = set([item.get('href') for item in soup.find_all('a', class_='related-wh')] + [item.find('a').get('href') for item in soup.find_all('div', class_='hp_thumb')])
        images = set(item.get('href') for item in soup.find_all('a', class_='image'))
        
        logging.info(f'{len(articles)} pages and {len(images)} image found in {url}')
        
        return dict(url=url, images={process_url(item) for item in images}, articles={process_url(item) for item in articles})

    def create_dataset(self, start=None, max_pages: int=0, max_images: int=0):
        if not start:
            start = self.last_visited
        
        if start not in self.visited:
            self.pages.appendleft(start)
            self.pages_set.add(start)
        
        n_pages = 0
        n_images = 0
        
        while self.pages:
            url = self.pages.popleft()
            self.pages_set.remove(url)
            try:
                if url not in self.visited:
                    logging.info(f'Analyzing {url}')
                    results = self.analyze_page(url=url)
                    
                    self.last_visited = results.get('url')
                    self.download_queue.update(results.get('images'))

                    self.visited.add(results.get('url'))
                    self.images.update(results.get('images'))
                    
                    n_images += len(results.get('images'))
                    n_pages += 1
                    
                    for link in results.get('articles'):
                        if link not in self.visited and link not in self.pages_set:
                            self.pages.append(link)
                            self.pages_set.add(link)
            
            except Exception as ex:
                logging.exception(f'Something went wrong here with: {url} 😵\n {ex}')
                    
            if (max_images and n_images >= max_images) or (max_pages and n_pages >= max_pages):
                break
        return self
    
    def download(self, to='./export', rescale_to: int=None, crop_to: ImgDim=None, processes=10):
        logging.info(f'Downloading {len(self.download_queue)} images in {to}.')
        
        if processes > 1:
            with Pool(processes=processes) as pool:
                pool.map(partial(download_image, rescale_to, crop_to, to), self.download_queue)
        else:
            for image_url in tqdm(self.download_queue):
                download_image(rescale_to=rescale_to, crop_to=crop_to, to=to, image_url=image_url)
        self.download_queue = set()
        return self
        
