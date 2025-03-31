# plugins/ai_plugin.py

import os
import openai

# Set your OpenAI API key from environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")  # Ensure this is set in your environment

# Function to interact with OpenAI API
async def ai(query):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=query,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.9,
        timeout=5
    )
    return response.choices[0].text.strip()

# Function to handle AI queries
async def ask_ai(client, m, message):
    try:
        # Check if the message contains a question
        if len(message.text.split(" ")) < 2:
            await m.edit("Please provide a question after the command.")
            return
        
        question = message.text.split(" ", 1)[1]
        # Generate response using OpenAI API
        response = await ai(question)
        # Send response back to user
        await m.edit(f"{response}")
    except Exception as e:
        # Handle other errors
        error_message = f"An error occurred: {e}"
        await m.edit(error_message)
