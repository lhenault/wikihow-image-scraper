# A simple and compliant WikiHow image scraper

## Overview

I needed to scrape some images from [WikiHow](https://www.wikihow.com/), so I built this to do so. It doesn't do anything crazy but allow you to crawl the website and:

- Save some images,
- Resize them,
- Crop them if needed

Please note that this project isn't aiming at maximal performance and speed, as I am willing to comply with their [robots.txt policy](https://www.wikihow.com/robots.txt), especially an expected rate of one page every 3 seconds at most. This is ensured through a simple decorator [here](/src/wikihow/utils.py#L15) used with `n_seconds=3`, and a single process for download.

## Setup

### Using Python3

I'd recommend to use a `pipenv`, a `conda env` or something similar to start fresh and avoid potential conflicts and issues. That being said, it is as boring as expected to setup the project:

```bash
pip install -r requirements.txt
```

And you should be ready to go.

### Within Docker (recommended)

Build the image using the provided `Dockerfile`:

```bash
docker build --pull --rm -f "Dockerfile" -t wikihow:latest "."
```

### Usage

Simply run `python create_dataset.py`, and set the options to what suits your use case.

```bash
$ python create_dataset.py -h
usage: create_dataset.py [-h] [-s START] [-p PAGES] [-i IMAGES] [-b BATCH_SIZE] [-D DIRECTORY] [-R RESCALE] [-H HEIGHT] [-W WIDTH]

A simple WikiHow image scraper

options:
  -h, --help            show this help message and exit
  -s START, --start START
                        Page from where we start exploring the site
  -p PAGES, --pages PAGES
                        Maximum number of pages to explore (0 : no limit). Use one to focus on a single one
  -i IMAGES, --images IMAGES
                        Maximum number of images to retrieve (0 : no limit)
  -b BATCH_SIZE, --batch_size BATCH_SIZE
                        The "batch" size: to process N by N pages and downloading data every Nth page (use 1 to download content only at the end).
  -D DIRECTORY, --directory DIRECTORY
                        Path to directory where images are stored
  -R RESCALE, --rescale RESCALE
                        Size of the smaller dimension after resizing (aspect ratio is preserved)
  -H HEIGHT, --height HEIGHT
                        Height after center crop
  -W WIDTH, --width WIDTH
                        Width after center crop

```

## License

MIT License

Copyright (c) 2022 Louis HENAULT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
