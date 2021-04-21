#!/usr/bin/python
##########################################################################################################
# We use the best scraper service API, Scraping Bee. 
# Sign up with this link and get your own API key:
# https://www.scrapingbee.com?fpr=nobnose-inc27
api_key = "CXUWSH6Y2BRB8F07MB7YXWPYWV2TQ4K51G4N6SGEU1YDADAVDW35ZT7WNISZ8YMCQ810OP9KG22ZI2P2"
##########################################################################################################
# This app scrapes nice VAN images from Autotrader to create a UK-based dataset of truck brands for ML,
# without anyone at Autotrader noticing, by using some clever magic, which comes at a monetary cost:
##########################################################################################################
# This is the URL to scrape
url='https://trucks.autotrader.co.uk'
rootdir='UKTrucksDataset'

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
# fdupe -rd UKTrucksDataset
#
# This app selects only the main image per advertised truck, which is usually a front-on view with a
# slight side angle, like in a fashion shoot. This is exactly what we want, since the 
# observation camera will mpstly be placed facing oncoming traffic on the side of the road.
# 
# The second curation step is to visually inspect all your new files and remove those that are
# not useful for ML, like a side view, interiour view, obvious dealership signage, a girly model
# draped across the truck's hood, big for-sale text and price in front window, etc., 
# If you remove these images, you can rerun the scraping process a few weeks later
# when the offending vehicles have been removed from the website.
#
# Finally, all the registration number plates need to be blanked out from the images. 
# This is still work in progress and is not perfect. Use the utility BlankRegPlate that is also 
# in this repo:
# 
# find UKTrucksDataset -type f -name "*.jpg" -exec BlankRegPlate {} \;
#
imagesPerBrand=150

# .. and these are the mpst frequently-encountered brands in the UK that we are interested in:
searchBrands=["CARTWRIGHT","CRANE FRUEHAUF","DAF","DENNIS","DENNIS EAGLE","DENNISON","DON-BUR","FODEN","FORD","FUSO","HINO","ISUZU","IVECO","MAN","MERCEDES-BENZ","MITSUBISHI","MONTRACON","RENAULT","ROTHDEAN","SCANIA","SCHMITZ","VOLVO"]

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
stream_handler.setLevel(logging.DEBUG)
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
# Get Id from href="
#  /classified/advert/cartwright/trailer/202104141349692
#  /classified/advert/cartwright/box/202104141349692
#  /classified/advert/renault/range-c/202104141349692
#  /classified/advert/daf/cf/202104141349692
patternVanId=re.compile(r'/classified/advert/.*/.*/(\d{15})?',re.IGNORECASE)

