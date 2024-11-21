import pandas as pd
import sys


# print top of file
print("<!doctype html>")
print("<html>")
print("<head>")
print('<meta charset="UTF-8"/>')
print('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0, user-scalable=yes" />')
print("<title>Table with expandable rows</title>")
print(
    '<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous">'
)
print('<link href="css/custom.css" rel="stylesheet" />')

# print css
print("<style>")
print(".expandChildTable:before {")
print('\tcontent: "+";')
print("\tdisplay: block;")
print("\tcursor: pointer;")
print("}")
print(".expandChildTable.selected:before {")
print('\tcontent: "-"')
print("}")
print(".childTableRow {")
print("\tdisplay: none;")
print("}")
print(".childTableRow table {")
print("\tborder: 2px solid #555;")
print("}")

print("</style>")
print("</head>")

# print body
print("<body>")
print('<div class="wrapper">')
print("\t<header>")
print('\t\t<h1 class="col-lg-9">Regtests</h1>')
print("\t</header>")

# print table
print('<table class="table">')

hdf = pd.HDFStore("./test_new.h5", "r")
set_df = hdf["regtestset"]
test_df = hdf["regtest"]
# print(hdf["regtestset"].head())

print("\t<thead>")
print("\t\t<tr>")
print("\t\t\t<th></th>")


for col in list(set_df.columns):
    print(f"\t\t\t<th>{col}</th>")
# print("\t\t\t<th>Customer</th>")
# print("\t\t\t<th>Telephone</th>")
print("\t\t</tr>")
print("\t</thead>")

for index, row in set_df.iterrows():
    print("\t\t<tr>")

    print('\t\t\t<td><span class="expandChildTable"></span></td>')
    for col in list(set_df.columns):
        print(f"\t\t\t<td>{row[col]}</td>")

    print("\t\t</tr>")

    # child table row
    print('\t\t<tr class="childTableRow">')
    print(f'\t\t\t<td colspan="{len(list(test_df.columns))}">')
    print('\t\t\t\t<table class="table">')

    print("\t\t\t\t\t<thead>")
    print("\t\t\t\t\t<tr>")
    for test_col in list(test_df.columns):
        print(f"\t\t\t\t\t\t<th>{test_col}</th>")

    print("\t\t\t\t\t</tr>")
    print("\t\t\t\t\t</thead>")
    print("\t\t\t\t\t<tbody>")
    for test_index, test_row in test_df.iterrows():
        print("\t\t\t\t\t<tr>")
        for test_col in list(test_df.columns):
            print(f"\t\t\t\t\t\t<td>{test_row[test_col]}</td>")
        print("\t\t\t\t\t</tr>")

        if test_index > 2500:
            break

    print("\t\t\t\t\t</tbody>")
    print("\t\t\t</td>")
    print("\t\t</tr>")


# end table and body
print("</table>")
print("</div>")


# print JQuery for expanding table
print('<script src="//code.jquery.com/jquery.js"></script>')
print(
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js" integrity="sha384-wHAiFfRlMFy6i5SRaxvfOCifBUQy1xHdJ/yoi7FRNXMRBu5WHdZYu1hA6ZOblgut" crossorigin="anonymous"></script>'
)
print(
    '<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script><!-- <script src="js/disqus-config.js"></script> -->'
)

print("<script>")
print("$(function() {")
print("\t$('.expandChildTable').on('click', function() {")
print("\t\t$(this).toggleClass('selected').closest('tr').next().toggle();")
print("\t})")
print("});")
print("</script>")
print("</body>")
print("</html>")
