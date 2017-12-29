import requests
from lxml import html
import re
from tika import parser
import sys, os
import urllib.request
import shutil
import logging
import json
import dateparser
import time
from constants import LAW_PAGE_CONSTANTS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#get the logger
import Logger
logger=Logger.getLogger('crawler')

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
    logger.info("trying to get the law description from the docx")
    description = ""
    law_suggestions_documnets = html_tree.xpath("//td[contains(@class, 'LawDocHistoryLeftTd')]//a")
    for suggestion in law_suggestions_documnets:
        download_link = suggestion.attrib['href']
        if not "docx" in download_link :
            continue
        # Download the file from `url` and save it locally under `tmp_file_path`:
        tmp_file_path = os.path.join(os.getcwd(), os.path.basename(download_link))
        try:
            logger.info("downloading file {} to {}".format(download_link, tmp_file_path))
            with urllib.request.urlopen(download_link) as response, open(tmp_file_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            logger.error("failed to download file {},{}".format(suggestion.attrib['href'], str(e)))
            if (os.path.isfile(tmp_file_path)):
                os.remove(tmp_file_path)
            continue
        description = extract_description_from_file(tmp_file_path);
        if (os.path.isfile(tmp_file_path)):
            try :
                os.remove(tmp_file_path)
            except Exception as e :
                logger.error(str(e))
        if len(description) > 1:
            return description
    return description

def get_law_description_from_div(html_tree) :
    logger.info("trying to get law description from the html itself")
    description = html_tree.xpath("//div[contains(@id, 'TakzirDiv')]/text()")[0]
    if (len(description)) > 80 : #div is not empty
        return description
    else :
        return ""


def get_initiators_from_div(html_tree) :
    initiators = []
    possible_divs = html_tree.xpath("//td[contains(@class, 'LawSecondaryDetailsTd')]/div")
    for div in possible_divs :
        div_text = div.xpath(".//text()")[1]
        if LAW_PAGE_CONSTANTS.LAW_PAGE_INITIATORS in div_text :
            #found the right div
            td = div.xpath("../../td")[1]
            initiators = td.xpath("./text()")[0]
            return initiators.strip().split(",")
    return initiators


'''get the a law decription from the law page url, returnes an empty string upon failure
    does not throw exceptions'''
def fill_data_from_law_page_url(url,out_dict):
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

    #remove empty lines
    description = "\n".join([ll.rstrip() for ll in description.splitlines() if ll.strip()])
    out_dict["description"] = description

    try:
        initiators = get_initiators_from_div(html_tree)
        out_dict["initiators"] = initiators
    except Exception as e:
        logger.error("failed getting initiators from law page url {} ".format(str(e)))

    return


def parse_title_for_time(search_term) :
    # notice that python knows to look at the hebrew string from right to left.
    search_term = clean_string(search_term)
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

def parse_title_for_comparing_strings(search_term) :
    # notice that python somehow knows to look at the hebrew string from right to left.
    search_term = clean_string(search_term)
    start_index = search_term.find("-")
    if start_index > -1:  # remove the start if found
        search_term = search_term[start_index + 2: len(search_term)]
    return search_term

def clean_string(string):
    return " ".join(string.strip().split())

def remove_all_non_hebrew_chars(string):
    regex = re.compile('[^א-ת1-9]')
    return regex.sub('', string)

def are_date_equal(json_date,html_date) :
    j = dateparser.parse(json_date)
    h = dateparser.parse(html_date)
    if j==None or h==None :
        return False
    return (j.day == h.day and
            j.month == h.month and
            j.year == h.year)

def find_min_index_of_weird_num(possible_name):
    starters = ["(נ/","(פ/","(מ/","(כ/"]
    index = len(possible_name);
    for s in starters :
        if possible_name.find(s) > -1 :
            index = min(index,possible_name.find(s))
    return index;

def get_law_page_url_from_json(vote_json) :
    #build the search term
    search_term = vote_json["raw_title"]
    date = vote_json["date"]
    # search_term = vote_json["title"]
    # date = vote_json["time"]
    search_term = parse_title_for_time(search_term)
    #build the query url
    query_url = LAW_PAGE_CONSTANTS.LAW_PAGE_QUERY_URL.format(search_term)
    query_url = clean_string(query_url)
    res = requests.get(query_url)
    #print(str(res.content, encoding='utf-8'))
    html_tree = html.fromstring(str(res.content, encoding='utf-8'))
    tr_query_result = html_tree.xpath("//div[contains(@id, 'divLawBillsResults')]//tr[contains(@class,'rgRow')]")
    law_page_url = ""
    #first try looking according to date
    logger.info("for law {} looking according to time of last discussion".format(vote_json["raw_title"]))
    for tr in tr_query_result :
        possible_dates_td = tr.xpath(".//td[contains(@class, 'rgSorted')]")#here should only get one result, but just in case
        for td in possible_dates_td :
            possible_date = td.xpath("./text()")[0]
            if are_date_equal(date,possible_date) :
                law_page_url = tr.xpath(".//a")[0].attrib['href']
                break;
        if law_page_url != "" :
            break
    #if didnt find according to time, try comparing a larger part of the string
    if law_page_url == "" :
        logger.info("for law {} looking according string comparing".format(vote_json["raw_title"]))
        search_term = parse_title_for_comparing_strings(vote_json["raw_title"])
        search_term = remove_all_non_hebrew_chars(search_term)
        a_query_result = html_tree.xpath("//div[contains(@id, 'divLawBillsResults')]//tr[contains(@class,'rgRow')]//a")
        matched_a_list = []
        loss_matched_a_list = [] # type: list
        for a in a_query_result:
            possible_name = clean_string(a.xpath(".//text()")[0]).replace("'\\","")
            possible_name = possible_name[:find_min_index_of_weird_num(possible_name)]
            possible_name = remove_all_non_hebrew_chars(possible_name)
            if possible_name == search_term :
                matched_a_list.append(a)
            if possible_name in search_term or search_term in possible_name :
                loss_matched_a_list.append(a)
        if len(matched_a_list) == 0:
            logger.warning("for law {} looking according string comparing yield no results".format(vote_json["raw_title"]))
            if len(loss_matched_a_list)>0 :
                logger.warning("for law {} taking the newest result of the losser comparison".format(vote_json["raw_title"]))
                law_page_url =  loss_matched_a_list[0].attrib['href']
        elif len(matched_a_list)== 1 :
            law_page_url = matched_a_list[0].attrib['href']
        else :#len > 1
            logger.warning("for law {} looking according string comparing yielded {} results, taking the newset one".format(vote_json["raw_title"],len(matched_a_list)))
            law_page_url = matched_a_list[0].attrib['href']

    if law_page_url != "" :
        return LAW_PAGE_CONSTANTS.LAW_PAGE_URL.format(law_page_url)
    else :
        return law_page_url


'''main function, recieves json containing the title of the law and it's time
   returns a summary of the law, upon failure returns an empty string
   does not throw exceptions'''
def build_law_dict(in_vote_json):
    out_dict = {}
    out_dict["description"] = ""
    out_dict["url"] = ""
    out_dict["initiators"] = []
    logger.info("trying to get law page url from json")
    try :
        url = get_law_page_url_from_json(in_vote_json)
        if url == "" :
            raise Exception("got empty url")
    except Exception as e :
        logger.error("failed to get law page url {}".format(str(e)))
        return out_dict
    out_dict["url"] = url
    logger.info("law page url is {}".format(url))
    logger.info("trying to get law data from url")
    fill_data_from_law_page_url(url, out_dict)
    return out_dict
    #return



def test() :
    json_data = open("vote_json.json").read()
    data = json.loads(json_data)
    for i in range(len(data['objects'])):
        curr_json = data['objects'][i]
        s = time.time()
        dict = build_law_dict(curr_json)
        e = time.time()
        print("for title {} law description is : ".format(curr_json["title"]))
        print(str(dict["initiators"]) + " , " + dict["url"])
        print("took {} seconds to get this description".format(e - s))
        print ("#"*10+" END "+"#"*10+'\n')

#
# url  = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=564206"
# url2 ="http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=LawReshumot&lawitemid=567248"
# url3 = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawBill.aspx?t=lawsuggestionssearch&lawitemid=2015276"
#




# print(get_law_description_from_url(get_law_page_url_from_json([18])))

#test()
# d={}
# fill_data_from_law_page_url(url,d)
# x=1

#x= 'חוק גיל פרישה (הורה שילדו נפטר) (הוראת שעה), התשע"ח-2017 (פ/2203/20) (כ/654)'
# d={}
# d["raw_title"] = 'אישור החוק - הצעת חוק גיל פרישה (הורה שילדו נפטר) (הוראת שעה), התשע"ח-2017'
# d["date"] = "12/12/2017 14:39"
# law_dict = build_law_dict(d)
# t=1
# #

#

# outer = re.compile("(/(פ/))")
# m = outer.search(x)
# t = m.group(0)
#
# y = x.replace("(","z")
# print(y)
# print (re.findall("(?z)",y))
# #
# print (x[:min(x.find("(נ/"),x.find("(פ/"),x.find("(מ/"))]
# m=re.match("(\.\\))",x)
# print(m)
