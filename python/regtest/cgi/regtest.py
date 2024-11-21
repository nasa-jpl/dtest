#!/usr/bin/python

import os, sys, re
import datetime
from urllib.parse import unquote

# sys.path.append("/home/atbe/dev/users/stobin/sandboxes/ROAMSDshell_sandbox/src/Dtest/python/regtest")
sys.path.append("/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg/ROAMSDshellPkg-Hourly-FC38/src/Dtest/python/regtest")

from queryHDF5 import (
    moduleStats,
    multipleModuleStats,
    getAllModuleNames,
    runStats,
    testStats,
    getAllSandboxNames,
    ModuleInfo,
    TestInfo,
)

if "REQUEST_SCHEME" in os.environ.keys():
    URL = os.environ["REQUEST_SCHEME"] + "://" + os.environ["SERVER_NAME"] + os.environ["REQUEST_URI"]
    QUERY_STRING = os.environ["QUERY_STRING"]
    URL_NO_QUERY = URL.replace("?" + QUERY_STRING, "")

    QUERY_PARAMS = {}
    if QUERY_STRING != "":
        query_parts = QUERY_STRING.split("&")
        for part in query_parts:
            if "=" in part:
                QUERY_PARAMS[part.split("=")[0]] = part.split("=")[1]

else:
    URL_NO_QUERY = "https://dartslab.jpl.nasa.gov/internal/www/cgi-bin/regtest.py"
    QUERY_STRING = ""  # "date=2023-07-25T10:51&file=regtest_FC38.h5&sandboxes=[ROAMSDshellPkg-Hourly-FC38, ROAMSDshellPkg-Hourly-FC38-2, ROAMSDshellPkg-Hourly-FC38-graphics, ]"
    URL = URL_NO_QUERY + "?" + QUERY_STRING
    QUERY_PARAMS = {}
    if QUERY_STRING != "":
        query_parts = QUERY_STRING.split("&")
        for part in query_parts:
            if "=" in part:
                QUERY_PARAMS[part.split("=")[0]] = part.split("=")[1]


# if 'date' not in list(QUERY_PARAMS.keys()):
#     QUERY_PARAMS['date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")

#     print(f'''
#     <html>
#     <head>
#     </head>
#     <body>
#         <script>
#             window.location.href = window.location.href + "?date={QUERY_PARAMS['date']}"
#         </script>
#     </body>
#     </html>
#     ''')
#     sys.exit(0)


if "date" in list(QUERY_PARAMS.keys()):
    DATETIME_OBJ = datetime.datetime.strptime(QUERY_PARAMS["date"], "%Y-%m-%dT%H:%M")
else:
    DATETIME_OBJ = datetime.datetime.now()

HDF5_DIR = "/home/dlab3/repo/PKGBUILDS/ROAMSDshellPkg"
HDF5_FILES = []
for entry in os.listdir(HDF5_DIR):
    if (entry.endswith(".h5") or entry.endswith(".hdf5")) and not re.search(r"\.(\d+)\.", entry):
        # print(entry)
        HDF5_FILES.append(entry)

DEFAULT_HDF5_FILENAME = "regtest_FC38.h5"

# if 'file' not in list(QUERY_PARAMS.keys()):
#     QUERY_PARAMS['file'] = DEFAULT_HDF5_FILENAME

#     print(f'''
#     <html>
#     <head>
#     </head>
#     <body>
#         <script>
#             window.location.href = window.location.href + "?file={QUERY_PARAMS['file']}"
#         </script>
#     </body>
#     </html>
#     ''')
#     sys.exit(0)

if "file" in list(QUERY_PARAMS.keys()):
    HDF5_FILENAME = os.path.join(HDF5_DIR, QUERY_PARAMS["file"])
else:
    HDF5_FILENAME = DEFAULT_HDF5_FILENAME


sandbox_dictionary_str = """
        sandbox_dict = {
"""
for hdf5_file in HDF5_FILES:
    sandbox_dictionary_str += f'\t\t"{hdf5_file}": ['
    sandboxes = getAllSandboxNames(os.path.join(HDF5_DIR, hdf5_file))
    for sbox in sandboxes:
        sandbox_dictionary_str += f'"{sbox}", '
    sandbox_dictionary_str += "],\n"

sandbox_dictionary_str += """
        }
"""

# print(sandbox_dictionary_str)

# if 'sandboxes' not in list(QUERY_PARAMS.keys()):
#     QUERY_PARAMS['sandboxes'] = getAllSandboxNames(HDF5_FILENAME, num_files=10)

