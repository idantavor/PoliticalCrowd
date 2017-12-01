import tika
import requests
from lxml import html
import re
from tika import parser
import sys, os
import urllib.request
import shutil

sys.path.insert(0, os.path.abspath('../'))
import Logger
logger = Logger.getLogger("crawler")

tika.initVM()




def get_law_description_from_docx(file_full_path) :
    ##get the summary text from the docx file
    res = ""
    try :
        parsed = parser.from_file(file_full_path)
        split = parsed["content"].split("???? ????")
        res = parsed["content"].split("???? ????")[1].split("------------------------")[0]
    except Exception as e :
        logger.error("failed to extract description from file {}".format(str(e)))
    return res

def get_law_description_from_url(url):
    description = ""
    res = requests.get(url)
    cookies = {}
    for c in res.cookies:
        print(c.name, c.value)
        cookies[c.name] = c.value
    # cookies["Path"] = "/;"
    # cookies["Domain"] = ".knesset.gov.il"
    res = requests.get(url,cookies=cookies)
    print (str(res.content,encoding='utf-8'))
    html_tree = html.fromstring(str(res.content,encoding='utf-8'))
    law_suggestions_documnets = html_tree.xpath("//td[contains(@class, 'LawDocHistoryLeftTd')]//a")
    for suggestion in reversed(law_suggestions_documnets) :#go from end to start probably from new to old
        download_link = suggestion.attrib['href']
        print (download_link)
        if re.fullmatch(".*\.docx",download_link) : #if is docx document
            # Download the file from `url` and save it locally under `tmp_file_path`:
            tmp_file_path = os.path.join(os.getcwd(), os.path.basename(download_link))
            try :
                with urllib.request.urlopen(suggestion.attrib['href']) as response, open(tmp_file_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
            except Exception as e:
                logger.error("failed to download file {},{}".format(suggestion.attrib['href'],str(e)))
            description = get_law_description_from_docx(tmp_file_path);
            if (os.path.isfile(tmp_file_path)) :
                os.remove(tmp_file_path)
            if len(description) > 1 :
                return description



url = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=564206"
print(get_law_description_from_url(url))




