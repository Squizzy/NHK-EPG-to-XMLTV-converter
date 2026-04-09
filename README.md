# NHK EPG to XMLTV converter

Thanks to the research of TheDreadPirate (and others) the application is running again as new NHK URI and format was identified.

## From

![NHK JSON](./assets/nhk_json.png)

## To

![NHK XMLTV](./assets/nhk_xmltv.png)
  
## The applications

- __`CreateNHKXMLTV.py`__

    Extracts NHK's EPG in JSON from its website  
    Converts it to an XMLTV file  
    Saves the XMLTV to a text file: `ConvertedNHK.xml`  
  
    python 3.x only, python 2.7 no longer maintained
  
- __`scrape_nhk_genres.py`__ 

    NHK genres scraping application identify the genres NHK defined.  
    Saves the genres to a text file: `genres.txt`  
    This can be copied and pasted over (but currently isn't) into `CreateNHKXMLTV.py`  
  
    A python 3.x only version is available

    NOTE: with the new NHK EPG, these genres do not seem to be used any more at the moment

## How to run the application which downloads and converts the EPG to XMLTV: `CreateNHKXMLTV`

### Python3

Currently hosted only in the __master__ branch of this github repository.  
Two files are needed: CreateNHKXMLTV.py and requirements.txt.

1. In a terminal, create a dedicated folder

    Open a console:

    > Windows, run Command Prompt (cmd.exe) or Powershell (powershell.exe)  
    > MacOS: run Terminal (Terminal.app)  
    > Linux: run Terminal (Terminal)

    Navigate to your preferred location then create the folder, e.g.:

    ```shell
    mkdir NHK-World-EPG-XMLTV-Extractor
    ```  

    ```shell
    cd NHK-World-EPG-XMLTV-Extractor
    ```

2. Download the required files from the repository

    - Either direct from here (place the files in the folder created earlier):
    > [CreateNHKXMLTV.py](https://github.com/Squizzy/NHK-World-XML-to-XMLTV/blob/master/Python/CreateNHKXMLTV.py)  
    > [requirements.txt](https://github.com/Squizzy/NHK-World-XML-to-XMLTV/blob/master/Python/requirements.txt)

    - or from the terminal:  

    ```shell
    curl -O https://github.com/Squizzy/NHK-World-XML-to-XMLTV/blob/master/Python/CreateNHKXMLTV.py
    ```

    ```shell
    curl -O https://github.com/Squizzy/NHK-World-XML-to-XMLTV/blob/master/Python/requirements.txt
    ```

3. Set up the environment:

    1. From the terminal in the folder created earlier, create a virtual environment in the folder (so all needed modules are isolated locally):

        ```shell
        python3 -m venv venv
        ```

    2. Load the environment:

        - For Windows:

        ```shell
        .\venv\Scripts\activate
        ```

        - For MacOS, Linux:

        ```shell
        source venv/bin/activate
        ```

    3. Load the required modules (Windows, MacOs, Linux):

        ```shell
        pip install -r requirements.txt
        ```

    This is now ready to run.

4. Launch

    ```shell
    python CreateNHKXMLTV.py
    ```

    New options added:
    -period (eg: 'python CreateNHKXMLTV.py -period 3' for 7-days EPG): 1: 1-, 2: 2-, 3: 7-, 4: 14- or 5: 28-days EPG
    -lang (eg: 'python CreateNHKXMLTV.py -lang en): select language of EPG (en and jp available)

5. The XMLTV is saved in the file `ConvertedNHK.xml`.

## How to run the application which recovers the genres NHK support

### NHK genres scraper: `scrape_nhk_genres.py`

Downloads the list of genres from the NHK World website (different URL from EPG)
attempts to extract genres as NHK defines them.
Saves the result into a text file, `genres.txt`.
The content of this text file can be copied and pasted into the create `CreateNHKXMLTV.py` file before it is run so the latest genres can be applied.

### Requirements

- Python 3.x.
- its modules dependencies are included in the requirements.txt file so no need to re-run it.

### Launch

```shell
python3 scrape_nhk_genres.py
```

Runs on Windows, MacOS, Linux.  

## Background info

NHK World is a Japanese television channel that broadcasts a wide range of programming, including news, sports, and entertainment.
This is information that was collected from different sources.

## Note

All other files in this repository have no value and are only here mostly for historical reason (until they are removed)

## Version history

### CreateNHKXMLTV.py

#### 20260609 - v2.0  
- Upgraded to use the new NHK EPG URI  
- Added command line arguments for options:  
  - EPG data now added one day at a time up to 28 days.  
  - Japanese or English EPG data is available

#### 20250715 - v1.5
- Error checking on NHK URL access added for feedback
- Progress feedback of application execution
- Changed to GPLv2 license

#### 20250715 - v1.4
- Merged refactored Python3 version of CreateNHKXMLTV.py into master branch.
- Corrected requirement.txt -> requirements.txt .

#### 20240502 - v1.3
- Version change to represent the refactored Python3 version of CreateNHKXMLTV.py in its devel branch.

#### 20240415 - v1.2
- Updated the URL for the NHK world EPG JSON as per external contributor fxbx recommendation
- Replaced deprecated utcfromtimestamp(), added timeOffsetVariable
- Cleaned up XML tree generation
- Added some new genres

#### 20190120 - v1.1
- Changed to pulling the file from URL
- Windows executable created using "auto-py-to-exe.exe .\CreateNHKXMLTV.py" (auto-pi-to-exe v2.5.1)\
  File to be found under "output" folder. Not virus checked.

#### 20190119 - v1.0.5
- Added second category (genre) for channels which have it

#### 20190119 - v1.0.4
- Corrected \<category\> (genre) to use all lowercase

#### 20190119 - v1.0.3
- Corrected \<Icon\> typo source xml

#### 20190119 - v1.0.2
- Added header, version, licence, and reference URL for later

#### 19 Jan 2019 - v1.0.1
- Some tidying up

#### 20190119 - v1.0
- First release as working version

### scrape_nhk_genres.py

#### 20250715 - v1.2
- Error checking on NHK URL access added for feedback
- Refactored for clarity
- Changed to GPLv2

#### 20250715 - v1.1
- Merged from development branch into master branch.

#### 20240921 - v1.0
- First release as a working version
