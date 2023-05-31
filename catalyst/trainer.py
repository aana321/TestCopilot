import os
import textract
import tiktoken
from config import *
from storageClient import *
from embeddingsInterface import file_handler


data_dir = os.path.join(os.curdir, FOLDER_NAME)


def get_pdf_files():
    pdf_files = sorted([x for x in os.listdir(data_dir) if 'DS_Store' not in x])
    return pdf_files


def verify_redis_connection(client):
    if client.ping():
        return True
    else:
        return False


def create_search_index(redis_client):
    try:
        redis_client.ft(INDEX_NAME).info()
        print("Index already exists")
    except Exception as e:
        print(e)
        # Create RediSearch Index
        print('Not there yet. Creating')
        create_hnsw_index(redis_client, VECTOR_FIELD_NAME, INDEX_NAME)


def ingest_data(pdf_files, redis_client):
    openai.api_key = OPEN_API_KEY
    tokenizer = tiktoken.get_encoding("cl100k_base")
    # Process each PDF file and prepare for embedding
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_dir, pdf_file)
        print(pdf_path)

        # Extract the raw text from each PDF using textract
        text = textract.process(pdf_path, method='pdfminer')

        # Chunk each document, embed the contents and load to Redis
        file_handler((pdf_file, text.decode("utf-8")), tokenizer, redis_client, VECTOR_FIELD_NAME)


def executor():
    try:
        print(get_pdf_files())
        redis_client = get_redis_connection(REDIS_HOST, REDIS_PORT)
        create_search_index(redis_client)
        ingest_data(get_pdf_files(), redis_client)
    except Exception as e:
        print(e)
        print('Retry....')


if __name__ == "__main__":
    executor()
