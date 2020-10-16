'''
https://stackoverflow.com/questions/43146528/how-to-extract-all-the-emojis-from-text/43146653
https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.resample.html
https://stackoverflow.com/questions/17706109/summing-the-number-of-occurrences-per-day-pandas
https://www.chartjs.org/docs/latest/
https://stackoverflow.com/questions/46786211/counting-the-frequency-of-words-in-a-pandas-data-frame
'''

import os
import pandas as pd
import emoji
import regex
import re
from collections import Counter
import json
import random
import time

from flask import Flask, render_template, request, redirect, send_from_directory, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config[
    "FILE_UPLOADS"] = "../data/uploads"
app.config["ALLOWED_FILE_EXTENSIONS"] = ["TXT"]


def allowed_file(filename):
    # We only want files with a . in the filename
    if not "." in filename:
        return False

    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]

    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in app.config["ALLOWED_FILE_EXTENSIONS"]:
        return True
    else:
        return False


def generate_random_hex(limit):
    hex_list = []
    for i in range(limit):
        random_number = random.randint(0, 16777215)
        hex_number = str(hex(random_number))
        hex_number = '#' + hex_number[2:]
        hex_list.append(hex_number)

    return hex_list


def convert_num_month(busiest_month):
    t = time.strptime(f"{busiest_month}", "%m")
    busiest_month = time.strftime("%B", t)
    return f'{busiest_month}'


def convert_num_12hour(busiest_hour):
    t = time.strptime(f"{busiest_hour}", "%H")
    busiest_hour = time.strftime("%I %p", t)
    return f'{busiest_hour}'


