#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
from api.logging import *
# 第三方 SMTP 服务
mail_host="smtp.qq.com"  #设置服务器
mail_user="@qq.com"    #用户名
mail_pass=""   #口令

sender = '@qq.com'
receivers = ['@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱


def send_mail(subject='',from_name = '',to_name = '',content = '',sub_type = 'plain',image_map = {},receivers = ['240694772@qq.com']):
    # log_info('send_mail begin',image_map)
    msg = MIMEMultipart()
    msg['From'] = Header("%s <%s>"%(from_name,sender))
    msg['To'] =  Header(to_name , 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg.attach(MIMEText(content, sub_type, 'utf-8'))
    for image_name in image_map: 
        image_path = image_map[image_name]
        f = open(image_path, 'rb')  #打开图片
        msgimage = MIMEImage(f.read())
        f.close()
        msgimage.add_header('Content-ID', '<%s>'%image_name)  # 设置图片
        msg.attach(msgimage)
    # try:
    smtpObj = smtplib.SMTP_SSL(mail_host, 465)
    smtpObj.login(mail_user,mail_pass)
    smtpObj.sendmail(sender, receivers, msg.as_string())
    smtpObj.quit() 
    log_info('mail sended receivers',receivers)
    # except smtplib.SMTPException:
    #     log_error ("Error: 无法发送邮件")#