#     print(f'''
#     <html>
#     <head>
#     </head>
#     <body>
#         <script>
#             sandboxes_str = "[{', '.join([sbox for sbox in QUERY_PARAMS['sandboxes']])}, ]"
#             window.location.href = window.location.href + "&sandboxes=" + sandboxes_str
#         </script>
#     </body>
#     </html>
#     ''')
#     sys.exit(0)

if "sandbox" in list(QUERY_PARAMS.keys()):
    sandbox_decoded = unquote(QUERY_PARAMS["sandbox"])
    SANDBOX = sandbox_decoded[1:-1]
else:
    SANDBOX = None


html_top = f"""
<html>
<head>
    <script src="//code.jquery.com/jquery.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.css" />

    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/jsfive@0.3.10/dist/browser/hdf5.js"></script>
</head>
<body>
"""

html_module_back_button = f"""
    <button id="moduleBackButton">Back to All Modules</button>
"""
html_test_back_button = f"""
    <button id="testBackButton"> Back to All Tests</button>
"""

html_run_back_button = f"""
    <button id="runBackButton">Back to All Runs</button>
"""

if "test" in list(QUERY_PARAMS.keys()):
    html_top += html_test_back_button
elif "module" in list(QUERY_PARAMS.keys()):
    html_top += html_module_back_button
elif "date" in list(QUERY_PARAMS.keys()):
    html_top += html_run_back_button


html_top += '\t<div class="container">'

html_date_and_file_picker = """
    <div class="roundedCorners" id="queryDiv">
        <h3>Regtest File Selector</h3>
        <div class="tooltip">?
            <span class="tooltiptext">Select the date. The file that is closest to the selected date will be displayed.</span>
        </div>
        <label for="datePicker">Select datetime of file:</label>
        <input type="datetime-local" id="datePicker"/>

        <br>
        <div class="tooltip">?
            <span class="tooltiptext">Select which HDF5 regtest database you want to view regtest information from. HDF5 files are named according to the sandboxes they have information for.</span>
        </div>
        <label for="filePicker">Select HDF5 database:</label>
        <select name="HDF5 Filename" id="filePicker"/>
    
"""
for hdf5_file in HDF5_FILES:
    html_date_and_file_picker += f'\t<option value="{hdf5_file}">{hdf5_file}</option>\n'
html_date_and_file_picker += "</select>\n"


html_sandbox_picker = """
        <br>
        <div class="tooltip">?
            <span class="tooltiptext">Some HDF5 regtest databases have regtest info from multiple sandboxes included. Select which sandboxes you want to be part of your query.</span>
        </div>
        <label for="sandboxCheckboxList">Sandboxes to include:</label>
        <ul id="sandboxCheckboxList">
        </ul>

        <button id="dateButton">Go!</button>
    </div>
"""


html_regtest_summary = """
    <div class="roundedCorners" id="summaryDiv">
        <h2>Regtest Run Summary</h2>
        <p><b>Sandbox:</b> {sandbox}</p>
        <p><b>Tests:</b> {test_percent}</p>
        <p><b>Start time:</b> {start_time}</p>
        <p><b>Full filename:</b> {regtest_filename}
    </div>
"""

html_module_table_top = f"""
        <div id="clear"></div>
    </div>
    <table id="example" class="display" style="width:100%">
        <thead>
            <tr>
                <th>Module</th>
                <th>Release</th>
                <th>Total</th>
                <th>Failed</th>
                <th>Percent</th>
                <th>Elapsed time (s)</th>
            </tr>
        </thead>
        <tbody>
"""

html_module_table_bottom = """
        </tbody>
        <tfoot>
            <tr>
                <th>Module</th>
                <th>Release</th>
                <th>Total</th>
                <th>Failed</th>
                <th>Percent</th>
                <th>Elapsed time (s)</th>
            </tr>
        </tfoot>
    </table>
"""

html_module_row = """
            <tr><td><a href={url}>{module}</a></td> <td>{release}</td> <td>{total}</td> <td>{failed}</td> <td>{percent}</td> <td>{elapsed_time}</td></tr>
"""

html_module_summary = """
    <div class="roundedCorners" id="summaryDiv">
        <h2>Module Summary</h2>
        <p><b>Module:</b> {module_name}</p>
        <p><b>Release:</b> {release}</p>
        <p><b>Tests:</b> {test_percent}</p>
        <p><b>Elapsed time (s):</b> {elapsed_time}</p>
        <p><b>Full filename:</b> {filename}</p>
    </div>
"""

