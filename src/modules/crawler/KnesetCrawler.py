import datetime

import requests
from lxml import html

from constants import URLS


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


get_law_list_by_min_date("7/11/2017")
