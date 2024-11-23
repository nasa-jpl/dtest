#!/usr/bin/env python

import os, sys
import stat
import time, datetime
import pandas as pd
import h5py
import numpy as np
from tqdm import tqdm
import copy

sys.path.append("/home/dlab3/FROM-DLAB/repo/RegtestWebsite/RegtestWebsite/regtestsite")
from regtest.utils import Dinit
from regtest.management import yamDb
import glob, re

from timeit import default_timer

import click

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from Dtest.regtest.queryHDF5 import (
    _getFailedTests,
    _findLastPassed,
    _testStats,
    _getPrevLogFilename,
)

key_modules_filename = "/home/dartsfn/lib/key_modules.py"


##########################################
# API Endpoints
##########################################


# sends out an email for a given regtest_filename
#   hdf5_filename - the filename of the HDF5 to get data from
#   regtest_filename - the filename of the regtest data file to send an email out for
#   regtest_host - the host machine that ran the regtests
#   email_from - the email address to send the email from
#   email_to - the email address to send the email to
#   html - if true, send the email in HTML format, otherwise send the email in plain text format
def sendEmailForRegtest(
    hdf5_filename,
    regtest_filename,
    regtest_host,
    email_from,
    email_to,
    email_title,
    html,
):
    # now format the email
    if html:
        try:
            email_msg = _getEmailMsgHTML(hdf5_filename, regtest_filename, regtest_host, email_title)
        except Exception as e:
            # create the email msg
            email_msg = MIMEMultipart("alternative")
            if email_title == "":
                email_title = (
                    regtest_filename.split("/")[-2]
                    + "  "
                    + regtest_filename.split("/")[-1].replace("regtest.data-", "")
                )
            email_msg["Subject"] = " ".join(["[regtest] ERROR", email_title, "HTML"])

            import traceback

            email_text = f"The following error occurred when generating the email:\n\t{traceback.format_exc()}"

            email_msg.attach(MIMEText(email_text, "html"))

        # write the regtest.html file to teh same directory the regtest came from
        # html_file_name = regtest_filename.replace('data', 'html')
        # with open(html_file_name, 'w') as f:
        #     f.write(email_msg.as_string())
    else:
        try:
            email_msg = _getEmailMsgText(hdf5_filename, regtest_filename, regtest_host, email_title)
        except Exception as e:
            # make the email msg
            if email_title == "":
                email_title = (
                    regtest_filename.split("/")[-2]
                    + "  "
                    + regtest_filename.split("/")[-1].replace("regtest.data-", "")
                )
            import traceback

            email_text = f"The following error occurred when generating the email:\n\t{traceback.format_exc()}"

            email_msg = MIMEText(email_text, "plain")
            email_msg["Subject"] = " ".join(["[regtest] ERROR", email_title, "Plain Text"])

        # write the regtest.mail file to the same directory the regtest came from
        mail_file_name = regtest_filename.replace("data", "mail")
        with open(mail_file_name, "w") as f:
            f.write(email_msg.as_string())

    # set from and to fields based on command line options
    email_msg["From"] = email_from
    email_msg["To"] = email_to

    # send the email
    s = smtplib.SMTP()
    s.connect()
    s.sendmail(email_msg["From"], email_msg["To"], email_msg.as_string())
    s.close()
    return


# writes files to a HDF5 file
#   hdf5_filename - the filename of the HDF5 to write to
#   regtest_filenames - a list of regtest data filenames whose info we append to the HDF5 file
#   append - if true, append the data, otherwise overwrite the entire file
#   from_date - the date to filter from, all files after the date will be considered
#   to_date - the date to filter to, all files before the date will be considered
#   max_to_append - the max number of files to append to the file
def writeFilesToHDF5(
    hdf5_filename,
    regtest_filenames,
    append,
    from_date="",
    to_date="",
    max_to_append=100000,
):
    # filter the regtest_filenames based on the from_date and to_date
    if from_date != "":
        from_datetime = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        regtest_filenames = [filename for filename in regtest_filenames if _getFileDate(filename) > from_datetime]
    if to_date != "":
        to_datetime = datetime.datetime.strptime(to_date, "%Y-%m-%d")
        regtest_filenames = [filename for filename in regtest_filenames if _getFileDate(filename) < to_datetime]

    # filter the filenames to make sure that only filenames that fit the regtest.data-YYYY-MM-DD-mm-ss format
    regtest_filenames = [
        filename
        for filename in regtest_filenames
        if re.search(r"regtest\.data-\d{4}-\d{2}-\d{2}-\d{2}_\d{2}$", filename)
    ]

    # set the HDF5 file open mode depending if we want to append or overwrite
    open_mode = "a" if append else "w"

    print(regtest_filenames)

    # open the HDF5 file
    with h5py.File(hdf5_filename, open_mode, libver="latest") as store:
        # if there number of files to append is not limited, simply loop through and add all of them
        if len(regtest_filenames) <= max_to_append:
            for regtest_filename in tqdm(regtest_filenames):
                _parseFile(store, regtest_filename, append)
        # otherwise, only add up to max_to_append new files
        else:
            file_ind = 0
            # tqdm around the number to append so that we get an accurate progress bar
            for _ in tqdm(range(max_to_append)):
                # add one file per for loop iteration - must find the next file that we haven't added yet
                while not _parseFile(store, regtest_filenames[file_ind], append):
                    file_ind += 1


