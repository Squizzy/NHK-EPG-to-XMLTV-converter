""" Python application to convert NHK EPG in JSON into XMLTV standard"""
__author__ = "Squizzy"
__copyright__ = "Copyright 2019-now, Squizzy"
__credits__ = "The respective websites, and whoever took time to share information\
                 on how to use Python and modules"
__license__ = "GPLv2"
__version__ = "2.0" # Python-3 only
__maintainer__ = "Squizzy"
__contributors__ = ["TheDreadPirate"] # TheDreadPirate: https://github.com/solidsnake1298


import argparse
import json
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as xml  # from xml.etree import ElementTree
import requests
import sys
from pathlib import Path
# from pprint import pprint
from icecream import ic


# Will save the downloaded JSON info if enabled, as {DEBUG_FOLDER}/{TEST_NHK_JSON}_<epg_date>_<language>.json
DEBUG:bool = True
TEST_NHK_JSON:str = 'DownloadedJSON'
DEBUG_FOLDER:str = 'debug_samples'


XMLTV_SOURCE_INFO_NAME:str = "NHK-EPG-to-XMLTV-converter by Squizzy"
XMLTV_SOURCE_INFO_URL:str = "https://github.com/Squizzy/NHK-EPG-to-XMLTV-converter"

# Location of the NHK EPG JSON to be downloaded.
# This might need occastional updating
# OBSOLETE: URL_OF_NHK_JSON:str = "https://nwapi.nhk.jp/nhkworld/epg/v7b/world/all.json"
URL_OF_NHK_JSON:str = ""

# Location of the NHK EPG URL at which the JSON can be found
# the daily EPG is now at the location below, with the json named "%Y%m%d".json
# up to 28-days EPG appears to be provided, and back in time quite far
URL_OF_NHK_JSON_ROOT: str = "https://masterpl.hls.nhkworld.jp/epg"
URL_OF_NHK_JSON_ROOT_EN: str = f"{URL_OF_NHK_JSON_ROOT}/w"
URL_OF_NHK_JSON_ROOT_JP: str = f"{URL_OF_NHK_JSON_ROOT}/wp"

# Location of the NHK streams for use in the XMLTV
URL_OF_NHK_JAPAN:str = "https://www3.nhk.or.jp" # Japanese website
URL_OF_NHK_WORLD:str = f"{URL_OF_NHK_JAPAN}/nhkworld" # World website

# Location of the NHK channel icon
URL_OF_NHK_CHANNEL_ICON:str = f"{URL_OF_NHK_JAPAN}/nhkworld/assets/images/icon_nhkworld_tv.png"

# Name of the file that is created by this application 
# which contains the XMLTV XML of the NHK EPG
XMLTV_XML_FILE:str = 'ConvertedNHK.xml'

# Local time zone that will be used for the timestamps in the XMLTV file
# Currently set for UTC as for Continental European use
TIMEZONE:timezone = timezone.utc

# In case the time offset is incorrect in the XMLTV file, the value below 
# can be modified to adjust it: For example -0100 would change to -1 UTC
TIME_OFFSET:str = ' +0000'


# Genres from NHK network

# Genres values come from NHK network under "genre" to become "category" in xmltv
# values can be updated by running additional script: scrape_nhk_genres.py 
# which retrives them from NHK's website directly and saves the result into "genres.txt" 
# the content of which can replace the numbered lines below directly.
# Of note: 24 has been found in the past but might not exist any more.

# Genres are called "category" in XMLTV
# These should not change too often but can be updated
# by the output of the scrapping tool Scrape_nhk_Genres.py
GENRES:dict[int|None, str] = {
          None: "General",
          11: "News",
          12: "Current Affairs",
          13: "Debate",
          14: "Biz & Tech",
          15: "Documentary",
          16: "Interview",
          17: "Food",
          18: "Travel",
          19: "Art & Design",
          20: "Culture & Lifestyle",
          21: "Entertainment",
          22: "Pop Culture & Fashion",
          23: "Science & Nature",
          24: "Documentary",
          25: "Sports",
          26: "Drama",
          27: "Interactive",
          28: "Learn Japanese",
          29: "Disaster Preparedness",
          30: "Kids", #fxbx: last cat as of 7-20-2023
          31: "Anime Manga (31 - to be confirmed)"
}


