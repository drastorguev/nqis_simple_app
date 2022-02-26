from flask import Flask
from flask import render_template, request

import pandas as pd
import seaborn as sns
import random


df = pd.read_csv('data/final_data.csv')
df['exch_date'] = pd.to_datetime(df['exch_date'])

app = Flask(__name__)

@app.route("/")
def serve_home():
    last_day_date = df['exch_date'].max()
    last_day_df = df[df['exch_date'] == last_day_date]
    last_day_vol = round(last_day_df['notional_1_base'].sum() / 1000000, 1)
    last_day_count = len(last_day_df['notional_1_base'])
    last_day_currency = last_day_df.groupby(['Notional Currency 1'])['notional_1_base'].sum().sort_values().index[-1]
    last_day_curr_vol = round(last_day_df.groupby(['Notional Currency 1'])['notional_1_base'].sum().sort_values()[-1]  / 1000000000, 1)

    top_ten_currencies = set(last_day_df.groupby(['Notional Currency 1'])['notional_1_base'].sum().sort_values().index[-10:])

    table_html = last_day_df[last_day_df['Notional Currency 1'].isin(top_ten_currencies)]. \
            groupby(['Product ID','Notional Currency 1'])['notional_1_base']. \
            sum().unstack().fillna(0).divide(1000000).round(1).to_html(classes=['table', 'table-striped', 'table-bordered'])

    return render_template('home.html', last_day_vol=last_day_vol, last_day_count=last_day_count,
                           last_day_curr_vol=last_day_curr_vol,
                           last_day_currency=last_day_currency, last_day_date=last_day_date.strftime('%d/%m/%Y'),
                           table_html=table_html)


@app.route("/by_date", methods=['GET', 'POST'])
def serve_data_page():
    keep_columns = set(
        ['Product ID', 'Action', 'Transaction Type', 'Leg 1 - Floating Rate Index', 'Leg 2 - Floating Rate Index',
         'Notional Currency 1', 'expiration_year', 'contract_length'])

    df_columns = [x for x in df.columns if x in keep_columns]


    global_min_date = df['exch_date'].min()
    global_max_date = df['exch_date'].max()

    global_exp_year_min_date = df['expiration_year'].min()
    global_exp_year_max_date = df['expiration_year'].max()

    request_min_date = request.args.get('min_date', global_min_date)
    if not request_min_date:
        request_min_date = global_min_date

    request_max_date = request.args.get('max_date', global_max_date)
    if not request_max_date:
        request_max_date = global_max_date

    request_min_exp_year = request.args.get('min_exp_year')
    if not request_min_exp_year:
        request_min_exp_year = global_exp_year_min_date

    request_max_exp_year = request.args.get('max_exp_year')
    if not request_max_exp_year:
        request_max_exp_year = global_exp_year_max_date

    df_temp = df[df['exch_date'].between(request_min_date, request_max_date)]


    df_temp = df_temp[(df_temp['expiration_year'] >= int(request_min_exp_year)) &
                      (df_temp['expiration_year'] <= int(request_max_exp_year))]

    time_variable = request.args.get('time_variable', 'exch_date')

    if time_variable not in ['expiration_year', 'exch_date']:
        time_variable = 'exch_date'

    sub_g_var = request.args.get('sub_group_variable', '')

    if sub_g_var in keep_columns:
        df_g = df_temp.groupby([time_variable, sub_g_var])['notional_1_base'].sum().unstack().fillna(0)
        df_g_dict = df_g.to_dict().items()
        chart_data = []

        palette = sns.color_palette(None, len(df_g_dict)).as_hex()
        random.shuffle(palette, random.seed(42))

        i = 0
        for k,v in df_g_dict:
            dataset = {
                'label': k,
                'data': list(v.values()),
                'backgroundColor': str(palette[i])
            }
            chart_data.append(dataset)
            i+=1

    else:

        df_g = df_temp.groupby([time_variable])['notional_1_base'].sum()
        chart_data = [{'label': f'Only Variable: {time_variable}', 'data': df_g.to_list()}]

    if time_variable == 'exch_date':
        chart_labels = df_g.index.to_series().dt.date.apply(lambda x: x.strftime('%d/%m/%y')).to_list()

    elif time_variable == 'expiration_year':
        chart_labels = df_g.index.to_series().to_list()

    total_volume = round(df_temp['notional_1_base'].sum() / 1000000, 1)
    total_mean = round(df_temp['notional_1_base'].mean() / 1000000, 1)
    total_count = len(df_temp)

    return render_template('date_page.html', df_data=df_g.to_dict(),
                           chart_labels=chart_labels, chart_data = chart_data,
                           global_min_date=global_min_date.strftime('%d/%m/%Y'), global_max_date=global_max_date.strftime('%d/%m/%Y'),
                           global_exp_year_min_date=global_exp_year_min_date,
                           global_exp_year_max_date=global_exp_year_max_date,
                           columns_list=df_columns,
                           total_volume_disp=total_volume,
                           total_count_disp=total_count,
                           total_mean_disp=total_mean)