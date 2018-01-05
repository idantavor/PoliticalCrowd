import requests
import smtplib
from constants import MAIL_RECIPIENTS
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
            msg = MIMEText(_message, _charset="UTF-8")
            msg['Subject'] = Header(subject, "utf-8")
            msg['To'] = ", ".join(_to)
            msg['From'] = _from
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login("heimdalltau@gmail.com","bibikiller")
            server.sendmail(_from, _to, msg.as_string(),)
            server.close()
            print('successfully sent the mail')
        except Exception as e:
            print("failed to send mail")
            raise e
