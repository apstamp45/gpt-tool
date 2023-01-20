import os
import sys
import math
import openai
import socket
import argparse
from argparse import RawTextHelpFormatter
import colorama
from colorama import Fore, Style

SAVES_DIRECTORY = os.path.expanduser('~/.local/share/gpt-tool/saves/')
COMMANDS_HELP = '''
commands:
  ;h                    Displays this help message.
  ;q                    Exits the program.
  ;u                    Removes the previous result and your previous message.
  ;s                    Sends the next message.
  ;S [filename]         Saves the current chat to either provided file,
                        previously provided file, or last loaded file for later use;
                        whichever came last.
  ;l                    Lists the available chat files to load.
  ;L <filename>         Loads the given file to the chat. WARNING: This will override the current chat!
  ;c                    Clears the terminal window to save some sanity.
  ;C                    Clears the chat (the stored text, not the terminal).
'''

def out(message: str, color: str):
    print(color + message + Style.RESET_ALL)

def err(message: str):
    print(Fore.LIGHTRED_EX + message + Style.RESET_ALL, file = sys.stderr)

def internet(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def save_chat_file(chat_file: str, chat: str):
    file = open(SAVES_DIRECTORY + '{}.chat'.format(chat_file), 'w')
    file.write(chat)
    file.close()
    out('File successfully saved to {}.chat'.format(SAVES_DIRECTORY + chat_file), Fore.LIGHTBLUE_EX)

def load_chat_file(chat_file: str) -> str:
    if not os.path.exists(SAVES_DIRECTORY + '{}.chat'.format(chat_file)):
        err('Error: save file does not exist: {}.chat'.format(SAVES_DIRECTORY + chat_file));
        return ''
    else:
        file = open(SAVES_DIRECTORY + '{}.chat'.format(chat_file), 'r')
        chat = file.read()
        file.close()
        out('File successfully loaded from {}.chat'.format(SAVES_DIRECTORY + chat_file), Fore.LIGHTBLUE_EX)
        return chat

def clear_lines(line_count: int):
    columns = os.get_terminal_size().columns
    print('\r' + ' ' * columns, end = '\r')
    for _ in range(0, line_count):
        print('\033[A' + ' ' * columns, end = '\r')

def get_complete_chat(chat_load: str, chat_history: list[str]) -> str:
    return chat_load + '\n'.join(chat_history)


def main():
    parser = argparse.ArgumentParser(
            prog = 'gpt-tool',
            description = 'A command line tool for using OpenAI\'s ChatGPT.',
            epilog = COMMANDS_HELP,
            formatter_class=RawTextHelpFormatter
            )
    parser.add_argument('-L', '--load', type = str, metavar = 'file',
                        help = 'Loads given chat file if present')
    colorama.init()
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if openai.api_key == '':
        err('Error: your API key is not set.\nYou can place "OPENAI_API_KEY=your OpenAI API key here" ' +
            'in your .bashrc or .zshrc, then run "source ~/.bash(zsh)rc" to reload.')
        return

    if not os.path.exists(SAVES_DIRECTORY):
        os.makedirs(SAVES_DIRECTORY)

    save_file_name = ''

    chat = ''
    chat_load = ''
    chat_history = []

    message = ''

    args = parser.parse_args()
    if args.load is not None:
        chat_load = load_chat_file(args.load)
        if chat_load != '':
            save_file_name = args.load

    out('Enter text and use ;s to send to ChatGPT\nEnter ;h to show list of commands', Fore.LIGHTBLUE_EX)
    line = input()
    while (line != ';q'):
        split_line = line.split()
        if (line == ';h'):
            out(COMMANDS_HELP, Fore.LIGHTBLUE_EX)

        elif (line == ';u'):
            if message != '':
                clear_lines(message.count('\n') + 1)
                message = ''
            elif (len(chat_history) > 0):
                removed_item = chat_history.pop()
                chat = get_complete_chat(chat_load, chat_history)
                lines_to_clear = 0
                separator = ''
                columns = os.get_terminal_size().columns
                for char in removed_item:
                    if char == '\n':
                        lines_to_clear += math.floor(len(separator) / columns) + 1
                        separator = ''
                    else:
                        separator += char
                lines_to_clear += math.floor(len(separator) / columns) + 1
                clear_lines(lines_to_clear + 1)
            else:
                err('Error: undo limit reached.')

        elif line == ';s':
            clear_lines(1)
            if internet():
                chat += message.strip() + '\n'
                chat_history.append(message.strip())
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
                    err('Error: There was a problem either with your internet connection, ' +
                        'or with your API key.\nMake sure the OPENAI_API_KEY enviornment ' +
                        'variable is set to your OpenAI API key, and that you have a secure ' +
                        'internet connection')
                    return
                except openai.error.ServiceUnavailableError:
                    err('Something went wron with the OpenAI server. Perhaps they are overloaded?')
                result = request.choices[0].text
                chat += result.strip() + '\n'
                chat_history.append(result.strip())
                out(result.strip(), Fore.LIGHTGREEN_EX)
            else:
                err('It seems that you do not have an internet connection.\n' +
                    'Try reconnecting to the internet and re-sending the message')

        elif len(split_line) > 0 and split_line[0] == ';S':
            if len(split_line) < 2 and save_file_name == '':
                err('Error: you must provide a filename to save the chat')
            elif save_file_name == '':
                save_chat_file(split_line[1], chat)
                save_file_name = split_line[1]
            else:
                save_chat_file(save_file_name, chat)

        elif len(split_line) > 0 and split_line[0] == ';L':
            if len(split_line) < 2:
                err('Error: you must provide a load file name')
            else:
                temp = load_chat_file(split_line[1])
                if temp != '':
                    chat_load = temp
                    chat = get_complete_chat(chat_load, chat_history)
                    save_file_name = split_line[1]

        elif line == ';l':
            out('Here is a list of available load file names:', Fore.LIGHTBLUE_EX)
            for file in os.listdir(SAVES_DIRECTORY):
                out(file.removesuffix('.chat'), Fore.LIGHTBLUE_EX)

        elif line == ';c':
            clear_lines(os.get_terminal_size().lines - 1)

        elif line == ';C':
            chat = ''
            out('Chat was cleared.', Fore.LIGHTBLUE_EX)

        else:
            message += line + '\n'

        line = input()

if __name__ == '__main__':
    main()

