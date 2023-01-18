import os
import sys
import openai

SAVES_DIRECTORY = '~/.local/share/gpt-tool/saves/'

openai.api_key = os.getenv('OPENAI_API_KEY')
chat = ''
previousChat = ''
message = ''

line = input('Enter text and use ;s to send to ChatGPT\nEnter ;q to quit, or ;h for help\n')
while (line != ';q'):
    splitLine = line.split()
    if (line == ';h'):
        print('''
;h                  Displays this help message.

;q                  Exits the program.

;u                  Removes the previous result and your previous message.

;s                  Sends the next message.

;S <filename>       Saves the current chat to given file for later use.

;l <filename>       Loads the given file to the chat. WARNING: This will override the current chat!
              ''')

    elif (line == ';u'):
        chat = previousChat

    elif line == ';s':
        previousChat = chat
        chat += message
        message = ""
        request = openai.Completion.create(
            model = 'text-davinci-003',
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

    elif splitLine[0] == ';S':
        if not os.path.exists(SAVES_DIRECTORY):
            os.makedirs(SAVES_DIRECTORY)
        if not len(splitLine):
            print('Error: you must provide a filename to save the chat', file = sys.stderr)
        else:
            saveFile = open(SAVES_DIRECTORY + '{}.chat'.format(splitLine[1]), 'w')
            saveFile.write(chat)
            saveFile.close()
            print('File successfully saved to {}.chat'.format(SAVES_DIRECTORY + splitLine[1]))

    elif splitLine[0] == ';l':
        if not os.path.exists(SAVES_DIRECTORY):
            os.makedirs(SAVES_DIRECTORY)
        if len(splitLine) < 2:
            print('Error: you must provide a filename to save the chat', file = sys.stderr)
        elif not os.path.exists(SAVES_DIRECTORY + '{}.chat'.format(splitLine[1])):
            print('Error: save file does not exist: {}.chat', file = sys.stderr);
        else:
            loadFile = open(SAVES_DIRECTORY + '{}.chat'.format(splitLine[1]), 'r')
            chat = loadFile.read()
            loadFile.close()
            print('File loaded from {}.chat'.format(SAVES_DIRECTORY + splitLine[1]))

    else:
        message += line + '\n'

    line = input()