html_test_table_top = f"""
        <div id="clear"></div>
    </div>
    <table id="example" class="display" style="width:100%">
        <thead>
            <tr>
                <th>Test</th>
                <th>Failed</th>
                <th>Timed Out</th>
                <th>
                <div class="tooltip">?
                    <span class="tooltiptext">Last 10 test results. '.' means failed, '*' means time out and 'P' means passed.</span>
                </div>
                Last 10</th>
                <th>Last Passed</th>
                <th>Elapsed Time (s)</th>
            </tr>
        </thead>
        <tbody>
"""
html_test_table_bottom = f"""
    <table id="example" class="display" style="width:100%">
        </tbody>
        <tfoot>
            <tr>
                <th>Test</th>
                <th>Failed</th>
                <th>Timed Out</th>
                <th>Last 10</th>
                <th>Last Passed</th>
                <th>Elapsed Time (s)</th>
            </tr>
        </tfoot>
    </table>
"""
html_test_row = """
            <tr><td><a href={url}>{test}</a></td> <td>{failed}</td> <td>{timed_out}</td> <td>{last10}</td> <td>{last_passed}</td><td>{elapsed_time}</td></tr>
"""

html_test_summary = """
    <div class="roundedCorners" id="summaryDiv">
        <h2>Test Summary</h2>
        <p><b>Test:</b> {test_name}</p>
        <p><b>Module:</b> {module_name}</p>
        <p><b>Release:</b> {release}</p>
        <p><b>Runs:</b> {runs_str}</p>
        <p><b>Cmps:</b> {cmps_str}</p>
        <p><b>Full filename:</b> {filename}</p>
    </div>
"""

html_test_runs_table_top = """
        <div id="clear"></div>
    </div>
    <table id="example" class="display" style="width:100%">
        <thead>
            <tr>
                <th>Date</th>
                <th>Failed</th>
                <th>Timed Out</th>
                <th>Runs</th>
                <th>Cmps</th>
            </tr>
        </thead>
        <tbody>
"""
html_test_runs_table_row = """
            <tr><td>{file_key}</td> <td>{failed}</td> <td>{timed_out}</td> <td>{runs_str}</td> <td>{cmps_str}</td></tr>
"""

html_test_runs_table_bottom = """
    <table id="example" class="display" style="width:100%">
        </tbody>
        <tfoot>
            <tr>
                <th>Date</th>
                <th>Failed</th>
                <th>Timed Out</th>
                <th>Runs</th>
                <th>Cmps</th>
            </tr>
        </tfoot>
    <table>
"""

html_run_table_top = """
        <div id="clear"></div>
    </div>
    <table id="{table_id}" class="display" style="width:100%">
        <thead>
            <tr>
                <th>File Name</th>
                <th>Total</th>
                <th>Failed</th>
                <th>Percent</th>
            </tr>
        </thead>
        <tbody>
"""

html_run_table_bottom = f"""
    <table id="example" class="display" style="width:100%">
        </tbody>
        <tfoot>
            <tr>
                <th>File Name</th>
                <th>Total</th>
                <th>Failed</th>
                <th>Percent</th>
            </tr>
        </tfoot>
    </table>
"""

html_run_table_row = """
            <tr><td><a href={url}>{filename}</td> <td>{total}</td> <td>{failed}</td> <td>{percent}</td></tr>
"""


html_module_datatable = """
    <script>
        new DataTable('#example', {
            order: [[3, 'desc']],
            lengthMenu: [
                [50, 100, -1],
                [50, 100, 'All']
            ],
            deferRender: true
        });
    </script>
</body>
</html>
"""

html_test_datatable = """
    <script>
        new DataTable('#example', {
            order: [[1, 'desc']],
            lengthMenu: [
                [50, 100, -1],
                [50, 100, 'All']
            ],
            deferRender: true,
            "columnDefs": [
                { "width": "200px", "targets": 3 }
            ]
        });
    </script>
"""
html_test_runs_datatable = """
    <script>
        new DataTable('#example', {
            order: [[0, 'desc']],
            deferRender: true,
        });
    </script>
"""

html_run_datatable = """
    <script>
        new DataTable('#{table_id}', {{
            order: [[0, 'desc']],
            lengthMenu: [
                [10],
                [10]
            ],
            deferRender: true
        }});
    </script>
"""

