import pandas as pd
from bokeh.io import curdoc, output_file, show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Div, CustomJS
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.plotting import figure

# Create sample dataframes
data1 = {
    "Name": ["Alice", "Bob", "Charlie", "David"],
    "Age": [25, 30, 35, 40],
    "City": ["New York", "Paris", "London", "Tokyo"],
}
df1 = pd.DataFrame(data1)

data2 = {
    "Name": ["Alice", "Bob", "Charlie", "David"],
    "Gender": ["Female", "Male", "Male", "Male"],
    "Occupation": ["Doctor", "Engineer", "Lawyer", "Teacher"],
}
df2 = pd.DataFrame(data2)

# Convert dataframes to bokeh ColumnDataSources
source1 = ColumnDataSource(df1)
source2 = ColumnDataSource(df2)

# Create tables of the data
columns1 = [TableColumn(field=col, title=col) for col in df1.columns]
data_table1 = DataTable(source=source1, columns=columns1, width=400, height=280, selectable=True)

columns2 = [TableColumn(field=col, title=col) for col in df2.columns]
data_table2 = DataTable(source=source2, columns=columns2, width=400, height=280, selectable=False)

# Create titles for the tables
title1 = Div(text="<h1>Table 1</h1>")
title2 = Div(text="<h1>Table 2</h1>")

# Create a callback function
callback = CustomJS(
    args=dict(source1=source1, source2=source2),
    code="""
    var selected_row = source1.selected.indices[0];
    var data1 = source1.data;
    var data2 = source2.data;
    var selected_name = data1['Name'][selected_row];
    var url = 'details.html?name=' + selected_name;
    window.location.href = url;
""",
)

# Attach the callback function to the row select event
source1.selected.js_on_change("indices", callback)

# Create a layout containing the tables and titles
layout = column(title1, data_table1, title2, data_table2)

# Show the layout
output_file("output1.html")
output_file("details.html", mode="inline")  # use a different file name for the second output file
show(layout)
