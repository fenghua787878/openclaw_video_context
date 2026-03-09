#!/usr/bin/env python3
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import sys

def send_email(script_content, recipients):
    # 配置文件路径 - 在工作目录中
    config_path = "/home/admin/.openclaw/workspace/email_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading config: {e}")
        return False
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = config['default_from']
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = "【内容闭环】今日短视频脚本已生成"
    
    # 添加脚本内容
    msg.attach(MIMEText(script_content, 'plain', 'utf-8'))
    
    try:
        # 连接SMTP服务器
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['username'], config['smtp_password'])
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

if __name__ == "__main__":
    # 读取脚本内容
    script_path = "/home/admin/content_loop/runs/daily_20260305_151749/script.md"
    with open(script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 收件人列表
    recipients = ["18689998904@qq.com", "1735236011@qq.com"]
    
    success = send_email(script_content, recipients)
    if success:
        print("✅ 邮件发送成功！")
    else:
        print("❌ 邮件发送失败！")