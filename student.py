# _*_coding:utf-8_*_

# 要扩展到其他平台的话，只需在写一个Client
# 并提供这个文件中用到的接口，就能实现刷课

from client import Client


class Student:
    def __init__(self, user, passwd):
        self.account = user
        self.password = passwd
        self.client = Client()

    def login(self):
        self.client.login(self.account, self.password)

    def choiceCourse(self):
        course = self.client.course()
        for i in course:
            print(i, course[i]["courseName"])

        checkCourse = int(input("请输入课程对应的序号:"))
        self.client.courseUtils(courseId=course[checkCourse]["courseId"],
                                clazzId=course[checkCourse]["clazzId"])

    def playVideo(self):
        jobs = self.client.lesson()
        for i in jobs:
            if jobs[i]["unfinishcount"]:
                self.client.playVideo(i)
