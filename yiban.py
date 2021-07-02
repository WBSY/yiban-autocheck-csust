import re
import requests
import util
class YiBan:
    CSRF = "64b5c616dc98779ee59733e63de00dd5" 
    COOKIES = {"csrf_token": CSRF}  # 固定cookie 无需更改
    HEADERS = {"Origin": "https://c.uyiban.com", "User-Agent": "yiban"}  # 固定头 无需更改

    class Yiban:
    CSRF = "64b5c616dc98779ee59733e63de00dd5"
    COOKIES = {"csrf_token": CSRF}
    HEADERS = {"Origin": "https://c.uyiban.com", "User-Agent": "YiBan"}
    EMAIL = {}

    def __init__(self, mobile, password):
        self.mobile = mobile
        self.password = password
        self.session = requests.session()
        self.name = ""

    def request(self, url, method="get", params=None, cookies=None):
        if method == "get":
            response = self.session.get(url=url, timeout=10, headers=self.HEADERS, params=params, cookies=cookies)
        else:
            response = self.session.post(url=url, timeout=10, headers=self.HEADERS, data=params, cookies=cookies)

        return response.json()

    def login(self):
        """
        登录
        :return:
        """
        params = {
            "mobile": self.mobile,
            "password": self.password,
            "imei": "0",
        }
        # 新的登录接口
        response = self.request("https://mobile.yiban.cn/api/v3/passport/login", params=params, cookies=self.COOKIES)
        if response is not None and response["response"] == 100:
            self.access_token = response["data"]["user"]["access_token"]
            self.HEADERS["Authorization"] = "Bearer " + self.access_token
            # 增加cookie
            self.COOKIES["loginToken"] = self.access_token
            return response
        else:
            return response

    def auth(self) -> json:
        """
        登录验证
        :return:
        """
        location = self.session.get("http://f.yiban.cn/iapp7463?access_token=" + self.access_token + "&v_time=" + str(int(round(time.time() * 100000))),
                                    allow_redirects=False, cookies=self.COOKIES)
        # 二次重定向
        act = self.session.get("https://f.yiban.cn/iapp/index?act=iapp7463", allow_redirects=False, cookies=self.COOKIES).headers["Location"]
        verifyRequest = re.findall(r"verify_request=(.*?)&", act)[0]
        response = self.request(
            "https://api.uyiban.com/base/c/auth/yiban?verifyRequest=" + verifyRequest + "&CSRF=" + self.CSRF,
            cookies=self.COOKIES)
        self.name = response["data"]["PersonName"]
        return response

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