##########################################
# Helper Functions
##########################################


def _getEmailMsgHTML(hdf5_filename, regtest_filename, regtest_host="Unknown", email_title=""):
    # html strings that will be formatted later
    html_start = """\
    <html>
    <head>
    <style type="text/css">
    html {
        background-color: #AAA;
    }
    body {
        font-family:arial, helvetica, courier, sans-serif;
        font-size:10pt;
        background-color: #EEF;
        margin: 20px;
        padding: 20px;
        border: 1px solid #99F;
    }
    h1, h2, h3 {
        margin-top: 0;
        padding-top: 0;
    }
    h1 {
        font-size: 150%;
    }
    h2 {
        font-size: 130%;
        margin-top: 10px;
    }
    h3 {
        font-size: 110%;
    }
    table {
        cellspacing: 0;
        cellpadding: 2;
        background-color: black;
    }
    th, td {
        padding-left: 4px;
        padding-right: 4px;
        background-color: #EEF;
        text-align: center;
    }
    th {
        font-size: 120%;
        background-color: #BBF;
        vertical-align: bottom;
    }
    th#left, td#left {
        text-align: left;
    }
    th#right, td#right {
        text-align: right;
    }
    td a {
        color: blue;
        text-decoration: none;
    }
    td a:visited { color: blue; }
    td a:hover { color: blue; text-decoration: underline; }
    tr.summary td {
        background-color: #DDF;
    }
    div.genDate {
        margin-top: 4px;
        font-size: %80;
        font-style: italic;
    }
    </style>
    </head>
    <body>
    """

    html_table_top = """\
        <h1>{caption}</h1>
        <table>
        <thead>
        <tr class="coltitles">
            <th id="left">MODULE</th> <th>TOTAL</th> <th>FAILURES (+-)</th> <th id="right">PERCENT</th> <th id="right">DURATION</th> <th id="right">OWNER</th>
        </tr>
        </thead>
        <tbody>
    """

    html_line = """\
    <tr><td id="left">{module}</td> <td>{total}</td> <td>{failed}</td> <td id="right">{percent}</td> <td id="right">{duration}</td> <td id="right">{owner}</td></tr>
    """

    html_summary = """\
    <tr class="summary"><td id="right">{module}</td> <td>{total}</td> <td>{failed}</td> <td id="right">{percent}</td> <td></td></tr>
    """

    html_table_end = """\
        </tbody>
        </table>
    """

    html_test_table_top = """\
        <h1>{caption}</h1>
        <p><b>*</b>: Asterisk next to failed test name means that it timed out.
        <p><b>#</b>: Pound sign next to failed test name means critical failure (run failure).</p>
        <p><b>Last 10</b>: Last 10 regtest runs -- \".\" means fail, \"*\" means timed out, \"P\" means pass.</p>
        <p><b>Last passed</b>: The last time the test passed. If blank, could not find the last time test passed.</p>
        <table>
        <thead>
        <tr class="coltitles">
            <th id="left">MODULE (Release)</th> <th id="left">TEST</th> {last10_col_header} <th id="left">LAST PASSED (Release)</th>
        </tr>
        </thead>
        <tbody>
    """
    html_test_table_row = """\
    <tr><td id="left">{module}</td> <td id="left">{test}</td> {last10_cols} <td id="left">{lastpassed}</td></tr>
    """

    html_end = """\
    <div class="genDate">Generated: {date}</div>
    </body>
    </html>
    """

    # make sure that there are multiple parts to the filename
    # we need the folder that the regtest data file is in to get the sandbox name
    filename_parts = regtest_filename.split("/")
    if len(filename_parts) < 2:
        raise Exception("No sandbox could be inferred from regtest data filename!")

    # sandbox group name to add for this file
    # will be the folder that the regtest file is in
    sandbox = filename_parts[-2]

    with h5py.File(hdf5_filename, libver="latest") as f:
        # make sure sandbox is in the HDF5 file
        if sandbox not in list(f.keys()):
            raise Exception("Sandbox not found in HDF5 store!")

        # sort the file keys in reverse chronological order (newest entries first)
        sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

        # store the current file key as well as the past one to compare
        regtest_file_key = None
        last_regtest_file_key = None

        # find the file group that corresponds to the regtest filename passed in
        for i, file_key in enumerate(sorted_file_keys):
            if f[sandbox][file_key].attrs["filename"] == regtest_filename:
                regtest_file_key = file_key

                if i + 1 < len(sorted_file_keys):
                    last_regtest_file_key = sorted_file_keys[i + 1]

                # now find the last file that's from the same sandbox like
                # sandbox_name = regtest_filename.split("/")[-2]

                # for j, past_file_key in enumerate(sorted_file_keys[i + 1 :]):
                #     past_sandbox_name = f[sandbox][past_file_key].attrs["filename"].split("/")[-2]

                #     if past_sandbox_name == sandbox_name:
                #         last_regtest_file_key = past_file_key
                #         break

                break

        # if the last_regtest_file_key is None, then we have a new file
        # check if there is an older log that just got rotated
        # the last log will have the filename <filename>.1.h5
        if last_regtest_file_key is None:
            last_hdf5_path = _getPrevLogFilename(f.filename)
            if os.path.exists(last_hdf5_path):
                last_f = h5py.File(last_hdf5_path, libver="latest")
                # sort the file keys in reverse chronological order (newest entries first)
                sorted_last_file_keys = sorted(list(last_f[sandbox].keys()), reverse=True)
                last_regtest_file_key = sorted_last_file_keys[0]

            else:
                last_f = f

        else:
            last_f = f

        if regtest_file_key is None:
            raise Exception(f"Entry for {regtest_filename} not found in HDF5 file {hdf5_filename}")

        # get the datetime associated with the regtest file key
        # used in queries
        datetime_obj = datetime.datetime.strptime(regtest_file_key, "%Y-%m-%d-%H_%M")

        # get a reference to the file group for the regtest filename
        file_group = f[sandbox][regtest_file_key]
        last_file_group = None if last_regtest_file_key is None else last_f[sandbox][last_regtest_file_key]

        # create the html string - start with the start and the beginning of the table
        html = html_start

        # get the module rows, sorted by failures and then by module name
        sorted_module_rows = _getModuleRows(f, sandbox, regtest_file_key, last_f, last_regtest_file_key)

        # get primary modules by using exec()
        # has primary modules listed in a variable called 'key_modules'
        exec(
            compile(open(key_modules_filename).read(), key_modules_filename, "exec"),
            globals(),
        )

        # make separate lists for broken primary modules and broken nonprimary modules
        broken_primary_modules_rows = [
            row for row in sorted_module_rows if row["module"] in key_modules and row["failed"][0] != "0"
        ]
        broken_nonprimary_modules_rows = [
            row for row in sorted_module_rows if row["module"] not in key_modules and row["failed"][0] != "0"
        ]

        # add a summary section at the top
        html += f"<h1>Summary</h1><p><b>Regtest file:</b> {regtest_filename}</p><p><b>Successes:</b> {file_group.attrs['num_successful']}/{file_group.attrs['num_tests']} ({100*file_group.attrs['num_successful']/file_group.attrs['num_tests']:.2f}%)</p>"
        html += (
            f"<p><b>Last regtest file:</b> {None if last_file_group is None else last_file_group.attrs['filename']}</p>"
        )
        last_percent_successful_str = (
            ""
            if last_file_group is None
            else f"{(100*last_file_group.attrs['num_successful']/last_file_group.attrs['num_tests']):.2f}"
        )
        html += f"<p><b>Last run successes:</b> {None if last_file_group is None else last_file_group.attrs['num_successful']}/{None if last_file_group is None else last_file_group.attrs['num_tests']} ({last_percent_successful_str}%)</p>"
        html += f"<p><b>Host machine:</b> {regtest_host}"
        html += "<hr>"

        # table for primary modules
        html += html_table_top.format(caption="Broken Primary Modules (sorted by number of failures)")
        for row in broken_primary_modules_rows:
            html += html_line.format(
                module=row["module"],
                total=row["total"],
                failed=row["failed"],
                percent=row["percent"],
                duration=row["elapsed_time"],
                owner=row["owner"],
            )
        html += html_table_end + "\n<br><hr><br>\n"

        # table for broken nonprimary modules
        html += html_table_top.format(caption="Broken Other Modules (sorted by number of failures)")
        for row in broken_nonprimary_modules_rows:
            html += html_line.format(
                module=row["module"],
                total=row["total"],
                failed=row["failed"],
                percent=row["percent"],
                duration=row["elapsed_time"],
                owner=row["owner"],
            )
        html += html_table_end + "\n<br><hr><br>\n"

        # table for all modules
        html += html_table_top.format(caption="All Modules (sorted by number of failures)")
        for row in sorted_module_rows:
            html += html_line.format(
                module=row["module"],
                total=row["total"],
                failed=row["failed"],
                percent=row["percent"],
                duration=row["elapsed_time"],
                owner=row["owner"],
            )
        html += html_summary.format(
            module="<b>OVERALL:</b>",
            total=file_group.attrs["num_tests"],
            success=file_group.attrs["num_successful"],
            failed=file_group.attrs["num_tests"] - file_group.attrs["num_successful"],
            percent=f"{100*file_group.attrs['num_successful']/file_group.attrs['num_tests']:.2f}",
        )
        html += html_table_end + "\n<br><hr><br>\n"

        # table for failed tests
        failed_test_infos = _getFailedTests(f, sandbox, regtest_file_key)

        last10_col_header = " ".join(f"<th>LAST 10 ({sandbox})" for sandbox in list(f.keys()))
        html += html_test_table_top.format(caption="Failed Tests", last10_col_header=last10_col_header)
        last_module_name = None

        for test_info in failed_test_infos:
            last10_strs = []
            for sbox in list(f.keys()):
                # get the last 10 runs for this test and print out a string representing it
                # P for pass, . for fail
                last10_infos = _testStats(f, sbox, test_info.module, test_info.name, 10, date=datetime_obj)

                def getInfoChar(test_info):
                    try:
                        if bool(test_info.timed_out):
                            return "*"
                        if int(test_info.num_runs_ok) < int(test_info.num_runs):
                            return "#"
                        if bool(test_info.passed):
                            return "P"
                    except Exception as e:
                        print(e)
                        return "."

                    return "."

                last10_str = "".join([getInfoChar(info) for info in last10_infos])
                if last10_str == "":
                    last10_str = "N/A"
                last10_strs.append(last10_str)

            last10_cols = " ".join(f"<td>{last10_str}</td>" for last10_str in last10_strs)

            # dont print FFFFFFF..., it's not necessary
            # if 'P' not in last10_str:
            #     last10_str = "All failed"

            # get the last time this test passed
            try:
                (_, lastpassed_info) = _findLastPassed(f, sandbox, test_info.module, test_info.name, date=datetime_obj)
                lastpassed_str = f"{str(lastpassed_info.start_time)[:-7]} ({lastpassed_info.module_release})"
            except Exception as e:
                print(e)
                lastpassed_str = ""

            try:
                asterisk_str = " *" if test_info.timed_out else ""
            except Exception as e:
                asterisk_str = ""

            try:
                critical_str = " #" if test_info.num_runs_ok < test_info.num_runs and asterisk_str == "" else ""
            except Exception as e:
                critical_str = ""

            # print(f"Runs:{test_info.num_runs_ok}/{test_info.num_runs}\tCmps:{test_info.num_cmps_ok}/{test_info.num_cmps}")
            module_str = (
                f"{test_info.module} ({test_info.module_release})" if test_info.module != last_module_name else ""
            )
            last_module_name = test_info.module
            # add a row for each failed test
            html += html_test_table_row.format(
                module=f"{module_str}",
                test=f"{test_info.name}{asterisk_str}{critical_str}",
                last10_cols=last10_cols,
                lastpassed=lastpassed_str,
            )

        html += html_table_end

        html += html_end.format(date=file_group.attrs["date_finished"])

        # create the email msg
        msg = MIMEMultipart("alternative")
        if email_title == "":
            email_title = (
                regtest_filename.split("/")[-2] + "  " + regtest_filename.split("/")[-1].replace("regtest.data-", "")
            )
        pass_str = f"{100*file_group.attrs['num_successful']/file_group.attrs['num_tests']:.2f}%/{file_group.attrs['num_tests']:04d}"
        msg["Subject"] = " ".join(["[regtest]", pass_str, email_title, "HTML"])

        msg.attach(MIMEText(html, "html"))

    return msg


