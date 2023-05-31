import streamlit as st
from streamlit_chat import message

from storageClient import get_redis_connection
from assistant import RetrievalAssistant, Message
from config import system_prompt


# Initialise database

## Initialise Redis connection
redis_client = get_redis_connection()

### CHATBOT APP

st.set_page_config(
    page_title="Rattle Reliability Copilot",
    page_icon=":robot:"
)

st.title('Rattle Reliability Copilot')
st.subheader("Streamline QA with our AI-powered chatbot - faster, smarter testing.")

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []


def query(question):
    response = st.session_state['chat'].ask_assistant(question)
    return response



prompt = st.text_input("What do you want to know: ", "", key="input")

if st.button('Submit', key='generationSubmit'):

    # Initialization
    if 'chat' not in st.session_state:
        st.session_state['chat'] = RetrievalAssistant()
        messages = []
        system_message = Message('system', system_prompt)
        messages.append(system_message.message())
    else:
        messages = []

    user_message = Message('user', prompt)
    messages.append(user_message.message())

    response = query(messages)

    # Debugging step to print the whole response
    # st.write(response)

    st.session_state.past.append(prompt)
    st.session_state.generated.append(response['content'])

if st.session_state['generated']:

    for i in range(len(st.session_state['generated']) - 1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