html_module_back_button_js = """
    <script>
        const module_back_button = document.getElementById("moduleBackButton");
        decoded_url = decodeURI(window.location.href);
        let url_params = decoded_url.split("&");

        let module_name = "";

        for (var i = 0; i < url_params.length; i++) {
            if (url_params[i].includes("module=")) {
                module_name = url_params[i].replace("module=", "");
            }
        }

        console.log(module_name)

        module_back_button.addEventListener("click", function () {
            new_href = window.location.href.replace("&module="+module_name, "");
            window.location.href = new_href;
        });
    </script>
"""

html_test_back_button_js = """
    <script>
        const test_back_button = document.getElementById("testBackButton");
        decoded_url = decodeURI(window.location.href);
        let url_params = decoded_url.split("&");

        let test_name = "";
        for (var i = 0; i < url_params.length; i++) {
            if (url_params[i].includes("test=")) {
                test_name = url_params[i].replace("test=", "");
            }
        }

        console.log(test_name)

        test_back_button.addEventListener("click", function () {
            new_href = window.location.href.replace("&test="+test_name, "");
            window.location.href = new_href;
        });
    </script>
"""

html_run_back_button_js = """
    <script>
        const run_back_button = document.getElementById("runBackButton");
        decoded_url = decodeURI(window.location.href);
        let url_params = decoded_url.split("&");
        let url_no_query = decoded_url.split("?")[0];

        run_back_button.addEventListener("click", function () {
            window.location.href = url_no_query;
        });
    </script>
"""

html_date_and_file_picker_js = (
    """
    <script>
"""
    + sandbox_dictionary_str
    + """

        const date_picker = document.getElementById("datePicker")
        const file_picker = document.getElementById("filePicker")
        const sandbox_list = document.getElementById("sandboxCheckboxList")

        const params = new Proxy(new URLSearchParams(window.location.search), {
            get: (searchParams, prop) => searchParams.get(prop),
        });

        let url_date = params.date;
        let url_file = params.file;
        let url_sandbox = params.sandbox;

        console.log(url_sandbox)

        if (url_date != null) {
            date_picker.value = decodeURI(url_date)
        }

        if (url_file != null) {
            file_picker.value = decodeURI(url_file)
        }

        sandbox_options = sandbox_dict[file_picker.value]
        if (sandbox_options != null) {
            for (var i = 0; i < sandbox_options.length; i++) {
                var li = document.createElement("li");
                li.setAttribute("id", sandbox_options[i]);

                li_checkbox = document.createElement("INPUT");
                li_checkbox.setAttribute("id", "checkbox"+sandbox_options[i])
                li_checkbox.setAttribute("type", "radio");
                li_checkbox.setAttribute("name", "sandbox_buttons");
                li_checkbox.setAttribute("value", sandbox_options[i]);

                // url_sandboxes_array = url_sandboxes.substring(1, url_sandboxes.length-1).split(', ')
                if (url_sandbox.includes(sandbox_options[i])) {
                    li_checkbox.setAttribute("checked", true);
                }
                


                li.appendChild(li_checkbox);
                li.appendChild(document.createTextNode(sandbox_options[i]));
                sandbox_list.appendChild(li);
            }
        }

        file_picker.addEventListener("change", function () {
            while (sandbox_list.firstChild) {
                sandbox_list.removeChild(sandbox_list.firstChild);
            }

            sandbox_options = sandbox_dict[file_picker.value]
            if (sandbox_options != null) {
                for (var i = 0; i < sandbox_options.length; i++) {
                    var li = document.createElement("li");
                    li.setAttribute("id", sandbox_options[i]);

                    li_checkbox = document.createElement("INPUT");
                    li_checkbox.setAttribute("id", "checkbox"+sandbox_options[i])
                    li_checkbox.setAttribute("type", "radio");
                    li_checkbox.setAttribute("name", "sandbox_buttons");
                    li_checkbox.setAttribute("value", sandbox_options[i]);
                    li_checkbox.setAttribute("checked", true);

                    


                    li.appendChild(li_checkbox);
                    li.appendChild(document.createTextNode(sandbox_options[i]));
                    sandbox_list.appendChild(li);
                }
            }
        });

        const date_button = document.getElementById("dateButton")
        date_button.addEventListener("click", function () {
            

            let new_url_date = encodeURI(date_picker.value)
            let new_url_file = encodeURI(file_picker.value)
            var new_url_sandbox = ''
            var checkbox_items = sandbox_list.getElementsByTagName("li");
            for (var i = 0; i < checkbox_items.length; i++) {
                if (checkbox_items[i].firstChild.checked) {
                    // new_url_sandboxes += checkbox_items[i].firstChild.value + ", "
                    new_url_sandbox = checkbox_items[i].firstChild.value;
                    break;
                }
            }
            // new_url_sandboxes += ']'

            console.log(url_sandbox)
            

            if (url_date == null) {
                window.location.href = window.location.href + "?date="+new_url_date
            } else {
                decoded_url = decodeURI(window.location.href)
                new_href = decoded_url.replace("sandbox="+url_sandbox, "sandbox='"+new_url_sandbox+"'")

                new_href = new_href.replace("date="+url_date, "date="+new_url_date)
                new_href = new_href.replace("file="+url_file, "file="+new_url_file)
                window.location.href = encodeURI(new_href)
            }
        });
    </script>
"""
)