# Arbitrary post code because the website insists on it
postcodes=['EX1 1AT','GU16 7HF','PO16 7GZ','L1 8JQ','SW1A 0AA','SW1A 2AB','SW1A 2AA']

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
      os.makedirs(brandPath,0o777)
    except:
      logger.warning('Directory %s already exists',searchBrand)

    _path, _dirs, _files = next(os.walk(brandPath))
    currentFileCount = len(_files)  
    imagesToGet = imagesPerBrand - currentFileCount
    logger.info('Getting %d images for truck brand %s',imagesToGet,searchBrand)
      
    # Front page search for each brand  
    imageCount = 0
    truckPrevIds=[]
    truckIds=[]
    # Go through all the pages for this brand until we have enough unique images in a brand's directory
    for page in range(1,int(imagesPerBrand/5)):
      if imageCount >= imagesToGet:
        break
      # Make up URL 'https://www.autotrader.co.uk/search?postcode=XXXXXXX&make=AUDI&page=XXXX',    
      pageManyVehiclesrURL='{}/search?postcode={}&make={}&page={}'.format(url,postcode,urllib.parse.quote(searchBrand),page)
      logger.info('%s: Getting page %d at %s', searchBrand,page,pageManyVehiclesrURL)
      for retry in range(1,4): # {
        response = send_request(pageManyVehiclesrURL,1)

        if response.status_code != 200:
          logger.error("Request error for URL %s resulted error code: %d", pageManyVehiclesrURL, response.status_code)
          logger.debug(response.content)
          break # no more pages for brand
        else:

          # Process many vehicle page (mostly 10 to 13 per page)
          soup = bs(response.content,'html.parser')
          # Check for errors
          try:
            title=soup.find('title').text.replace(' ','')
            if 'denied' in title:
              logger.fatal('Access denied by web server. Exiting.')
              logger.debug(soup.prettify())
              exit(1)
            else:
              break
          except:
            if retry > 3:
              logger.fatal('Some other access denial from web server. Calling it a day,')
              logger.debug(soup.prettify())
              exit(1)
            else:
              logger.warning("Retry # %d %s",retry,pageManyVehiclesrURL)
      # } for

      # Check if redirected to previous page by comparing list of Car Ids
      # of this page to the previous one. If they are the same, it means 
      # that there are no more pages left for this brand          
      truckPrevIds = truckIds.copy() # save previous state
      truckIds.clear()

      # <h1 _ngcontent-serverapp-c19="" 
      #   class="stock-summary__title">
      #   <a _ngcontent-serverapp-c19="" 
      #     title="Heil Fuel tanker 41300lt" 
      #     href="/classified/advert/heil/fuel-tanker-41300lt/202103310800354?journey=FeaturedListing&amp;origin=search&amp;make=HEIL&amp;sort=Distance&amp;postcode=L1%208JQ">Heil Fuel tanker 41300lt
      #   </a>
      # </h1>

      heading1s = soup.find_all('h1',class_='stock-summary__title') # find all h1 headings
      logger.info('Found %d trucks on page %d', len(heading1s), page)
      vehicleCounter=0
      for heading1 in heading1s:
        vehicleCounter+=1
        anchor = heading1.find('a')  # find one and only anchor 'a'
        href = anchor.attrs["href"]

        # Get anchor's href link to get car details, find 15-digit using patternVanId pre-compiled regex
        match = re.search(patternVanId,href)
        try:
          truckDetailsId = match.group(1)            
        except:
          logger.warning("Advert panel. Skipping.")
          continue

        truckIds.append(truckDetailsId)
        file_path="{}/{}/{}.jpg".format(rootdir,searchBrand,truckDetailsId)                 
        if os.path.exists(file_path):
          logger.warning('File %s already exists. Skipping.', file_path)
        else:
          logger.info("Getting page %d van %d details truckId %s into %s", page,   vehicleCounter, truckDetailsId,file_path)
          # Make up van details URL 
          # https://trucks.autotrader.co.uk/classified/advert/cartwright/trailer/202104201576071 or
          # https://trucks.autotrader.co.uk/classified/advert/cartwright/trailer/202104201576071?journey=PremiumListing&origin=search&make=CARTWRIGHT&sort=Distance&postcode=SW1A%202AA
          truckDetailsURL=url+href
          # Fetch URL
          truckGalleryPageResponse=send_request(truckDetailsURL,1)
          soupGallery = bs(truckGalleryPageResponse.content,'html.parser')          

          #df = open(truckDetailsId+'.html','w')
          #df.write(soupGallery.prettify())
          #df.close()

          # Get first image only since it is likely to be a front-facing view:
          # <a _ngcontent-serverapp-c8="" class="gallery__main__image">
          #   <img _ngcontent-serverapp-c8="" src="https://m.atcdn.co.uk/a/media/w756h567/77263ebf48494500954958fef68e38b7.jpg"/>
          # </a>

          anchorTruck = soupGallery.find('a', class_='gallery__main__image')
          # Get src=..., something like <img src="https://m.atcdn.co.uk/a/media/w756h567/5905274d7f294250909a6c73d1611b75.jpg"...>
          try:
            imageTruck = anchorTruck.img
          except:
            logger.warning('Retrying with different class name #2 for %s', truckDetailsURL)
            divTruck = soupGallery.find('div', class_='fpa-gallery__placeholder  ') 
            try:
              imageTruck = divTruck.img
            except:
              logger.error('Giving up, could not find an img tag in the div. Skipping...')
              # totally give up. Fuck.
              continue

          urlTruckImage=imageTruck.attrs["src"]
          # Get image file and put in searchBrand directory
          logger.info('Getting image from %s',urlTruckImage)
          tic = time.perf_counter()
          try:
            with Watchdog(30): # 30 seconds timeout
              truckImageResponse=requests.get(urlTruckImage)
          except Watchdog:
            logger.timeout("Scraping image using Beautiful Soup timed out. Last try: %s",urlTruckImage)
            time.sleep(1)
            try:
              truckImageResponse=requests.get(urlTruckImage)
            except:
              logger.error("SSL Handshake error. Skipping.")
              continue
          except:
            try:
              logger.warning("SSL Handshake error. Retrying one more time")
              time.sleep(1)
              truckImageResponse=requests.get(urlTruckImage)
            except:
              logger.error("SSL Handshake error. Skipping.")
              continue
          
          logger.info('Writing file %s. Time to retrieve: %04f seconds',file_path, (time.perf_counter()-tic))
          f = open(file_path,'wb')
          f.write(truckImageResponse.content)
          f.close()
          imageCount = imageCount + 1
          if imageCount >= imagesToGet:
            break
        # } anchor

        truckIds.sort()
        truckPrevIds.sort()
        if truckIds == truckPrevIds:
          # A redirection happened.
          logger.warning("No more %s brand trucks available. Last page was %s.",searchBrand,pageManyVehiclesrURL)
          break # no more pages for brand
  # } for
  logger.info("All truck brands scraped.")
# } main          

if __name__ == "__main__":
  main()
