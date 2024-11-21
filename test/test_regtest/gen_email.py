import os
import argparse
import smtplib
from Dtest.regtest.processRegtestData import sendEmailForRegtest


class DummySMTP:
    def connect(self):
        pass

    def close(self):
        pass

    def sendmail(self, header_from, header_to, message):
        print(f"FROM: {header_from}")
        print(f"TO: {header_to}")
        print(message)


smtplib.SMTP = DummySMTP

parser = argparse.ArgumentParser()
parser.add_argument("--format", choices=("plain", "html"))

args = parser.parse_args()
html = args.format == "html"

sendEmailForRegtest(
    "test.h5",
    os.path.abspath("regtest.data-2024-04-22-06_05"),
    regtest_host="myhost",
    email_from="myfrom",
    email_to="myto",
    email_title="mytitle",
    html=html,
)
