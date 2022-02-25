from flask import Flask
from flask import render_template, request

import pandas as pd


df = pd.read_csv('data/final_data.csv')

app = Flask(__name__)

@app.route("/")
def serve_home():
    return render_template('home.html')


@app.route("/by_date", methods=['GET', 'POST'])
def serve_data_page():
    global_min_date = df['exch_date'].min()
    global_max_date = df['exch_date'].max()

    request_min_date = request.args.get('min_date', global_min_date)
    request_max_date = request.args.get('max_date', global_max_date)

    df_temp = df[df['exch_date'].between(request_min_date, request_max_date)]

    df_g = df_temp.groupby(['exch_date'])['notional_1_base'].sum().tail(30)
    df_g_labels = df_g.index.to_series().to_list()
    df_g_data = df_g.to_list()

    return render_template('date_page.html', df_data=df_g.to_dict(),
                           these_labels=df_g_labels, these_data = df_g_data,
                           request_min_date=global_min_date, request_max_date=global_max_date,
                           global_min_date=global_min_date, global_max_date=global_max_date)