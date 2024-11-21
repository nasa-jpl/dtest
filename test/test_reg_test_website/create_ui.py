import pandas as pd
from bokeh.models import ColumnDataSource, Div, TapTool, CustomJS
from bokeh.plotting import figure, show, save
from bokeh.io import output_file, curdoc
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.layouts import column, gridplot

# Create a sample dataframe
# data = {'Name': ['Alice', 'Bob', 'Charlie', 'David'],
#         'Age': [25, 30, 35, 40],
#         'City': ['New York', 'Paris', 'London', 'Tokyo']}
# df = pd.DataFrame(data)


def makeTable(tableName):
    # Convert dataframe to bokeh ColumnDataSource
    source = ColumnDataSource(tableName)

    # Create a table of the data
    columns = [TableColumn(field=col, title=col) for col in tableName.columns]
    data_table = DataTable(source=source, columns=columns, width=2000, height=280)

    # Show the data table and scatter plot side-by-side
    output_file("output.html")
    show(column(data_table))


def update_data():
    # get a new dataframe (for example, from a database or API)
    new_df = pd.DataFrame({"A": [4, 5, 6], "B": [7, 8, 9]})
    # update the data source
    source.stream(new_df)


hdf = pd.HDFStore("/home/dartsfn/pkgs/src/reg_test_website_data/testing5", "r")
# makeTable(hdf['regtest'])
# makeTable(hdf['regtestset'])
# makeTable(hdf['subregtest'])
# makeTable(hdf['proto_moduleset'])

source = ColumnDataSource(hdf["regtestset"])
columns = [TableColumn(field=col, title=col) for col in hdf["regtestset"].columns]
data_table1 = DataTable(source=source, columns=columns, width=2000, height=280, selectable=True)

# Create a callback function
callback = CustomJS(
    args=dict(source=source),
    code="""
    var selected_row = source.selected.indices[0];
    console.log("clicked");
    var data1 = source.data;
    var url = 'second_view.html?id=' + selected_row;
    window.location.href = url;
""",
)

# Attach the callback function to the row select event
source.selected.js_on_change("indices", callback)

source = ColumnDataSource(hdf["regtest"])
columns = [TableColumn(field=col, title=col) for col in hdf["regtest"].columns]
data_table2 = DataTable(source=source, columns=columns, width=2000, height=280)

source = ColumnDataSource(hdf["subregtest"])
columns = [TableColumn(field=col, title=col) for col in hdf["subregtest"].columns]
data_table3 = DataTable(source=source, columns=columns, width=2000, height=280)

source = ColumnDataSource(hdf["proto_moduleset"])
columns = [TableColumn(field=col, title=col) for col in hdf["proto_moduleset"].columns]
data_table4 = DataTable(source=source, columns=columns, width=2000, height=280)

source = ColumnDataSource(hdf["module"])
columns = [TableColumn(field=col, title=col) for col in hdf["module"].columns]
data_table5 = DataTable(source=source, columns=columns, width=2000, height=280)

hdf.close()

title1 = Div(text="<h1>RegtestSet</h1>")
title2 = Div(text="<h1>Regtest</h1>")
title3 = Div(text="<h1>SubRegtest</h1>")
title4 = Div(text="<h1>ProtoModuleset</h1>")
title5 = Div(text="<h1>Module</h1>")
# Lay out the tables and titles in a column
layout = column(title1, data_table1, title2, data_table2, title3, data_table3, title4, data_table4, title5, data_table5)
# source.selected.js_on_change('indices', update_data)
layout = column(title1, data_table1, title2, data_table2, title3, data_table3, title4, data_table4, title5, data_table5)
# Lay out the tables in a grid
# grid = gridplot([[data_table1, data_table2]])
curdoc().add_root(layout)
# Show the grid
output_file("output.html")
# save(layout)

show(layout)  # Use this rather than save(layout) if you want to view as well as save output.html


# # add the DataTable to a layout and add a button to trigger the update
# layout = column(table)
# button = Button(label="Update Data")
# button.on_click(update_data)
# layout = column(button, layout)
