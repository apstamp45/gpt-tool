import os
import sys
import math
import socket
import openai
# import configparser
import argparse
from argparse import RawTextHelpFormatter
import colorama
from colorama import Fore, Style

SAVES_DIRECTORY = os.path.expanduser('~/.local/share/gpt-tool/saves/')
CONFIG_FILE = os.path.expanduser('~/.local/share/gpt-tool/gpt_tool.conf')

DEFAULT_EDITOR = '/usr/bin/vim'

COMMANDS_HELP = '''
commands:
  ;h                    Displays this help message.
  ;q                    Exits the program.
  ;;                    Sends the next message.
  ;s [filename]         Saves the current chat to either provided file,
                        previously provided file, or last loaded file;
                        whichever came last.
  ;S                    Lists the available chat files to load.
  ;l <filename>         Loads the given file to the chat. WARNING: This will override the current chat!
  ;L                    Saves the current chat, opens the file in text editor, then reloads the file.
                        The chat must already have been loaded previously.
  ;x                    Clears the terminal window to save some sanity.
  ;X                    Clears the chat (the stored text, not the terminal).
  ;z                    Removes the previous result and your previous message.
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
        out('Chat file does not exist: {}.chat'.format(SAVES_DIRECTORY + chat_file), Fore.YELLOW);
        return ''
    else:
        file = open(SAVES_DIRECTORY + '{}.chat'.format(chat_file), 'r')
        chat = file.read()
        file.close()
        out('File successfully loaded from {}.chat'
            .format(SAVES_DIRECTORY + chat_file), Fore.LIGHTBLUE_EX)
        return chat

def clear_lines(line_count: int):
    columns = os.get_terminal_size().columns
    print('\r' + ' ' * columns, end = '\r')
    for _ in range(0, line_count):
        print('\033[A' + ' ' * columns, end = '\r')

def get_complete_chat(chat_load: str, chat_history: list[str]) -> str:
    return chat_load + '\n'.join(chat_history)

def edit_file(file_path: str):
    editor = DEFAULT_EDITOR
    if os.getenv('EDITOR') != '':
        editor = os.getenv('EDITOR')
    else:
        out("EDITOR environment variable is not set. using {} as default."
            .format(DEFAULT_EDITOR), Fore.YELLOW)
    os.system('{} {}'.format(editor, file_path))

def main():
    parser = argparse.ArgumentParser(
           prog = 'gpt-tool',
            description = 'A command line tool for using OpenAI\'s ChatGPT.\n' +
            'https://github.com/apstamp45/gpt-tool/',
            epilog = COMMANDS_HELP,
            formatter_class=RawTextHelpFormatter
            )
    parser.add_argument('-l', '--load-chat', type = str, metavar = 'file',
                        help = 'Loads given chat file if present')
    # parser.add_argument('-F', '--config-file', type = str, metavar = 'config-file',
                        # help = 'Loads given config file')
    parser.add_argument('-L', '--edit-chat', type = str, metavar = 'chat-file',
                        help = 'Edits the given chat file in default text editor then quits')
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
    if args.load_chat is not None:
        chat_load = load_chat_file(args.load_chat)
        if chat_load != '':
            save_file_name = args.load_chat

    if args.edit_chat is not None:
        edit_file(SAVES_DIRECTORY + args.edit_chat + '.chat')
        return

    out('Enter text and use ;; to send to ChatGPT\n' +
        'Enter ;h to show list of commands', Fore.LIGHTBLUE_EX)
    line = input()
    while (line != ';q'):
        split_line = line.split()
        if (line == ';h'):
            out(COMMANDS_HELP, Fore.LIGHTBLUE_EX)

        elif (line == ';z'):
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
                out('Undo limit reached.', Fore.YELLOW)

        elif line == ';;':
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
                    result = request.choices[0].text
                    chat += result.strip() + '\n'
                    chat_history.append(result.strip())
                    out(result.strip(), Fore.LIGHTGREEN_EX)
                except openai.error.APIConnectionError:
                    err('Error: There was a problem either with your internet connection, ' +
                        'or with your API key.\nMake sure the OPENAI_API_KEY enviornment ' +
                        'variable is set to your OpenAI API key, and that you have a secure ' +
                        'internet connection')
                    return
                except (openai.error.ServiceUnavailableError, openai.error.RateLimitError):
                    out('WARNING: Something went wrong with the OpenAI server.' +
                        'Perhaps they are overloaded?', Fore.YELLOW)
            else:
                out('It seems that you do not have an internet connection.\n' +
                    'Try reconnecting to the internet and re-sending the message',
                    Fore.YELLOW)

        elif len(split_line) > 0 and split_line[0] == ';s':
            if len(split_line) < 2 and save_file_name == '':
                out('You must provide a filename to save the chat', Fore.YELLOW)
            elif save_file_name == '':
                save_chat_file(split_line[1], chat)
                save_file_name = split_line[1]
                chat_history = []
            else:
                save_chat_file(save_file_name, chat)
                chat_history = []

        elif len(split_line) > 0 and split_line[0] == ';l':
            if len(split_line) < 2:
                out('You must provide a load file name to load', Fore.YELLOW)
            else:
                temp = load_chat_file(split_line[1])
                if temp != '':
                    chat_load = temp
                    chat = get_complete_chat(chat_load, chat_history)
                    save_file_name = split_line[1]
                    chat_history = []

        elif line == ';L':
            if save_file_name == '':
                out("Cannot open chat file: none was loaded.", Fore.YELLOW)
            else:
                save_chat_file(save_file_name, chat)
                chat_history = []
                edit_file(SAVES_DIRECTORY + save_file_name + '.chat')
                chat = get_complete_chat(load_chat_file(SAVES_DIRECTORY + save_file_name + '.chat'),
                                         chat_history)

        elif line == ';S':
            out('Here is a list of available load file names:', Fore.LIGHTBLUE_EX)
            for file in os.listdir(SAVES_DIRECTORY):
                out(file.removesuffix('.chat'), Fore.LIGHTBLUE_EX)

        elif line == ';x':
            clear_lines(os.get_terminal_size().lines - 1)

        elif line == ';X':
            chat = ''
            out('Chat was cleared.', Fore.LIGHTBLUE_EX)

        else:
            message += line + '\n'

        line = input()

if __name__ == '__main__':
    main()

