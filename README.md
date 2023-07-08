Accelerate your development and testing process with our cutting-edge AI-powered assistant! Whether you need guidance on application testing or insights on retail analytics, our chatbot has got you covered. With a simple file upload feature and lightning-fast responses, we make quality assurance a breeze.
The project has two parts

catalyst -  Rattle Copilot Backend, backend tech stack includes (python, openai, FastAPI, redis, unicorn, pandas)
aurora - Rattle Copilot Interface, frontend built with react-app


Local Setup of Catalyst


If you don’t have Python installed, install it from here. Recommended Version (3.9.6)


Clone this repository.


Navigate into the project directory:

$ cd rattle-reliability-copilot/catalyst




Create a new virtual environment:

$ python -m venv venv
$ . venv/bin/activate




Install the requirements:

$ pip install -r requirements.txt





Data Ingestion


We're going to use Redis as our database for both document contents and the vector embeddings. You will need the full Redis Stack to enable use of Redisearch, which is the module that allows semantic search.

$ docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest 




Setup your data from datum folder


Run the script

$ python trainer.py  




Note: Index create takes little time, the script might stop saying 'Not there yet. Creating'. In such a case, rerun the script.

Starting the backend server


Run the http server

$ uvicorn main:app --reload


or

$ python main.py



Swagger Doc
http://127.0.0.1:8000/docs#/default 
http://127.0.0.1:8000/redoc
You can use the following curl to test your backend server:

   $ curl --location --request POST 'http://localhost:8000/get_answer' \
   --header 'accept: application/json' \
   --header 'Content-Type: application/json' \
   --data-raw '{"prompt":"Help me with payment related test cases"}'
   ```
   






Copilot Interface with Streamlit
To test your backend code, if you have trouble deploying aurora, you can continue testing your code with streamlit. This gives a basic user interface.

Test your bot


$ streamlit run bot.py



Local Setup of Aurora

Starting the frontend server

Head to your project directory


   $ cd rattle-reliability-copilot/aurora



Start the server


   $ npm install
   $ npm start




Head to http://localhost:3000/


Build the app



   $  npm run build



Points to note

Please ingest data using catalyst/trainer.py before proceeding with the local setup
Dockerfile for frontend and backend are in progress for building images for containerised deployment
Go through catalyst/helperBot.ipynb for basic understanding of the application
