import pandas as pd
import trafilatura
from urllib.parse import urlparse
import itertools
from simhash import Simhash
import streamlit as st
from io import BytesIO

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

def create_csv(data):
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

def create_excel(data):
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output

def get_features(text):
    return text.split()

def text_similarity(text1, text2):
    hash1 = Simhash(get_features(text1))
    hash2 = Simhash(get_features(text2))
    return hash1.distance(hash2)

def duplication_rate(distance, hash_bits=64):
    return (1 - distance / hash_bits) * 100

def main(urls):
    urls_contents = []

    for url in urls:
        content = fetch_content(url)
        host = urlparse(url).hostname
        urls_contents.append({'host': host, 'url': url, 'contenu': content})

    df = pd.DataFrame(urls_contents)
    pairs = []

    for (i, row1), (j, row2) in itertools.combinations(df.iterrows(), 2):
        source_url = row1['url']
        target_url = row2['url']
        source_text = row1['contenu']
        target_text = row2['contenu']
        
        if source_text and target_text:
            distance = text_similarity(source_text, target_text)
            rate = duplication_rate(distance)
            pairs.append({
                'source': source_url,
                'target': target_url,
                'simhash_distance': distance,
                'duplication_rate': rate
            })

    df_pairs = pd.DataFrame(pairs)
    return urls_contents, df_pairs

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
        urls_contents, df_pairs = main(urls)
        st.success("Processing completed. Check the generated CSV and XLSX files.")
        
        # Show dataframes
        st.subheader("URL Contents")
        st.dataframe(pd.DataFrame(urls_contents))
        
        st.subheader("URL Pairs with Simhash Distance and Duplication Rate")
        st.dataframe(df_pairs)
        
        # Prepare files for download
        csv_urls = create_csv(urls_contents)
        csv_pairs = create_csv(df_pairs)
        
        st.download_button("Download URL Contents CSV", csv_urls, "urls_categorisees.csv", "text/csv")
        st.download_button("Download URL Pairs CSV", csv_pairs, "pairs.csv", "text/csv")
    else:
        st.error("Please provide URLs either by uploading a file or pasting URLs in the text area.")
