import requests
import smtplib
from constants import MAIL_RECIPIENTS
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

    @staticmethod
    def send_mail(subject,_message,_from="bibi@gmail.com",_to=MAIL_RECIPIENTS):
        try:
            message = """From: {}\nTo: {}\nSubject: {}\n\n{}
            """.format(_from, ", ".join(_to), subject, _message)
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login("heimdalltau@gmail.com","bibikiller")
            server.sendmail(_from, _to, message,)
            server.close()
            print('successfully sent the mail')
        except Exception as e:
            print("failed to send mail")
            raise e