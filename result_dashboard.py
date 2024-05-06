#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask application for the CoSim WepApp.

Research group of Politecnico di Torino Energy Center Lab.

- author: Daniele Salvatore Schiera
- copyright: Copyright 2020. Energy Center Lab - Politecnico di Torino"
- credits: Daniele Salvatore Schiera
- maintainer: Daniele Salvatore Schiera
- email: daniele.scheira@polito.it
- status: Development
"""
import datetime
import json
import os
import datetime

import dash
import plotly.graph_objs as go
#import zmq
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd

#from utils import read_scenario_runtime, zmq_receiver, retrive_outputs_db, retrive_entity_timeseries_db, \
#    load_graph_runtime, set_live_cache, zmq_sender

# Load stylesheets
external_css = ["https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"]  # ['https://codepen.io

# Load scripts
external_js = []  # ["https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"]

# Run app Dash, suppress_callback_exceptions=True permits to avoid warnings if some html components are not directly
# loaded in layout but added in callbacks
app = dash.Dash(__name__, external_stylesheets=external_css, external_scripts=external_js,
                suppress_callback_exceptions=False, title='CoSim Dashboard', update_title=None,
                assets_folder=os.path.join(os.getcwd(), 'dashboard_assets/') )

# init settings for runtime scenario loading # TODO: integrare tutto in callback  tab stream senza inizializzare prima
# global live_cache  # TODO: avoid!
#scenario_name, start_date, attrs_live, attrs_input = read_scenario_runtime()
#start_time = pd.to_datetime(start_date)
# global attr_sender
# if attrs_input:
#     attr_sender = create_command_sender(port = "5571")  # TODO: due zmq non vanno insieme
# start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
# live_cache = set_live_cache(attrs_live, max_length=500)

# Init database list in directory outputs.
# default_db = 'output_sim_demo.hdf5'
# TODO: ATT se si si sta runnando la demo, ouput sim demo dovrebbe essere non utilizzabile! perche nel frattempo sta
#  scrivendo il file sopra, e non potrei aprirlo!
#outputs_db_list = retrive_outputs_db()
# entities_attrs_dict = retrive_entity_timeseries_db(default=True)


# Layout of the WebApp
app.layout = html.Div(className='container-fluid', children=
[html.Div(className='row align-items-center', children=
[html.Div([html.H1(f'CoSim Web Dashboard', style={'text-align': 'center'})], className='col-10'),
 html.Div(className='col', children=
 [html.Div(className='float-right', children=
 html.Img(src='assets/COESI_logo.png', style={"height": 100}))]), ]),
 html.Div(children=[
     dcc.Tabs(id='tabs', children=[
         dcc.Tab(value='data', label='Datasets timeseries', children=[
             html.Div([
                 html.P('Select the database (from Outputs folder):'),
                 dcc.Dropdown(
                     id='select-db',
                     # options=[{'label': s, 'value': s} for s in outputs_db_list.keys()],
                     # value=default_db if default_db in outputs_db_list.keys() else
                     # list(outputs_db_list.keys())[0],
                     multi=False
                 ),
                 html.P('Select the Entity:'),
                 dcc.Dropdown(id='select-entity',
                              multi=True
                              ),
                 html.Div(id='inter-value', children=json.dumps({}), style={'display': 'none'}),
                 html.P('Select the attributes to plot the timeseries:'),
                 dcc.Dropdown(id='select-attr',
                              multi=True
                              ),
                 html.Div(id='graph-content-db', children=html.Div(id='graphs-db'))

             ])])
     ])
 ])
 ])


@app.callback(Output('select-db', 'options'),
              [Input('tabs', 'value')])
def update_list_scenario(tab):
    if tab == 'data':
        path = 'C:\\Users\\Pietro\\Code\\Cosim_RL\\federations'
        outputs_db_list = os.listdir(path)
        return [directory for directory in outputs_db_list if os.path.isdir(os.path.join(path, directory))]
    else:
        return []


# selection db
@app.callback([Output('select-entity', 'options'),
               Output('inter-value', 'children')],
              [Input('select-db', 'value')])
def selection_db(db):

    if db is not None:
        path = 'C:\\Users\\Pietro\\Code\\Cosim_RL\\federations'
        res_path = os.path.join(path, db, 'results')

        #return [[{'label': s, 'value': s} for s in entities_attrs_dict.keys()], ent_json]
        outputs_db_list = os.listdir(res_path)
        ret1 =[] #[{'label': s.split('.')[0], 'value': s.split('.')[0]} for s in outputs_db_list]
        ret2 ={}
        for s in outputs_db_list:
            fed_name = s.split('.')[0]
            fed_json = os.path.join(res_path,s)
            data = json.load(open(fed_json))
            ret1.extend({'label':fed_name+'.'+d, 'value':fed_name+'.'+d} for d in data.keys())
            for k in data.keys():
                ret2[fed_name+'.'+k] = {}
                for var in data[k]['inputs'].keys():
                    ret2[fed_name+'.'+k][var] = data[k]['inputs'][var]
                for var in data[k]['outputs'].keys():
                    ret2[fed_name + '.' + k][var] = data[k]['outputs'][var]
                for var in data[k]['messages'].keys():
                    ret2[fed_name + '.' + k][var] = data[k]['messages'][var]
                for var in data[k]['params'].keys():
                    ret2[fed_name + '.' + k][var] = data[k]['params'][var]
        return [ret1, json.dumps(ret2)]
    else:
        return [[], []]


# selection entity
@app.callback(Output('select-attr', 'options'),
              [Input('select-entity', 'value')],
              [State('inter-value', 'children')])
def selection_entity(entities, value):
    attr_list = []
    if entities is not None:
        entities_attrs_dict = json.loads(value)
        for entity in entities:
            attr_list.extend(list(entities_attrs_dict[entity].keys()))
            # attr_list.extend(list(entities_attrs_dict[entity]['outputs'].keys()))
            # attr_list.extend(list(entities_attrs_dict[entity]['messages'].keys()))
            # attr_list.extend(list(entities_attrs_dict[entity]['params'].keys()))

        return [{'label': s, 'value': s} for s in attr_list]
    else:
        return []


# plot attr time series
@app.callback(Output('graphs-db', 'children'),
              [Input('select-attr', 'value')],
              [State('select-entity', 'value'),
               State('inter-value', 'children')])
def update_graph_attr(attrs, entities, data):
    print(data)
    ctx = dash.callback_context
    graphs = []
    # figs = make_subplots(rows=len(attrs), cols=1, shared_xaxes=True,
    #                      vertical_spacing=0.001)

    if ctx.triggered[0]['prop_id'].split('.')[0] == 'select-attr':
        if entities is not None:
            if attrs is not None:
                # if len(attrs) > 2:
                #     class_choiche = 'col-4'
                # elif len(attrs) == 2:
                #     class_choiche = 'col-2'
                # else:
                #     class_choiche = 'col'
                d = json.loads(data)
                for entity in entities:
                    for attr in attrs:
                        id_graph = 1
                        if attr in list(d[entity].keys()):
                            fig = go.Scatter(line={'shape': 'hv'},
                                             y=d[entity][attr],
                                             x=[start_time + datetime.timedelta(seconds=x) for x in d['time']['t']],
                                             name=entity + '.' + attr,
                                             mode='lines+markers',
                                             # fill='tozeroy',
                                             # fillcolor='#6897bb',
                                             marker=dict(size=3))
                            #
                            # figs.add_trace(fig, row=id_graph,col=1)
                            # figs.add_traces()
                            # id_graph = id_graph +1
                            graphs.append(html.Div(dcc.Graph(
                                id=str(id_graph),  # entity + '.' + attr,
                                figure={'data': [fig], 'layout': go.Layout(title='{}'.format(entity + '.' +
                                                                                             attr), yaxis=dict(
                                    range=[min(d[entity][attr]),
                                           max(d[entity][attr])]))}
                            ), className='col'))  # class_choiche))
                            id_graph = +1

        # graphs = html.Div(dcc.Graph(figure=figs))

    return graphs


# @app.callback(Output('relayout','children'),
#               [Input('0','relayoutData')])
# def relayout_event():

if __name__ == '__main__':
    app.run_server(debug=True, port=8049, use_reloader=False)#, threaded=False, processes=4)
    # processes permits to o enable your dash app to handle multiple callbacks in parallel. For production
    # applications, it’s recommended that you use gunicorn.
