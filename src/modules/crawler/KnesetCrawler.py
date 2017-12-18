import datetime
import time
import requests
from lxml import html
from constants import URLS, API,UTILS,VOTE_TYPE_IMAGE_LABELS
from dbconnector import *
from py2neo import Graph
import LawPage
import json

graph = bolt_connect()  # type: Graph


def auto_retry(num_of_retries):
    # auto retry decorator for functions that needs retries
    def decorator(f):
        def wrapper(*args,**kwargs):
            max_retries=num_of_retries
            retry=1
            while True:
                print("retry number {}".format(retry))
                try:
                    res=f(*args,**kwargs)
                    return res
                except Exception as e:
                    retry+=1
                    if retry>max_retries:
                        raise e
                    else:
                        continue
        return wrapper
    return decorator


def execute_api_call(url, max_retries=3):
    retries = 0
    while retries < max_retries:
        retries+=1
        print("requesting {} - retry {}".format(url,retries))
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
    raise Exception("failed to get response for {} after {} retries".format(url,max_retries))


def add_party(party_dict):
    p = Party.createPartyFromJson(party_dict)
    graph.push(p)
    return p


def add_elected_officials():
    member_json = execute_api_call(API.MEMBER)
    for member in member_json['objects']:
        if not member["is_current"]:
            continue
        resource_url = "{}/{}".format(API.BASE, member["resource_uri"])
        extended_member = execute_api_call(resource_url)
        party = Party.select(graph, primary_value=extended_member['party_name']).first()
        m = ElectedOfficial.createElectedOfficialFromJson(extended_member, party)
        graph.push(m)


def delete_db():
    selection = ''
    while selection not in ['y', 'n', 'Y', 'N']:
        selection = input("are you sure you want to delete the db ? [y/n]\n")
    if selection in ['Y', 'y']:
        graph = bolt_connect()
        graph.begin(autocommit=True)
        graph.delete_all()


def update_laws(date:datetime.datetime):
    url=API.query_call(API.VOTE,limit=100)
    res=execute_api_call(url)
    for vote in res['objects']:
        print(vote['time'])

def get_party_and_role_from_role_title(role_title):
    res=role_title.split(',')
    party=res[0]
    role_suffix=','.join(res[1:])
    role=None if  role_suffix=="" else role_suffix
    return party,role

def get_member_dict(member_page_url,image_link,member_name):
    print("getting url for member {}".format(member_name))
    html_tree = html.fromstring(UTILS.get_url(member_page_url,encoding='utf8'))
    title=html_tree.xpath('//div[@class="MKRoleDiv"]//h3/text()')[0]
    party,role=get_party_and_role_from_role_title(title)
    return {"name":member_name,"title":role,"img_url":image_link,"party":party,"homepage_url":member_page_url,"is_active":True}

def get_non_voting_officials_dict_list()->list:
    res=[]
    html_tree = html.fromstring(UTILS.get_url(URLS.MEMBERS_URL))
    elem_ministers = html_tree.xpath('//table[@id="dlMinister"]//td[.//@class="PhotoAsistno"]')
    for elem_minister in elem_ministers:
        image_url="{}{}".format(URLS.BASE_URL,elem_minister.xpath('./img/@src')[0])
        name = elem_minister.xpath('./a/text()')[0]
        res.append({"name":name,"img_url":image_url,"is_active":False,})
    return res

def get_party_to_member_dict()->dict:
    res_dict={}
    html_tree = html.fromstring(UTILS.get_url(URLS.MEMBERS_URL))
    elem_members=html_tree.xpath('//table[@id="dlMkMembers"]//td[.//@class="PhotoAsistno" or .//@class="PhotoAsist"]')
    print("number of members collected {}".format(len(elem_members)))
    for elem_member in elem_members:
        image_url="{}{}".format(URLS.BASE_URL,elem_member.xpath('./img/@src')[0])
        name=elem_member.xpath('./a/text()')[0]
        mk_id=elem_member.xpath('./a/@href')[0].split('=')[1]
        member_page_url="{}{}".format(URLS.MEMBER_PAGE_BASE_URL,mk_id)
        member_dict=get_member_dict(member_page_url,image_url,name)
        member_party=member_dict['party']
        if member_party in res_dict:
            res_dict[member_party].append(member_dict)
        else:
            res_dict[member_party]=[member_dict]

    return res_dict

