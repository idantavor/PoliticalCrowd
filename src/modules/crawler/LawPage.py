import requests
from lxml import html
import re
from tika import parser
import sys, os
import urllib.request
import shutil
import json
import dateparser
import time
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


def parse_title(search_term) :
    # notice that python somehow knows to look at the hebrew string from right to left.
    start_index = search_term.find("-")
    if start_index > -1:  # remove the start if found
        search_term = search_term[start_index + 1: len(search_term)]

    comma_index = search_term.find(",")
    right_bracket_index = search_term.find("(")
    end_index = -1
    if comma_index > -1 and right_bracket_index > -1:
        end_index = min(right_bracket_index, comma_index)
    elif comma_index > -1 and right_bracket_index <= -1:
        end_index = comma_index
    elif comma_index <= -1 and right_bracket_index > -1:
        end_index = right_bracket_index
    else:
        end_index = -1
    if end_index > -1:  # remove the ending if found
        search_term = search_term[:end_index]
    return search_term

def are_date_equal(json_date,html_date) :
    j = dateparser.parse(json_date)
    h = dateparser.parse(html_date)
    if j==None or h==None :
        return False
    return (j.day == h.day and
            j.month == h.month and
            j.year == h.year)


def get_law_page_url_from_json(vote_json) :
    #build the search term
    search_term = vote_json["title"]
    date = vote_json["time"]
    search_term = parse_title(search_term)
    #build the query url
    query_url = LAW_PAGE_CONSTANTS.LAW_PAGE_QUERY_URL.format(search_term)
    res = requests.get(query_url)
    #print(str(res.content, encoding='utf-8'))
    html_tree = html.fromstring(str(res.content, encoding='utf-8'))
    tr_query_result = html_tree.xpath("//div[contains(@id, 'divLawBillsResults')]//tr[contains(@class,'rgRow')]")
    law_page_url = ""
    for tr in tr_query_result :
        possible_dates_td = tr.xpath(".//td[contains(@class, 'rgSorted')]")#here should only get one result, but just in case
        for td in possible_dates_td :
            possible_date = td.xpath("./text()")[0]
            if are_date_equal(date,possible_date) :
                law_page_url = tr.xpath(".//a")[0].attrib['href']
                break;
        if law_page_url != "" :
            break
    if law_page_url != "" :
        return LAW_PAGE_CONSTANTS.LAW_PAGE_URL.format(law_page_url)
    else :
        return law_page_url


'''main function, recieves json containing the title of the law and it's time
   returns a summary of the law, upon failure returns an empty string
   does not throw exceptions'''
def get_law_description(vote_json):
    res = ""
    logger.debug("trying to get law page url from json")
    try :
        url = get_law_page_url_from_json(vote_json)
        if url == "" :
            raise Exception("failed to get law page url")
    except Exception as e :
        logger.error(str(e))
        return res
    logger.debug("law page url is {}".format(url))
    logger.debug("trying to get law description from url")
    try:
        res = get_law_description_from_url(url)
        if res == "":
            raise Exception("failed to get law description from url")
    except Exception as e:
        logger.error(str(e))
        return res
    #remove empty lines
    res = "\n".join([ll.rstrip() for ll in res.splitlines() if ll.strip()])
    #return
    return res



def test() :
    json_data = open("vote_json.json").read()
    data = json.loads(json_data)
    for i in range(len(data['objects'])):
        curr_json = data['objects'][i]
        s = time.time()
        description = get_law_description(curr_json)
        e = time.time()
        print("for title {} law description is : ".format(curr_json["title"]))
        print(description)
        print("took {} seconds to get this description".format(e - s))
        print ("#"*10+" END "+"#"*10+'\n')


# url  = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=564206"
# url2 ="http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=LawReshumot&lawitemid=567248"
# url3 = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=2015276"
#




# print(get_law_description_from_url(get_law_page_url_from_json([18])))

test()