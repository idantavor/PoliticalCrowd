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
    LAW_PAGE_INITIATORS = "חברי הכנסת היוזמים"

VOTE_TYPE_IMAGE_LABELS={
    "ABSTAINED":"../images/Vote_h_3.gif",
    "FOR":"../images/Vote_h_1.gif",
    "AGAINST":"../images/Vote_h_2.gif",
    "DIDNT_VOTE":"../images/Vote_h_0.gif"
}

MAIL_RECIPIENTS=['i.tavor@gmail.com']

class MAIL_CONSTANTS:
    class SUBJECTS:
        CRAWLER_ERROR="[ERROR] Knesset Crawler encountered an error"
        CRAWLER_INFO = "[INFO] Knesset Crawler report"

    class MESSAGES:
        @staticmethod
        def get_start_message(date):
            return "Crawler started , crawling from {}".format(date)

        @staticmethod
        def get_summary_message(summary_list):
            ret="Crawler finished iteration -total of {} objects where added to the db\n operations:\n-".format(len(summary_list))
            if len(summary_list)>0:
                ret+="\n-".join(summary_list)
            return ret

        @staticmethod
        def get_error_message(error):
            return "Crawler encountered an error:\n{}".format(str(error))