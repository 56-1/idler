# _*_ coding:utf-8 _*_

from hashlib import md5
from time import time, sleep
from sys import exit
from json import JSONDecodeError, loads
from logging import error, warning
from collections import defaultdict

from requests import request, HTTPError
from requests.utils import dict_from_cookiejar, add_dict_to_cookiejar
from bs4 import BeautifulSoup as bs


def requestUtils(method="get", url="", params="", body="", headers="", cookies=""):
    try:
        response = request(method=method, url=url, params=params, data=body,
                           headers=headers, cookies=cookies)
        response.raise_for_status()
    except (ConnectionError, TimeoutError, HTTPError) as e:
        error(str(e))
        exit(1)

    return response


def encrypt(message):
    t = md5()
    t.update(message.encode("UTF-8"))
    return t.hexdigest()


class Client:
    def __init__(self):
        self.url = ""
        self.headers = ""
        self.cookiesForCourse = ""
        self.cookiesForClass = ""
        self.uid = ""
        self.personId = ""
        self.courseId = ""
        self.clazzId = ""
        self.headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; Mi Note 3 MIUI/V11.0.4.0.PCHCNXM) "
                          "com.chaoxing.mobile/ChaoXingStudy_3_4.3.4_android_phone_494_27 ("
                          "@Kalimdor)_60b50a8d826f48fc96a55289f81605af",
            "Accept-Language": "zh_CN",
            "Accept-Encoding": "gzip",
            "Host": "mooc1-api.chaoxing.com"
        }

    def login(self, account, password):
        """登录获取cookies,用于后面拉取课程"""
        method = "post"
        url = "http://passport2-api.chaoxing.com/v11/loginregister"
        self.headers["Host"] = "passport2-api.chaoxing.com"  # Host一定要正确，不然不给数据

        params = {"cx_xxt_passport": "json"}
        body = {"uname": account, "code": password, "loginType": 1, "roleSelect": "true"}

        response = requestUtils(method=method, url=url, params=params, body=body, headers=self.headers)
        try:
            content = response.json()
        except JSONDecodeError as e:
            error(str(e))
            exit(1)

        if not content["status"]:
            error(content["mes"])
            exit(1)

        self.headers["Host"] = "sso.chaoxing.com"
        response = requestUtils(method, url=content["url"], headers=self.headers, cookies=response.cookies)

        self.cookiesForCourse = response.cookies
        try:
            content = response.json()
        except JSONDecodeError as e:
            error(str(e))

        self.uid = content['msg']['puid']

    def course(self):
        """拉取所有课程并用dict存储，序号：课程"""
        url = "https://mooc1-api.chaoxing.com/gas/person"
        params = {"userid": self.uid, "view": "json", "selectuser": "true",
                  "fields": "clazz.fields(id,bbsid,state,name,classscore,chatid,studentcount,course.fields(id,"
                            "teacherfactor,name,imageurl,creatorId)),course.fields(id,bbsid,name,teacherfactor,"
                            "imageurl,creatorId,clazz.fields(id,bbsid,name,classscore,studentcount,"
                            "chatid)).isteachcourse(true)"}

        self.headers["Host"] = "mooc1-api.chaoxing.com"
        response = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForCourse)
        self.cookiesForClass = response.cookies  # got jrose, k8s, route

        try:
            content = response.json()
        except JSONDecodeError as e:
            error(str(e))
            exit(1)

        clazz = content["data"][-1]["clazz"]
        courseData = clazz["data"]
        course = defaultdict(dict)
        for i, v in enumerate(courseData):
            try:
                t = v["course"]["data"][0]

                courseName = t["name"]
                courseId = t["id"]
                clazzId = v["id"]

                course[i+1]["courseName"] = courseName
                course[i+1]["courseId"] = str(courseId)
                course[i+1]["clazzId"] = str(clazzId)
            except IndexError:
                continue

        return course

    def courseUtils(self, courseId, clazzId):
        """拉取用于刷课的cookies"""
        self.courseId = courseId
        self.clazzId = clazzId

        url = "https://passport2.chaoxing.com/api/cookie"
        self.headers["Host"] = "passport2.chaoxing.com"

        response = requestUtils(url=url, headers=self.headers, cookies=self.cookiesForCourse)
        t = dict_from_cookiejar(response.cookies)  # for get other cookies
        add_dict_to_cookiejar(self.cookiesForClass, t)

        url = "https://mooc1-api.chaoxing.com/gas/clazzperson"
        params = {"courseid": courseId, "clazzid": clazzId, "userid": self.uid,
                  "view": "json", "fields": "clazzid,popupagreement,personid,clazzname"}

        self.headers["Host"] = "mooc1-api.chaoxing.com"
        response = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)
        try:
            content = response.json()
        except JSONDecodeError as e:
            error(str(e))
            exit(1)

        self.personId = content["data"][0]["personid"]

    def lesson(self):
        """拉取所有课时，inf_enc， token不必要"""
        url = "https://mooc1-api.chaoxing.com/gas/clazz"
        params = {"id": self.clazzId, "view": "json", "token": "4faa8662c59590c6f43ae9fe5b002b42",
                  "fields": "id,bbsid,classscore,isstart,chatid,name,state,isthirdaq,isfiled,information,discuss,"
                            "visiblescore,begindate,coursesetting.fields(id,courseid,hiddencoursecover,"
                            "hiddenwrongset),course.fields(id,infocontent,name,objectid,classscore,bulletformat,"
                            "imageurl,privately,teacherfactor,unfinishedJobcount,jobcount,state,app,knowledge.fields("
                            "id,name,indexOrder,parentnodeid,status,layer,label,begintime,attachment.fields(id,type,"
                            "objectid,extension,name).type(video)))",
                  "_time": str(int(time() * 1000)), "inf_enc": "f7fcadda9e62f79707af49453c270bed"}

        response = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)
        try:
            content = response.json()
        except JSONDecodeError as e:
            error(str(e))
            exit(1)

        course = content["data"][0]["course"]["data"]
        knowledge = course[0]["knowledge"]["data"]
        classQueue = [str(x["id"]) for x in knowledge]

        method = "post"
        url = "https://mooc1-api.chaoxing.com/job/myjobsnodesmap"
        params = {"token": "4faa8662c59590c6f43ae9fe5b002b42", "_time": str(int(time() * 1000))}
        t = ["=".join([x, params[x]]) for x in params]
        t = "&".join(t)
        params["inf_enc"] = encrypt(t)

        body = {"view": "json", "clazzid": self.clazzId, "userid": self.uid, "courseid": self.courseId,
                "nodes": ",".join(classQueue), "time": str(int(time() * 1000))}

        response = requestUtils(method=method, url=url, body=body, headers=self.headers, cookies=self.cookiesForClass)
        try:
            jobs = response.json()
        except JSONDecodeError as e:
            error(str(e))

        return jobs

    def playVideo(self, nodeId):
        """获取刷课所需的全部数据，进行刷课"""
        # 为了获取jobid和objectid
        url = "https://mooc1-api.chaoxing.com/gas/knowledge"

        params = {"id": nodeId, "courseid": self.clazzId, "view": "json", "_time": str(int(time() * 1000)),
                  "token": "4faa8662c59590c6f43ae9fe5b002b42", "inf_enc": "4a4b759c6b8db81f09a5a1dac4c90097",
                  "fields": "id,parentnodeid,indexorder,label,layer,name,begintime,createtime,lastmodifytime,status,"
                            "jobUnfinishedCount,clickcount,openlock,card.fields(id,knowledgeid,title,knowledgeTitile,"
                            "description,cardorder).contentcard(all)"}

        response = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)
        try:
            content = response.json()
        except JSONDecodeError as e:
            error(str(e))
            exit(1)

        try:
            className = content["data"][0]["name"]
            card = content["data"][0]["card"]
            data = card["data"][0]
            description = data["description"]  # html apartment include jobid objectid mid
            soup = bs(description, "lxml")
            tags = soup.find_all("iframe")
        except (IndexError, KeyError):
            return

        for position, tag in enumerate(tags):
            data = loads(tag["data"])

            objectId = data["objectid"]
            jobId = data["jobid"]
            mid = data['mid']

            # 获得视频时长
            url = f"https://mooc1-api.chaoxing.com/ananas/status/{objectId}"
            params = {"k": "2134", "flag": "normal", "_dc": "1594027727050"}
            response = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)
            try:
                content = response.json()
            except JSONDecodeError as e:
                error(str(e))

            duration = content["duration"]
            dtoken = content["dtoken"]

            def initVideo():
                url = "http://mooc1-api.chaoxing.com/richvideo/initdatawithviewer"
                params = {"start": "0", "mid": mid, "view": "json"}

                _ = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)

                url = "https://mooc1-api.chaoxing.com/richvideo/subtitle"
                params = {"mid": mid, "view": "json"}
                _ = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)

            initVideo()

            url = f"https://mooc1-api.chaoxing.com/multimedia/log/a/{self.personId}/{dtoken}"

            params = {"otherInfo": f"nodeId_{nodeId}-cpi_{self.personId}", "duration": f"{duration}",
                      "akid": "null", "jobid": jobId, "clipTime": f"0_{duration}", "clazzId": f"{self.clazzId}",
                      "objectId": objectId, "userid": f"{self.uid}", "dtype": "Video", "view": "json"}

            print(f"Starting:{className}:{position+1}")

            for i in range(0, duration + 60, 60):
                playingTime = duration if i >= duration else i
                isdrag = 4 if playingTime == duration else 3 if playingTime == 0 else 0

                params["isdrag"] = isdrag
                params["playingTime"] = playingTime

                message = f"[{self.clazzId}][{self.uid}][{jobId}][{objectId}][{playingTime * 1000}]" \
                          f"[d_yHJ!$pdA~5][{duration}000][0_{duration}]"
                params["enc"] = encrypt(message)

                response = requestUtils(url=url, params=params, headers=self.headers, cookies=self.cookiesForClass)
                try:
                    content = response.json()
                except JSONDecodeError as e:
                    error(str(e))

                t = int((playingTime + 1) / duration * 100)
                print(f"{t}%", end=" ", flush=True)

                if content["isPassed"] and (playingTime == 0 or playingTime == duration):
                    print("")
                    break

                sleep(30)  # 视频播放倍速2.0 60 / 2 = 30

            print(f"Finished:{className}:{position+1}")
