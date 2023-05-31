import openai
import pandas as pd
import numpy as np
from typing import Iterator
from numpy import array, average
from regex import regex
from config import TEXT_EMBEDDING_CHUNK_SIZE, EMBEDDINGS_MODEL
from storageClient import load_vectors


def get_average_of_column_of_list(two_dimensional_list):
    """This function takes a list of lists as input, where each inner list represents a row of values. The function then
    calculates the average value for each column of the input list and returns a list containing the column averages.
    To use this function, you will need to make sure that each inner list has the same number of elements. Otherwise,
    the function may raise an error. """

    if len(two_dimensional_list) == 1:
        return two_dimensional_list[0]
    else:
        list_array = array(two_dimensional_list)
        average_list = average(list_array, axis=0)
        return average_list.tolist()


def get_embeddings(text_array, engine):
    """
    This function uses OpenAI's Engine class to generate embeddings for the input text_array.
    The id parameter specifies the ID of the OpenAI engine to be used for generating the embeddings.

    The embeddings method of the Engine class is then called with input=text_array as the argument to generate
    embeddings for the text. The embeddings are returned as a dictionary in the "data" field of the response.

    :param text_array: input to generate embeddings
    :param engine: ID of the OpenAI engine to be used for generating the embeddings
    :return: The embeddings are returned as a dictionary in the "data" field of the response
    """

    return openai.Engine(id=engine).embeddings(input=text_array)["data"]


# Split a text into smaller chunks of size n, preferably ending at the end of a sentence
def split_text_on_token(text, n, tokenizer):
    """
    This is a Python function that can be used to split a given text into smaller chunks of a specified size n,
    based on the tokenization of the text using a provided tokenizer.

    The function takes in three input parameters:
    :param text: the text to be chunked
    :param n: the desired chunk size, in tokens
    :param tokenizer: tokenizer object that is used to encode and decode the text into tokens
    :return: The function returns a generator object
    """
    tokens = tokenizer.encode(text)
    """Yield successive n-sized chunks from text."""
    i = 0
    while i < len(tokens):
        # Find the nearest end of sentence within a range of 0.5 * n and 1.5 * n tokens
        j = min(i + int(1.5 * n), len(tokens))
        while j > i + int(0.5 * n):
            # Decode the tokens and check for full stop or newline
            chunk = tokenizer.decode(tokens[i:j])
            if chunk.endswith(".") or chunk.endswith("\n"):
                break
            j -= 1
        # If no end of sentence found, use n tokens as the chunk size
        if j == i + int(0.5 * n):
            j = min(i + n, len(tokens))
        yield tokens[i:j]
        i = j


# Create embeddings for a text using a tokenizer and an OpenAI engine
def create_embeddings_for_text(text, tokenizer):
    """Return a list of tuples (text_chunk, embedding) and an average embedding for a text."""

    # store the token chunks depending on the tokenizer and size in a list named as token_chunks
    token_chunks = list(split_text_on_token(text, TEXT_EMBEDDING_CHUNK_SIZE, tokenizer))
    # iterate over token chunks and decode the token chunks into text to create an array of text depending on token
    # and embedding size
    text_chunks = [tokenizer.decode(token_chunk) for token_chunk in token_chunks]

    # get embeddings for every text chunk from open api
    embeddings_response = get_embeddings(text_chunks, EMBEDDINGS_MODEL)
    # creating an array of embeddings from the embedding response
    embeddings = [embedding["embedding"] for embedding in embeddings_response]

    text_embeddings = list(zip(text_chunks, embeddings))

    average_embedding = get_average_of_column_of_list(embeddings)

    return text_embeddings, average_embedding


def create_unique_id_for_file_chunk(filename, chunk_index):
    """
    The purpose of the function is to create a unique ID for a file chunk, which can be used to identify the chunk in a larger context.
    :param filename: name of the file
    :param chunk_index: index value
    :return: returns the resulting string, which is the unique ID for the file chunk
    """
    return str(filename + "-!" + str(chunk_index))


def clean_text(text):
    # Remove any characters except alphabets, numbers, dots, and slashes (for URLs)
    cleaned_text = regex.sub(r'[^\w./ ]+', '', text)
    # Replace multiple spaces with a single space
    cleaned_text = regex.sub(' +', ' ', cleaned_text)
    # Replace any forward slashes with a space
    cleaned_text = cleaned_text.replace('/', ' ')
    # Replace any double dots with a single dot
    cleaned_text = cleaned_text.replace('..', '.')
    return cleaned_text.strip()


