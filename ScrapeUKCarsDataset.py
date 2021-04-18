#!/usr/bin/python
##########################################################################################################
api_key = "CXUWSH6Y2BRB8F07MB7YXWPYWV2TQ4K51G4N6SGEU1YDADAVDW35ZT7WNISZ8YMCQ810OP9KG22ZI2P2"
##########################################################################################################
# This app scrapes nice car images from Autotrader to create a UK-based dataset of car brands for ML,
# without anyone at Autotrader noticing, by using some clever magic, which comes at a monetary cost:
# We use the best scraper service API, Scraping Bee. Sign up with this link and get your own API key:
# https://www.scrapingbee.com?fpr=nobnose-inc27
##########################################################################################################
# This is the URL to scrape
url='https://www.autotrader.co.uk'
rootdir='UKCarsDataset'

# We ideally want about 100 images per brand for a healthy dataset for the Machine Learning. 
# A rule of thumb is that 100 images should be sufficient to teach an ML instance about each category. 
# You can top up images until you have this amount by re-running this app after every curation
# exercise. Also run this app every few weeks to top up the image counts for those more obscure 
# brands for which you have not yet managed to get 100 good images so far. 
# Expect to loose 25% of the new images per curation exercise, so it is a good idea to set the
# number of images per brand to 150 the first time that you run it. 
# 
# The first curation step is to remove all duplicate images. These are caused by advertisers using 
# generic stock images or simply their logo. There is unlikely going to be be any useful,so just 
# summarily remove them first of all with the command
#
# fdupe -rd UKCarsDataset
#
# This app selects only the main image per advertised car, which is usually a front-on view with a
# slight side angle, like in a fashion shoot. This is exactly what we want, since the 
# observation camera will mpstly be placed facing oncoming traffic on the side of the road.
# 
# The second curation step is to visually inspect all your new files and remove those that are
# not useful for ML, like a side view, interiour view, obvious dealership signage, a girly model
# draped across the car's hood, big for-sale text and price in front window, etc., 
# If you remove these images, you can rerun the scraping process a few weeks later
# when the offending vehicles have been removed from the website.
#
# Finally, all the registration number plates need to be blanked out from the images. 
# This is still work in progress and is not perfect. Use the utility BlankRegPlate that is also 
# in this repo:
# 
# find UKCarsDataset -type f -name "*.jpg" -exec BlankRegPlate {} \;
#
imagesPerBrand=100

# .. and these are the mpst frequently-encountered brands in the UK that we are interested in:
searchBrands=["ALFA ROMEO","ALPINE","ASTON MARTIN","AUDI","BENTLEY","BMW","BUGATTI","CADILLAC","CHEVROLET","CHRYSLER","CITROEN","CORVETTE","DACIA","DAEWOO","DAIHATSU","DAIMLER","DODGE","DS AUTOMOBILES","FERRARI","FIAT","FORD","GMC","GREAT WALL","HONDA","HUMMER","HYUNDAI","INFINITI","ISUZU","IVECO","JAGUAR","JEEP","KIA","LAMBORGHINI","LANCIA","LAND ROVER","LEXUS","LINCOLN","LONDON TAXIS INTERNATIONAL","LOTUS","MASERATI","MAYBACH","MAZDA","MCLAREN","MERCEDES-BENZ","MG","MINI","MITSUBISHI","MORGAN","MORRIS","NISSAN","PEUGEOT","POLESTAR","PONTIAC","PORSCHE","PROTON","RELIANT","RENAULT","ROLLS-ROYCE","ROVER","SAAB","SEAT","SKODA","SMART","SSANGYONG","SUBARU","SUZUKI","TESLA","TOYOTA","TRIUMPH","TVR","VAUXHALL","VOLKSWAGEN","VOLVO",]

##########################################################################################################
from bs4 import BeautifulSoup as bs
from random import randrange
import requests
import re
import os
import time
import urllib.parse

# Setup logging:
import logging
logger = logging.getLogger(__name__)  # __name__=  __main__ here
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(message)s]',datefmt='%Y%m%d %H:%M:%S')
file_handler=logging.FileHandler(__file__.replace('.py','.log'))
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
stream_handler=logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.WARNING)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
# Use logger.debug, logger.info, logger.error, logger.warning, logger.critical with C sprintf-style messages

