import pandas as pd
import re
from urlextract import URLExtract

extractor = URLExtract()

def parse_and_preprocess(chat_text):
    # Step 1: Regex patterns to identify message boundaries and components
    line_start_pattern = re.compile(r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\s?[APap]?\.?[Mm]?\.?\]\s[^:]+:')
    details_pattern = re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}[\s\u202f]?[APap]?\.?[Mm]?\.?)\]\s([^:]+):')

    # Step 2: Parse messages
    messages = line_start_pattern.split(chat_text)[1:]
    headers = line_start_pattern.findall(chat_text)
    
    chat_data = []

    for i in range(len(messages)):
        match = details_pattern.match(headers[i])
        if not match:
            continue
        date, time, sender = match.groups()
        time = time.replace('\u202f', ' ').strip()
        timestamp_str = f"{date} {time}"

        try:
            timestamp = pd.to_datetime(timestamp_str, format='%d/%m/%y %I:%M:%S %p')
        except ValueError:
            try:
                timestamp = pd.to_datetime(timestamp_str, format='%d/%m/%Y %H:%M:%S')
            except ValueError:
                continue

        message = messages[i].strip()
        chat_data.append([timestamp, sender.strip(), message])

    # Step 3: Create DataFrame
    df = pd.DataFrame(chat_data, columns=['timestamp', 'sender', 'message'])

    # Step 4: Derived columns (no emoji column now)
    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.time
    df['hour'] = df['timestamp'].dt.hour
    df['day_name'] = df['timestamp'].dt.day_name()
    df['month'] = df['timestamp'].dt.month_name()

    df['word_count'] = df['message'].apply(lambda x: len(x.split()))
    df['char_count'] = df['message'].apply(len)
    df['url_count'] = df['message'].apply(lambda x: len(extractor.find_urls(x)))
    df['media_flag'] = df['message'].apply(lambda x: '<Media omitted>' in x or x.lower().startswith('<media') or x.lower().startswith('omitted>'))

    return df


def basic_chat_stats(df):
    total_messages = df.shape[0]
    total_words = df['word_count'].sum()
    total_chars = df['char_count'].sum()
    media_msgs = df['media_flag'].sum()
    links_shared = df['url_count'].sum()

    senders = df['sender'].value_counts().to_dict()

    return {
        'Total Messages': total_messages,
        'Total Words': total_words,
        'Total Characters': total_chars,
        'Media Messages': media_msgs,
        'Links Shared': links_shared,
        'Messages Per Person': senders
    }

import streamlit as st

st.title("WhatsApp Chat Visualizer")

uploaded_file = st.file_uploader("Upload WhatsApp chat (.txt)", type=["txt"])

if uploaded_file is not None:
    chat_text = uploaded_file.getvalue().decode("utf-8")
    df = parse_and_preprocess(chat_text)
    st.success("Chat processed successfully!")

    stats = basic_chat_stats(df)

    st.header("📊 Basic Chat Statistics")
    for k, v in stats.items():
        if isinstance(v, dict):
            for sender, count in v.items():
                st.write(f"**{sender}:** {count} messages")
        else:
            st.write(f"**{k}:** {v}")
