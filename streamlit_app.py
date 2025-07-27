import pandas as pd
import re

def count_urls(text):
    """Simple regex-based URL counter"""
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return len(url_pattern.findall(text))

def parse_and_preprocess(chat_text):
    # Regex to identify start of each message
    line_start_pattern = re.compile(r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\s?[APap]?\.?[Mm]?\.?\]\s[^:]+:')
    details_pattern = re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}[\s\u202f]?[APap]?\.?[Mm]?\.?)\]\s([^:]+):')

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

        # Handle multiple date formats
        timestamp = None
        for fmt in ('%d/%m/%y %I:%M:%S %p', '%d/%m/%Y %H:%M:%S'):
            try:
                timestamp = pd.to_datetime(timestamp_str, format=fmt)
                break
            except ValueError:
                continue
        if not timestamp:
            continue

        message = messages[i].strip()
        chat_data.append([timestamp, sender.strip(), message])

    df = pd.DataFrame(chat_data, columns=['timestamp', 'sender', 'message'])

    # Extract features
    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.time
    df['hour'] = df['timestamp'].dt.hour
    df['day_name'] = df['timestamp'].dt.day_name()
    df['month'] = df['timestamp'].dt.month_name()
    df['word_count'] = df['message'].apply(lambda x: len(x.split()))
    df['char_count'] = df['message'].apply(len)
    df['url_count'] = df['message'].apply(count_urls)
    df['media_flag'] = df['message'].apply(lambda x: '<Media omitted>' in x or x.lower().startswith('<media') or x.lower().startswith('omitted>'))

    return df


def basic_chat_stats(df):
    total_messages = df.shape[0]
    total_words = df['word_count'].sum()
    total_chars = df['char_count'].sum()
    media_msgs = df['media_flag'].sum()
    link_msgs = df['url_count'].sum()
    senders = df['sender'].value_counts().to_dict()

    return {
        'Total Messages': total_messages,
        'Total Words': total_words,
        'Total Characters': total_chars,
        'Media Messages': media_msgs,
        'Links Shared': link_msgs,
        'Messages Per Person': senders
    }


import streamlit as st

st.title("WhatsApp Chat Analyzer")

uploaded_file = st.file_uploader("Upload a WhatsApp chat (.txt file)", type=["txt"])

if uploaded_file is not None:
    chat_text = uploaded_file.getvalue().decode("utf-8")
    df = parse_and_preprocess(chat_text)
    st.success("Chat processed!")

    st.subheader("Basic Chat Stats")
    stats = basic_chat_stats(df)
    for key, value in stats.items():
        if isinstance(value, dict):
            for sender, count in value.items():
                st.write(f"**{sender}**: {count} messages")
        else:
            st.write(f"**{key}**: {value}")

    st.subheader("Sample Data")
    st.dataframe(df.head(20))



import matplotlib.pyplot as plt
import seaborn as sns

# Meassages per day

df = parse_and_preprocess(chat_text)

st.subheader("1. Daily Message Count")

daily_msgs = df.groupby('date').size()

fig, ax = plt.subplots()
daily_msgs.plot(kind='line', ax=ax)
ax.set_xlabel("Date")
ax.set_ylabel("Messages")
ax.set_title("Messages Per Day")
st.pyplot(fig)

st.line_chart(daily_msgs)
