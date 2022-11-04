
import logging
from functools import partial
from collections import deque
from multiprocessing import Pool
from urllib.parse import urlparse, urljoin

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
        image = WebImage(url=get_image_file(image_url))
        image.open().rescale(rescale_to).crop(crop_to).save(to=to)
    except Exception as ex:
        logging.exception(f'Error trying to download image from {image_url} 😬\n{ex}')


class WikiHowImages:
    def __init__(self, entrypoint: str='https://www.wikihow.com/Main-Page') -> None:
        self.entrypoint = entrypoint
        self.visited = set()
        self.images = set()
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
        
        logging.info(f'{len(articles)} pages and {len(images)} image found')
        
        return dict(url=url, images={process_url(item) for item in images}, articles={process_url(item) for item in articles})

    def create_dataset(self, start=None, max_pages: int=0, max_images: int=0, from_scratch: bool=True):
        if not start:
            start = self.last_visited
        
        pages       = deque([start])
        images      = set() if from_scratch else self.images
        visited     = set() if from_scratch else self.visited
        
        while pages:
            url = pages.popleft()
            try:
                results = self.analyze_page(url=url)
                
                self.last_visited = results.get('url')
                self.download_queue.update(results.get('images'))

                visited.add(results.get('url'))
                images.update(results.get('images'))
                
                for link in results.get('articles'):
                    if link not in visited:
                        pages.append(link)
            except Exception as ex:
                logging.exception('Something went wrong here with: {url} 😵\n {ex}')
                    
            if (max_images and len(images) >= max_images) or (max_pages and len(visited) >= max_pages):
                break
        
        self.images.update(images)
        self.visited.update(visited)
        return self
    
    def download(self, to='./export', rescale_to: int=None, crop_to: ImgDim=None, processes=10):
        pool = Pool(processes=processes)
        pool.map(partial(download_image, rescale_to, crop_to, to), self.download_queue)
        self.download_queue = set()
        
