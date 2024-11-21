import os, sys
import stat
import time, datetime
import pandas as pd

from timeit import default_timer

pd.set_option("io.hdf.default_format", "table")
from optparse import make_option

sys.path.append("/home/dlab3/FROM-DLAB/repo/RegtestWebsite/RegtestWebsite/regtestsite")
from regtest.utils import Dinit
from regtest.management import yamDb
import glob, re


def getFileDate(f):
    if not os.path.exists(f):
        raise Exception("File '%s' does not exist!" % f)
    fstats = os.stat(f)
    return datetime.datetime.fromtimestamp(fstats[stat.ST_CTIME])


RTYPE_CHOICES = {
    "daily": "D",
    "hourly": "H",
    "release": "R",
    "other": "O",
}


def main():
    start_time = default_timer()

    h5_file_name = sys.argv[1]
    # /home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC36/regtest.data-2022-09-04-15_05 (example path)
    test_file_path = sys.argv[2]
    print("running!")

    make_option("--file", dest="file", default=None, help="Full path to the file to digest"),

    make_option("--suite", dest="suite", default=None, help="The test suite"),

    make_option(
        "--rtype",
        dest="rtype",
        default="hourly",
        choices=list(RTYPE_CHOICES.keys()),
        help="Type of Regtest Set " + str(list(RTYPE_CHOICES.keys())),
    ),

    make_option(
        "--force", dest="force", action="store_true", default=False, help="Add a regtest set even if it exists"
    ),

    make_option("--exclude-tags", dest="exclude_tags", default=None, help="Add optional exclude tags"),

    make_option("--run-only", dest="run_only", default=None, help="Add optional run only tags"),
    help = "Add a RegtestSet item based on a sandbox regtest.data file"

    def appendData(hdf_name, dataframe):
        hdf = pd.HDFStore(h5_file_name)
        new_df = hdf[hdf_name].append(dataframe, ignore_index=True)
        if hdf_name == "proto_moduleset":
            hdf.put(hdf_name, new_df, format="table", data_columns=True, min_itemsize=50000)
        else:
            hdf.put(hdf_name, new_df, format="table", data_columns=True, min_itemsize=100)
        hdf.close()

    def handle(*args, **options):
        totalmodulesadded = 0
        file = options.get("file")
        # print(options)
        # print(file)

        # Get the dataframes from the h5 file
        hdf = pd.HDFStore(h5_file_name)
        # df_regtest = hdf['df_regtest']
        # df_regtestset = hdf['df_regtestset']
        # df_subregtest = hdf['df_subregtest']
        # df_proto_moduleset = hdf['df_proto_moduleset']

        suite = options.get("suite")

        # Get the type of regression test set
        rtype = options.get("rtype")

        exclude_tags = options.get("exclude_tags")
        run_only = options.get("run_only")

        # Make sure the user gave a file
        if not file:
            raise Exception("You must use specify the full path to a regtest.data file using the --file option.")
        if not os.path.exists(file):
            raise Exception("File '%s' does not exist!" % file)

        # Make sure the user gave a regtest set name
        set_name = None
        set_start_time = None
        set_finish_time = None

        # Construct the name
        if rtype == "release":
            # Get the start time of the regtest set sandbox
            set_start_time = getFileDate(os.path.join(os.path.dirname(file), "REGTESTSTART"))
            set_finish_time = getFileDate(os.path.join(os.path.dirname(file), "REGTESTEND"))

            # Construct the regtest set name
            set_name = os.path.split(os.path.dirname(file))[-1] + "-" + set_start_time.strftime("%Y-%m-%d")

        if rtype == "daily":
            # Get the start time of the regtest set sandbox
            set_start_time = getFileDate(os.path.join(os.path.dirname(file), "REGTESTSTART"))
            set_finish_time = getFileDate(os.path.join(os.path.dirname(file), "REGTESTEND"))

            # Construct the regtest set name
            set_name = os.path.split(os.path.dirname(file))[-1]

        # print("RTYPE HERE")
        print("rtype: " + rtype)
        print("this may take a few minutes")
        if rtype == "hourly":
            try:
                (year, month, day, h_m) = os.path.split(file)[-1].replace("regtest.data-", "").split("-")
                (hour, minute) = h_m.split("_")
            except:
                raise Exception("Error parsing regtest.data filename")

            # Get the start time of the regtest set sandbox
            set_start_time = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
            set_finish_time = set_start_time

            # Construct the regtest set name
            set_name = suite + "-" + os.path.split(file)[-1].replace("regtest.data-", "")
            # Manifest name with minutes globbed so nothing breaks
            manifest_file = "Manifest.config" + os.path.split(file)[-1].replace("regtest.data", "")[:-2] + "*"

        # # See if this regtest has already been added
        # if RegtestSet.objects.filter(name=set_name):
        #     print("Warning: Regtest Set %s exists!" % set_name)
        #     if not options.get('force'):
        #         raise Exception("Regtest set %s is already in the database!" % set_name)

        # Make sure a set name was given
        if not set_name:
            raise Exception("Unable to determine regtest set name!")

        # Parse the regtest data file
        sys.path.append(os.path.dirname(Dinit.__file__))
        exec(compile(open(file).read(), file, "exec"), globals())

        # Check to make sure the regtest data got loaded
        try:
            regdata
        except NameError:
            raise Exception("Error parsing file '%s' (does not seem to be a regtest data file)!" % file)

        # Get the module names
        modules = sorted(regdata.keys())
        # `testing`
        # print(regdata.keys())

        # Check the modules to find out when the first and last module completed
        start_time = datetime.datetime(3000, 1, 1, 0, 0, 0)
        end_time = datetime.datetime(2000, 1, 1, 0, 0, 0)
        for mod in modules:
            if regdata[mod]["end_time"] > end_time:
                end_time = regdata[mod]["end_time"]
            if regdata[mod]["end_time"] < start_time:
                start_time = regdata[mod]["end_time"]

        # Make sure we have times for the RegtestSet
        if not set_start_time:
            set_start_time = start_time
        if not set_finish_time:
            set_finish_time = set_start_time

        # Figure out the type
        set_type = rtype.upper()[0:1]

        # Check that at least 20% of tests have passed before adding to database
        total = 0
        success = 0
        for module in modules:
            for test in sorted(regdata[module]["tests"]):
                success += regdata[module]["tests"][test]["success"]
                total += 1
        if (
            float(success) / float(total) < 0.2
        ):  # consider rolling this up into a variable then storing it (reduce live load)
            raise Exception("Less than 20% of tests have passed. We will not be adding this test to the database.")

        # try:
        # print("MODULES")
        # print(modules)
        for mod in modules:
            # print("REGTESTSET_DATA")
            # if regdata[mod]['top_test_dir']:
            #     sandbox_info = regdata[mod]['top_test_dir'][0:regdata[mod]['top_test_dir'].find('src')-1]
            #     break
            sandbox_info = regdata[mod]["top_test_dir"][0 : regdata[mod]["top_test_dir"].find("src") - 1]
            columns = [
                "name",
                "suite",
                "start_time",
                "finsh_time",
                "num_tests",
                "num_tests_ok",
                "set_type",
                "sandbox_info",
                "exclude_tags",
                "run_only",
            ]
            regtestset_data = {
                "name": set_name,
                "suite": suite,
                "start_time": set_start_time,
                "finish_time": set_finish_time,
                "num_tests": total,
                "num_tests_ok": success,
                "set_type": set_type,
                "sandbox_info": sandbox_info,
                "exclude_tags": exclude_tags,
                "run_only": run_only,
            }
            try:
                df_regtestset_curr
            except NameError:
                df_regtestset_curr = pd.DataFrame([regtestset_data], columns=columns)
            else:
                break
                df_new_row = pd.DataFrame([regtestset_data], columns=columns)
                df_regtestset_curr = df_regtestset_curr.append(df_new_row, ignore_index=True)
                # appendData("regtestset", regtestset_data, columns)

            curr_regtestset_id = len(df_regtestset_curr) + len(hdf["regtestset"]) - 1
        # except:
        #     print("REGTESTSET_DATA")
        #     columns = ['name', 'suite', 'start_time', 'finsh_time', 'num_tests',
        #                    'num_tests_ok', 'set_type', 'sandbox_info', 'exclude_tags', 'run_only']
        #     regtestset_data = {
        #         'name': set_name, 'suite': suite, 'start_time': set_start_time, 'finish_time': set_finish_time,
        #         'num_tests': total, 'num_tests_ok': success, 'set_type': set_type, 'sandbox_info': sandbox_info,
        #         'exclude_tags': exclude_tags, 'run_only': run_only
        #     }
        #     try:
        #         df_regtestset_curr
        #     except NameError:
        #         df_regtestset_curr = pd.DataFrame(regtestset_data, columns=columns, index=[0])
        #     else:
        #         df_new_row = pd.DataFrame(regtestset_data, columns=columns, index=[0])
        #         df_regtestset_curr = df_regtestset_curr.append(df_new_row)
        # appendData("regtestset", regtestset_data, columns)

        # Add tests for all modules. connect to releases database
        yam = yamDb.yamDb()

        # temp storage for the modules (name X total X success X stalled)
        # otherwise this will have to be processed more than once (not good)
        for module in modules:  # can use this to also populate module_set (naming it mod_set() )

            # Module info
            module_data = {"name": module, "maintainer_id": 2}
            columns = ["name", "maintainer_id"]
            curr_module_id = len(hdf["module"]) - 1
            if module_data["name"] not in hdf["module"]["name"].values:
                try:
                    df_module_curr
                except NameError:
                    df_module_curr = pd.DataFrame([module_data], columns=columns)
                else:
                    df_new_row = pd.DataFrame([module_data], columns=columns)
                    df_module_curr = df_module_curr.append(df_new_row, ignore_index=True)
                curr_module_id = len(df_module_curr) + len(hdf["module"]) - 1

            release = yam.getModuleReleaseAfterInfo(module, end_time)["release"]
            # initialize the data for module set (modset_db):
            m_total = 0
            m_success = 0
            m_stalled = 0
            m_simtime = 0
            # need to make two lists for each module: a list of passes, and a list of failures then convert into comma separated strings
            passedtestslist = []
            failedtestslist = []

            # Process each test
            for test in sorted(regdata[module]["tests"]):
                # `tdata=testdata
                tdata = regdata[module]["tests"][test]
                m_total = m_total + 1  # this is a basic incrementation; this goes to the module set

                test_start_time = regdata[module]["start_time"]
                test_finish_time = regdata[module]["end_time"]
                if "start_time" in tdata:
                    test_start_time = tdata["start_time"]
                if "end_time" in tdata:
                    test_finish_time = tdata["end_time"]

                tdata = regdata[module]["tests"][test]  # this is called twice for some reason
                passed = tdata["success"]
                m_success = m_success + passed  # in regtest table, passed is 0 or 1; this goes to the module set

                # print("_______________________________________")
                # print("TESTING DATA OUTPUT")
                # print(tdata)
                (num_runs_ok, num_runs) = tdata["run"]
                (num_val_ok, num_val) = (0, 0)  # FIX# tdata['val']
                (num_cmp_ok, num_cmp) = tdata["cmp"]
                # print(num_cmp_ok)
                # print(num_cmp)
                test_hostname = ""

                test_elapsed_time = tdata["elapsed_time"]
                m_simtime = m_simtime + test_elapsed_time  # this goes to the module set

                test_timed_out = tdata["timed_out"]
                m_stalled = m_stalled + test_timed_out  # this goes to the module set

                if passed:
                    passedtestslist.append(test)
                    # print("passed:" + test)
                else:
                    # append single star for validation failure ((num_runs != num_runs_ok) or () )
                    # failed tests have stars *'s
                    if num_cmp == num_cmp_ok:
                        failedtestslist.append(test + "*")
                        # print(test + "failed comparison")
                    elif test_timed_out:
                        failedtestslist.append(test + "**")
                        # print(test + " timed out!!")
                    else:
                        failedtestslist.append(test)
                        # print("failed: " + test)
                regtest_data = {
                    "name": test,
                    "passed": passed,
                    "num_runs": num_runs,
                    "num_runs_ok": num_runs_ok,
                    "num_comparisons": num_cmp,
                    "num_comparisons_ok": num_cmp_ok,
                    "num_validations": num_val,
                    "num_validations_ok": num_val_ok,
                    "start_time": test_start_time,
                    "finish_time": test_finish_time,
                    "hostname": test_hostname,
                    "module_id": curr_module_id,
                    "module_release": release,
                    "elapsed_time": test_elapsed_time,
                    "timed_out": test_timed_out,
                    "regtest_set_id": curr_regtestset_id,
                }
                # print("REGTEST_DATA")
                columns = [
                    "name",
                    "passed",
                    "num_runs",
                    "num_runs_ok",
                    "num_comparisons",
                    "num_comparisons_ok",
                    "num_validations",
                    "num_validations_ok",
                    "module_release",
                    "start_time",
                    "finish_time",
                    "hostname",
                    "elapsed_time",
                    "timed_out",
                    "module_id",
                    "regtest_set_id",
                ]
                if len(regtest_data["name"]) > 100:
                    regtest_data["name"] = regtest_data["name"][:99]
                try:
                    df_regtest_curr
                except NameError:
                    df_regtest_curr = pd.DataFrame([regtest_data], columns=columns)
                else:
                    df_new_row = pd.DataFrame([regtest_data], columns=columns)
                    df_regtest_curr = df_regtest_curr.append(df_new_row, ignore_index=True)
                curr_regtest_id = len(df_regtest_curr) + len(hdf["regtest"]) - 1
                # appendData("regtest", df_regtest_curr)
                # df_new_row.astype({'module_id':'int64', 'regtest_set_id':'int64'})
                # print("NEW DTYPES")
                # print(df_new_row.dtypes)
                # print("CURR DTYPES")
                # print(hdf['testput3'].dtypes)
                # print(df_new_row)
                # print(hdf['testput3'])
                # print(df_new_row['module_release'][0])

                # do the subtests for each test
                try:
                    for sub_tests in regdata[module]["tests"][test]["sub_tests"]:
                        sub_test_name = sub_tests
                        sub_test_completion_status = regdata[module]["tests"][test]["sub_tests"][sub_test_name][
                            "completion_status"
                        ]
                        sub_test_return_code = str(
                            regdata[module]["tests"][test]["sub_tests"][sub_test_name]["return_code"]
                        )
                        sub_test_type = "T"

                        columns = ["name", "completion_status", "return_code", "set_type", "regtest_id"]
                        sub_test_completion_status = 1 if sub_test_completion_status == True else 0
                        subregtest_data = {
                            "name": sub_test_name,
                            "completion_status": sub_test_completion_status,
                            "return_code": sub_test_return_code,
                            "set_type": sub_test_type,
                            "regtest_id": curr_regtest_id,
                        }
                        # print("SUBREGTEST_DATA")
                        if len(subregtest_data["name"]) > 100:
                            subregtest_data["name"] = subregtest_data["name"][:99]
                        try:
                            df_subregtest_curr
                        except NameError:
                            df_subregtest_curr = pd.DataFrame([subregtest_data], columns=columns)
                        else:
                            df_new_row = pd.DataFrame([subregtest_data], columns=columns)
                            df_subregtest_curr = df_subregtest_curr.append(df_new_row, ignore_index=True)
                        # print("NEW DTYPES")
                        # print(df_new_row.dtypes)
                        # print("CURR DTYPES")
                        # print(hdf['subregtest'].dtypes)
                        # print(df_new_row)
                        # print(sub_test_db)

                    for sub_cmps in regdata[module]["tests"][test]["sub_cmps"]:
                        sub_cmp_name = sub_cmps
                        sub_cmp_completion_status = regdata[module]["tests"][test]["sub_cmps"][sub_cmp_name][
                            "completion_status"
                        ]
                        sub_cmp_return_code = str(
                            regdata[module]["tests"][test]["sub_cmps"][sub_cmp_name]["return_code"]
                        )
                        sub_cmp_type = "C"
                        sub_cmp_completion_status = 1 if sub_cmp_completion_status == True else 0
                        columns = ["name", "completion_status", "return_code", "set_type", "regtest_id"]
                        subregtest_data = {
                            "name": sub_test_name,
                            "completion_status": sub_cmp_completion_status,
                            "return_code": sub_cmp_return_code,
                            "set_type": sub_cmp_type,
                            "regtest_id": curr_regtest_id,
                        }
                        # print("SUBREGTEST_CMP_DATA")
                        # print(subregtest_data)
                        if len(subregtest_data["name"]) > 100:
                            subregtest_data["name"] = subregtest_data["name"][:99]
                        try:
                            df_subregtest_curr
                        except NameError:
                            df_subregtest_curr = pd.DataFrame([subregtest_data], columns=columns)
                        else:
                            df_new_row = pd.DataFrame([subregtest_data], columns=columns)
                            df_subregtest_curr = df_subregtest_curr.append(df_new_row, ignore_index=True)

                except:
                    print("No subtests for this module.")
            # pump module info into modset_db
            # test data:
            # m_total=0
            # m_success=0
            # m_stalled=0
            # m_simtime=0

            passedtestsstring = ",\n".join(str(x) for x in passedtestslist)
            failedtestsstring = ",\n".join(str(x) for x in failedtestslist)
            proto_moduleset_data = {
                "proto_release": release,
                "proto_total": m_total,
                "proto_success": m_success,
                "proto_timedout": m_stalled,
                "proto_simtime": m_simtime,
                "proto_passedtests": passedtestsstring,
                "proto_failedtests": failedtestsstring,
                "proto_module_id": curr_module_id,
                "proto_regtest_set_id": curr_regtestset_id,
            }
            columns = [
                "proto_release",
                "proto_total",
                "proto_success",
                "proto_timedout",
                "proto_simtime",
                "proto_passedtests",
                "proto_failedtests",
                "proto_module_id",
                "proto_regtest_set_id",
            ]
            # print("PROTO_MODULESET_DATA")
            if len(proto_moduleset_data["proto_passedtests"]) > 20000:
                # print(proto_moduleset_data['proto_passedtests'])
                print("long field")
            try:
                df_proto_moduleset_curr
            except NameError:
                df_proto_moduleset_curr = pd.DataFrame([proto_moduleset_data], columns=columns)
            else:
                df_new_row = pd.DataFrame([proto_moduleset_data], columns=columns)
                df_proto_moduleset_curr = df_proto_moduleset_curr.append(df_new_row, ignore_index=True)

            # Uncomment for VERBOSE mode:
            """
            print("\n\n\n\n\n\n\n")
            print("DIAGNOSTICS:\n")
            print(module)
            print(release)
            print(m_total)
            print(m_success)
            print(m_total - m_success)
            print(m_stalled)
            print(m_simtime)

            print("\n\n\n")
            print("Tests that passed for " + module)
            print(passedtestsstring)
            print("\nTests that failed for " + module)
            print(failedtestsstring)
            print("\n\n\n")

            print("Module count:")
            totalmodulesadded = totalmodulesadded + 1
            print(totalmodulesadded)
            print("\n\n\n\n\n\n\n")
            """
        appendData("regtest", df_regtest_curr)
        appendData("regtestset", df_regtestset_curr)
        # appendData("regtestsetid", df_regtestset_curr)
        appendData("subregtest", df_subregtest_curr)
        appendData("proto_moduleset", df_proto_moduleset_curr)
        try:
            df_module_curr
        except NameError:
            print("module check")
        else:
            appendData("module", df_module_curr)
        print("Saved %d tests (%d passed) for %d modules" % (total, success, totalmodulesadded))
        hdf.close()

        # Uncomment for VERBOSE mode:

        """ # print out all module names and the stats for each one
        for module in modules:
            #print(module)

            m_total = 0
            m_success = 0 # this is sometimes called 'passed'; need it to compute number failed
            m_stalled = False
            m_simtime = 0

            # Process each test
            for test in sorted(regdata[module]['tests']):
                tdata = regdata[module]['tests'][test]
                m_total = m_total + 1 # this is a basic incrementation

                test_start_time = regdata[module]['start_time']
                test_finish_time = regdata[module]['end_time']
                if 'start_time' in tdata:
                    test_start_time = tdata['start_time']
                if 'end_time' in tdata:
                    test_finish_time = tdata['end_time']

                tdata = regdata[module]['tests'][test]
                passed = tdata['success']
                m_success = m_success + passed # in regtest table, passed is 0 or 1

                #print(tdata)
                (num_runs_ok, num_runs) = tdata['run']
                (num_val_ok, num_val) = (0, 0)              #FIX# tdata['val']
                (num_cmp_ok, num_cmp) = tdata['cmp']
                test_hostname = ''

                test_elapsed_time = tdata['elapsed_time']
                m_simtime = m_simtime + test_elapsed_time
                test_timed_out = tdata['timed_out']
                m_stalled = m_stalled + test_timed_out

            print(module)
            print(m_total)
            print(m_total - m_success)
            print(m_stalled)
            print(m_simtime)
            print("\n")

        # print out all module names and the stats for each one"""

    # handle(file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC36-2/regtest.data-2023-03-15-11_35", rtype="hourly", suite="suiteName") #
    # handle(file=test_file_path, rtype="hourly", suite="suiteName")
    # Add 5 tests
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-05_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-06_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-07_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-08_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-09_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-10_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-11_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-12_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-13_05",
        rtype="hourly",
        suite="suiteName",
    )
    handle(
        file="/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/regtest.data-2023-06-11-14_05",
        rtype="hourly",
        suite="suiteName",
    )

    end_time = default_timer()
    print(f"Adding data took {end_time - start_time} seconds")


if __name__ == "__main__":
    main()
