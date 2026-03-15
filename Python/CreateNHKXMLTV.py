""" Python application to convert NHK EPG in JSON into XMLTV standard"""
__author__ = "Squizzy"
__copyright__ = "Copyright 2019-now, Squizzy"
__credits__ = "The respective websites, and whoever took time to share information\
                 on how to use Python and modules"
__license__ = "GPLv2"
__version__ = "1.5" # Python-3 only
__maintainer__ = "Squizzy"

import json
from datetime import datetime, timezone
import xml.etree.ElementTree as xml
import requests # type: ignore
import sys
# from pprint import pprint
from icecream import ic
# from NHK_json_dataclasses import JSONProgramDetails


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
XMLTV_XML_FILE: str = 'ConvertedNHK.xml'

# Downloaded JSON file for tests, or created when DEBUG is on
DEBUG: bool = False
TEST_NHK_JSON: str = 'DownloadedJSON.json'

# Local time zone that will be used for the timestamps in the XMLTV file
# Currently set for UTC as for Continental European use
TIMEZONE: timezone = timezone.utc

# In case the time offset is incorrect in the XMLTV file, the value below 
# can be modified to adjust it: For example -0100 would change to -1 UTC
TIME_OFFSET: str = ' +0000'


# Genres from NHK network

# Genres values come from NHK network under "genre" to become "category" in xmltv
# values can be updated by running additional script: scrape_nhk_genres.py 
# which retrives them from NHK's website directly and saves the result into "genres.txt" 
# the content of which can replace the numbered lines below directly.
# Of note: 24 has been found in the past but might not exist any more.

