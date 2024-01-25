from django.shortcuts import render
import json
# import openai
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from chatbot_app.config import OPENAI_KEY, DB_NAME, USER, PASSWORD, HOST, PORT, MODEL_NAME
import os
import psycopg2
import constants

from langchain_community.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

os.environ["OPENAI_API_KEY"] = constants.OPENAI_API_KEY

# openai.api_key = OPENAI_KEY



# Create your views here.

# Front-end views
def chat(request):
    return render(request, 'chat.html')



def connect_to_database():
    connection = psycopg2.connect(
    host = HOST,
    database = DB_NAME,
    user = USER,
    password = PASSWORD
    )
    return connection


# 
# def extract_data_from_database(connection):
#     cursor = connection.cursor()

#     # Example query - replace with your own SQL query
#     query = "SELECT * FROM it_qas_data limit 20;"
#     cursor.execute(query)

#     # Fetch all the results
#     data = cursor.fetchall()

#     # Get the column names
#     column_names = [desc[0] for desc in cursor.description]

#     # Convert the result to a list of dictionaries
#     result_as_dict = [dict(zip(column_names, row)) for row in data]

#     cursor.close()
#     return str(result_as_dict)


def extract_table_names(connection):

    cursor = connection.cursor()
    query_tables = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    cursor.execute(query_tables)

    table_names = cursor.fetchall()
    cursor.close()

    table_names = [name_tuple[0] for name_tuple in table_names]

    return table_names

    
def extract_data_from_database(connection, table_names):

   
    data_dict = {}
    for name in table_names:
        if name == 'sharepoint_data':
            cursor = connection.cursor()
            query = f'Select * from {name} limit 20;'
            cursor.execute(query)
            data = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            result_as_dict = [dict(zip(column_names, map(str, row))) for row in data]
            data_dict[name] = result_as_dict 
            cursor.close()

    return str(data_dict)


embeddings = OpenAIEmbeddings()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
documents = os.path.join(base_dir, 'ai_app', 'documents')
print(documents)


loader = DirectoryLoader("documents", glob="**/*.txt", recursive = True)
index = VectorstoreIndexCreator(vectorstore_cls=Chroma, 
                                    embedding=embeddings, 
                                    text_splitter=CharacterTextSplitter(separator = "\n",chunk_size=400, chunk_overlap=50),
                                    vectorstore_kwargs={ "persist_directory": '/documents'}
                                    ).from_loaders([loader])

def third_model(user_message):
    
    response =  index.query(user_message, llm=ChatOpenAI())

    return response


def ai_response(request):


    connection = connect_to_database()
    # users_table = extract_data_from_database(connection)
    table_names = extract_table_names(connection)
    tables_data = extract_data_from_database(connection, table_names)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_folder = os.path.join(base_dir, 'ai_app', 'kb')
    # file_path = os.path.join(kb_folder, 'steps.txt')

    # with open(file_path, 'r', encoding='utf-8') as file:
    #     steps = file.read()

    

    try:
        data = json.loads(request.body)
        user_message = data.get('userMessage', '')
        # print(f"User Message: {user_message}")
        
        
    except json.JSONDecodeError:
        # Handle JSON decoding error
        response = {'reply': 'Invalid JSON data'}
        return JsonResponse(response, status=400)
    
    # Retrieve or initialize conversation history from the session
    conversation_history = request.session.get('conversation_history', [])

    # Add the user message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})
    
    # response = openai.ChatCompletion.create(
    #             model=MODEL_NAME,
    #             messages=[
    #                 {"role": "system", "content": "You are a helpful assistant."},
    #                 {"role": "system", "content": steps},
    #                 # {"role": "system", "content": tables_data},
    #                 *conversation_history
    #             ]
    #         )
    
    # print(response['usage'])
    response = third_model(user_message)
    # print(conversation_history)
    
     # Extract the assistant's reply from the API response
    # assistant_reply = response['choices'][0]['message']['content']
    assistant_reply = response

    # Add the assistant's reply to the conversation history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    # conversation_history = []

    # Update the conversation history in the session
    request.session['conversation_history'] = conversation_history

    return HttpResponse(assistant_reply)


