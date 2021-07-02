import re
import requests
import util
import time
class YiBan:
    CSRF = "sui-bian-fang-dian-dong-xi"  # 随机值 随便填点东西
    COOKIES = {"csrf_token": CSRF}  # 固定cookie 无需更改
    HEADERS = {"Origin": "https://c.uyiban.com", "User-Agent": "yiban"}  # 固定头 无需更改

    def __init__(self, account, passwd):
        self.account = account
        self.passwd = passwd
        self.session = requests.session()
        self.name = ""
        self.iapp = ""

    def request(self, url, method="get", params=None, cookies=None):
        if method == "get":
            req = self.session.get(url, params=params, timeout=10, headers=self.HEADERS, cookies=cookies)
        else:
            req = self.session.post(url, data=params, timeout=10, headers=self.HEADERS, cookies=cookies)
        try:
            return req.json()
        except:
            return None

    def login(self):
        params = {
            "mobile": self.account,
            "imei": "0",
            "password": self.passwd
            }
        r = self.request(url="https://mobile.yiban.cn/api/v3/passport/login", params=params)
        if r is not None and str(r["response"]) == "100":
            self.access_token = r["data"]["user"]["access_token"]
            self.COOKIES["loginToken"] = r["data"]["user"]["access_token"]
            return r
        else:
            return r

    def getHome(self):
        params = {
            "access_token": self.access_token,
        }
        r = self.request(url="https://mobile.yiban.cn/api/v3/home", params=params, cookies=self.COOKIES)
        self.name = r["data"]["user"]["userName"]
        for i in r["data"]["hotApps"]:
            if i["name"] == "易班校本化":
                self.iapp = re.findall(r"(iapp.*)\?", i["url"])[0]
        return r
    def auth(self):
        params = {
            "act": self.iapp,
            "v": self.access_token
        }
        location = self.session.get("https://f.yiban.cn/iapp/index",params=params,
                                    allow_redirects=False, cookies=self.COOKIES).headers.get("Location")
        if location is None:
            raise Exception("该用户可能没进行校方认证，无此APP权限")
        verifyRequest = re.findall(r"verify_request=(.*?)&", location)[0]
        result_auth = self.request(
            "https://api.uyiban.com/base/c/auth/yiban?verifyRequest=%s&CSRF=%s" % (verifyRequest, self.CSRF),
            cookies=self.COOKIES)
        data_url = result_auth["data"].get("Data")
        if data_url is not None:  # 授权过期
            result_html = self.session.get(url=data_url, headers=self.HEADERS,
                                           cookies={"loginToken": self.access_token}).text
            re_result = re.findall(r'input type="hidden" id="(.*?)" value="(.*?)"', result_html)
            post_data = {"scope": "1,2,3,"}
            for re_i in re_result:
                post_data[re_i[0]] = re_i[1]
            usersure_result = self.session.post(url="https://oauth.yiban.cn/code/usersure",
                                                data=post_data,
                                                headers=self.HEADERS, cookies={"loginToken": self.access_token})
            if usersure_result.json()["code"] == "s200":
                return self.auth()
            else:
                return False
        else:
            return True

    def getUncompletedList(self):
        params = {
            "CSRF": self.CSRF,
            "StartTime": util.get_today(),
            "EndTime": util.get_time()
        }
        return self.request("https://api.uyiban.com/officeTask/client/index/uncompletedList", params=params,
                            cookies=self.COOKIES)

    def getCompletedList(self):
        params = {
            "CSRF": self.CSRF,
            "StartTime": util.get_7_day_ago(),
            "EndTime": util.get_time()
        }
        return self.request("https://api.uyiban.com/officeTask/client/index/completedList", params=params,
                            cookies=self.COOKIES)

    def getJsonByInitiateId(self, initiate_id):
        params = {
            "CSRF": self.CSRF
        }
        return self.request("https://api.uyiban.com/workFlow/c/work/show/view/%s" % initiate_id, params=params,
                            cookies=self.COOKIES)

    def getTaskDetail(self, taskId):
        return self.request(
            "https://api.uyiban.com/officeTask/client/index/detail?TaskId=%s&CSRF=%s" % (taskId, self.CSRF),
            cookies=self.COOKIES)

    def submit(self, data, extend, wfid):
        params = {
            "data": data,
            "extend": extend
        }
        return self.request(
            "https://api.uyiban.com/workFlow/c/my/apply/%s?CSRF=%s" % (wfid, self.CSRF), method="post",
            params=params,
            cookies=self.COOKIES)

    def getShareUrl(self, initiateId):
        return self.request(
            "https://api.uyiban.com/workFlow/c/work/share?InitiateId=%s&CSRF=%s" % (initiateId, self.CSRF),
            cookies=self.COOKIES)