# Add custom logger for timeouts
logging.TIMEOUT = 45
logging.addLevelName(logging.TIMEOUT, "TIMEOUT")
def timeout(self, message, *args, **kws):    
    self._log(logging.TIMEOUT, message, args, **kws) 
logging.Logger.timeout = timeout


# Set up Process Watchdog 
import signal
class Watchdog(Exception):  # Usage: 
  def __init__(self, time=5):
    self.time = time 
  def __enter__(self):
    signal.signal(signal.SIGALRM, self.handler)
    signal.alarm(self.time)  
  def __exit__(self, type, value, traceback):
    signal.alarm(0)    
  def handler(self, signum, frame):
    raise self  
  def __str__(self):
    return "Function call took more than %ds to complete" % self.time


# Precomile regex patterns
# Get car-details/202010145004040 from href="/car-details/202102128983367?...
patternCarId=re.compile(r'/car-details/(\d{15})?',re.IGNORECASE)


# Arbitrary post code because the website insists on it
postcodes=['PE67XT','RH106JT','NW116LU','SW1A 0AA','SW1A 2AB']

# Send a request via ScrapingBee and returns a response that contains:
# HTTP Status Code: response.status_code
# HTTP Response Body: response.content
def send_request(fetchurl,withJS=0):  
  startTime = time.perf_counter()

  try:    
    with Watchdog(30): # 30 seconds timeout
      logger.info("Requesting %s %s JS rendering",fetchurl, ("with" if withJS==9 else "without"))
      response = requests.get(
        url="https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": api_key ,
            "url": fetchurl,  
            "render_js": "false" if withJS==0 else "true",
            "wait" : 2000,
          },        
        )
  except Watchdog:
    logger.timeout("Scraping Bee API call timed out. Last try: %s",fetchurl)
    time.sleep(1)
    try:      
      with Watchdog(30): # 30 seconds timeout
        response = requests.get(
          url="https://app.scrapingbee.com/api/v1/",
          params={
              "api_key": api_key ,
              "url": fetchurl,  
              "render_js": "false" if withJS==0 else "true",
              "wait" : 2000,
            },        
          )      
    except Watchdog:
      logger.fatal("Network issue. Giving up & exiting.")
      exit(1)
  except:
    logger.warning("SSL Handshake error. Retrying after 1sec")    
    try:
      time.sleep(1)
      logger.info("Again requesting %s %s JS rendering",fetchurl, ("with" if withJS==9 else "without"))
      response = requests.get(
        url="https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": api_key ,
            "url": fetchurl,  
            "render_js": "false" if withJS==0 else "true",
            "wait" : 2000,
          },        
        )      
    except:
      logger.fatal("Network issue. Giving up & exiting.")
      exit(1)
  return response



