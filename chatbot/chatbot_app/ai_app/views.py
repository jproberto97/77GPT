from django.shortcuts import render
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import os
# import django_app.chatbot.chatbot_app.constants as constants
import constants
import os
from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import ChatOpenAI, OpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_community.callbacks import get_openai_callback
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
import time

os.environ["OPENAI_API_KEY"] = constants.OPENAI_API_KEY


# Create your views here.

# Front-end views
def chat(request):
    return render(request, 'chat.html')


documents = []

def process_file(file_path):
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith('.docx') or file_path.endswith('.doc'):
            loader = Docx2txtLoader(file_path)
            documents.extend(loader.load())
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path, encoding='utf-8')
            documents.extend(loader.load())

    # Specify the root folder
root_folder = './documents'

# Walk through the directory tree
for folder, _, files in os.walk(root_folder):
    for file in files:
        file_path = os.path.join(folder, file)
        process_file(file_path)

# To split and chunks the loaded documents into smaller token
text_splitter = CharacterTextSplitter(separator = "\n",chunk_size=400, chunk_overlap=50)
docs =  text_splitter.split_documents(documents)
# For embeddings
embeddings = OpenAIEmbeddings()
# For text searching
db = FAISS.from_documents(docs, embeddings)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
chain = load_qa_chain(llm, chain_type="stuff")




def model_respomse(user_prompt):


        docs = db.similarity_search(user_prompt)
        response = chain.invoke({'input_documents': docs, 'question': user_prompt}, return_only_outputs=True)
        
        return response['output_text']


def ai_response(request):
   
    try:
        data = json.loads(request.body)
        user_message = data.get('userMessage', '')
        start = time.time()
       
        
    except json.JSONDecodeError:
        # Handle JSON decoding error
        response = {'reply': 'Invalid JSON data'}
        return JsonResponse(response, status=400)
    
    # Retrieve or initialize conversation history from the session
    conversation_history = request.session.get('conversation_history', [])

    # Add the user message to the conversation history
    conversation_history.append({"role": "user", "content": user_message})
    
    # response = model_respomse(user_message)
    with get_openai_callback() as cb:
                    
                    response = model_respomse(user_message)
                    print(response)

                    # end = datetime.now()
                    end = time.time()
                    response_time = end - start

                    print(cb)
                    print(response_time)
    assistant_reply = response

    # Add the assistant's reply to the conversation history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    # conversation_history = []

    # Update the conversation history in the session
    request.session['conversation_history'] = conversation_history

    return HttpResponse(assistant_reply)


