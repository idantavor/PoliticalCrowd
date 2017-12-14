class URLS:
    LAW_OFFERS_BASE_URL = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawSuggestionsSearch.aspx?t=LawSuggestionsSearch&st=CurrentKnesset"
    VOTES_BASE_URL = "http://www.knesset.gov.il/vote/heb/vote_search.asp"

class LAW_OFFER_TYPE:
    PRIVATE="פרטית"
    COMITTEE="ועדה"
    GOVERNEMENT="ממשלתית"

class LAW_PAGE_CONSTANTS :
    DOCX_START_DELIMITER = "דברי הסבר"
    DOCX_END_DELIMITER = "------------------------"
    LAW_PAGE_QUERY_URL = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/LawSuggestionsSearch.aspx?t=lawsuggestionssearch&st=currentknesset&wn={}&ki=20&sb=LatestSessionDate&so=D"
    LAW_PAGE_URL   = "http://main.knesset.gov.il/Activity/Legislation/Laws/Pages/{}"