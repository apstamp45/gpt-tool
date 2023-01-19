import os
import sys
import openai
import socket
from colorama import Fore, Style

SAVES_DIRECTORY = '~/.local/share/gpt-tool/saves/'

def out(message, color):
    print(color + message + Style.RESET_ALL)

def err(message):
    print(Fore.LIGHTRED_EX + message + Style.RESET_ALL, file = sys.stderr)

def internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def main():
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if openai.api_key == '':
        err('Error: your API key is not set.\nYou can place "OPENAI_API_KEY=your OpenAI API key here" in your .bashrc or .zshrc, then run "source ~/.bash(zsh)rc" to reload.')
        return

    if not os.path.exists(SAVES_DIRECTORY):
        os.makedirs(SAVES_DIRECTORY)

    chat = ''
    previousChat = ''
    message = ''
    saveFileName = ''

    out('Enter text and use ;s to send to ChatGPT\nEnter ;q to quit, or ;h for help', Fore.LIGHTBLUE_EX)
    line = input()
    while (line != ';q'):
        splitLine = line.split()
        if (line == ';h'):
            out('''
;h                  Displays this help message.

;q                  Exits the program.

;u                  Removes the previous result and your previous message.

;s                  Sends the next message.

;S [filename]       Saves the current chat to either provided file,
                    previously provided file, or last loaded file for later use;
                    whichever came last.

;l <filename>       Loads the given file to the chat. WARNING: This will override the current chat!

;L                  Lists the available chat files to load.
                  ''', Fore.LIGHTBLUE_EX)

        elif (line == ';u'):
            chat = previousChat

        elif line == ';s':
            if internet():
                previousChat = chat
                chat += message
                message = ""
                try:
                    request = openai.Completion.create(
                        model = 'text-davinci-003',
                        prompt = chat,
                        temperature = 0.7,
                        max_tokens = 256,
                        top_p = 1,
                        frequency_penalty = 0,
                        presence_penalty = 0
                    )
                except openai.error.APIConnectionError:
                    err('Error: There was a problem either with your internet connection, or with your API key.\nMake sure the OPENAI_API_KEY enviornment variable is set to your OpenAI API key, and that you have a secure internet connection')
                    return
                result = request.choices[0].text
                out(result, Fore.LIGHTGREEN_EX)
            else:
                err('It seems that you do not have an internet connection.\nTry reconnecting to the internet and re-sending the message')

        elif len(splitLine) > 0 and splitLine[0] == ';S':
            if len(splitLine) < 2 and saveFileName == '':
                err('Error: you must provide a filename to save the chat')
            elif saveFileName == '':
                saveFile = open(SAVES_DIRECTORY + '{}.chat'.format(splitLine[1]), 'w')
                saveFile.write(chat)
                saveFile.close()
                saveFileName = splitLine[1]
                out('File successfully saved to {}.chat'.format(SAVES_DIRECTORY + splitLine[1]), Fore.LIGHTBLUE_EX)
            else:
                saveFile = open(SAVES_DIRECTORY + '{}.chat'.format(saveFileName), 'w')
                saveFile.write(chat)
                saveFile.close()
                out('File successfully saved to {}.chat'.format(SAVES_DIRECTORY + saveFileName), Fore.LIGHTBLUE_EX)

        elif len(splitLine) > 0 and splitLine[0] == ';l':
            if len(splitLine) < 2:
                err('Error: you must provide a filename to save the chat')
            elif not os.path.exists(SAVES_DIRECTORY + '{}.chat'.format(splitLine[1])):
                err('Error: save file does not exist: {}.chat'.format(SAVES_DIRECTORY + splitLine[1]));
            else:
                loadFile = open(SAVES_DIRECTORY + '{}.chat'.format(splitLine[1]), 'r')
                chat = loadFile.read()
                loadFile.close()
                saveFileName = splitLine[1]
                out('File successfully loaded from {}.chat'.format(SAVES_DIRECTORY + splitLine[1]), Fore.LIGHTBLUE_EX)

        elif line == ';L':
            out('Here is a list of available load files:', Fore.LIGHTBLUE_EX)
            for file in os.listdir(SAVES_DIRECTORY):
                out(file.removesuffix('.chat'), Fore.LIGHTBLUE_EX)

        else:
            message += line + '\n'

        line = input()
    print(Style.RESET_ALL)

if __name__ == '__main__':
    main()

