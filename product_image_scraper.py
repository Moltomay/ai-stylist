import requests
from bs4 import BeautifulSoup
import re
import logging
import urllib3
import urllib.parse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_product_image(url):
    """
    Scrape the main product image from a given product URL.
    
    Args:
        url (str): The product page URL to scrape
    
    Returns:
        str: URL of the product image, or None if no image found
    """
    if not url or not isinstance(url, str):
        logger.error(f"Invalid URL provided: {url}")
        return None

    try:
        # More comprehensive headers to mimic different browsers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Detailed logging of request parameters
        logger.debug(f"Attempting to scrape image from URL: {url}")
        logger.debug(f"Request headers: {headers}")
        
        # Send a GET request to the URL with additional parameters
        response = requests.get(
            url, 
            headers=headers, 
            timeout=15,  # Increased timeout
            verify=False,  # Disable SSL verification to handle various certificate issues
            allow_redirects=True  # Follow redirects
        )
        
        # Log detailed response information
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Comprehensive list of potential image selectors
        image_selectors = [
            # Most specific selectors first
            ['img[data-testid="product-media-primary"]'],  # Nike
            ['img.product-image__main'],  # Nordstrom
            ['img[data-auto-id="productThumbnail"]'],  # ASOS
            ['img#landingImage', 'img#imgBlkFront'],  # Amazon
            ['img.c-product-image__img'],  # Urban Outfitters
            ['img.product-media__image'],  # Adidas
            
            # Generic selectors
            ['img.product-image', 'img.ProductImage', 'img#ProductImage', 'img.main-image'],
            
            # Fallback: look for largest image
            ['img']
        ]
        
        # Try different selector strategies
        for selector_group in image_selectors:
            logger.debug(f"Trying image selectors: {selector_group}")
            
            for selector in selector_group:
                images = soup.select(selector)
                logger.debug(f"Found {len(images)} images for selector {selector}")
                
                for img in images:
                    # Extract image source with multiple attribute checks
                    src = (
                        img.get('src') or 
                        img.get('data-src') or 
                        img.get('srcset') or 
                        img.get('data-image') or 
                        img.get('data-original')
                    )
                    
                    # Validate image URL
                    if src:
                        # Ensure full URL
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif not src.startswith('http'):
                            # Handle relative URLs
                            base_url = f"{response.url.split('/')[0]}//{response.url.split('/')[2]}"
                            src = urllib.parse.urljoin(base_url, src)
                        
                        logger.info(f"Found product image: {src}")
                        return src
        
        logger.warning(f"No product image found for URL: {url}")
        return None
    
    except requests.RequestException as e:
        logger.error(f"Request error for URL {url}: {e}")
        # Log additional details about the error
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        return None

def batch_scrape_product_images(product_links):
    """
    Batch scrape product images for multiple product links.
    
    Args:
        product_links (dict): Dictionary of product links
    
    Returns:
        dict: Dictionary of product links with added image URLs
    """
    # Create a copy of the input to avoid modifying the original
    products_with_images = product_links.copy()
    
    # Scrape images for each product
    for category, product in products_with_images.items():
        if product.get('link'):
            try:
                logger.info(f"Attempting to scrape image for {category}: {product['link']}")
                image_url = scrape_product_image(product['link'])
                if image_url:
                    products_with_images[category]['image_url'] = image_url
                    logger.info(f"Successfully scraped image for {category}")
                else:
                    logger.warning(f"No image found for {category}")
            except Exception as e:
                logger.error(f"Error scraping image for {category}: {e}")
    
    return products_with_images

# Example usage
if __name__ == '__main__':
    # Test the scraper with sample URLs
    test_urls = [
        'https://www.nike.com/t/air-force-1-07-mens-shoes-jBrhDk/CW2288-111',
        'https://www.adidas.com/us/ultraboost-22-shoes/GZ9974.html',
        'https://www.nordstrom.com/s/nike-air-force-1-07-sneaker-men/5623532'
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        image_url = scrape_product_image(url)
        print(f"Scraped image URL: {image_url}")