def total_url_in_text(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return len([x[0] for x in url])


def total_emojis_in_text(text):
    emoji_list = []
    data = regex.findall(r'\X', text)
    for word in data:
        if any(char in emoji.UNICODE_EMOJI for char in word):
            emoji_list.append(word)

    return len(emoji_list)


def emojis_in_text(text):
    emoji_list = []
    data = regex.findall(r'\X', text)
    for word in data:
        if any(char in emoji.UNICODE_EMOJI for char in word):
            emoji_list.append(word)

    if len(emoji_list) > 0:
        return "".join(emoji_list)


def data_preprocess(chat_file):
    ###

    pd.set_option('max_colwidth', 50)
    pd.set_option('display.max_columns', None)

    whatsapp_chat_file = open(chat_file, 'r')
    df = pd.DataFrame(data=[line.split(' - ', 1) for line in whatsapp_chat_file], columns=['DateTime', 'Message'])
    df[['Member', 'Message']] = df.Message.apply(lambda x: pd.Series(str(x).split(":", 1))).dropna()
    df = df.dropna()

    df['DateTime'] = pd.to_datetime(df['DateTime'])

    df.index = df['DateTime']

    # print(df)

    chat_start = df.index[0].strftime("%b %d %Y")
    chat_end = df.index[-1].strftime("%b %d %Y")

    total_messages = df['Message'].count()

    total_emojis = df['Message'].apply(total_emojis_in_text).sum()

    different_emojis = df['Message'].apply(emojis_in_text).dropna()
    different_emojis_list = []
    for x in different_emojis:
        for y in x:
            if y not in different_emojis_list:
                different_emojis_list.append(y)

    emojis = df['Message'].apply(emojis_in_text)
    most_frequent_emojis = sorted(Counter("".join(emojis.dropna().tolist())).items(), key=lambda pair: pair[1],
                                  reverse=True)

    common_emoji_emoji, common_emoji_count = most_frequent_emojis[0]

    total_media = df['Message'].str.contains('<Media omitted>').sum()

    total_urls = df['Message'].apply(total_url_in_text).sum()

    total_messages_member_one = df['Member'].value_counts()[0]
    total_messages_member_two = df['Member'].value_counts()[1]
    average_messages = int(round(df['Member'].value_counts().mean()))

    name_member_one = df['Member'].unique()[0]
    name_member_two = df['Member'].unique()[1]

    data_busy_hour = df.groupby(df.index.hour).count()
    data_busy_day = df.groupby(df.index.day).count()
    data_busy_month = df.groupby(df.index.month).count()

    busiest_hour = data_busy_hour.sort_values(by=['Message'], ascending=False).index[0]
    busiest_hour_message_count = data_busy_hour['Message'][busiest_hour]

    busiest_day = data_busy_day.sort_values(by=['Message'], ascending=False).index[0]
    busiest_day_message_count = data_busy_day['Message'][busiest_day]

    busiest_month = data_busy_month.sort_values(by=['Message'], ascending=False).index[0]
    busiest_month_message_count = data_busy_month['Message'][busiest_month]

    busiest_data = {
        'busiest_hour': f"{convert_num_12hour(busiest_hour)}",
        'busiest_hour_message_count': f"{busiest_hour_message_count}",
        'busiest_day': f'{busiest_day}',
        'busiest_day_message_count': f'{busiest_day_message_count}',
        'busiest_month': f"{convert_num_month(busiest_month)}",
        'busiest_month_message_count': f"{busiest_month_message_count}",
    }

    data_busy_hour_json = {
        "labels": [convert_num_12hour(i) for i in data_busy_hour.index.tolist()],
        "datasets": [
            {
                "label": "Messages per Hour",
                "backgroundColor": generate_random_hex(data_busy_hour['Message'].shape[0]),
                "data": data_busy_hour['Message'].values.tolist()
            }
        ]
    }

    data_busy_day_json = {
        "labels": data_busy_day.index.tolist(),
        "datasets": [
            {
                "label": "Messages per Day",
                "backgroundColor": generate_random_hex(data_busy_day['Message'].shape[0]),
                "data": data_busy_day['Message'].values.tolist()
            }
        ]
    }

    data_busy_month_json = {
        "labels": [convert_num_month(i) for i in data_busy_month.index.tolist()],
        "datasets": [
            {
                "label": "Messages per Month",
                "backgroundColor": generate_random_hex(data_busy_month['Message'].shape[0]),
                "data": data_busy_month['Message'].values.tolist()
            }
        ]
    }

    chat_data = {
        "chat_start": chat_start,
        "chat_end": chat_end,
        "total_messages": total_messages,
        "total_emojis": total_emojis,
        "total_media": total_media,
        "total_urls": total_urls,
        "total_messages_member_one": total_messages_member_one,
        "total_messages_member_two": total_messages_member_two,
        "average_messages": average_messages,
        "name_member_one": name_member_one,
        "name_member_two": name_member_two,
        "common_emoji_emoji": common_emoji_emoji,
        "common_emoji_count": common_emoji_count,
        "different_emojis": len(different_emojis_list)
    }

    return chat_data, \
           json.dumps(data_busy_hour_json), json.dumps(data_busy_day_json), json.dumps(data_busy_month_json), \
           busiest_data

    ###


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/visualize/<filename>')
def visualize(filename):
    chat_file = f"{app.config['FILE_UPLOADS']}/{filename}"

    CHECK_FLAG = "Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them. Tap to learn more."
    whatsapp_chat_file = open(chat_file, 'r')

    if CHECK_FLAG in f"{whatsapp_chat_file.readlines()}":
        chat_data, \
        data_busy_hour_json, data_busy_day_json, data_busy_month_json, \
        busiest_data = data_preprocess(chat_file)

        return render_template('base.html', chat_data=chat_data,
                               data_busy_hour_json=data_busy_hour_json,
                               data_busy_day_json=data_busy_day_json,
                               data_busy_month_json=data_busy_month_json,
                               busiest_data=busiest_data)
    else:
        return render_template('base_error.html', error="Invalid File Format")


@app.route("/upload-chat", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":

        if request.files:
            chat_file = request.files["chat_file"]

            if chat_file.filename == "":
                print("No filename")
                return redirect(request.url)

            if allowed_file(chat_file.filename):
                filename = secure_filename(chat_file.filename)

                file_path = os.path.join(app.config["FILE_UPLOADS"], filename)

                chat_file.save(file_path)

                # print(f"File: {chat_file.filename} saved at {file_path}")

                return redirect(url_for('visualize', filename=filename))

            else:
                print("That file extension is not allowed")
                return redirect(request.url)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
    # 10.0.2.2:5000 for android virtual device
