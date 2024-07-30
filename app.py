import pandas as pd
import trafilatura
from urllib.parse import urlparse
import itertools
from simhash import Simhash
import streamlit as st
from io import StringIO

def fetch_content(url):
    downloaded = trafilatura.fetch_url(url)
    return trafilatura.extract(downloaded)

def read_urls_from_text(text):
    return [line.strip() for line in text.split('\n') if line.strip()]

def read_urls_from_file(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        df = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or XLSX file.")
    return df['url'].tolist()

def create_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

def create_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

def get_features(text):
    return text.split()

def text_similarity(text1, text2):
    hash1 = Simhash(get_features(text1))
    hash2 = Simhash(get_features(text2))
    return hash1.distance(hash2)

def main(urls):
    urls_contents = []

    for url in urls:
        content = fetch_content(url)
        host = urlparse(url).hostname
        urls_contents.append({'host': host, 'url': url, 'contenu': content})

    create_csv(urls_contents, 'urls_categorisees.csv')

    df = pd.DataFrame(urls_contents)
    couples = []

    for (i, row1), (j, row2) in itertools.combinations(df.iterrows(), 2):
        if row1['host'] != row2['host']:
            couples.append({'source': row1['url'], 'target': row2['url']})

    create_csv(couples, 'couples.csv')

    input_texts = [{'identifiant': row['url'], 'texte': row['contenu']} for index, row in df.iterrows()]
    create_excel(input_texts, 'input-text.xlsx')

    df_couples = pd.DataFrame(couples)
    df_couples['simhash_distance'] = pd.Series(dtype=int)
    
    df_texts = pd.DataFrame(input_texts)

    for index, row in df_couples.iterrows():
        source_url = row['source']
        target_url = row['target']
        
        source_text = df_texts[df_texts['identifiant'] == source_url]['texte'].iloc(0)
        target_text = df_texts[df_texts['identifiant'] == target_url]['texte'].iloc(0)
        
        distance = text_similarity(source_text, target_text)
        df_couples.at[index, 'simhash_distance'] = distance

    df_couples.to_csv('couples.csv', index=False)

st.title("URL Content Similarity Checker")
st.write("Upload a CSV/XLSX file with URLs or paste URLs below:")

uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])
url_text = st.text_area("Or paste your URLs here (one per line):")

if st.button("Process"):
    if uploaded_file is not None:
        urls = read_urls_from_file(uploaded_file)
    else:
        urls = read_urls_from_text(url_text)
    
    if urls:
        main(urls)
        st.success("Processing completed. Check the generated CSV and XLSX files.")
        st.download_button("Download URL Contents CSV", "urls_categorisees.csv")
        st.download_button("Download URL Pairs CSV", "couples.csv")
        st.download_button("Download Input Texts Excel", "input-text.xlsx")
    else:
        st.error("Please provide URLs either by uploading a file or pasting URLs in the text area.")
