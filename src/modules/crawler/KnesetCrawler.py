import argparse
import time
import dateparser
import traceback
import requests
from dateutil import relativedelta
from lxml import html

import LawPage
from Logger import getLogger
from constants import URLS, VOTE_TYPE_IMAGE_LABELS, MAIL_CONSTANTS
from dbconnector import *
from utils import UTILS
import logging
logger = getLogger('crawler')

graph = bolt_connect()  # type: Graph


def auto_retry(num_of_retries):
    # auto retry decorator for functions that needs retries
    def decorator(f):
        def wrapper(*args, **kwargs):
            max_retries = num_of_retries
            retry = 1
            while True:
                print("retry number {}".format(retry))
                try:
                    res = f(*args, **kwargs)
                    return res
                except Exception as e:
                    retry += 1
                    if retry > max_retries:
                        raise e
                    else:
                        continue

        return wrapper

    return decorator


def delete_db():
    selection = ''
    while selection not in ['y', 'n', 'Y', 'N']:
        selection = input("are you sure you want to delete the db ? [y/n]\n")
    if selection in ['Y', 'y']:
        graph = bolt_connect()
        graph.begin(autocommit=True)
        graph.delete_all()


def get_party_and_role_from_role_title(role_title):
    res = role_title.split(',')
    party = res[0]
    role_suffix = ','.join(res[1:])
    role = None if role_suffix == "" else role_suffix
    return party, role


def normalize(string):
    if string is None:
        return None
    else:
        return " ".join(string.strip().split())


def get_member_dict(member_page_url, image_link, member_name):
    logger.info("getting url for member {}".format(member_name))
    html_tree = html.fromstring(UTILS.get_url(member_page_url, encoding='utf8'))
    title = html_tree.xpath('//div[@class="MKRoleDiv"]//h3/text()')[0]
    party, role = get_party_and_role_from_role_title(title)
    return {"name": member_name, "title": role, "img_url": image_link, "party": party, "homepage_url": member_page_url,
            "is_active": True}


def get_non_voting_officials_dict_list() -> list:
    res = []
    html_tree = html.fromstring(UTILS.get_url(URLS.MEMBERS_URL))
    elem_ministers = html_tree.xpath(
        '//table[@id="dlMinister"]//td[.//@class="PhotoAsistno" or .//@class="PhotoAsist"]')
    logger.info("found {} non voting minister officials".format(len(elem_ministers)))
    for elem_minister in elem_ministers:
        image_url = "{}{}".format(URLS.BASE_URL, elem_minister.xpath('./img/@src')[0])
        name = elem_minister.xpath('./a/text()')[0]
        res.append({"name": name, "img_url": image_url, "is_active": False, })
    return res


def get_party_to_member_dict() -> dict:
    res_dict = {}
    html_tree = html.fromstring(UTILS.get_url(URLS.MEMBERS_URL))
    elem_members = html_tree.xpath('//table[@id="dlMkMembers"]//td[.//@class="PhotoAsistno" or .//@class="PhotoAsist"]')
    logger.info("found {} voting elected officials ".format(len(elem_members)))
    for elem_member in elem_members:
        image_src = elem_member.xpath('./img/@src')[0]  # type: str
        if image_src.startswith("http"):
            image_url = image_src
        else:
            image_url = "{}{}".format(URLS.BASE_URL, image_src)
        name = elem_member.xpath('./a/text()')[0]
        mk_id = elem_member.xpath('./a/@href')[0].split('=')[1]
        member_page_url = "{}{}".format(URLS.MEMBER_PAGE_BASE_URL, mk_id)
        member_dict = get_member_dict(member_page_url, image_url, name)
        member_party = member_dict['party']
        if member_party in res_dict:
            res_dict[member_party].append(member_dict)
        else:
            res_dict[member_party] = [member_dict]
    return res_dict


def add_parties_and_members_to_db():
    party_to_members_dict = get_party_to_member_dict()
    for party, members_list in party_to_members_dict.items():
        p = Party.createPartyFromJson({'number_of_seats': len(members_list), 'name': party})
        graph.push(p)
        for member_dict in members_list:
            m = ElectedOfficial.createElectedOfficialFromJson(member_dict, p)
            graph.push(m)
    non_memebers_dict_list = get_non_voting_officials_dict_list()
    p = Party.createPartyFromJson({'number_of_seats': len(non_memebers_dict_list), 'name': 'אינם חברי כנסת'})
    graph.push(p)
    for member_dict in non_memebers_dict_list:
        m = ElectedOfficial.createElectedOfficialFromJson(member_dict, p)
        graph.push(m)


def dstring_to_timestamp(date):
    return dateparser.parse(date).timestamp()


