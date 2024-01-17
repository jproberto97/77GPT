from django.shortcuts import render
import json
import openai
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from chatbot_app.config import OPENAI_KEY, DB_NAME, USER, PASSWORD, HOST, PORT
import os
import psycopg2

openai.api_key = OPENAI_KEY



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
def extract_data_from_database(connection):
    cursor = connection.cursor()

    # Example query - replace with your own SQL query
    query = "SELECT * FROM users;"
    cursor.execute(query)

    # Fetch all the results
    data = cursor.fetchall()

    # Get the column names
    column_names = [desc[0] for desc in cursor.description]

    # Convert the result to a list of dictionaries
    result_as_dict = [dict(zip(column_names, row)) for row in data]

    cursor.close()
    return str(result_as_dict)



def ai_response(request):


    connection = connect_to_database()
    users_table = extract_data_from_database(connection)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_folder = os.path.join(base_dir, 'ai_app', 'kb')
    file_path = os.path.join(kb_folder, 'step.txt')

    with open(file_path, 'r', encoding='utf-8') as file:
        steps = file.read()


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
    
    response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "system", "content": steps},
                    {"role": "system", "content": users_table},
                    *conversation_history
                ]
            )
    print(response)
    
     # Extract the assistant's reply from the API response
    assistant_reply = response['choices'][0]['message']['content']

    # Update the conversation history in the session
    request.session['conversation_history'] = conversation_history

    return HttpResponse(assistant_reply)