def add_parties_and_members_to_db():
    party_to_members_dict=get_party_to_member_dict()
    for party,members_list in party_to_members_dict.items():
        p = Party.createPartyFromJson({'number_of_seats':len(members_list),'name':party})
        graph.push(p)
        for member_dict in members_list:
            m=ElectedOfficial.createElectedOfficialFromJson(member_dict, p)
            graph.push(m)
    non_memebers_dict_list=get_non_voting_officials_dict_list()
    p = Party.createPartyFromJson({'number_of_seats': len(non_memebers_dict_list), 'name': 'אינם חברי כנסת'})
    graph.push(p)
    for member_dict in non_memebers_dict_list:
        m = ElectedOfficial.createElectedOfficialFromJson(member_dict, p)
        graph.push(m)

def get_votes(date_from="1/1/2003",date_to=None,retries=10):
    result_votes=[]
    datetime_from=datetime.datetime.strptime(date_from, "%d/%m/%Y")
    datetime_to =datetime.date.today() if date_to is None else datetime.datetime.strptime(date_from, "%d/%m/%Y")
    post_data={ "mk_individual_desc":"",
                "faction_desc":"",
                "New_Q":"1",
                "ckDates":"D",
                "sWord":"",
                "sSubject":"",
                "mk_individul_id_t":"",
                "faction_id_t":"",
                "dtFmYY":datetime_from.year,
                "dtFmMM":datetime_from.month,
                "dtFmDD":datetime_from.day,
                "dtToYY":datetime_to.year,
                "dtToMM":datetime_to.month,
                "dtToDD":datetime_to.day}
    more_results_data={
        "mk_individul_id_t":"",
        "ckMkIndiv":"",
        "RStart": ''
    }
    res=requests.post(URLS.VOTES_SEARCH_URL,post_data)
    if res.status_code != requests.codes.ok:
        raise Exception("failed to get response for {}".format(URLS.VOTES_SEARCH_URL))
    cookies=res.cookies
    res=requests.post(URLS.VOTES_SEARCH_URL,post_data,cookies=cookies)
    cookies.update(res.cookies)
    if res.status_code != requests.codes.ok:
        raise Exception("failed to get response for {}".format(URLS.VOTES_SEARCH_URL))
    html_tree = html.fromstring(str(res.content, encoding='windows-1255', errors='ignore'))
    while True:
        #print(str(res.content,encoding='windows-1255', errors='ignore'))
        result_meta_data_str = html_tree.xpath('//td[@class="DataText3"]/text()')[1]
        total_results = int(result_meta_data_str.split()[0].strip())
        next_cnt = int(result_meta_data_str.split()[-1].strip())
        elem_votes=html_tree.xpath('//tr[./td/a[@class="DataText6"]]')
        for elem_vote in elem_votes:
            vote_dict={
            "raw_title":elem_vote.xpath('.//a/text()')[0],
            "type":elem_vote.xpath('.//a/text()')[0].split("-")[0].strip(),
            "url":elem_vote.xpath('.//a/@href')[0],
            "date":elem_vote.xpath('./td[4]/text()')[0].strip(),
            "vote_num":elem_vote.xpath('./td[3]/text()')[0].strip(),
            "meeting_num" : elem_vote.xpath('./td[2]/text()')[0].strip()
            }
            result_votes+=[vote_dict]
        if next_cnt < total_results:
            #retry machanism is a must here since the knesset site is shit
            retry=1
            more_results_data["RStart"]=str(next_cnt)
            while retry<retries:
                print(retry)
                res=requests.post(URLS.VOTES_SEARCH_URL,more_results_data,cookies=cookies)
                content_string = str(res.content, encoding='windows-1255', errors='ignore')
                if "תקלה בהעברת המשתנים" in content_string:
                    retry+=1
                    continue
                else:
                    break
            cookies.update(res.cookies)
            html_tree = html.fromstring(content_string)
            continue
        else:
            break
    return result_votes