def get_votes(date_from="1/1/2003", date_to=None, retries=45):
    result_votes = []
    datetime_from = datetime.datetime.strptime(date_from, "%d/%m/%Y")
    datetime_to = datetime.date.today() if date_to is None else datetime.datetime.strptime(date_from, "%d/%m/%Y")
    post_data = {"mk_individual_desc": "",
                 "faction_desc": "",
                 "New_Q": "1",
                 "ckDates": "D",
                 "sWord": "",
                 "sSubject": "",
                 "mk_individul_id_t": "",
                 "faction_id_t": "",
                 "dtFmYY": datetime_from.year,
                 "dtFmMM": datetime_from.month,
                 "dtFmDD": datetime_from.day,
                 "dtToYY": datetime_to.year,
                 "dtToMM": datetime_to.month,
                 "dtToDD": datetime_to.day}
    more_results_data = {
        "mk_individul_id_t": "",
        "ckMkIndiv": "",
        "RStart": ''
    }
    logger.info('fetching votes between {} to {}'.format(str(datetime_from), str(datetime_to)))
    res = requests.post(URLS.VOTES_SEARCH_URL, post_data)
    if res.status_code != requests.codes.ok:
        logger.error("failed to get response for {}".format(URLS.VOTES_SEARCH_URL))
        raise Exception("failed to get response for {}".format(URLS.VOTES_SEARCH_URL))
    cookies = res.cookies
    res = requests.post(URLS.VOTES_SEARCH_URL, post_data, cookies=cookies)
    cookies.update(res.cookies)
    if res.status_code != requests.codes.ok:
        logger.error("failed to get response for {}".format(URLS.VOTES_SEARCH_URL))
        raise Exception("failed to get response for {}".format(URLS.VOTES_SEARCH_URL))
    html_tree = html.fromstring(str(res.content, encoding='windows-1255', errors='ignore'))
    first_loop = True
    while True:
        result_meta_data_str = html_tree.xpath('//td[@class="DataText3"]/text()')[1]
        total_results = int(result_meta_data_str.split()[0].strip())
        if first_loop:
            logger.info("found {} votes".format(total_results))
            first_loop = False
        if total_results == 0:
            return result_votes
        next_cnt = int(result_meta_data_str.split()[-1].strip())
        logger.info("fetching results {}-{}".format(next_cnt - 20, next_cnt))
        elem_votes = html_tree.xpath('//tr[./td/a[@class="DataText6"]]')
        for elem_vote in elem_votes:
            vote_dict = {
                "raw_title": elem_vote.xpath('.//a/text()')[0],
                "type": elem_vote.xpath('.//a/text()')[0].split("-")[0].strip(),
                "url": "{}/{}".format(URLS.VOTES_BASE_URL, elem_vote.xpath('.//a/@href')[0]),
                "date": elem_vote.xpath('./td[4]/text()')[0].strip(),
                "vote_num": elem_vote.xpath('./td[3]/text()')[0].strip(),
                "meeting_num": elem_vote.xpath('./td[2]/text()')[0].strip(),
                "timestamp": dstring_to_timestamp(elem_vote.xpath('./td[4]/text()')[0].strip())
            }
            result_votes += [vote_dict]
        if next_cnt < total_results:
            # retry machanism is a must here since the knesset site is shit
            retry = 1
            more_results_data["RStart"] = str(next_cnt)
            while retry < retries:
                res = requests.post(URLS.VOTES_SEARCH_URL, more_results_data, cookies=cookies)
                content_string = str(res.content, encoding='windows-1255', errors='ignore')
                if "תקלה בהעברת המשתנים" in content_string:
                    retry += 1
                    time.sleep(2)
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
    summary_list = []
    vote_list = get_votes(date_from=date_from)
    for vote in vote_list:
        # check if the vote is already in the db
        print(vote['raw_title'])
        res = Vote.select(graph, primary_value=vote['raw_title']).first()
        if res is not None:
            print("found object for {}".format(vote['raw_title']))
            continue
        else:
            law_name = LawPage.parse_title_for_time(vote['raw_title'])
            # check if the law is already in the db
            try:
                law_obj = Law.select(graph, primary_value=law_name).first()  # type: Law
                if law_obj is None:
                    logger.debug("new law detected - {}".format(law_name))
                if law_obj is None or law_obj.description == "":
                    # create new law object to conatin the vote
                    law_dict = LawPage.build_law_dict(vote)
                    url = law_dict['url']
                    description = law_dict['description']
                    initiators = law_dict['initiators']  # type: list
                    if law_obj is None:
                        law_obj = Law.createLaw(law_name, vote['timestamp'], None, description, url)  # type: Law
                        summary_list.append("new law added :{}".format(law_name))
                    else:
                        law_obj.description = description
                    for initiator in initiators:
                        initiator_member = ElectedOfficial.select(graph, normalize(initiator)).first()
                        if initiator_member is None:
                            logger.error(
                                "fail to retreive initiator elected official {} from db by serching for {}".format(
                                    initiator, normalize(initiator)))
                        else:
                            law_obj.proposed_by.add(initiator_member)
                voting_details = get_vote_detail_dict(vote['url'])
                vote_obj = Vote.createVoteFromJson(vote, law_obj, voting_details, graph)
                summary_list.append("new vote added :{}".format(vote['raw_title']))
                if law_obj.timestamp < vote_obj.timestamp:
                    law_obj.timestamp = vote_obj.timestamp
                graph.push(law_obj)
                graph.push(vote_obj)
            except Exception as e:
                logger.error("Error handling vote {} : {}".format(vote['raw_title'], str(e)))
    return summary_list


