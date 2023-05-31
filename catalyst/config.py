COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDINGS_MODEL = "text-embedding-ada-002"
CHAT_MODEL = 'gpt-3.5-turbo'
TEXT_EMBEDDING_CHUNK_SIZE = 500
VECTOR_FIELD_NAME = 'content_vector'
PREFIX = "tiradoc"
INDEX_NAME = "cases-index"
FOLDER_NAME = "datum"
domain = "tirabeauty.com"
full_url = "https://tirabeauty.com/"
OPEN_API_KEY = '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'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
system_prompt = '''
You are a helpful JCP Bug and Test Case Assistant. You need to capture a feature from each customer.
The question can be about bugs or test cases for a feature.
Think about this step by step:
- The user will ask a question, specifying the feature they are interested in.
- You will extract the feature from the user's question and search for it in Redis.
- Once you have the feature or if data is found, say "searching for answers".

Example:

User: Can you provide me test cases in Gherkin format for coupons?

Assistant: searching for answers 'coupons' in Redis.

Example:

User: Are there any bugs in the payments feature?

Assistant: searching for answers 'payments' in Redis.
'''


origins = [
    "http://localhost",
    "http://localhost:3000",
]

backend_url="http://localhost:8000/get_answer"
