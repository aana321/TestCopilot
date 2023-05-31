import openai
from termcolor import colored
import streamlit as st
import re

from storageClient import get_redis_connection, get_redis_results, query_redis

from config import CHAT_MODEL, COMPLETIONS_MODEL, INDEX_NAME, OPEN_API_KEY

from typing import List



redis_client = get_redis_connection()
openai.api_key = OPEN_API_KEY

# A basic class to create a message as a dict for chat
class Message:

    def __init__(self, role, content):
        self.role = role
        self.content = content

    def message(self):
        return {"role": self.role, "content": self.content}


# New Assistant class to add a vector database call to its responses
class RetrievalAssistant:

    def __init__(self):
        self.conversation_history = []

    def _get_assistant_response(self, prompt):

        try:
            completion = openai.ChatCompletion.create(
                model=CHAT_MODEL,
                messages=prompt,
                temperature=0.1

            )

            response_message = Message(completion['choices'][0]['message']['role'],
                                       completion['choices'][0]['message']['content'])
            return response_message.message()

        except Exception as e:

            return f'Request failed with exception {e}'

    # The function to retrieve Redis search results
    def _get_search_results(self, prompt):
        latest_question = prompt
        search_content = get_redis_results(redis_client, latest_question, INDEX_NAME)['result'][0]
        return search_content
    
    """
    This function added a check to see if the latest user prompt is asking for bug or test cases
    for specific feature.
    If the latest prompt is asking for test cases or bugs, it searches for it in Redis.
    If Redis has no result for the test cases, it searches for it in OpenAI's GPT and saves the result in Redis for future use.
    Finally, it returns the test cases in Gherkin format.
    """ 
    def ask_assistant(self, next_user_prompt):

        [self.conversation_history.append(x) for x in next_user_prompt]
        assistant_response = self._get_assistant_response(self.conversation_history)

        # Answer normally unless the trigger sequence is used "searching_for_answers"
        if 'searching for answers' in assistant_response['content'].lower():
            print("in if assistant response: ",assistant_response)

            question_extract = openai.Completion.create(
                model = COMPLETIONS_MODEL, 
                prompt=f'''
                Extract the user's latest feature and the bug for that question from this 
                conversation: {self.conversation_history}. Extract it as a sentence stating the feature and bug"
            '''
            )
            search_result = self._get_search_results(question_extract['choices'][0]['text'])
            self.conversation_history.insert(
                -1,{
                "role": 'system',
                "content": f'''
                Answer the user's question using this content: {search_result}. 
                If you cannot answer the question, fallback to a generic response using the OpenAI ChatGPT API.
                '''
                }
            )
            
            assistant_response = self._get_assistant_response(
                self.conversation_history
                )
            
            self.conversation_history.append(assistant_response)
            print("answer", assistant_response)
            return assistant_response
        else:
            print("in else assistant response: ",assistant_response)
            self.conversation_history.append(assistant_response)
            return assistant_response


    def pretty_print_conversation_history(self, colorize_assistant_replies=True):
        for entry in self.conversation_history:
            if entry['role'] == 'system':
                pass
            else:
                prefix = entry['role']
                content = entry['content']
                output = colored(prefix + ':\n' + content, 'green') if colorize_assistant_replies and entry[
                    'role'] == 'assistant' else prefix + ':\n' + content
                # prefix = entry['role']
                print(output)