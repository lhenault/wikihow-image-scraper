import os
import time
import functools
from io import BytesIO
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image
import requests

ImgDim = Tuple[int, int]

 
def wait(n_seconds):
    def decorator_wait(func):
        @functools.wraps(func)
        def wrapper_wait(*args, **kwargs):
            time.sleep(n_seconds)
            return func(*args, **kwargs)
        return wrapper_wait
    return decorator_wait


def center_crop(img: Image, size: ImgDim):        
    width = img.size[0]
    height = img.size[1]

    new_width = min(width, size[0])
    new_height = min(height, size[1])

    left = int(np.ceil((width - new_width) / 2))
    right = width - int(np.floor((width - new_width) / 2))

    top = int(np.ceil((height - new_height) / 2))
    bottom = height - int(np.floor((height - new_height) / 2))
    
    center_cropped_img = img.crop((left, top, right, bottom))

    return center_cropped_img


def rescale(img, size: int=512):
    width = img.size[0]
    height = img.size[1]
    
    if width >= height:
        new_height = size
        new_width  = int(new_height * width / height)
    else:
        new_width  = size
        new_height = int(new_width * height / width)
    
    return img.resize((new_width, new_height), Image.ANTIALIAS)

def load_url(url: str, crop_to: ImgDim=None, save_to: Path=None) -> Image:
    r = requests.get(url=url)
    img = Image.open(BytesIO(r.content))
    
    if crop_to:
        img = center_crop(img=img, size=crop_to)
    
    if save_to:
        img.save(fp=save_to)
        
    return img


class WebImage:
    def __init__(self, url) -> None:
        self.url = url
        self.data = None
    
    def open(self):
        self.data = load_url(self.url)
        return self
    
    def rescale(self, size=512):
        if self.data:
            self.data = rescale(img=self.data, size=size)
        return self
    
    def crop(self, crop_to: ImgDim=None):
        if crop_to and self.data:
            self.data = center_crop(img=self.data, size=crop_to)
        return self
    
    def save(self, to='./dataset', filename=None, format='png'):
        os.makedirs(to, exist_ok=True)
        if not filename:
            filename = Path(self.url).stem
        
        save_to = Path(os.path.join(to, f'{filename}.{format}'))
        self.data.save(save_to)
        
        return self