##########################################################################################################
# Main
##########################################################################################################
def main():
  for searchBrand in searchBrands:
    postcode=urllib.parse.quote(postcodes[randrange(len(postcodes))]) # mix the postcodes up a little

    # Get number of files already 
    brandPath="{}/{}".format(rootdir,searchBrand)
    try:
      os.mkdir(brandPath,0o777)
    except:
      logger.warning('Directory %s already exists',searchBrand)
    _path, _dirs, _files = next(os.walk(brandPath))
    currentFileCount = len(_files)  
    imagesToGet = imagesPerBrand - currentFileCount
    logger.info('Getting %d images for car brand %s',imagesToGet,searchBrand)
      
    # Front page search for each car brand  
    imageCount = 0
    carPrevIds=[]
    carIds=[]
    # Go through all the pages for this brand until we have enough unique images in a brand's directory
    for page in range(1,99):
      if imageCount >= imagesToGet:
        break
      # Make up URL 'https://www.autotrader.co.uk/car-search?postcode=XXXXXXX&make=AUDI&page=XXXX',    
      page10CarURL='{}/car-search?postcode={}&make={}&page={}'.format(url,postcode,urllib.parse.quote(searchBrand),page)
      logger.info('%s: Getting page %d at %s', searchBrand,page,page10CarURL)
      response = send_request(page10CarURL)
      if response.status_code != 200:
        logger.error("Request error for URL %s resulted error code: %d", page10CarURL, response.status_code)
        logger.debug(response.content)
        break # no more pages for brand
      else:
        # Process 10-car page (mostly 10 to 13)
        soup = bs(response.content,'html.parser')
        # Check for errors
        title=soup.find('title').text.replace(' ','')
        if 'denied' in title:
          logger.error('Access denied by web server.')
          logger.debug(soup.prettify())
          exit(1)
        else:        
          # Check if redirected to previous page by comparing list of Car Ids
          # of this page to the previous one. If they are the same, it means 
          # that there are no more pages left for this brand          
          carPrevIds = carIds.copy() # save previous state
          carIds.clear()

          anchors = soup.find_all('a',class_='js-click-handler listing-fpa-link tracking-standard-link')         
          logger.info('Found %d cars on page %d', len(anchors), page)
          carCounter=0
          for anchor in anchors:   
            carCounter+=1
            href = anchor.attrs["href"]
            # Get anchor's href link to get car details, find 15-digit carDetailsId 
            # in 'href="/car-details/202102128983367?...'
            #                        ===============
            match = re.search(patternCarId,href)
            try:
              carDetailsId = match.group(1)            
            except:
              logger.warning("Advert panel. Skipping.")
              continue

            carIds.append(carDetailsId)
            file_path="{}/{}/{}.jpg".format(rootdir,searchBrand,carDetailsId)                 
            if os.path.exists(file_path):
              logger.warning('File %s already exists. Skipping.', file_path)
            else:
              logger.info("Getting page %d car %d details CarId %s into %s", page, carCounter, carDetailsId,file_path)
              # Make up car details URL https://www.autotrader.co.uk/car-details/202010145004040
              carDetailsURL=url+'/car-details/'+carDetailsId
              # Fetch URL
              carGalleryPageResponse=send_request(carDetailsURL,1)
              soupGallery = bs(carGalleryPageResponse.content,'html.parser')
              # Get first image only since it is likely to be a front-facing view:
              divCar = soupGallery.find('div', class_='fpa-gallery__placeholder')               
              # Get src=..., something like <img src="https://m.atcdn.co.uk/a/media/w800h600/7bd9c19191ad4dc78bd8c21ec8148734.jpg"...>
              try:
                imageCar = divCar.img
              except:
                logger.warning('Retrying with different class name #2 for %s', carDetailsURL)
                divCar = soupGallery.find('div', class_='fpa-gallery__placeholder  ') 
                try:
                  imageCar = divCar.img
                except:
                  logger.error('Giving up, could not find an img tag in the div. Skipping...')
                  # totally give up
                  continue

              urlCarImage=imageCar.attrs["src"]
              # Get image file and put in searchBrand directory
              logger.info('Getting image from %s',urlCarImage)
              tic = time.perf_counter()
              try:
                with Watchdog(30): # 30 seconds timeout
                  carImageResponse=requests.get(urlCarImage)
              except Watchdog:
                logger.timeout("Scraping image using Beautiful Soup timed out. Last try: %s",urlCarImage)
                time.sleep(1)
                try:
                  carImageResponse=requests.get(urlCarImage)
                except:
                  logger.error("SSL Handshake error. Skipping.")
                  continue
              except:
                try:
                  logger.warning("SSL Handshake error. Retrying one more time")
                  time.sleep(1)
                  carImageResponse=requests.get(urlCarImage)
                except:
                  logger.error("SSL Handshake error. Skipping.")
                  continue
              
              logger.info('Writing file %s. Time to retrieve: %04f seconds',file_path, (time.perf_counter()-tic))
              f = open(file_path,'wb')
              f.write(carImageResponse.content)
              f.close()
              imageCount = imageCount + 1
              if imageCount >= imagesToGet:
                break
          # } anchor

          carIds.sort()
          carPrevIds.sort()
          if carIds == carPrevIds:
            # A redirection happened.
            logger.warning("No more %s brand cars available. Last page was %s.",searchBrand,page10CarURL)
            break # no more pages for brand
  # } for
  logger.info("All car brands scraped.")
# } main          

if __name__ == "__main__":
  main()
