import argparse
import logging
from tqdm import tqdm

from wikihow.wikihow import WikiHowImages

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = 'A simple WikiHow image scraper',
    )
        
    # Crawler parameters
    parser.add_argument('-s', '--start', type=str, default='https://www.wikihow.com/Main-Page', help='Page from where we start exploring the site')
    parser.add_argument('-p', '--pages', type=int, default=1, help='Maximum number of pages to explore (0 : no limit). Use one to focus on a single one')
    parser.add_argument('-i', '--images', type=int, default=0, help='Maximum number of images to retrieve (0 : no limit)')
    parser.add_argument('-b', '--batch_size', type=int, default=1, help='The "batch" size: to process N by N pages and downloading data every Nth page (use 1 to download content only at the end).')
    parser.add_argument('-P', '--processes', type=int, default=1, help='Number of processes for image downloads, experiment at your own risk.')

    # Output directory
    parser.add_argument('-D', '--directory', type=str, default='./data', help='Path to directory where images are stored')
    
    # Image processing parameters
    parser.add_argument('-R', '--rescale', type=int, default=512, help='Size of the smaller dimension after resizing (aspect ratio is preserved)')

    parser.add_argument('-H', '--height', type=int, default=512, help='Height after center crop')
    parser.add_argument('-W', '--width', type=int, default=512, help='Width after center crop')
    
    # Logs
    parser.add_argument('-L', '--loglevel', type=str, default=logging.INFO, help='Logging level')
    
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    
    # Data gathering
    dataset = WikiHowImages(entrypoint=args.start)
    
    def run_batch(dataset, start):
        return dataset.create_dataset(
            start=start,
            max_pages=args.batch_size,
            max_images=max(1, args.images - len(dataset.images)) if args.images else 0
        ).download(
            rescale_to=args.rescale, 
            crop_to=(args.width, args.height), 
            to=args.directory,
            processes=args.processes
        )
        
    if args.pages:   
        for _ in tqdm(range(args.pages // args.batch_size)):
            dataset = run_batch(dataset, start=dataset.last_visited)
    else:
        while True:
            dataset = run_batch(dataset, start=dataset.last_visited)
            if not dataset.pages:
                break