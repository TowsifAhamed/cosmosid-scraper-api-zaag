import psycopg2
import json
import os
from psycopg2 import sql

# Establish a connection to the PostgreSQL database
connection = psycopg2.connect(
    dbname="cosmosidscrpdb",
    user="zaaguser",
    password="zaagpass",
    host="localhost",
    # port="your_port"
)

# Create a cursor object
cursor = connection.cursor()

# Create table for collected links data
def create_collected_links_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS collected_links (
        name TEXT NOT NULL,
        url TEXT PRIMARY KEY,
        folder TEXT
    );
    """
    cursor.execute(create_table_query)
    connection.commit()

# Create table for exported results data
def create_exported_results_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS exported_results (
        url TEXT REFERENCES collected_links(url),
        result TEXT,
        taxonomy_level TEXT NULL,
        downloaded_file TEXT,
        PRIMARY KEY (url, result, taxonomy_level)
    );
    """
    cursor.execute(create_table_query)
    connection.commit()

# Insert or update collected links data
def upsert_collected_links(collected_links):
    upsert_query = """
    INSERT INTO collected_links (name, url, folder)
    VALUES (%s, %s, %s)
    ON CONFLICT (url) DO UPDATE SET
    name = EXCLUDED.name,
    folder = EXCLUDED.folder;
    """
    for link in collected_links:
        cursor.execute(upsert_query, (link['name'], link['url'], link['folder']))
    connection.commit()

# Insert or update exported results data
def upsert_exported_results(exported_results):
    upsert_query = """
    INSERT INTO exported_results (url, result, taxonomy_level, downloaded_file)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (url, result, taxonomy_level) DO UPDATE SET
    downloaded_file = EXCLUDED.downloaded_file;
    """
    for result in exported_results:
        taxonomy_level = result.get('taxonomy_level', 'N/A')  # This field might be missing
        cursor.execute(upsert_query, (result['link_url'], result['result'], taxonomy_level, result['downloaded_file']))
    connection.commit()

# Load JSON data from the files and upsert into PostgreSQL
def load_and_upsert_data():
    # Load collected_links.json
    if os.path.exists('collected_links.json'):
        with open('collected_links.json', 'r') as json_file:
            collected_links = json.load(json_file)
            upsert_collected_links(collected_links)

    # Load exported_results.json
    if os.path.exists('exported_results.json'):
        with open('exported_results.json', 'r') as json_file:
            exported_results = json.load(json_file)
            upsert_exported_results(exported_results)

    # Print the number of rows in each table
    cursor.execute("SELECT COUNT(*) FROM collected_links;")
    collected_links_count = cursor.fetchone()[0]
    print(f"Number of rows in collected_links: {collected_links_count}")

    cursor.execute("SELECT COUNT(*) FROM exported_results;")
    exported_results_count = cursor.fetchone()[0]
    print(f"Number of rows in exported_results: {exported_results_count}")

# Main execution
def main():
    create_collected_links_table()
    create_exported_results_table()
    load_and_upsert_data()
    
    # Close the cursor and connection
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
