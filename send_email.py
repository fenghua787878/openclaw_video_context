#!/usr/bin/env python3
import smtplib
import json
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def send_email(script_content, recipients):
    # 使用绝对路径
    config_path = "/home/admin/content_loop/email_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"配置文件未找到: {config_path}")
        return False
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = config['default_from']
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = "【内容闭环】今日短视频脚本"
    
    # 添加正文
    msg.attach(MIMEText(script_content, 'plain', 'utf-8'))
    
    try:
        # 连接SMTP服务器
        if config.get('use_ssl', False):
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
        else:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls', True):
                server.starttls()
        
        # 登录并发送
        server.login(config['username'], config['smtp_password'])
        server.send_message(msg)
        server.quit()
        return True
        
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python send_email.py <script_file> <recipients_json>")
        sys.exit(1)
    
    script_file = sys.argv[1]
    recipients = json.loads(sys.argv[2])
    
    try:
        with open(script_file, 'r', encoding='utf-8') as f:
            script_content = f.read()
    except FileNotFoundError:
        print(f"脚本文件未找到: {script_file}")
        sys.exit(1)
    
    success = send_email(script_content, recipients)
    if success:
        print("邮件发送成功！")
        sys.exit(0)
    else:
        print("邮件发送失败！")
        sys.exit(1)