import pandas as pd
import numpy as np
import openai
from redis import Redis
from redis.commands.search.field import VectorField
from redis.commands.search.field import TextField, NumericField
from redis.commands.search.query import Query

from config import EMBEDDINGS_MODEL, PREFIX, VECTOR_FIELD_NAME


# Get a Redis connection
def get_redis_connection(host='localhost', port='6379', db=0):
    r = Redis(host=host, port=port, db=db, decode_responses=False)
    return r


# Create a Redis index to hold our data
def create_hnsw_index(redis_conn, vector_field_name, index_name, vector_dimensions=1536, distance_metric='COSINE'):
    redis_conn.ft(index_name).create_index([
        VectorField(vector_field_name, "HNSW",
                    {"TYPE": "FLOAT32", "DIM": vector_dimensions, "DISTANCE_METRIC": distance_metric}),
        TextField("filename"),
        TextField("text_chunk"),
        NumericField("file_chunk_index")
    ])


# Create a Redis pipeline to load all the vectors and their metadata
def load_vectors(client: Redis, input_list, vector_field_name):
    """
    This function loads vector representations for a list of texts into a Redis database.
    Here's how it works:
    * client is the Redis client object that will be used to interact with the Redis database.
    * input_list is a list of text objects. Each text object must have an id field, a metadata field that is a dictionary, and a vector field that is a numpy array containing the vector representation of the text.
    * vector_field_name is the name of the metadata field that will contain the vector representation of the text.

    The function first creates a Redis pipeline object p that will allow it to execute multiple Redis commands in a single transaction for better performance. Then, for each text object in input_list, it does the following:
    * Constructs a Redis hash key key that is composed of a prefix, the id of the text, and a suffix.
    * Gets the metadata dictionary from the text object and adds the vector representation of the text to it as a binary string using np.array(text['vector'], dtype='float32').tobytes().
    * Sets the Redis hash key to the metadata dictionary using p.hset(key, mapping=item_metadata).

    Finally, the pipeline object p is executed using p.execute(), which sends all the commands to the Redis server for execution.
    """

    p = client.pipeline(transaction=False)
    for text in input_list:
        # hash key
        key = f"{PREFIX}:{text['id']}"

        # hash values
        item_metadata = text['metadata']
        #
        item_keywords_vector = np.array(text['vector'], dtype='float32').tobytes()
        item_metadata[vector_field_name] = item_keywords_vector

        # HSET
        p.hset(key, mapping=item_metadata)

    p.execute()

"""
This function search for the text file in redis on the basis of prompt given by the user. It will return the answer if 
the record is found in redis, but if the record does not exists in redis then it will use the openAI api search and find
the generic record similar to matching feature asked by the user. This is optimised query which uses smaller vector size 
and more selective query in terms of document matching. Previously it matches all the documents in the index but now its 
only searches for relevant text in document. Also the top-k results is minimised to 1 previously it was
"""

def build_optimise_query(query, top_k=1):
    embedded_query = np.array(openai.Embedding.create(
        input=query,
        model=EMBEDDINGS_MODEL,
    )["data"][0]['embedding'], dtype=np.float32).tobytes()
    
    q = Query(f'@text_chunk:({query})=>[KNN {top_k} @{VECTOR_FIELD_NAME} $vec_param AS vector_score]').sort_by('vector_score').paging(0,
                                                                                                                  top_k).return_fields(
        'vector_score', 'filename', 'text_chunk', 'text_chunk_index').dialect(2)
    params_dict = {"vec_param": embedded_query}
    
    return q, params_dict

def build_deafult_query(query, top_k=2):
    embedded_query = np.array(openai.Embedding.create(
        input=query,
        model=EMBEDDINGS_MODEL,
    )["data"][0]['embedding'], dtype=np.float32).tobytes()

    q_default = Query(f'*=>[KNN {top_k} @{VECTOR_FIELD_NAME} $vec_param AS vector_score]').sort_by('vector_score').paging(0,
                                                                                                                  top_k).return_fields(
        'vector_score', 'filename', 'text_chunk', 'text_chunk_index').dialect(2)
    params_dict_default = {"vec_param": embedded_query}
    
    return q_default, params_dict_default


def query_redis(redis_conn, query, index_name, top_k=2):
    q, params_dict = build_deafult_query(query, top_k)

    results = redis_conn.ft(index_name).search(q, query_params=params_dict)

    return results

    # if len(results.doc) > 0:
    #     return results
    # else:
    #     return fallback_openai(query)



# Fallback to OpenAI search for test cases
def fallback_openai(query):
    openai_results = openai.Completion.create(
        engine = "davinci",
        prompt = query,
        max_tokens = 60,
        n = 1,
        stop = None,
        temperature = 0.7,
    )
    # Extract the top result from the OpenAI response
    top_result = openai_results.choices[0].text.strip()
    
    # Create a mock result object to match the Redis result object
    class Result:
        def __init__(self, text_chunk, vector_score):
                self.text_chunk = text_chunk
                self.vector_score = vector_score
    mock_result = Result(text_chunk=top_result, vector_score=0.0)
    # Return a list with the mock result
    return [mock_result]

# Get mapped documents from Weaviate results
def get_redis_results(redis_conn, query, index_name):
    # Get most relevant documents from Redis
    query_result = query_redis(redis_conn, query, index_name)

    # Extract info into a list
    query_result_list = []
    for i, result in enumerate(query_result.docs):
        result_order = i
        text = result.text_chunk
        score = result.vector_score
        query_result_list.append((result_order, text, score))

    # Display result as a DataFrame for ease of us
    result_df = pd.DataFrame(query_result_list)
    result_df.columns = ['id', 'result', 'certainty']
    return result_df
