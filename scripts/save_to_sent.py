import imaplib
import json
import os
import time
from email.message import EmailMessage

def save_sent():
    cred_path = "/home/jom/SynologyDrive/AI Dashboard/_CORE_Private/mail_credentials.json"
    if not os.path.exists(cred_path): return
    with open(cred_path) as f: creds = json.load(f)
    
    with open("/home/jom/SynologyDrive/AI Dashboard/outbox/Newspaper_Digest.html", "r") as f:
        html_content = f.read()

    recipients = ["eps_group_a@siamrajplc.com", "eps_group_b@siamrajplc.com", "eps_group_c@siamrajplc.com", "eps_group_d@siamrajplc.com", "eps_group_r@siamrajplc.com"]
    ccs = ["nussara@siamrajplc.com", "udomlak@siamrajplc.com", "naphon@siamrajplc.com", "Thanyathon@siamrajplc.com"]
    
    msg = EmailMessage()
    msg["Subject"] = "Dashboard สรุปโครงการ BOI และแนวโน้มกลุ่มอุตสาหกรรม ประจำเดือน ตุลาคม 2569"
    msg["From"] = creds.get("from", creds['user'] + "@siamrajplc.com")
    msg["To"] = ", ".join(recipients)
    msg["Cc"] = ", ".join(ccs)
    msg.set_content(html_content, subtype='html')
    
    try:
        imap = imaplib.IMAP4_SSL("mail.siamrajplc.com")
        imap.login(creds['user'], creds['password'])
        imap.append("Sent", None, imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        imap.logout()
        print("Saved to Sent folder with correct headers.")
    except Exception as e:
        print(f"Failed to save to Sent: {e}")

if __name__ == "__main__":
    save_sent()
