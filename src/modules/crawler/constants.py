import requests
class URLS:
    LAW_OFFERS_BASE_URL = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawSuggestionsSearch.aspx?t=LawSuggestionsSearch&st=CurrentKnesset"
    VOTES_BASE_URL = "http://www.knesset.gov.il/vote/heb"
    MEMBERS_URL = "http://www.knesset.gov.il/presence/heb/PresentList.aspx"
    BASE_URL="http://www.knesset.gov.il"
    KNESSET_MAIN_BASE="http://main.knesset.gov.il"
    MEMBER_PAGE_BASE_URL='http://main.knesset.gov.il/mk/current/pages/MkPersonalDetails.aspx?MKID='
    VOTES_SEARCH_URL = "{}/vote_res_list.asp".format(VOTES_BASE_URL)

class API:
    BASE="https://oknesset.org"
    BASE_API="{}/{}".format(BASE,"api/v2")
    VOTE="{}/{}".format(BASE_API,"vote/")
    MEMBER = "{}/{}".format(BASE_API, "member/")
    MEMBER_AGENDAS = "{}/{}".format(BASE_API, "member-agendas/")
    PARTY = "{}/{}".format(BASE_API, "party/")
    LAW = "{}/{}".format(BASE_API, "law/")

    @staticmethod
    def query_call(url,offset=None,limit=None):
        offset_str = "offset={}".format(offset) if offset else None
        limit_str = "limit={}".format(limit) if limit else None
        if offset_str or limit_str:
            query_string='&&'.join([query for query in [offset_str,limit_str] if query is not None])
            url+='?'+query_string
        return url

class LAW_OFFER_TYPE:
    PRIVATE="פרטית"
    COMITTEE="ועדה"
    GOVERNEMENT="ממשלתית"

class VOTE_TYPE():
    TYPE_SET=set()
    TYPE=['אישור החוק', 'הודעת הממשלה', 'הודעת וועדה', 'הודעת ועדת הכנסת', 'הודעת יושב-ראש ועדת הכנסת', 'הודעת ראש הממשלה',
     'החלטה בדבר', 'החלטה בדבר תיקון טעות בחוק', 'הסתייגות', 'העברת הנושא לוועדה שתקבע ועדת הכנסת', 'הצבעה',
     'הצעה בדבר הרכב הוועדה המסדרת', 'הצעה לדחות את ההצבעה למועד אחר', 'הצעת אי-אמון בממשלה', 'הצעת הוועדה המסדרת',
     'הצעת הסיכום', 'הצעת ועדה', 'הצעת ועדת הכנסת', 'הצעת סיכום', 'הצעת סיעה', 'התנגדות להחיל דין רציפות',
     'לא לכלול את הנושא בסדר היום של המליאה', 'להחזיר את הצעת החוק לוועדה', 'להחיל דין רציפות', 'להסיר מסדר-היום',
     'להסיר מסדר-היום את הצעת החוק', 'להעביר את הנושא לוועדה', 'להעביר את הצעת החוק לוועדה',
     'להעביר את הצעת החוק לוועדה שתקבע ועדת הכנסת', 'להשהות את ההצבעה על הצעת החוק',
     'לכלול את הנושא בסדר היום של המליאה', 'קריאה שנייה', 'שם החוק']

class LAW_PAGE_CONSTANTS :
    DOCX_START_DELIMITER = "דברי הסבר"
    DOCX_END_DELIMITER = "------------------------"
    LAW_PAGE_QUERY_URL = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawSuggestionsSearch.aspx?t=lawsuggestionssearch&st=currentknesset&wn={}&ki=20&sb=LatestSessionDate&so=D"
    LAW_PAGE_URL   = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/{}"

VOTE_TYPE_IMAGE_LABELS={
    "ABSTAINED":"../images/Vote_h_3.gif",
    "FOR":"../images/Vote_h_1.gif",
    "AGAINST":"../images/Vote_h_2.gif",
    "DIDNT_VOTE":"../images/Vote_h_0.gif"
}
class UTILS:

    @staticmethod
    def single_get_url(url,retries=3,cookies=None):
        """
        get resposne
        :param url:
        :param retries:
        :param cookies:
        :return:
        """
        attempt = 1
        while attempt <= retries:
            res = requests.get(url,cookies=cookies)
            if res.status_code != requests.codes.ok:
                attempt+=1
                continue
            return res
        raise Exception("failed to get response for {}".format(url))

    @staticmethod
    def get_url(url, encoding='windows-1255', _retries=3, multiple=True, get_cookies=False,cookies=None):
        print("getting {}".format(url))
        res = UTILS.single_get_url(url,retries=_retries,cookies=cookies)
        cookie_jar=res.cookies
        if multiple:
            res=UTILS.single_get_url(url,cookies=cookie_jar)
            cookie_jar.update(res.cookies)
        if get_cookies:
            return cookie_jar,str(res.content,encoding=encoding,errors='ignore')
        else:
            return str(res.content,encoding=encoding,errors='ignore')