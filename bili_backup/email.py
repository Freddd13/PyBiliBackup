'''
Date: 2023-10-23 18:24:50
LastEditors: Kumo
LastEditTime: 2024-06-21 22:16:19
Description: 
'''

from .utils.logger import LoggerManager

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.application import MIMEApplication

import os

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger

# @log_manager.apply_log_method_to_all_methods
class EmailHandler:
    def __init__(self, email,smtp_host,smtp_port, mail_license, receivers):
        self.email = email
        self.smtp_host =smtp_host
        self.smtp_port = smtp_port
        self.mail_license = mail_license
        self.receivers = receivers


    def perform_sending(self, subject, content, sheet_files=[], log_files = []):
        message = MIMEMultipart()
        message['From'] = self.email
        message['To'] =  ';'.join(self.receivers)
        message['Subject'] = Header(subject, 'utf-8')
        message.attach(MIMEText(content, 'plain', 'utf-8'))
        
        # sheet files
        # for file in sheet_files:
        #     filename = os.path.basename(file)
        #     logger.debug("sending filename: "+filename)
        #     att = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
        #     att["Content-Type"] = 'application/octet-stream'
        #     att["Content-Disposition"] = 'attachment; filename=' + '\"'+ filename +'\"'
        #     message.attach(att)
        
        # log files
        for file in log_files:
            filename = os.path.basename(file)
            att = MIMEText(open(file, 'r', errors='ignore').read(), 'base64', 'utf-8')
            att["Content-Type"] = 'application/octet-stream'
            att["Content-Disposition"] = 'attachment; filename=' + '\"'+ filename +'\"'
            message.attach(att)

        # sending
        try:
            context=ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, port=self.smtp_port) as smtp:
                smtp.starttls(context=context)
                smtp.login( self.email, self.mail_license)
                smtp.sendmail(self.email, self.receivers, message.as_string())
                logger.info("send email success")

        except Exception as e:
            logger.error(str(e))
            logger.error("Fail to send mail!")