# Import the .json from the URL
def import_nhk_epg_json(json_url:str = "") -> dict:
    """Downloads the NHK EPG JSON data from the specified URL and loads it into a variable.
    Args:
        json_url(str): URL to download the NHK EPG JSON data.
    Returns:
        (dict): the downloaded json parsed as a dict
    """
    if not json_url or json_url == "":
        raise ValueError("No URL provided for the EPG JSON. Aborting")
    
    response: requests.Response = requests.get(url = json_url)
    
    match response.status_code:
        case 200:
            try:
                data: dict = response.json()
            except requests.exceptions.JSONDecodeError:
                print("problem with the parsing of the JSON file downloaded from NHK")
                sys.exit(1)
            except Exception as e:
                print(f"problem recovering the JSON data from the website data: {e}")
    
        case 404:
            print(f"Network error {response.status_code}: \n \
                    The NHK file containing the EPG JSON does not exist at the URL provided.\n \
                    Aborting.")
            sys.exit(1)
        
        case 403:
            print(f"Network error {response.status_code}: \n \
                    The NHK EPG JSON file exists but NHK rejects the request.\n \
                    Try again later, aborting")
            sys.exit(1)
    
        case _:
            print(f"Network error {response.status_code}: \n \
                    Problem with the URL to the NHK JSON file provided.\n \
                    Aborting")
            sys.exit(1)
    
    print("NHK World EPG JSON file downloaded successfully")
    
    return data


def json_to_xmltv_datetime(json_datetime: str) -> str:
    """ Converts date/time from the NHK EPG JSON to XMLTV time format
    Args:
        json_datetime (str): the date/time provided as a string in the EPG JSON downloaded
    Returns:
        str: the date/time in XMLTV format.
    """
    try:
        json_datetime_details = datetime.strptime(json_datetime, '%Y-%m-%dT%H:%M:%S%z')
        xmltv_datetime=json_datetime_details.strftime('%Y%m%d%H%M%S')
        
    except Exception as e:
        print(f"Error converting the json date and time ({json_datetime}) to xmltv format. Aborting.")
        exit(1)
        
    return xmltv_datetime


def duration_in_mins(json_start_time:str, json_end_time:str) -> int:
    """ Calculate the duration of a programme, given the start and then time
    Args:
        json_start_time, json_end_time (str): start and end as provided by the NHK EPG JSON
    Returns:
        (int): the duration in minutes
    """
    duration:int = 0
    
    try:
        start_time = datetime.strptime(json_start_time, '%Y-%m-%dT%H:%M:%S%z').timestamp()
        end_time = datetime.strptime(json_end_time, '%Y-%m-%dT%H:%M:%S%z').timestamp()
        duration = abs(int((end_time - start_time)/60))
        
    except Exception as e:
        print(f"Error converting the json date and time ({start_time} or {end_time}) to calculate the duration. skipping.")
        
    return duration
    

def add_xml_element(parent:xml.Element, tag:str, attributes:dict[str,str]|None = None, text:str|None = None) -> xml.Element:
    """ Add an XML element to a tree
    Args:
        parent (xml.Element): The parent node in the XML tree
        tag (str): The name of the XML tag to be added.
        attributes (dict, optional): Dictionary of attributes for the XML tag. Defaults to None.
        text (str, optional): The text content for the XML element. Defaults to None.
    Returns:
        xml.Element: the XML node created
    """
    element:xml.Element = xml.SubElement(parent, tag)
    if attributes:
        for key, value in attributes.items():
            element.set(key, value)
    if text:
        element.text = text
    return element


