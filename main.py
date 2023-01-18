import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
chat = ""
previousChat = ""
message = ""

line = input("Enter text to start chatting\nEnter ;q to quit, or ;h for help\n") + '\n'
while (line != ";q\n"):
    if (line == ";h\n"):
        print('''
              ;h    Displays this help message

              ;q    Exits the program

              ;u    Removes the previous result and your previous message

              ;s    Sends the next message
              ''')
    elif (line == ";u\n"):
        chat = previousChat
    elif (line == ";s\n"):
        previousChat = chat
        chat += message
        message = ""
        request = openai.Completion.create(
            model = "text-davinci-003",
            prompt = chat,
            temperature = 0.7,
            max_tokens = 256,
            top_p = 1,
            frequency_penalty = 0,
            presence_penalty = 0
        )
        result = request.choices[0].text
        print(result)
        chat += result
    else:
        message += line
    line = input() + '\n'