def add_votes_to_db(date_from='1/8/2003'):
   vote_list=get_votes(date_from=date_from)
   for vote in vote_list:
       #check if the vote is already in the db
       res=Vote.select(graph,primary_value=vote['raw_title']).first()
       print(res)
       if res is not None:
           continue
       else:
           law_name = LawPage.parse_title(vote['raw_title'])
           #check if the law is already in the db
           print(law_name)
           try:
               law_obj=Law.select(graph,primary_value=law_name).first()
               if law_obj is None:
                   print("failed to find law for {}".format(law_name))
                   #create new law object to conatin the vote
                   law_dict=LawPage.build_law_dict(vote)
                   url=law_dict['url']
                   description=law_dict['description']
                   initiators=law_dict['initiators'] # type: list
                   law_obj=Law.createLaw(law_name,None,None,description,url) # type: Law
                   for initiator in initiators:
                       initiator_member=ElectedOfficial.select(graph,initiator).first()
                       law_obj.proposed_by.add(initiator_member)
               voting_details=get_vote_detail_dict("{}/{}".format(URLS.VOTES_BASE_URL,vote['url']))
               vote_obj=Vote.createVoteFromJson(vote,law_obj,voting_details,graph)
               graph.push(law_obj)
               graph.push(vote_obj)
           except Exception as e:
               print(e)

def get_vote_detail_dict(vote_url):
    res_dict={}
    html_tree = html.fromstring(UTILS.get_url(vote_url))
    for vote_type,vote_image_label in VOTE_TYPE_IMAGE_LABELS.items():
        elem_vote_table=html_tree.xpath('//table[./tr/td/img[@src="{}"]]'.format(vote_image_label))

        if len(elem_vote_table)==0:
            res_dict[vote_type]=[]
            res_dict["{}_cnt".format(vote_type)] = 0
        else:
            voting_members=elem_vote_table[0].xpath('.//a/text()')
            res_dict["{}_cnt".format(vote_type)] = len(voting_members)
            res_dict[vote_type]=[" ".join(member.split()) for member in voting_members]
    return res_dict

def get_law_list_by_min_date(date):
    min_date_threshold_exceeded = False
    min_date = datetime.datetime.strptime(date, "%d/%m/%Y")
    page_cnt = 0
    while (not min_date_threshold_exceeded):
        page_cnt += 1
        res = requests.get(URLS.LAW_OFFERS_BASE_URL, params={"pn": page_cnt})
        if res.status_code != requests.codes.ok:
            raise Exception("failed to get response for {}".format(URLS.LAW_OFFERS_BASE_URL))
        html_tree = html.fromstring(str(res.content, encoding='utf-8'))
        elem_offer_rows = html_tree.xpath('.//tr[@class="rgRow"]')
        for elem_offer in elem_offer_rows:
            elem_link = elem_offer.xpath(".//a")[0]
            elem_offer_columns = elem_offer.xpath("./td")
            offer_kneset_num = elem_offer_columns[0].text
            offer_type = elem_offer_columns[2].text
            offer_status = elem_offer_columns[4].text
            offer_date = elem_offer_columns[5].text
            offer_date_obj = lowest_date = datetime.datetime.strptime(offer_date, "%d/%m/%Y")

            offer_name = elem_link.text
            offer_link = elem_link.xpath('@href')[0]
            if offer_date_obj.date() <= min_date.date():
                min_date_threshold_exceeded = True
                break
            print("offer:{} kneset#:{} offer_type:{} offer_status:{} offer_link:{} offer_date:{}".format(
                offer_name,
                offer_kneset_num,
                offer_type,
                offer_status,
                offer_link,
                offer_date
            ))
            # call next function for vote extraction and summary


#delete_db()
#delete_db()
#add_parties_and_members_to_db()
#a=ElectedOfficial.select(graph,"ציפי חוטובלי").first()
add_votes_to_db('1/12/2017')
# res=UTILS.get_url("https://www.knesset.gov.il/vote/heb/vote_search.asp")
# html_tree = html.fromstring(res)
# res=html_tree.xpath('//select[@name="sSubject"]/option/@value')
# print(res)
#add_parties_and_members_to_db()
#add_parties_and_members_to_db()
# get_law_list_by_min_date("7/11/2017")
# for i in d[:1]:
#     print(i)
#     vote_url="{}/{}".format(URLS.VOTES_BASE_URL,i['vote_url'])
#     r=get_vote_detail_dict(vote_url)
#     for i in r["FOR"]:
#         a=ElectedOfficial.select(graph,primary_value=i).first()# type: ElectedOfficial
#         print([p.name for p in a.member_of_party])
#print(get_party_to_member_dict())
#get_party_to_member_dict()
# members=execute_api_call(API.PARTY)
# print(len(members["objects"]))
#add_elected_officials()
#add_votes_to_db('10/12/2017')