def file_handler(file, tokenizer, redis_conn, text_embedding_field):
    filename = file[0]
    file_body_string = file[1]

    # Clean up the file string by replacing newlines and double spaces and semi-colons
    # clean_file_body_string = file_body_string.replace("  ", " ").replace("\n", "; ").replace(';', ' ')
    clean_file_body_string = clean_text(file_body_string)

    # Add the filename to the text to embed
    text_to_embed = "Filename is: {}; {}".format(
        filename, clean_file_body_string)

    # Create embeddings for the text
    try:
        text_embeddings, average_embedding = create_embeddings_for_text(
            text_to_embed, tokenizer)
        # print("[handle_file_string] Created embedding for {}".format(filename))
    except Exception as e:
        print("[handle_file_string] Error creating embedding: {}".format(e))

    # Get the vectors array of triples: file_chunk_id, embedding, metadata for each embedding
    # Metadata is a dict with keys: filename, file_chunk_index
    vectors = []
    for i, (text_chunk, embedding) in enumerate(text_embeddings):
        id = create_unique_id_for_file_chunk(filename, i)
        vectors.append(({'id': id
            , "vector": embedding, 'metadata': {"filename": filename
                , "text_chunk": text_chunk
                , "file_chunk_index": i}}))

    try:
        load_vectors(redis_conn, vectors, text_embedding_field)

    except Exception as e:
        print(f'Ran into a problem uploading to Redis: {e}')


def file_handler_batch(file, tokenizer, redis_conn, text_embedding_field, batch_size=100):
    filename = file[0]
    file_body_string = file[1]

    # Clean up the file string by replacing newlines and double spaces and semi-colons
    clean_file_body_string = clean_text(file_body_string)

    # Add the filename to the text to embed
    text_to_embed = "Filename is: {}; {}".format(filename, clean_file_body_string)

    # Create embeddings for the text
    try:
        # Tokenize the text
        tokenized_text = tokenizer(text_to_embed, padding=True, truncation=True, return_tensors='pt')
        
        # Create a BatchGenerator object with the given batch size
        batch_generator = BatchGenerator(batch_size=batch_size)
        
        # Generate batches of tokenized text
        for batch_num, batch in enumerate(batch_generator(tokenized_text)):
            # Convert the tokenized text to embeddings
            embeddings = get_embeddings(batch, EMBEDDINGS_MODEL)
            
            # Get the vectors array of triples: file_chunk_id, embedding, metadata for each embedding
            # Metadata is a dict with keys: filename, file_chunk_index
            vectors = []
            for i, embedding in enumerate(embeddings):
                text_chunk = tokenizer.decode(batch['input_ids'][i])
                id = create_unique_id_for_file_chunk(filename, batch_num * batch_size + i)
                vectors.append({'id': id, "vector": embedding, 'metadata': {"filename": filename, "text_chunk": text_chunk, "file_chunk_index": batch_num * batch_size + i}})
            
            # Load the vectors into Redis
            try:
                load_vectors(redis_conn, vectors, text_embedding_field)
            except Exception as e:
                print(f'Ran into a problem uploading to Redis: {e}')
            
    except Exception as e:
        print("[handle_file_string] Error creating embedding: {}".format(e))



# Make a class to generate batches for insertion
class BatchGenerator:
    """
    This is a Python class that defines a batch generator for processing large DataFrames in smaller chunks.
    Here's what the class does:
    * The __init__ method takes in a batch size as an argument and sets it as an instance variable.
    * The to_batches method takes in a DataFrame and yields smaller chunks of the DataFrame as iterators. It first determines how many splits are needed by calling the splits_num method. If the DataFrame has only one split, the method yields the entire DataFrame. Otherwise, it splits the DataFrame into chunks using np.array_split and yields each chunk as an iterator.
    * The splits_num method takes in the number of elements in the DataFrame and returns the number of splits required to process the DataFrame in batches. It does this by dividing the number of elements by the batch size and rounding up to the nearest integer.
    * The __call__ method is a shorthand for the to_batches method and returns an iterator of batches.
    Overall, this class provides a convenient way to process large DataFrames in smaller batches, which can be useful for reducing memory usage and improving performance. It can be used as a helper class for machine learning models or data processing pipelines that require processing large amounts of data efficiently.
    """

    def __init__(self, batch_size: int = 10) -> None:
        self.batch_size = batch_size

    # Makes chunks out of an input DataFrame
    def to_batches(self, df: pd.DataFrame) -> Iterator[pd.DataFrame]:
        splits = self.splits_num(df.shape[0])
        if splits <= 1:
            yield df
        else:
            for chunk in np.array_split(df, splits):
                yield chunk

    # Determines how many chunks DataFrame contains
    def splits_num(self, elements: int) -> int:
        return round(elements / self.batch_size)

    __call__ = to_batches