html_div_css = """
    <style>
        div.roundedCorners
        {
            padding: 10px;
            border: 2px solid #000;
            border-radius: 15px;
            -moz-border-radius: 15px;
        }

        div.container
        {
            padding-left: 5px;
            padding-right: 5px;
            padding-top: 10px;
            padding-bottom: 10px;
        }

        #queryDiv
        {
            background-color: #e0e0e0;
            float: right;
            width: 30%;
        }

        #summaryDiv
        {
            background-color: #e0e0e0;
            float: left;
            width: 65%;
        }

        #clear {
            clear: both;
        }

        #sandboxCheckboxList
        {
            list-style-type: None;
        }

        #moduleBackButton
        {
            padding: 5px;
            margin: 3px;
        }

        #runBackButton
        {
            padding: 5px;
            margin: 3px;
        }

        .tooltip {
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted black;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            width: 250px;
            background-color: black;
            color: #fff;
            text-align: center;
            font-weight: normal;
            border-radius: 6px;
            padding: 5px;
            
            /* Position the tooltip */
            position: absolute;
            z-index: 1;
            top: -5px;
            right: 105%;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            transition: linear 0.3s;
        }
    </style>
"""

html_end = """
</body>
</html>
"""

html = html_top

# landing page: date not present in query params
# select between runs from from multiple sandboxes from multiple days
if "date" not in list(QUERY_PARAMS.keys()):

    for hdf5_file in HDF5_FILES:
        hdf5_filename = os.path.join(HDF5_DIR, hdf5_file)
        sandboxes = getAllSandboxNames(os.path.join(HDF5_DIR, hdf5_file))
        for sandbox in sandboxes:

            html += f"<h2>{sandbox}</h2>"

            html += html_run_table_top.format(table_id=sandbox)

            # get run info for last 50 runs
            run_infos = runStats(hdf5_filename, sandbox, num_past_runs=50, date=datetime.datetime.now())
            for run_info in run_infos:
                filename_date_str = run_info.filename[run_info.filename.find("20") :]
                datetime_obj = datetime.datetime.strptime(filename_date_str, "%Y-%m-%d-%H_%M")
                html += html_run_table_row.format(
                    url=URL_NO_QUERY
                    + f'?file={hdf5_file}&date={datetime_obj.strftime("%Y-%m-%dT%H:%M")}&sandbox=\'{sandbox}\'',
                    filename=run_info.filename.split("/")[-1],
                    total=run_info.num_tests,
                    failed=run_info.num_tests - run_info.num_tests_ok,
                    percent=f"{100*run_info.num_tests_ok/run_info.num_tests:.2f}",
                )

            html += html_run_table_bottom
            html += html_run_datatable.format(table_id=sandbox)
# if 'test' in params, we are looking at a test specific page
elif "test" in list(QUERY_PARAMS.keys()):
    html += html_date_and_file_picker + html_sandbox_picker

    test_name = QUERY_PARAMS["test"]
    module_name = QUERY_PARAMS["module"]
    test_infos = testStats(HDF5_FILENAME, SANDBOX, module_name, test_name, date=DATETIME_OBJ, num_past_runs=50)
    module_infos = moduleStats(HDF5_FILENAME, SANDBOX, module_name, date=DATETIME_OBJ, num_past_runs=50)
    run_infos = runStats(HDF5_FILENAME, SANDBOX, date=DATETIME_OBJ)

    html += html_test_summary.format(
        test_name=test_name,
        module_name=module_name,
        release=module_infos[0].release,
        runs_str=f"{test_infos[0].num_runs_ok}/{test_infos[0].num_runs}",
        cmps_str=f"{test_infos[0].num_cmps_ok}/{test_infos[0].num_cmps}",
        filename=run_infos[0].filename,
    )
    html += html_test_runs_table_top

    for test_info in test_infos:
        failed_str = "<b>True</b>" if not test_info.passed else "False"
        html += html_test_runs_table_row.format(
            file_key=test_info.file_key,
            failed=failed_str,
            timed_out=test_info.timed_out,
            runs_str=f"{test_info.num_runs_ok}/{test_info.num_runs}",
            cmps_str=f"{test_info.num_cmps_ok}/{test_info.num_cmps}",
        )

    html += html_test_runs_table_bottom
    html += html_test_runs_datatable

    html += html_test_back_button_js