def get_vote_detail_dict(vote_url):
    res_dict = {}
    html_tree = html.fromstring(UTILS.get_url(vote_url))
    for vote_type, vote_image_label in VOTE_TYPE_IMAGE_LABELS.items():
        elem_vote_table = html_tree.xpath('//table[./tr/td/img[@src="{}"]]'.format(vote_image_label))

        if len(elem_vote_table) == 0:
            res_dict[vote_type] = []
            res_dict["{}_cnt".format(vote_type)] = 0
        else:
            voting_members = elem_vote_table[0].xpath('.//a/text()')
            res_dict["{}_cnt".format(vote_type)] = len(voting_members)
            res_dict[vote_type] = [" ".join(member.split()) for member in voting_members]
    return res_dict


def parse_args(args):
    global graph
    parser = argparse.ArgumentParser(description='Knesset Crawler Main Tool')
    parser.add_argument('--from_date', '-fd',
                        default=str(datetime.datetime.today() - relativedelta.relativedelta(months=1)),
                        dest="from_date", help="start scraping for laws and votes starting from this date")
    parser.add_argument('--db_addr', dest="db_ip", default=None, help="database ip address")
    parser.add_argument('--interval', dest="interval", default=10, help="scraping interval in minutes", type=int)
    parser.add_argument('--mail', action='store_true', dest="mail", default=False, help="send mail debugs")
    parser.add_argument('--members', action='store_true', dest="members", default=False,
                        help="crawl for members and parties")
    parser.add_argument('--local', action='store_true', dest="is_local", default=False,
                        help="is db resides on local machine")
    parser.add_argument('--delete_db', action='store_true', help="delete all db content", default=False,
                        dest="delete_db")
    parser.add_argument('--add_jobs', action='store_true', help="add job objects to db", default=False, dest="add_jobs")
    parser.add_argument('--add_residency', action='store_true', help="add residency objects to db", default=False,
                        dest="add_residency")

    parsed_args = parser.parse_args(args)
    parsed_args.from_date = dateparser.parse(parsed_args.from_date)
    if parsed_args.is_local:
        graph = bolt_connect(ip='127.0.0.1')
    elif parsed_args.db_ip is not None:
        graph = bolt_connect(ip=parsed_args.db_ip)
    else:
        graph = bolt_connect()
    return parsed_args


def main(args):
    pargs = parse_args(args[1:])
    if pargs.delete_db:
        delete_db()
        exit(0)
    if pargs.members:
        add_parties_and_members_to_db()
        exit(0)
    if pargs.add_jobs:
        JobCategory.add_jobs_to_db(graph, logger)
        exit(0)
    if pargs.add_residency:
        Residency.add_residencies_to_db(graph, logger)
        exit(0)
    try:
        first_time = True
        now = datetime.datetime.now()
        while True:
            if first_time:
                date = pargs.from_date.strftime('%d/%m/%Y')
            else:
                date = now.strftime('%d/%m/%Y')
            if pargs.mail:
                UTILS.send_mail(MAIL_CONSTANTS.SUBJECTS.CRAWLER_INFO, MAIL_CONSTANTS.MESSAGES.get_start_message(date))
            logger.info("crawler started interation from {}".format(date))
            summary = add_votes_to_db(date)
            if pargs.mail:
                UTILS.send_mail(MAIL_CONSTANTS.SUBJECTS.CRAWLER_INFO,
                                MAIL_CONSTANTS.MESSAGES.get_summary_message(summary))
            logger.info("crawler finised iteration")
            first_time = False
            now = datetime.datetime.now()
            time.sleep(60 * pargs.interval)
    except Exception as e:
        UTILS.send_mail(MAIL_CONSTANTS.SUBJECTS.CRAWLER_ERROR, MAIL_CONSTANTS.MESSAGES.get_error_message(e))
        logger.error('Crawler encountered an error :\n{}\nSTACK TRACE:\n{}'.format(e, traceback.print_stack()))
