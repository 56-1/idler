# _*_ coding:utf-8_*_

from student import Student

account = input("请输入用户名：")
password = input("请输入密码：")

student = Student(account, password)

student.login()
student.choiceCourse()
student.playVideo()
