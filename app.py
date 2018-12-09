import random

import dash
import dash_core_components as dcc

import dash_html_components as html
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS

import pandas as pd

from datetime import date
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)
server = app.server

# read data
DF = pd.read_csv('./data/lenta_ru/gb_filtered.csv')
# create new column with date string
DF['year_month'] = DF[['year', 'month']].apply(lambda x: date(year=x[0], month=x[1], day=1).strftime('%Y-%m'), axis=1)
# delete bad years data
DF = DF[DF['year'] >= 2000]
# min and max date in data frame
MIN_DF_YEAR = min(DF['year'])
MAX_DF_YEAR = max(DF['year'])


# create topic dictionary of matches: data frame column topic_n --> russian topic description
with open('./data/lenta_ru/topic_names.txt') as f:
    topic_names = f.read().splitlines()
    TOPIC_DICT = {f'topic_{i}': theme for i, theme in enumerate(topic_names)}

app.layout = html.Div(children=[

    html.Div([

        html.Div([
            html.H3(children='Themes filters'),
            html.Div([
                html.Label('Select count of themes'),
                dcc.Slider(
                    id='top-n-theme-count-slider',
                    min=0,
                    max=40,
                    step=10,
                    value=20,
                    marks={i: str(i) for i in [i for i in range(0, 40+1, 5)]},
                ),
            ], style={'margin-bottom': 20}),
            html.Label('Select several theme'),
            dcc.Dropdown(
                id='themes-dropdown',
                multi=True
            ),
        ], style={'width': '34%', 'display': 'inline-block', 'margin-right': 30}),

        html.Div([
            html.H3(children='Dates filters'),
            html.Label('Select date range'),
            dcc.RangeSlider(
                id='year-range-slider',
                marks={str(year): str(year) for year in range(2000, 2019)},
                min=MIN_DF_YEAR,
                max=MAX_DF_YEAR,
                value=[MIN_DF_YEAR, MAX_DF_YEAR]
            ),
        ], style={'width': '34%', 'display': 'inline-block', 'vertical-align': 'top'}),

    ]),

    html.Div([
        dcc.Graph(
            id='stacked-bar-graph'
        )
    ]),

    html.Div([
        dcc.Graph(id='line-graph'),
    ]),

    html.Div([
        dcc.Graph(id='first-difference-line-graph'),
    ]),

    html.Div([
        dcc.Graph(id='bar-graph')
    ]),

    html.Div([
        dcc.Graph(id='word-cloud-graph')
    ]),

])


@app.callback(
    Output(component_id='themes-dropdown', component_property='options'),
    [Input(component_id='top-n-theme-count-slider', component_property='value'),
     Input(component_id='year-range-slider', component_property='value')])
def set_themes_options(top_n_theme_count, selected_year_range):

    # data frame columns with topic statistics
    df_topic_columns = [col for col in DF.columns if col.find('topic') != -1]

    # select only top n largest topics
    top_n_topic_columns = DF[(DF['year'] >= selected_year_range[0]) & (DF['year'] <= selected_year_range[1])] \
                            [df_topic_columns].sum(axis=0).sort_values(ascending=False) \
                             .head(top_n_theme_count)

    top_n_topic_columns = list(top_n_topic_columns.index)

    return [{'label': TOPIC_DICT[v], 'value': v} for v in top_n_topic_columns]

@app.callback(
    Output(component_id='stacked-bar-graph', component_property='figure'),
    [Input(component_id='top-n-theme-count-slider', component_property='value'),
     Input(component_id='themes-dropdown', component_property='value'),
     Input(component_id='themes-dropdown', component_property='options'),
     Input(component_id='year-range-slider', component_property='value')])
def update_stacked_bar_graph(selected_top_n_theme_count, selected_themes, available_themes,
                             selected_year_range):

    # if none of themes not be selected, than choose all themes
    _selected_themes = selected_themes if selected_themes else [v['value'] for v in available_themes]

    # choose years only in date range
    df = DF[(DF['year'] >= selected_year_range[0]) & (DF['year'] <= selected_year_range[1])]

    data = []
    # select data for figure
    for topic in _selected_themes:
        data.append({
            'type': 'bar',
            'x': df['year_month'].values,
            'y': [int(e) if e else None for e in df[topic].values],
            'name': TOPIC_DICT[topic]
        })

    # figure dict
    figure = {
        'data': data,
        'layout': {
            'title': 'Stacked Bar Chart',
            'barmode': 'stack',
            'yaxis': {
                'hoverformat': '.0f'
            }
        }
    }

    return figure

@app.callback(
    Output(component_id='line-graph', component_property='figure'),
    [Input(component_id='top-n-theme-count-slider', component_property='value'),
     Input(component_id='themes-dropdown', component_property='value'),
     Input(component_id='themes-dropdown', component_property='options'),
     Input(component_id='year-range-slider', component_property='value')])