# Genres are called "category" in XMLTV
# These should not change too often but can be updated
# by the output of the scrapping tool Scrape_nhk_Genres.py
GENRES: dict[int|None, str] = {
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
        JsonInURL (str): URL to download the NHK EPG JSON data.
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
        start_time = datetime.strptime(json_start_time, '%Y-%m-%dT%H:%M:%S%z')
        end_time = datetime.strptime(json_end_time, '%Y-%m-%dT%H:%M:%S%z')
        duration = int(abs((end_time - start_time).seconds / 60))
        
    except Exception as e:
        print(f"Error converting the json date and time ({start_time} or {end_time}) to calculate the duration. skipping.")
        
    return duration
    

def Add_xml_element(parent:xml.Element, tag:str, attributes:dict[str,str]|None = None, text:str|None = None) -> xml.Element:
    """ Add an XML element to a tree
    Args:
        parent (xml.Element): The parent node in the XML tree
        tag (str): The name of the XML tag to be added.
        attributes (dict, optional): Dictionary of attributes for the XML tag. Defaults to None.
        text (str, optional): The text content for the XML element. Defaults to None.
    Returns:
        xml.Element: the XML node created
    """
    element: xml.Element = xml.SubElement(parent, tag)
    if attributes:
        for key, value in attributes.items():
            element.set(key, value)
    if text:
        element.text = text
    return element


def Xml_beautify(elem:xml.Element, level:int=0) -> bool:
    """ indent: beautify the xml to be output, rather than having it stay on one line
        Origin: http://effbot.org/zone/element-lib.htm#prettyprint """
    i:str = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            Xml_beautify(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
    return True


# def generate_xmltv_xml.header() ->

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
    
    channel:xml.Element = Add_xml_element(parent=root, 
                                          tag='channel', 
                                          attributes={'id': 'nhk-world'})
    
    Add_xml_element(parent=channel,
                    tag='display-name',
                    attributes={'lang': 'en'},
                    text='NHK World')
    
    Add_xml_element(parent=channel, 
                    tag='icon',
                    attributes={'src': URL_OF_NHK_CHANNEL_ICON})
    
    Add_xml_element(parent=channel, 
                    tag='url', 
                    text=URL_OF_NHK_WORLD)

    return root


def generate_xmltv_xml_programme(root:xml.Element, programme_to_add:dict = {}) -> xml.Element:
    """ Generates a program for the programs list to add to the root of the XMLTV document 
    Args:
        root (xml.Element): the root to which to add the program
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
    programme:xml.Element = Add_xml_element(
                                parent=root, 
                                tag='programme', 
                                attributes={'start': json_to_xmltv_datetime(programme_to_add["startTime"]) + TIME_OFFSET,
                                            'stop' : json_to_xmltv_datetime(programme_to_add["endTime"]) + TIME_OFFSET,
                                            'channel':'nhk-world'})

    Add_xml_element(parent=programme, 
                    tag='title', 
                    attributes={'lang': 'en'}, 
                    text=programme_to_add["title"])
    
    Add_xml_element(parent=programme, 
                    tag='sub-title', 
                    attributes={'lang': 'en'}, 
                    text=programme_to_add["episodeTitle"])
    
    Add_xml_element(parent=programme, 
                    tag='desc', 
                    attributes={'lang': 'en'}, 
                    text=programme_to_add["description"])
    
    Add_xml_element(parent=programme, 
                    tag='episode-num',              
                    attributes={'system': 'onscreen'}, 
                    text=programme_to_add["epis odeId"][-3:])
    
    Add_xml_element(parent=programme, 
                    tag='icon', 
                    attributes={'src': programme_to_add["episodeThumbnailURL"],
                                # "width": "100",  # if needed 
                                # "height": "100"  # if needed
                                })

    Add_xml_element(parent=programme,
                    tag="length",
                    attributes={"units":"minutes"},
                    text=str(duration_in_mins(programme_to_add['endTime'], programme_to_add['startTime']))
                    )

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
    #     Add_xml_element(programme, 'category', attributes={'lang': 'en'}, text=category2)
 
    
    return root



def Generate_xmltv_xml(nhkimported: dict) -> xml.Element:
    """Generates the XMLTV XML tree from the NHK JSON EPG data

    Args:
        nhkimported (JSON): The NHK JSON data to be converted to XMLTV XML
        
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

    channel = Add_xml_element(root, 'channel', attributes={'id': 'nhk.world'})
    Add_xml_element(channel, 'display-name', text='NHK World')
    Add_xml_element(channel, 'icon', attributes={'src': URL_OF_NHK_CHANNEL_ICON})

    # Go through all items, though only interested in the Programmes information here
    for item in nhkimported["channel"]["item"]:

        # construct the program info xml tree
        programme: xml.Element = Add_xml_element(
                                    root, 
                                    'programme', 
                                    attributes={'start': Convert_unix_to_xmltv_date(item["pubDate"]) + TIME_OFFSET, 
                                                'stop': Convert_unix_to_xmltv_date(item["endDate"]) + TIME_OFFSET, 
                                                'channel':'nhk.world'})

        Add_xml_element(programme, 'title', attributes={'lang': 'en'}, text=item["title"])
        Add_xml_element(programme, 'sub-title', attributes={'lang': 'en'}, text=item["subtitle"] if item["subtitle"] else item["airingId"])
        Add_xml_element(programme, 'desc', attributes={'lang': 'en'}, text=item["description"])
        Add_xml_element(programme, 'episode-num', text=item["airingId"])
        Add_xml_element(programme, 'icon', attributes={'src': URL_OF_NHK_ROOT + item["thumbnail"]})

        genre: str = item["genre"]["TV"]
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

        Add_xml_element(programme, 'category', attributes={'lang': 'en'}, text=category1)
        
        if category2 != "":
            Add_xml_element(programme, 'category', attributes={'lang': 'en'}, text=category2)
        
    if not Xml_beautify(root):
        print("Problem beautifying the XML")
        sys.exit(1)
    
    print("NHK WORLD EPG data converted to XMLTV standard")
    
    return root


def Save_xmltv_xml_to_file(root: xml.Element) -> bool:
    """Store the XML tree to a file

    Args:
        root (_type_): The XMLTV XML tree to store to file
    """
    # Export the xml to a local file
    tree:xml.ElementTree = xml.ElementTree(root)
    with open(XMLTV_XML_FILE, 'w+b') as outFile:
        tree.write(outFile)
    
    print(f"{XMLTV_XML_FILE} created successfully")
    return True


def main() -> int:
    """Main application
    Returns:
        0: Successful execution
    """
    json_data: dict = Import_nhk_epg_json(URL_OF_NHK_JSON)
    
    if DEBUG:
        with open(TEST_NHK_JSON, 'w', encoding="utf-8") as jsonfile:
            json.dump(json_data, jsonfile)
            
        # load the json file from local storage
        with open(TEST_NHK_JSON, 'r', encoding='utf8') as nhkjson:
            json_data = json.load(nhkjson)    

    XmltvXml: xml.Element = Generate_xmltv_xml(json_data)
    
    Save_xmltv_xml_to_file(XmltvXml)
    
    return 0



if __name__ == "__main__":
    main()