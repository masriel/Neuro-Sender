import os
from dotenv import load_dotenv, dotenv_values

import psycopg2
from pyrogram import Client, filters

from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferMemory

# Load environment variables from .env files
config = dotenv_values(".env")
load_dotenv("config.env")

# Get API credentials and other configuration values from environment variables
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
key = os.getenv("OPENAI_API_KEY")

# Initialize Pyrogram client and OpenAI language model
app = Client("my_account", api_id, api_hash)
open_ai_llm = ChatOpenAI(openai_api_key=key, model_name='gpt-3.5-turbo')

# Initialize ConversationChain with memory
conversation = ConversationChain(
    llm=open_ai_llm,
    memory=ConversationBufferMemory(llm=open_ai_llm)
)


# Command handler for "/start" command
@app.on_message(filters.command("start"))
async def start(client, message):
    await client.send_message(message.chat.id, "Hi!")


# Message handler for messages starting with "!"
@app.on_message(filters.regex(r"^!"))
async def handle_start(client, message):
    user = int(os.getenv("USER_ID"))
    cur_user = message.from_user.id
    if cur_user == user:
        text = message.text[1:]
        await send_message(client, text)


# Message handler for all other messages
@app.on_message()
async def handle_new_message(client, message):
    if message.text.startswith("!"):
        return
    try:
        username = message.from_user.username
    except Exception:
        username = ""
    conversation(message.text)
    update_info('@' + username, conversation.memory.buffer)
    await send_reply(client, '@' + username)


# Database connection function
def connection():
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="Neuro-sender",
        user="postgres",
        password="123"
    )
    return conn


# Function to add new information to the database
def add_info(userid, message):
    conn = connection()
    cur = conn.cursor()

    search = "SELECT clientname FROM public.clienthistory WHERE clientname = %s"

    cur.execute(search, (userid,))
    result = cur.fetchone()
    if result:
        update_info(userid, message)
    else:
        sql = "INSERT INTO public.clienthistory (clientname, messagetext) VALUES (%s, %s)"

        data = (userid, message)
        cur.execute(sql, data)
        conn.commit()
    cur.close()
    conn.close()


# Function to update existing information in the database
def update_info(username, message):
    conn = connection()
    cur = conn.cursor()

    sql_update = "UPDATE public.clienthistory SET messagetext = %s WHERE clientname = %s"

    data = (message, username)
    cur.execute(sql_update, data)
    conn.commit()

    cur.close()
    conn.close()


# Function to send a message and update the database
async def send_message(client, message):
    conversation(message)
    peoples = 'masriel_ka', 'GorodXA1', 'ice_striker', 'xiaodi4ao'
    for i in peoples:
        await client.send_message('@' + i, message)
        add_info('@' + i, conversation.memory.buffer)


# Function to send a reply message
async def send_reply(client, username):
    await client.send_message(username, conversation.memory.chat_memory.messages[
        len(conversation.memory.chat_memory.messages) - 1].content)


# Entry point of the application
if __name__ == "__main__":
    app.run()