def _getEmailMsgText(hdf5_filename, regtest_filename, regtest_host="Unknown", email_title=""):
    # make sure that there are multiple parts to the filename
    # we need the folder that the regtest data file is in to get the sandbox name
    filename_parts = regtest_filename.split("/")
    if len(filename_parts) < 2:
        raise Exception("No sandbox could be inferred from regtest data filename!")

    # sandbox group name to add for this file
    # will be the folder that the regtest file is in
    sandbox = filename_parts[-2]

    with h5py.File(hdf5_filename, libver="latest") as f:
        # make sure sandbox is in the HDF5 file
        if sandbox not in list(f.keys()):
            raise Exception("Sandbox not found in HDF5 store!")

        # sort the file keys in reverse chronological order (newest entries first)
        sorted_file_keys = sorted(list(f[sandbox].keys()), reverse=True)

        # store the current file key as well as the past one to compare
        regtest_file_key = None
        last_regtest_file_key = None

        # find the file group that corresponds to the regtest filename passed in
        for i, file_key in enumerate(sorted_file_keys):
            print(f[sandbox][file_key].attrs["filename"])
            if f[sandbox][file_key].attrs["filename"] == regtest_filename:
                regtest_file_key = file_key

                if i + 1 < len(sorted_file_keys):
                    last_regtest_file_key = sorted_file_keys[i + 1]

                # now find the last file that's from the same sandbox like
                # sandbox_name = regtest_filename.split("/")[-2]

                # for j, past_file_key in enumerate(sorted_file_keys[i + 1 :]):
                #     past_sandbox_name = f[sandbox][past_file_key].attrs["filename"].split("/")[-2]

                #     if past_sandbox_name == sandbox_name:
                #         last_regtest_file_key = past_file_key
                #         break

                break
        # if the last_regtest_file_key is None, then we have a new file
        # check if there is an older log that just got rotated
        # the last log will have the filename <filename>.1.h5
        if last_regtest_file_key is None:
            last_hdf5_path = _getPrevLogFilename(f.filename)
            if os.path.exists(last_hdf5_path):
                last_f = h5py.File(last_hdf5_path, libver="latest")
                # sort the file keys in reverse chronological order (newest entries first)
                sorted_last_file_keys = sorted(list(last_f[sandbox].keys()), reverse=True)
                last_regtest_file_key = sorted_last_file_keys[0]

            else:
                last_f = f

        else:
            last_f = f

        if regtest_file_key is None:
            raise Exception(f"Entry for {regtest_filename} not found in HDF5 file {hdf5_filename}")

        # get the datetime associated with the regtest file key
        # used in queries
        datetime_obj = datetime.datetime.strptime(regtest_file_key, "%Y-%m-%d-%H_%M")

        # get a reference to the file group for the regtest filename
        file_group = f[sandbox][regtest_file_key]
        last_file_group = None if last_regtest_file_key is None else f[sandbox][last_regtest_file_key]

        # create the html string - start with the start and the beginning of the table
        if email_title == "":
            email_title = (
                regtest_filename.split("/")[-2] + "  " + regtest_filename.split("/")[-1].replace("regtest.data-", "")
            )
        text = email_title + "\n\n"

        # get the module rows, sorted by failures and then by module name
        sorted_module_rows = _getModuleRows(f, sandbox, regtest_file_key, last_f, last_regtest_file_key)

        # get primary modules by using exec()
        # has primary modules listed in a variable called 'key_modules'
        # key_modules_filename = "/home/atbe/sim-utils/lib/key_modules.py"
        exec(
            compile(open(key_modules_filename).read(), key_modules_filename, "exec"),
            globals(),
        )

        # make separate lists for broken primary modules and broken nonprimary modules, still sorted by number of failures
        broken_primary_modules_rows = [
            row for row in sorted_module_rows if row["module"] in key_modules and row["failed"][0] != "0"
        ]
        broken_nonprimary_modules_rows = [
            row for row in sorted_module_rows if row["module"] not in key_modules and row["failed"][0] != "0"
        ]

        # add a summary section at the top
        text += f"Summary:\nRegtest file: {regtest_filename}\nSuccesses: {file_group.attrs['num_successful']}/{file_group.attrs['num_tests']} ({100*file_group.attrs['num_successful']/file_group.attrs['num_tests']:.2f}%)\n"
        text += f"Last regtest file: {None if last_file_group is None else last_file_group.attrs['filename']}\n"
        last_percent_successful_str = (
            ""
            if last_file_group is None
            else f"{(100*last_file_group.attrs['num_successful']/last_file_group.attrs['num_tests']):.2f}"
        )
        text += f"Last run successes: {None if last_file_group is None else last_file_group.attrs['num_successful']}/{None if last_file_group is None else last_file_group.attrs['num_tests']} ({last_percent_successful_str}%)\n"
        text += f"Host machine: {regtest_host}\n"
        text += "-------------------------\n"

        # primary broken modules table
        text += "Primary Broken Modules (sorted by number of failures):\n"
        text += _getModuleTableText(broken_primary_modules_rows)
        # print out the primary modules
        text += f"\n\nPrimary Modules: {', '.join(key_modules)}\n"

        # nonprimary borken modules table
        text += "\n\nOther Broken Modules (sorted by number of failures):\n"
        text += _getModuleTableText(broken_nonprimary_modules_rows)

        # all modules table
        text += "\n\nAll Modules (sorted by number of failures):\n"
        text += _getModuleTableText(sorted_module_rows)
        text += ("-" * 100) + "\n"
        # add summary
        text += f"\tOVERALL:\t\t{file_group.attrs['num_tests']}\t{file_group.attrs['num_tests']-file_group.attrs['num_successful']}\t\t{100*file_group.attrs['num_successful']/file_group.attrs['num_tests']:.2f}\n"

        # table for failed tests
        failed_test_infos = _getFailedTests(f, sandbox, regtest_file_key)
        text += "\n\nFailed Tests:\n"
        text += "\tAsterisk (*) next to failed test name means that it timed out.\n"
        text += "\tPound symbol (#) next to failed test name means critical failure (run failure)."
        text += '\tLast 10: Last 10 regtest runs -- "." means fail, "*" means timed out, "P" means pass.\n'
        text += "\tLast passed: The last time the test passed. If blank, could not find the last time test passed.\n"

        last10_col_header = "\t".join(f"LAST 10 ({sandbox})" for sandbox in list(f.keys()))
        text += ("=" * 100) + "\n"
        text += f"MODULE (Release)\t\t\tTEST\t\t\t\t\t\t\t\t{last10_col_header}\t\tLAST PASSED (Release)\n"
        text += ("=" * 100) + "\n"

        last_module_name = None
        for test_info in failed_test_infos:
            # get the last 10 runs for this test and print out a string representing it
            # P for pass, . for fail
            last10_strs = []
            for sbox in list(f.keys()):
                last10_infos = _testStats(f, sbox, test_info.module, test_info.name, 10, date=datetime_obj)

                def getInfoChar(test_info):
                    try:
                        if bool(test_info.timed_out):
                            return "*"
                        if int(test_info.num_runs_ok) < int(test_info.num_runs):
                            return "#"
                        if bool(test_info.passed):
                            return "P"
                    except Exception as e:
                        print(e)
                        return "."

                    return "."

                last10_str = "".join([getInfoChar(info) for info in last10_infos])
                if last10_str == "":
                    last10_str = "N/A"
                last10_strs.append(last10_str)

            last10_cols = "\t".join(f"{last10_str}" for last10_str in last10_strs)
            # dont print FFFFFFF..., it's not necessary
            # if 'P' not in last10_str:
            #     last10_str = "All failed"

            # get the last time this test passed
            try:
                (_, lastpassed_info) = _findLastPassed(f, sandbox, test_info.module, test_info.name, date=datetime_obj)
                lastpassed_str = f"{str(lastpassed_info.start_time)[:-7]} ({lastpassed_info.module_release})"
            except Exception as e:
                lastpassed_str = ""

            module_str = (
                f"{test_info.module} ({test_info.module_release})" if test_info.module != last_module_name else ""
            )
            last_module_name = test_info.module

            # get the spacing right
            module_spacing_str = "\t" * (3 - len(module_str) // 8)
            test_spacing_str = "\t" * (8 - len(test_info.name) // 8)

            try:
                asterisk_str = " *" if test_info.timed_out else ""
            except Exception as e:
                asterisk_str = ""

            try:
                critical_str = " #" if test_info.num_runs_ok < test_info.num_runs and asterisk_str == "" else ""
            except Exception as e:
                critical_str = ""

            text += f"{module_str}{module_spacing_str}{test_info.name}{asterisk_str}{critical_str}{test_spacing_str}{last10_cols}\t{lastpassed_str}\n"

        # make the email msg
        msg = MIMEText(text, "plain")
        pass_str = f"{100*file_group.attrs['num_successful']/file_group.attrs['num_tests']:.2f}%/{file_group.attrs['num_tests']:04d}"
        msg["Subject"] = " ".join(["[regtest]", pass_str, email_title, "Plain Text"])

    last_f.close()

    return msg


# formats a table given 'module rows', which have information pertaining to a specific module row
def _getModuleTableText(module_rows):
    # top of the table
    text = ("=" * 100) + "\n"
    text += "MODULE\t\t\t\t\t\tTOTAL\tFAILURES (+-)\tPERCENT\tDURATION\tOWNER\n"
    text += ("=" * 100) + "\n"

    # print a row for each module
    for module_row in module_rows:
        spacing_str = "\t" * (6 - len(module_row["module"]) // 8)
        text += f"{module_row['module']}{spacing_str}{module_row['total']}\t{module_row['failed']}\t\t{module_row['percent']}\t\t{module_row['elapsed_time']}\t\t{module_row['owner']}\n"

    return text


# gets the module rows for printing in the table given a regtest file key and the last regtest file key
# sorts the modules in order of failures
def _getModuleRows(f, sandbox, regtest_file_key, last_f, last_regtest_file_key):
    file_group = f[sandbox][regtest_file_key]
    last_file_group = None if last_regtest_file_key is None else last_f[sandbox][last_regtest_file_key]

    module_rows = []

    for module_name in list(file_group.keys()):
        # get number of tests and failed tests
        num_tests = file_group[module_name].attrs["num_tests"]
        success_tests = file_group[module_name].attrs["num_successful"]
        failed_tests = num_tests - success_tests
        if "elapsed_time" in file_group[module_name].attrs:
            # Use the cached total if it's available
            elapsed_time = file_group[module_name].attrs["elapsed_time"]
        else:
            elapsed_time = sum(float(t) for t in file_group[module_name]["elapsed_time"])

        # make sure the module exists in the last regtest run, could've been new this run
        if last_file_group is not None and module_name in list(last_file_group.keys()):
            # find the number of failed tests in this module in the last run
            last_failed_tests = (
                last_file_group[module_name].attrs["num_tests"] - last_file_group[module_name].attrs["num_successful"]
            )
        else:
            last_failed_tests = failed_tests

        # format the strings
        num_tests_str = f"{num_tests}"
        failed_tests_str = f"{failed_tests}"
        # if there was a difference in failed tests,
        if failed_tests - last_failed_tests != 0:
            plus_str = "+" if failed_tests - last_failed_tests > 0 else ""
            failed_tests_str += f" ({plus_str}{failed_tests - last_failed_tests})"

        percent_str = f"{100*success_tests / num_tests:.1f}"
        elapsed_time_str = "N/A" if elapsed_time is None else str(int(elapsed_time))

        owner_str = "TBD"

        module_rows.append(
            {
                "module": module_name,
                "total": num_tests_str,
                "failed": failed_tests_str,
                "percent": percent_str,
                "elapsed_time": elapsed_time_str,
                "owner": owner_str,
            }
        )

    # sort module rows based on failures
    def module_row_compare(mod_row1, mod_row2):
        mod_name1 = mod_row1["module"]
        mod_name2 = mod_row2["module"]

        module_dataset1 = file_group[mod_name1]
        module_dataset2 = file_group[mod_name2]

        num_failures1 = module_dataset1.attrs["num_tests"] - module_dataset1.attrs["num_successful"]
        num_failures2 = module_dataset2.attrs["num_tests"] - module_dataset2.attrs["num_successful"]

        # sort by number of module failures first - put highest failures first
        if num_failures1 != num_failures2:
            return num_failures2 - num_failures1
        # if number of failures are the same, then sort by module name
        else:
            if mod_name1 < mod_name2:
                return -1
            elif mod_name1 > mod_name2:
                return 1
            else:
                return 0

    # actually sort the module rows
    from functools import cmp_to_key

    sorted_module_rows = sorted(module_rows, key=cmp_to_key(module_row_compare))

    return sorted_module_rows


# returns the date the file was last edited
def _getFileDate(f):
    if not os.path.exists(f):
        raise Exception("File '%s' does not exist!" % f)
    fstats = os.stat(f)
    return datetime.datetime.fromtimestamp(fstats[stat.ST_CTIME])


def _parseFile(store, filename, append):

    # make sure that there are multiple parts to the filename
    # we need the folder that the regtest data file is in to get the sandbox name
    filename_parts = filename.split("/")
    if len(filename_parts) < 2:
        print("No sandbox could be inferred from regtest data filename!")
        return False

    # sandbox group name to add for this file
    # will be the folder that the regtest file is in
    sandbox_groupname = "/" + filename_parts[-2]

    # create the sandbox if it doesn't exist
    if sandbox_groupname[1:] not in list(store.keys()):
        sandbox_group = store.create_group(sandbox_groupname)
    # otherwise, get a reference to it
    else:
        sandbox_group = store[sandbox_groupname]

    # get a list of file keys sorted chronologically, latest to earliest
    sorted_file_keys = sorted(list(sandbox_group.keys()), reverse=True)

    # file group name to add for this file
    # group name will be the file name but with "regtest.data-" chopped off
    # i.e. /home/dlab3/repo/PKGBUILDS/.../regtest.data-2023-06-11-05_05 becomes /2023-06-11-05_05
    file_groupname = "/" + filename.split("/")[-1].replace("regtest.data-", "")

    # if append is True, check if key already exists
    # do this first thing before compiling the file
    if file_groupname[1:] in list(sandbox_group.keys()):
        return False

    # Parse and load the regtest data file
    sys.path.append(os.path.dirname(Dinit.__file__))
    try:
        exec(compile(open(filename).read(), filename, "exec"), globals())
    except Exception as e:
        print(f"Failed to fully extract data from {filename}")
        print(f"Error: {e}")
        return False

    # Check to make sure the regtest data got loaded
    try:
        regdata
    except NameError:
        print(f"Error parsing file {filename} (does not seem to be a regtest data file)!")
        return False

    # get a list of all the module objects
    modules = sorted(regdata.keys())

    # connect to releases database
    yam = yamDb.yamDb()

    ########################
    # FILE LEVEL INFO
    ########################

    # add a new group for the date associated with this file
    file_group = store.create_group(f"{sandbox_groupname}/{file_groupname}")

    # get a list of file keys earlier than this file, from latest to earliest
    earlier_sorted_file_keys = [file_key for file_key in sorted_file_keys if file_key < file_groupname[1:]]

    # get a list of file keys later than this file, from earliest to latest
    later_sorted_file_keys = list(
        reversed([file_key for file_key in sorted_file_keys if file_key > file_groupname[1:]])
    )

    # add metadata for the file group
    # date finished
    file_group.attrs["date_finished"] = str(_getFileDate(filename))

    # total number of tests and number of successes
    total_tests = 0
    successful_tests = 0
    for module in modules:
        for test in sorted(regdata[module]["tests"]):
            successful_tests += regdata[module]["tests"][test]["success"]
            total_tests += 1
    file_group.attrs["num_successful"] = successful_tests
    file_group.attrs["num_tests"] = total_tests

    # file name
    file_group.attrs["filename"] = filename

    # start time
    file_group.attrs["start_time"] = str(regdata[modules[0]]["start_time"])

    ##########################
    # MODULE LEVEL INFO
    ##########################
    for module in modules:

        # get a list of all tests in this module
        tests = sorted(regdata[module]["tests"])

        # total number of tests and number of successes
        total_module_tests = 0
        successful_module_tests = 0
        module_elapsed_time = 0.0
        for test in tests:
            successful_module_tests += regdata[module]["tests"][test]["success"]
            total_module_tests += 1
            module_elapsed_time += regdata[module]["tests"][test]["elapsed_time"]

        # h5py string type - needed for writing strings to HDF5
        # 300 characters should more than enough for longest test names
        utf8_type = h5py.string_dtype("utf-8", 300)

        # list of columns for each test
        test_dataset_columns = [
            "name",
            "passed",
            "num_runs_ok",
            "num_runs",
            "num_comparisons_ok",
            "num_comparisons",
            "start_time",
            "elapsed_time",
            "timed_out",
            "last_passed_file_key",
        ]

        # list of datatypes for each column
        test_dataset_types = [
            (utf8_type),  # name
            (bool),  # passed
            (int),  # num_runs_ok
            (int),  # num_runs
            (int),  # num_comparisons_ok
            (int),  # num_comparisons
            (utf8_type),  # start_time
            (utf8_type),  # elapsed_time
            (bool),  # timed_out
            (utf8_type),  # last passed file key
        ]

        # create the datatype for the numpy record array
        test_dataset_dt = np.dtype({"names": test_dataset_columns, "formats": test_dataset_types})

        # create the empty numpy record array
        # number of rows = number of tests
        test_dataset_arr = np.recarray((total_module_tests,), dtype=test_dataset_dt)

        for test_ind, test in enumerate(tests):

            ######################
            # TEST LEVEL INFO
            ######################

            # get actual data for this test
            test_data = regdata[module]["tests"][test]

            # whether or not the test passed
            passed = test_data["success"]

            # if not passed:
            #     print(f"{module} -- {test}")

            # how many successful runs and total runs
            (num_runs_ok, num_runs) = test_data["run"]
            # how many successful comparisons and total comparisons
            (num_cmps_ok, num_cmps) = test_data["cmp"]

            # start time for this test
            start_time = str(regdata[module]["start_time"])

            # elapsed time for this test to run as a string
            elapsed_time = str(test_data["elapsed_time"])

            # whether or not this test timed out
            timed_out = test_data["timed_out"]

            if not passed:
                last_passed_file_key = ""
                # find the last time this test passed
                for regtest_ind, file_key in enumerate(earlier_sorted_file_keys):
                    # break out of the loop once we've looked through 20 HDF5 entries
                    # can reasonably conclude that the test is new to this regtest run
                    # if regtest_ind > 20:
                    #     break

                    if module not in list(store[sandbox_groupname][file_key].keys()):
                        break

                    prev_module_dataset = store[sandbox_groupname][file_key][module]
                    # get the names of the tests - must decode the byte strings
                    prev_test_names = np.array([x.decode("ascii") for x in prev_module_dataset["name"]])

                    # check that the test exists
                    if test not in prev_test_names:
                        break

                    # test exists in this file key!
                    # get the row corresponding to the test -- squeeze to remove extra dimension
                    prev_test_row = prev_module_dataset[prev_test_names == test].squeeze()
                    # get the last passed info from the previous test, then break
                    last_passed_file_key = prev_test_row["last_passed_file_key"].astype("U30")
                    break

                # if the last_passed_file_key is still "", we need to check the last log file
                last_filename = _getPrevLogFilename(store.filename)
                if os.path.exists(last_filename):
                    with h5py.File(last_filename, "r") as last_f:
                        last_sorted_file_keys = sorted(last_f[sandbox_groupname].keys(), reverse=True)
                        last_file_key = last_sorted_file_keys[0]
                        if module in list(last_f[sandbox_groupname][last_file_key].keys()):
                            prev_module_dataset = last_f[sandbox_groupname][last_file_key][module]
                            # get the names of the tests - must decode the byte strings
                            prev_test_names = np.array([x.decode("ascii") for x in prev_module_dataset["name"]])
                            if test in prev_test_names:
                                # test exists in this file key!
                                # get the row corresponding to the test -- squeeze to remove extra dimension
                                prev_test_row = prev_module_dataset[prev_test_names == test].squeeze()
                                # get the last passed info from the previous test, then break
                                last_passed_file_key = prev_test_row["last_passed_file_key"].astype("U30")
            else:
                # if it passed, we have to update all regtest runs after this one for this test
                last_passed_file_key = file_groupname[1:]

                for file_key in later_sorted_file_keys:
                    if module not in list(store[sandbox_groupname][file_key].keys()):
                        continue
                    later_module_dataset = store[sandbox_groupname][file_key][module]
                    # get the names of the tests - must decode the byte strings
                    later_test_names = np.array([x.decode("ascii") for x in later_module_dataset["name"]])

                    # check that the test exists
                    if test not in later_test_names:
                        continue
                    # test exists in this file key!
                    # get the row corresponding to the test -- squeeze to remove extra dimension
                    later_test_row = later_module_dataset[later_test_names == test].squeeze()

                    later_last_passed_file_key = later_test_row["last_passed_file_key"].astype("U30")
                    later_passed = later_test_row["passed"]

                    # if the last_passed_file_key is empty or is an earlier test than this regtest, we must update it
                    # but only if passed is false
                    if not later_passed and (
                        later_last_passed_file_key == "" or file_groupname[1:] > later_last_passed_file_key
                    ):
                        # update the last_passed_file_key for the later file entry
                        # must update HDF5 file directly
                        new_row = copy.copy(later_test_row)
                        new_row["last_passed_file_key"] = file_groupname[1:]
                        store[sandbox_groupname][f"{file_key}/{module}"][list(later_test_names).index(test)] = new_row

                    elif later_passed:
                        # once we find that the test passed in the future, we do not to update anymore
                        break

            # assemble the row and put it into the record array
            row = (
                test,
                passed,
                num_runs_ok,
                num_runs,
                num_cmps_ok,
                num_cmps,
                start_time,
                elapsed_time,
                timed_out,
                last_passed_file_key,
            )
            test_dataset_arr[test_ind] = row

        # create the dataset
        module_dataset = file_group.create_dataset(
            module,
            (total_module_tests,),
            data=test_dataset_arr,
            compression="gzip",
            compression_opts=9,
        )

        # add metadata to the dataset
        # how many total tests and succesfuls tests
        module_dataset.attrs["num_successful"] = successful_module_tests
        module_dataset.attrs["num_tests"] = total_module_tests
        # approx. time to run the module's tests in serial
        module_dataset.attrs["elapsed_time"] = module_elapsed_time

        # module release at the time of this test
        end_time = regdata[module]["end_time"]
        release = yam.getModuleReleaseAfterInfo(module, end_time)["release"]

        module_dataset.attrs["release"] = release

        # start time for running this module
        start_time = regdata[module]["start_time"]
        module_dataset.attrs["start_time"] = str(start_time)

    return True
