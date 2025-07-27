import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import random
from collections import Counter


st.title("📱 WhatsApp Chat Visualizer")

# File upload
uploaded_file = st.file_uploader("Upload WhatsApp chat (.txt)", type=["txt"])

# Preprocessing function
def parse_and_preprocess(chat_text):
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

    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.time
    df['hour'] = df['timestamp'].dt.hour
    df['day_name'] = df['timestamp'].dt.day_name()
    df['month'] = df['timestamp'].dt.month_name()
    df['word_count'] = df['message'].apply(lambda x: len(x.split()))
    df['char_count'] = df['message'].apply(len)
    df['url_count'] = df['message'].apply(lambda x: len(re.findall(r'https?://\S+|www\.\S+', x)))
    df['media_flag'] = df['message'].apply(lambda x: '<Media omitted>' in x or x.lower().startswith('<media') or x.lower().startswith('omitted>'))

    return df

if uploaded_file is not None:

    chat_text = uploaded_file.getvalue().decode("utf-8")
    df = parse_and_preprocess(chat_text)
    st.success("Chat parsed successfully!")

    st.header("📊 Chat Visualizations")

    # 5. Word Cloud (Simulated using Counter and matplotlib)
    st.subheader("5. Word Cloud")

    # Combine all messages
    all_words = ' '.join(df['message'].dropna().astype(str)).lower()

    # Remove common stopwords (you can expand this list)
    stopwords = set([
        "the", "to", "and", "i", "you", "a", "of", "is", "in", "it", "for", "on", "that",
        "this", "was", "with", "are", "but", "be", "have", "not", "at", "my", "me", "we",
        "so", "do", "just", "your", "if", "they", "what", "can", "all", "no"
    ])

    # Tokenize and filter words
    words = [word.strip(".,!?()[]\"'") for word in all_words.split()]
    words = [word for word in words if word not in stopwords and len(word) > 2 and not word.startswith("http")]

    word_freq = Counter(words)
    most_common = word_freq.most_common(50)

    # Create a pseudo wordcloud using scatter plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")

    for word, freq in most_common:
        x, y = random.uniform(0, 1), random.uniform(0, 1)
        size = min(freq * 2,30)  # Adjust multiplier as needed
        ax.text(x, y, word, fontsize=size, alpha=0.7,
                ha='center', va='center', transform=ax.transAxes,
                color=(random.random(), random.random(), random.random()))

    st.pyplot(fig)
    
    # 1. Daily Messages
    st.subheader("1. Messages Per Day")
    daily_msgs = df.groupby('date').size()
    fig, ax = plt.subplots()
    daily_msgs.plot(kind='line', ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Messages")
    ax.set_title("Messages Per Day")
    st.pyplot(fig)

    # 2. Messages by Hour
    st.subheader("2. Messages by Hour of Day")
    hourly_msgs = df.groupby('hour').size()
    fig, ax = plt.subplots()
    hourly_msgs.plot(kind='bar', color='skyblue', ax=ax)
    ax.set_xlabel("Hour (24hr)")
    ax.set_ylabel("Messages")
    ax.set_title("Hourly Chat Activity")
    st.pyplot(fig)

    # 3. Messages by Sender
    st.subheader("3. Messages Per Sender")
    sender_msgs = df['sender'].value_counts()
    fig, ax = plt.subplots()
    sender_msgs.plot(kind='bar', color='lightcoral', ax=ax)
    ax.set_ylabel("Total Messages")
    ax.set_title("Message Count by Sender")
    st.pyplot(fig)

    # 4. Heatmap: Hour vs Sender
    st.subheader("4. Heatmap: Sender vs Hour")
    heatmap_data = df.groupby(['sender', 'hour']).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=.5, annot=True, fmt='d', ax=ax)
    ax.set_title("Messages by Hour and Sender")
    st.pyplot(fig)