elif "module" in list(QUERY_PARAMS.keys()):

    html += html_date_and_file_picker + html_sandbox_picker

    module_name = QUERY_PARAMS["module"]
    module_infos = moduleStats(HDF5_FILENAME, SANDBOX, module_name, get_test_infos=True, date=DATETIME_OBJ)
    run_infos = runStats(HDF5_FILENAME, SANDBOX, date=DATETIME_OBJ)

    elapsed_time_str = f"{float(module_infos[0].elapsed_time):.2f}"

    html += html_module_summary.format(
        module_name=module_name,
        release=module_infos[0].release,
        test_percent=f"{module_infos[0].num_tests_ok}/{module_infos[0].num_tests} ({100*module_infos[0].num_tests_ok/module_infos[0].num_tests:.2f}%)",
        filename=run_infos[0].filename,
        elapsed_time=elapsed_time_str,
    )
    html += html_test_table_top

    for test in module_infos[0].tests:
        if not test.passed:
            last10_infos = testStats(HDF5_FILENAME, SANDBOX, module_name, test.name, 10, date=DATETIME_OBJ)

            def getInfoChar(passed, timed_out):
                try:
                    if bool(timed_out):
                        return "*"
                    if bool(passed):
                        return "P"
                except Exception as e:
                    return "."

                return "."

            last10_str = "".join([getInfoChar(info.passed, info.timed_out) for info in last10_infos])
        else:
            last10_str = ""

        failed_str = "<b>True</b>" if not test.passed else "False"
        test_url = URL + f"&test={test.name}"
        elapsed_time_str = f"{float(test.elapsed_time):.2f}"
        html += html_test_row.format(
            url=test_url,
            test=test.name,
            failed=failed_str,
            timed_out=test.timed_out,
            last10=last10_str,
            last_passed=test.last_passed_file_key,
            elapsed_time=elapsed_time_str,
        )

    html += html_test_table_bottom
    html += html_test_datatable

    html += html_module_back_button_js
else:
    html += html_date_and_file_picker + html_sandbox_picker

    run_infos = runStats(HDF5_FILENAME, SANDBOX, date=DATETIME_OBJ)
    html += html_regtest_summary.format(
        sandbox=run_infos[0].filename.split("/")[-2],
        test_percent=f"{run_infos[0].num_tests_ok}/{run_infos[0].num_tests} ({100*run_infos[0].num_tests_ok/run_infos[0].num_tests:.2f}%)",
        start_time=run_infos[0].start_time,
        regtest_filename=run_infos[0].filename,
    )
    html += html_module_table_top

    module_names = getAllModuleNames(HDF5_FILENAME, SANDBOX, num_files=5)
    all_module_infos = multipleModuleStats(
        HDF5_FILENAME, SANDBOX, module_names, get_test_infos=False, date=DATETIME_OBJ
    )
    for module_infos in all_module_infos:
        module_info = module_infos[0]

        module_url = URL
        if "module" in list(QUERY_PARAMS.keys()):
            module_url = URL.replace(f"module={QUERY_PARAMS['module']}", f"module={module_info.name}")
        else:
            module_url += f"&module={module_info.name}"
        elapsed_time_str = f"{float(module_info.elapsed_time):.2f}"
        html += html_module_row.format(
            url=module_url,
            module=module_info.name,
            release=module_info.release,
            total=module_info.num_tests,
            failed=module_info.num_tests - module_info.num_tests_ok,
            percent=f"{100*module_info.num_tests_ok/module_info.num_tests:.2f}",
            elapsed_time=elapsed_time_str,
        )

    html += html_module_table_bottom
    html += html_module_datatable
    html += html_run_back_button_js


html += html_date_and_file_picker_js
html += html_div_css
html += html_end

print(html)