def update_line_graph(selected_top_n_theme_count, selected_themes, available_themes,
                             selected_year_range):

    # if none of themes not be selected, than choose all themes
    _selected_themes = selected_themes if selected_themes else [v['value'] for v in available_themes]

    # choose years only in date range
    df = DF[(DF['year'] >= selected_year_range[0]) & (DF['year'] <= selected_year_range[1])]

    data = []
    # select data for figure
    for topic in _selected_themes:
        data.append(go.Scatter(
            x=df['year_month'].values,
            y=[int(e) if e else None for e in df[topic].values],
            mode='lines+markers',
            name=TOPIC_DICT[topic]
        ))

    # figure dict
    figure = {
        'data': data,
        'layout': {
            'title': 'Line Chart',
            'yaxis': {'type': 'linear'},
            'xaxis': {'type': 'date', 'showline': True, 'range': ['2000-01', '2018-07'], 'showgrid': False}
        }
    }

    return figure

@app.callback(
    Output(component_id='first-difference-line-graph', component_property='figure'),
    [Input(component_id='top-n-theme-count-slider', component_property='value'),
     Input(component_id='themes-dropdown', component_property='value'),
     Input(component_id='themes-dropdown', component_property='options'),
     Input(component_id='year-range-slider', component_property='value')])
def update_first_difference_line_graph(selected_top_n_theme_count, selected_themes, available_themes,
                             selected_year_range):

    # if none of themes not be selected, than choose all themes
    _selected_themes = selected_themes if selected_themes else [v['value'] for v in available_themes]

    # choose years only in date range
    df = DF[(DF['year'] >= selected_year_range[0]) & (DF['year'] <= selected_year_range[1])]

    data = []
    # select data for figure
    for topic in _selected_themes:
        data.append(go.Scatter(
            x=df['year_month'].values,
            y=[int(e) if e else None for e in df[topic].diff().fillna(0).values],
            mode='lines+markers',
            name=TOPIC_DICT[topic]
        ))

    # figure dict
    figure = {
        'data': data,
        'layout': {
            'title': 'First Difference Line Chart',
            'yaxis': {'type': 'linear'},
            'xaxis': {'type': 'date', 'showline': True, 'range': ['2000-01', '2018-07'], 'showgrid': False}
        }
    }

    return figure

@app.callback(
    Output(component_id='word-cloud-graph', component_property='figure'),
    [Input(component_id='top-n-theme-count-slider', component_property='value'),
     Input(component_id='themes-dropdown', component_property='value'),
     Input(component_id='themes-dropdown', component_property='options'),
     Input(component_id='year-range-slider', component_property='value')])
def update_word_cloud_graph(selected_top_n_theme_count, selected_themes, available_themes,
                             selected_year_range):

    words = ['just', 'some', 'random', 'words', 'and', 'more', 'other', 'things']
    colors = [DEFAULT_PLOTLY_COLORS[random.randrange(1, 10)] for i in range(len(words))]
    weights = [random.randint(15, 35) for i in range(len(words))]

    data = go.Scatter(
        x=[random.random() for i in range(30)],
        y=[random.random() for i in range(30)],
        mode='text',
        text=words,
        marker={'opacity': 0.3},
        textfont={'size': weights,
                'color': colors}
    )
    layout = go.Layout({
        'xaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
        'yaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
        'title': 'Word Cloud'
    })

    figure = go.Figure(
        data=[data],
        layout=layout
    )

    return figure


@app.callback(
    Output(component_id='bar-graph', component_property='figure'),
    [Input(component_id='top-n-theme-count-slider', component_property='value'),
     Input(component_id='themes-dropdown', component_property='value'),
     Input(component_id='themes-dropdown', component_property='options'),
     Input(component_id='year-range-slider', component_property='value')])
def update_bar_graph(selected_top_n_theme_count, selected_themes, available_themes,
                             selected_year_range):

    # if none of themes not be selected, than choose all themes
    _selected_themes = selected_themes if selected_themes else [v['value'] for v in available_themes]

    # choose years only in date range
    df = DF[(DF['year'] >= selected_year_range[0]) & (DF['year'] <= selected_year_range[1])]

    data = []
    # select data for figure
    for topic in _selected_themes:
        data.append(go.Box(
            y=df[topic].values,
            name=TOPIC_DICT[topic]
        ))

    layout = go.Layout({
        'title': 'Vertical Box Plot',
        'showlegend': False,
        'yaxis': {
            'hoverformat': '.0f'
        }
    })

    figure = go.Figure(
        data=data,
        layout=layout
    )

    return figure

if __name__ == '__main__':
    app.run_server(debug=True)
