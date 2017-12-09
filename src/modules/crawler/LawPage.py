import requests
from lxml import html
import re
from tika import parser
import sys, os
import urllib.request
import shutil
import json
from constants import LAW_PAGE_CONSTANTS

#get the logger
sys.path.insert(0, os.path.abspath('../'))
import Logger
logger = Logger.getLogger("crawler")


def extract_description_from_file(file_full_path) :
    res = ""
    if re.fullmatch(".*\.docx", file_full_path):  # if is docx document
        try :
            parsed = parser.from_file(file_full_path)
            res = parsed["content"].split(LAW_PAGE_CONSTANTS.DOCX_START_DELIMITER)[1].split(LAW_PAGE_CONSTANTS.DOCX_END_DELIMITER)[0]
        except Exception as e :
            logger.error("failed to extract description from file {}".format(str(e)))
    #only suuports docx atm, pdf are not extracted nicely
    return res

def get_law_description_from_file(html_tree) :
    logger.debug("trying to get the law description from the docx")
    description = ""
    law_suggestions_documnets = html_tree.xpath("//td[contains(@class, 'LawDocHistoryLeftTd')]//a")
    for suggestion in law_suggestions_documnets:
        download_link = suggestion.attrib['href']
        # Download the file from `url` and save it locally under `tmp_file_path`:
        tmp_file_path = os.path.join(os.getcwd(), os.path.basename(download_link))
        try:
            logger.debug("downloading file {} to {}".format(download_link, tmp_file_path))
            with urllib.request.urlopen(download_link) as response, open(tmp_file_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            logger.error("failed to download file {},{}".format(suggestion.attrib['href'], str(e)))
            if (os.path.isfile(tmp_file_path)):
                os.remove(tmp_file_path)
            continue
        description = extract_description_from_file(tmp_file_path);
        if (os.path.isfile(tmp_file_path)):
            os.remove(tmp_file_path)
        if len(description) > 1:
            return description
    return description

def get_law_description_from_div(html_tree) :
    logger.debug("trying to get law description from the html itself")
    description = html_tree.xpath("//div[contains(@id, 'TakzirDiv')]/text()")[0]
    if (len(description)) > 80 : #div is not empty
        return description
    else :
        return ""

'''get the a law decription from the law page url, returnes an empty string upon failure
    does not throw exceptions'''
def get_law_description_from_url(url):
    res = requests.get(url)
    cookies = {}
    for c in res.cookies:
        #print(c.name, c.value)
        cookies[c.name] = c.value
    res = requests.get(url,cookies=cookies)
    #print (str(res.content,encoding='utf-8'))
    html_tree = html.fromstring(str(res.content,encoding='utf-8'))

    description = ""
    try :
        description = get_law_description_from_div(html_tree)
    except Exception as e :
        logger.error(str(e))

    if (description == "") :
        try:
            description = get_law_description_from_file(html_tree)
        except Exception as e:
            logger.error(str(e))

    return description


def get_law_page_url_from_json(vote_json) :
    title = vote_json["title"]
    #clean the title
    x=1

url  = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=564206"
url2 ="http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=LawReshumot&lawitemid=567248"
url3 = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=2015276"
#print (get_law_description_from_url(url3))



json_data=open("vote_json.json").read()
data = json.loads(json_data)
get_law_page_url_from_json(data['objects'][0])