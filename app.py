import argparse
import pandas as pd
import trafilatura
from urllib.parse import urlparse
import itertools
from simhash import Simhash

def fetch_content(url):
    downloaded = trafilatura.fetch_url(url)
    return trafilatura.extract(downloaded)

def read_urls(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

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

def main(urltxt):
    urls = read_urls(urltxt)
    urls_contents = []

    for url in urls:
        content = fetch_content(url)
        host = urlparse(url).hostname
        urls_contents.append({'host': host, 'url': url, 'contenu': content})

    # Save the URLs with their contents to a CSV file
    create_csv(urls_contents, 'urls_categorisees.csv')

    # Create URL pairs with different hosts
    df = pd.DataFrame(urls_contents)
    couples = []

    for (i, row1), (j, row2) in itertools.combinations(df.iterrows(), 2):
        if row1['host'] != row2['host']:
            couples.append({'source': row1['url'], 'target': row2['url']})

    # Save the URL pairs to a CSV file
    create_csv(couples, 'couples.csv')

    # Create an Excel file for the texts
    input_texts = [{'identifiant': row['url'], 'texte': row['contenu']} for index, row in df.iterrows()]
    create_excel(input_texts, 'input-text.xlsx')

    # Compute SimHash distances for the URL pairs
    df_couples = pd.DataFrame(couples)
    df_couples['simhash_distance'] = pd.Series(dtype=int)
    
    df_texts = pd.DataFrame(input_texts)

    for index, row in df_couples.iterrows():
        source_url = row['source']
        target_url = row['target']
        
        source_text = df_texts[df_texts['identifiant'] == source_url]['texte'].iloc[0]
        target_text = df_texts[df_texts['identifiant'] == target_url]['texte'].iloc[0]
        
        distance = text_similarity(source_text, target_text)
        df_couples.at[index, 'simhash_distance'] = distance

    # Save the updated couples with SimHash distances to the CSV file
    df_couples.to_csv('couples.csv', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process URLs and compare text similarity using SimHash.")
    parser.add_argument('--li', '-list-urls', type=str, required=True, help='Txt file with URL lists.')
    args = parser.parse_args()
    urltxt = args.li
    main(urltxt)