def xml_beautify(elem:xml.Element, level:int=0) -> None:
    """ indent: beautify the xml to be output, rather than having it stay on one line
        Origin: http://effbot.org/zone/element-lib.htm#prettyprint """
    i:str = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            xml_beautify(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
    return True


def generate_xmltv_xml_root() -> xml.Element:
    """ Generates the root of the XMLTV document 
    Args:
        None
    Returns:
        (xml.Element): the root document
    """
    root:xml.Element = xml.Element(
                        'tv', 
                        attrib={
                            'source-data-url': URL_OF_NHK_JSON_ROOT_EN, 
                            'source-info-name': XMLTV_SOURCE_INFO_NAME, 
                            'source-info-url': XMLTV_SOURCE_INFO_URL,
                            })

    return root


def generate_xmltv_xml_channel(root:xml.Element) -> xml.Element:
    """ Generates a channel for the channels list to add to the root of the XMLTV document 
    Args:
        root (xml.Element): the root to which to add the channel
    Returns:
        (xml.Element): the root document with the added channel
    """
    if root is None:
        print("No root xml element provided to generate the xmltv. Aborting")
        exit(1)
    
    channel:xml.Element = add_xml_element(parent=root, 
                                          tag='channel', 
                                          attributes={'id': 'nhk-world'})
    
    add_xml_element(parent=channel,
                    tag='display-name',
                    attributes={'lang': 'en'},
                    text='NHK World')
    
    add_xml_element(parent=channel, 
                    tag='icon',
                    attributes={'src': URL_OF_NHK_CHANNEL_ICON})
    
    add_xml_element(parent=channel, 
                    tag='url', 
                    text=URL_OF_NHK_WORLD)

    return root


def generate_xmltv_xml_programme(root:xml.Element, programme_to_add:dict = {}, lang:str = 'en') -> xml.Element:
    """ Generates a program for the programs list to add to the root of the XMLTV document 
    Args:
        root (xml.Element): the root to which to add the program
        programme_to_add (dict): the XML of the individual program to add to the root
        lang (str): The language of the EPG (jp or en (default))
    Returns:
        (xml.Element): the root document with the added program
    """
    if root is None:
        print("No root xml element provided to add the program to. Aborting.")
        exit(1)
    
    if programme_to_add is {}:
        print("no program info to process and add to the xmltv. Skipping.")
        return root
    
    # construct the program info xml tree
    programme:xml.Element = add_xml_element(
                                parent=root, 
                                tag='programme', 
                                attributes={'start': json_to_xmltv_datetime(programme_to_add["startTime"]) + TIME_OFFSET,
                                            'stop' : json_to_xmltv_datetime(programme_to_add["endTime"]) + TIME_OFFSET,
                                            'channel':'nhk-world'})

    add_xml_element(parent=programme, 
                    tag='title', 
                    attributes={'lang': 'en'}, 
                    text=programme_to_add["title"])
    
    add_xml_element(parent=programme, 
                    tag='sub-title', 
                    attributes={'lang': 'en'}, 
                    text=programme_to_add["episodeTitle"])
    
    add_xml_element(parent=programme, 
                    tag='desc', 
                    attributes={'lang': 'en'}, 
                    text=programme_to_add["description"])
    
    add_xml_element(parent=programme, 
                    tag='episode-num',              
                    attributes={'system': 'onscreen'}, 
                    text=programme_to_add["episodeId"][-3:])
    
    add_xml_element(parent=programme, 
                    tag='icon', 
                    attributes={'src': programme_to_add["episodeThumbnailURL"],
                                # "width": "100",  # if needed 
                                # "height": "100"  # if needed
                                })

    add_xml_element(parent=programme,
                    tag="length",
                    attributes={"units":"minutes"},
                    text=str(duration_in_mins(programme_to_add['endTime'], programme_to_add['startTime']))
                    )

    # Below left in case NHK EPG genres become available again

    # Genre description has changed, hiding until more info available to use the categories again
    # genre: str = programme_to_add["genre"]["TV"]
    # category1: str = ""
    # category2: str = ""
    # if genre == "":
    #     category1 = GENRES[None]
    # elif isinstance(genre, str):
    #     category1 = GENRES[int(genre)].lower()
    # elif isinstance(genre, list):
    #     category1 = GENRES[int(genre[0])].lower()
    #     category2 = GENRES[int(genre[1])].lower()
    # else:
    #     category1 = GENRES[None]

    # Add_xml_element(programme, 'category', attributes={'lang': 'en'}, text=category1)
    
    # if category2 != "":
    #     Add_xml_element(programme, 'category', attributes={'lang': lang}, text=category2)
  
    return root


def Generate_xmltv_xml(nhkimported: dict) -> xml.Element:
    """ SUPERSEDED
    Generates the XMLTV XML tree from the NHK JSON EPG data
    Args:
        nhkimported (dict): The NHK JSON data to be converted to XMLTV XML
    Returns:
        root (xml.tree): the XML tree created
    """
    # Start filling in the table XML tree with content that is useless and might not change
    root: xml.Element = xml.Element(
                            'tv', 
                            attrib={
                                'source-data-url': URL_OF_NHK_JSON, 
                                'source-info-name': 'NHK World EPG Json', 
                                'source-info-url': 'https://www3.nhk.or.jp/nhkworld/'})

    channel = add_xml_element(root, 'channel', attributes={'id': 'nhk.world'})
    add_xml_element(channel, 'display-name', text='NHK World')
    add_xml_element(channel, 'icon', attributes={'src': URL_OF_NHK_CHANNEL_ICON})

    # Go through all items, though only interested in the Programmes information here
    for programme_to_add in nhkimported["channel"]["programme_to_add"]:

        # construct the program info xml tree
        programme: xml.Element = add_xml_element(
                                    root, 
                                    'programme', 
                                    attributes={'start': json_to_xmltv_datetime(programme_to_add["pubDate"]) + TIME_OFFSET, 
                                                'stop': json_to_xmltv_datetime(programme_to_add["endDate"]) + TIME_OFFSET, 
                                                'channel':'nhk.world'})

        add_xml_element(programme, 'title', attributes={'lang': 'en'}, text=programme_to_add["title"])
        add_xml_element(programme, 'sub-title', attributes={'lang': 'en'}, text=programme_to_add["subtitle"] if programme_to_add["subtitle"] else programme_to_add["airingId"])
        add_xml_element(programme, 'desc', attributes={'lang': 'en'}, text=programme_to_add["description"])
        add_xml_element(programme, 'episode-num', text=programme_to_add["airingId"])
        add_xml_element(programme, 'icon', attributes={'src': URL_OF_NHK_JAPAN + programme_to_add["thumbnail"]})

        genre: str = programme_to_add["genre"]["TV"]
        category1: str = ""
        category2: str = ""
        if genre == "":
            category1 = GENRES[None]
        elif isinstance(genre, str):
            category1 = GENRES[int(genre)].lower()
        elif isinstance(genre, list):
            category1 = GENRES[int(genre[0])].lower()
            category2 = GENRES[int(genre[1])].lower()
        else:
            category1 = GENRES[None]

        add_xml_element(programme, 'category', attributes={'lang': 'en'}, text=category1)
        
        if category2 != "":
            add_xml_element(programme, 'category', attributes={'lang': 'en'}, text=category2)
    
    if not Xml_beautify(root):
        print("Problem beautifying the XML")
        sys.exit(1)
    
    print("NHK WORLD EPG data converted to XMLTV standard")
    
    return root


def save_xmltv_xml_to_file(root: xml.Element) -> bool:
    """Store the XML tree to a file
    Args:
        root (xml.Element): The XMLTV XML tree to store to file
    Returns:
        (bool): True if the XMLTV file has been created and populated.
    """
    # Export the xml to a local file
    tree:xml.ElementTree = xml.ElementTree(root)
    
    try:
        with open(XMLTV_XML_FILE, 'w+b') as outFile:
            tree.write(outFile)
    
        print(f"{XMLTV_XML_FILE} created successfully")
        return True
    
    except IOError as e:
        print(f"Error writing XMLTV file {XMLTV_XML_FILE}: {e}")
        return False


def get_number_of_days(duration_selection:int|None = None) -> int:
    """ Determines the number of days of EPG (from today) for the xmltv file 
    Args:
        duration_selection (int|None): the duration passed as an arg in command line, if any
    Returns:
        (int): the selected number of days
    """
    number_of_days_options:dict[int, int] = {0: 0, 1: 1, 2: 2, 3: 7, 4: 14, 5: 28}
    
    choice:int = -1
    
    # If a choice has been used as an argument when calling the app, use it 
    if duration_selection:
        choice = duration_selection
    
    # Loop until an allowable choice has been made
    while choice not in number_of_days_options.keys():
        try:
            choice = int(input("Select: 1 [one day (today)],  2 [two days], 3 [one week], 4 [two weeks], 5 [4 weeks], 0 [exit]: "))
        except ValueError as e:
            pass
    
    return number_of_days_options[choice]


def main(duration_selection:int|None = None, lang:str = 'en') -> int:
    """Main application
    Args:
        duration_selection (int|None): the duration passed as an arg in command line, if any
        lang (str): the language of the EPG to download ('en' or 'jp) passed as an arg in command line, if any, else 'en'
    Returns:
        (int): 0 (Successful generation of the XMLTV file) or 1 (failure)
    """
    nhk_xmltv:xml.Element 
    
    # should never happen, but safety first...
    if lang not in ['en', 'jp']:
        print("incorrect language selected, defaulting to english")
        lang='en'

    # get the number of days, either from the command line argument or from interactive request
    number_of_days:int = get_number_of_days(duration_selection=duration_selection)

    # should never happen, but safety first...
    if number_of_days not in [0, 1, 2, 7, 14, 28]:
        print("incorrect number of days provided, defaulting to 1")
        number_of_days = 1
        
    if number_of_days == 0:
        print("Exit selected")
        exit(0)
        
    # Generate the root
    nhk_xmltv = generate_xmltv_xml_root()
    
    # Generate and add the channel description to the root
    nhk_xmltv = generate_xmltv_xml_channel(nhk_xmltv)  
    
    # Generate and add the programmes for the select days to the root
    for day in range(number_of_days):
        # format the date
        epg_date = datetime.strftime(datetime.now(tz=TIMEZONE) + timedelta(days=day), "%Y%m%d")
        
        # Select the URI depending on the date and language
        if lang=='jp':
            print("japanese version")
            URL_OF_NHK_JSON:str = f"{URL_OF_NHK_JSON_ROOT_JP}/{epg_date}.json"
        else:
            print("english version")
            URL_OF_NHK_JSON:str = f"{URL_OF_NHK_JSON_ROOT_EN}/{epg_date}.json"
        print(URL_OF_NHK_JSON)
        
        # Download the EPG JSON for the day, and extract the list of programmes
        epg_date_json_data_list = import_nhk_epg_json(URL_OF_NHK_JSON)["data"]
        
        # Save the file if debugging
        if DEBUG:
            Path(f'./{DEBUG_FOLDER}').mkdir(parents=True, exist_ok=True)
            with open(f'{DEBUG_FOLDER}/{TEST_NHK_JSON}_{epg_date}_{lang}.json', 'w', encoding="utf-8") as jsonfile:
                json.dump(epg_date_json_data_list, jsonfile)
            
            # load the json file from local storage
            with open(f'{DEBUG_FOLDER}/{TEST_NHK_JSON}_{epg_date}_{lang}.json', 'r', encoding='utf8') as nhkjson:
                epg_date_json_data_list = json.load(nhkjson)
        
        
        # Generate the XMLTV programmes list for this day
        count = 0
        for programme in epg_date_json_data_list:
            nhk_xmltv = generate_xmltv_xml_programme(root=nhk_xmltv, programme_to_add=programme, lang=lang)
            count += 1
        print(f"{epg_date}: {count} / {len(epg_date_json_data_list)} programmes added.")
    
    # Prepare a beautified version of the XMLTV (aesthetics only)
    xml_beautify(nhk_xmltv)

    # Attempt to save the XMLTV file to disk
    if not save_xmltv_xml_to_file(nhk_xmltv):
        print("Creation of the XMLTV file failed at saving the file")
        return 1
    
    return 0


if __name__ == "__main__":

    usage:str = 'python CreateNHKXMLTV.py [-help] [-period <period>] [-lang <language>] [-debug <debug_status>]\n' + \
                '\t<period>       (optional): Number of days to generate the NHKTV EPG for, starting today. Interactively asked if not provided.\n' + \
                '\t<lang>         (optional): language of the EPG to download. only Japanese and English available. Defaults to English.\n' + \
                '\t<debug_status> (optional): enables debug'

    help_days:str = '1: one day (today), 2: two days, 3: one week, 4: two weeks, 5: 4 weeks. \n'
    
    help_lang:str = 'en: English (default), jp: Japanese'
    
    help_debug:str = 'True: debug enabled (default), False: debug not enabled'

    parser = argparse.ArgumentParser(
                            prog='CreateNHKXMLTV',
                            description="generate XMLTV EPG from NHK's EPG JSON", 
                            usage=usage, 
                            add_help=True)
    parser.add_argument('-period', required=False, type=int,  help=help_days,                choices=[1, 2, 3, 4, 5])
    parser.add_argument('-lang',   required=False, type=str,  help=help_lang,  default='en', choices=['en', 'jp'])
    parser.add_argument('-debug',  required=False, type=bool, help=help_debug, default=False)

    args = parser.parse_args()

    if args.debug:
        DEBUG = args.debug
        
    main(duration_selection=args.period, lang=args.lang)
