# Vehicle Brand Dataset Scraping

This app scrapes car images from Autotrader website in order to create a dataset of car brands for Machine Learning (ML). 
Autotrader is one of those websites that the owners would prefer are on scraped in bulk, since their commercial advantage with this 
website could be usurped. They have therefore made is very difficult to scrape, but it can be done without anyone at Autotrader noticing, 
by using some clever magic that comes at a monetary cost: This app uses the best scraper service API currently available, Scraping Bee. 

For now, the app only scrapes the UK-based website in order to build a UK'based dataset of car brands

## What would we use this dataset for?

Firstly, crime prevention and detection. Following on, much more else too, like finer traffic control management.

With a compehensive set of images of car brands, it should be possible to "teach" a machine-learning application 
to recognise car brands in real time from live video and camera observations. This gives an added attribute to
an vehicle of interest's registration / license plate, or at least provide backup information where
the licenses plate could not be read.

The better quality the learning data is (i.e. the less extraneous information is included), the faster, smaller and more
efficient the resulting image analysis will be. This means that image processing can possibly be done directly on the 
embedded camera hardware using Edge-AI and Tiny-ML techhniques. One advantage of doing the analysis locally at the camera is that 
the omage processing results can be transmitted much faster and in real time, over very low bandwith and over great distances, 
than the actual image itself. Typically, the LoRa transmission protocol is used for transmitting the essential data in real-time, 
and the images themselves can be manually collected over WiFi during routine drive-by data collection. 

![Overview](.images/HighLevelOverview.png)

# Scrape your own Dataset

You can either download the published dataset from https://www.kaggle.com/bignosethethird/uk-car-brands-dataset
or build your own dataset, or use this code as an example of how to scrape a website that _really_, _really_ does not want to be scraped.

## Get your own cool API key!

If you want to enhance the dataset further or create datasets for other countries in which Autotrader operates, 
you can make a few configuration changes in the ScrapeUKCarsDataset.py Python script. 

You will also need your own API key, at $29 per month. Sign up through this link and get your own API key <sup id="a1">[1](#f1)</sup>:


https://www.scrapingbee.com?fpr=nobnose-inc27

## Getting a healthy data set for Machine Learning

We ideally want about 100 images per brand for a healthy dataset for the Machine Learning. 
A rule of thumb is that 100 images should be sufficient to teach an ML instance about each category. 
You can top up images until you have this amount by re-running this app after every curation
exercise. Also run this app every few weeks to top up the image counts for those more obscure 
brands for which you have not yet managed to get 100 good images so far. 
Expect to loose 25% of the new images per curation exercise, so it is a good idea to set the
number of images per brand to 150 the first time that you run it:

```
imagesPerBrand=150
```

## Running the scraper

Update your API key in the first line of the script and set your current working directory to a partition with lost of space available. 

If you want to add to the existing set, unpack the set there. You can get the latest, curated publication of the dataset here on kaggle.com:

https://www.kaggle.com/bignosethethird/uk-car-brands-dataset

Then run the script to augment the dataset.

```
./ScrapeUKCarsDataset.py
```

A log file will be created, called ScrapeUKCarsDataset.log when ScrapeUKCarsDataset.py is run. You can view the logfile:

```
tail -f ScrapeUKCarsDataset.log
```

Or better still, use the ```logwatch``` utiliy that is also in this git repo for groovy colourful text output.

```
logwatch.sh ScrapeUKCarsDataset.log
```

## Curation Round 1

The first curation step is to remove all duplicate images. These are caused by advertisers using 
generic stock images or simply their logo. There is unlikely going to be be any useful,so just 
summarily remove them first of all with the command

```
fdupe -rd UKCarsDataset
```

This app selects only the main image per advertised car, which is usually a front-on view with a
slight side angle, like in a fashion shoot. This is exactly what we want, since the 
observation camera will mpstly be placed facing oncoming traffic on the side of the road.

## Curation Round 2

The second curation step is to visually inspect all your new files and remove those that are
not useful for ML, like a side view, interiour view, obvious dealership signage, a girly model
draped across the car's hood, big for-sale text and price in front window, etc., 
If you remove these images, you can rerun the scraping process a few weeks later
when the offending vehicles have been removed from the website.

## Curation Round 3

Finally, all the registration number plates need to be blanked out from the images. 
This is still work in progress and is not perfect. Use the utility BlankRegPlate that is also 
in this repo:

```
find UKCarsDataset -type f -name "*.jpg" -exec BlankRegPlate {} \;
```

Images where the number plate blanking failed will be notified and you may need to manually remove them using a GIMP or Photoshop, or just remove them and just go scrape some more images.

---
<sup><b id="f1">1</b> Excuse the underhand attempt to score a little affiliation fee. This project stagnated in 2013 and needs some urgent funding!(#a1)</sup>

---
 Some pictures to drool over from the more select brands:
 
 
 ![AstonMartin](.images/AstonMartin.png)
 
 ![Ferrari](.images/Ferrari.png)
 
 ![Lamborghini](.images/Lamborghini.png)
 
 ![Lotus](.images/Lotus.png)
 
 ![McLaren](.images/McLaren.png)
 
 ![Rolls Royce](.images/RollsRoyce.png)

 
 

