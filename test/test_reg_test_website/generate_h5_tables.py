import sys
import pandas as pd, datetime

# import regtestsite.regtest.management.final_files.upload_regtests_to_hdf5 as upload_regtests_to_hdf5
pd.set_option("io.hdf.default_format", "table")
import warnings

warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)
from IPython.display import display


def main():
    create_all_tables(sys.argv[1])


### TESTING ###


def create_all_tables(newFileName):
    create_regtest_df(newFileName, "regtest")
    create_regtestset_df(newFileName, "regtestset")
    create_subregtest_df(newFileName, "subregtest")
    create_module_df(newFileName, "module")
    create_proto_moduleset_df(newFileName, "proto_moduleset")


### CREATE 5 REGTEST DATAFRAMES ###
def create_regtestset_df(newFileName, name):
    hdf = pd.HDFStore(newFileName)
    test_data = {
        "name": "test",
        "suite": "test",
        "start_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "finish_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "num_tests": 0,
        "num_tests_ok": 0,
        "set_type": "test",
        "sandbox_info": "test",
        "exclude_tags": "test",
        "run_only": "test",
    }
    df_data = pd.DataFrame(
        [test_data],
        columns=[
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
        ],
    )
    hdf.put(name, df_data, format="table", data_columns=True, min_itemsize=100)
    # hdf.append(name, df_data, min_item size=100)
    display(df_data)
    hdf.close()


def create_regtestset_id(newFileName, name):
    hdf = pd.HDFStore(newFileName)
    test_data1 = {
        "name": "test",
        "suite": "test",
        "start_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "finish_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "num_tests": 0,
        "num_tests_ok": 0,
        "set_type": "test",
        "sandbox_info": "test",
        "exclude_tags": "test",
        "run_only": "test",
    }
    test_data2 = {
        "name": "test1",
        "suite": "test",
        "start_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "finish_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "num_tests": 0,
        "num_tests_ok": 0,
        "set_type": "test",
        "sandbox_info": "test",
        "exclude_tags": "test",
        "run_only": "test",
    }
    df_data = pd.DataFrame(
        [test_data1],
        columns=[
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
        ],
    )
    hdf.put(name, df_data, format="table", data_columns=True, min_itemsize=100)
    # hdf.append('regtestsetid', df_data, min_itemsize=100)
    display(df_data)
    hdf.close()


def create_regtest_df(newFileName, name):
    hdf = pd.HDFStore(newFileName)
    test_data = {
        "name": "test",
        "passed": 0,
        "num_runs": 0,
        "num_runs_ok": 0,
        "num_comparisons": 0,
        "num_comparisons_ok": 0,
        "num_validations": 0,
        "num_validations_ok": 0,
        "module_release": "test",
        "start_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "finish_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "hostname": "test",
        "elapsed_time": 0.0,
        "timed_out": 0,
        "module_id": 0,
        "regtest_set_id": 0,
    }
    df_data = pd.DataFrame(
        [test_data],
        columns=[
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
        ],
    )
    hdf.put(name, df_data, format="table", data_columns=True, min_itemsize=100)
    # hdf.append(name, df_data, min_itemsize=100)
    hdf.close()


def create_subregtest_df(newFileName, name):
    hdf = pd.HDFStore(newFileName)
    test_data = {
        "name": "test",
        "completion_status": 0,
        "return_code": "0",
        "set_type": "test",
        "regtest_id": 0,
    }
    df_data = pd.DataFrame([test_data], columns=["name", "completion_status", "return_code", "set_type", "regtest_id"])
    hdf.put(name, df_data, format="table", data_columns=True, min_itemsize=100)
    # hdf.append(name, df_data, min_itemsize=100)
    hdf.close()


def create_module_df(newFileName, name):
    hdf = pd.HDFStore(newFileName)
    test_data = {"name": "test", "maintainer_id": 0}
    df_data = pd.DataFrame([test_data], columns=["name", "maintainer_id"])
    hdf.put(name, df_data, format="table", data_columns=True, min_itemsize=200)
    hdf.close()


def create_proto_moduleset_df(newFileName, name):
    hdf = pd.HDFStore(newFileName)
    test_data = {
        "proto_release": "test",
        "proto_total": 0,
        "proto_success": 0,
        "proto_timedout": 0,
        "proto_simtime": 0.0,
        "proto_passedtests": "test",
        "proto_failedtests": "test",
        "proto_module_id": 0,
        "proto_regtest_set_id": 0,
    }
    df_data = pd.DataFrame(
        [test_data],
        columns=[
            "proto_release",
            "proto_total",
            "proto_success",
            "proto_timedout",
            "proto_simtime",
            "proto_passedtests",
            "proto_failedtests",
            "proto_module_id",
            "proto_regtest_set_id",
        ],
    )
    # df_proto_moduleset = df_proto_moduleset.set_index('id')
    hdf.put(name, df_data, format="table", data_columns=True, min_itemsize=50000)  # this it the max min_itemsizse
    # hdf.append(name, df_data, min_itemsize=50000)
    hdf.close()


### READ AND APPEND ###
def read_test_hdf5():
    hdf = pd.HDFStore(
        "/home/dlab3/FROM-DLAB/repo/RegtestWebsite/RegtestWebsite/regtestsite/regtest/management/hdf_files/hdf5_regtests.h5",
        mode="r",
    )
    print(hdf.keys())
    hdf.close()


def append_regtestset():
    hdf = pd.HDFStore("regtests.h5")
    df = hdf["df_regtestset"]
    row_data = {
        "id": 1,
        "name": "ROAM",
        "suite": "Unknown",
        "start_time": datetime.datetime(2023, 1, 1, 0, 0, 0, 0),
        "finish_time": datetime.datetime(2023, 4, 4, 0, 0, 0, 0),
        "num_tests": 1063,
        "num_tests_ok": 155,
        "set_type": "H",
        "sandbox_info": "Unknown",
        "exclude_tags": "N/A",
        "run_only": "N/A",
    }
    if row_data["name"] in df["name"].values:
        print(row_data["name"] + "already exists in this dataframe.")
    else:
        df_new_row = pd.DataFrame(
            row_data,
            columns=[
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
            ],
            index=[0],
        )
        hdf.append("df_regtestset", df_new_row)
    hdf.close()


if __name__ == "__main__":
    main()
