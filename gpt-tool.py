import os
import math
import socket
import openai
import argparse
from argparse import RawTextHelpFormatter
import colorama
from colorama import Fore, Style

SAVES_DIRECTORY = os.path.expanduser('~/.local/share/gpt-tool/saves/')
# CONFIG_FILE = os.path.expanduser('~/.local/share/gpt-tool/gpt_tool.conf')

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
  ;z                    Removes the previous result or your previous message.
  ;Z                    Redoes the previous undo.
'''

def out(message: str, color: str):
    print(color + message + Style.RESET_ALL)

def internet(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def save_chat_file(chat_file: str, chat_load: str,
                   chat_history: list[str], chat_history_index: int, message: str) -> str:
    file = open(SAVES_DIRECTORY + '{}.chat'.format(chat_file), 'w')
    load = get_complete_chat(chat_load, chat_history, chat_history_index, message)
    file.write(load)
    file.close()
    out('File successfully saved to {}.chat'.format(SAVES_DIRECTORY + chat_file), Fore.LIGHTBLUE_EX)
    return load

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

def get_complete_chat(chat_load: str, chat_history: list[str], chat_history_index: int, message: str) -> str:
    chat = ''
    for i in range(0, chat_history_index + 1):
        chat += chat_history[i].strip() + '\n'
    return chat_load.strip() + '\n' + chat.strip() + '\n' + message.strip()

def edit_file(file_path: str):
    editor = DEFAULT_EDITOR
    if os.getenv('EDITOR') != '':
        editor = os.getenv('EDITOR')
    else:
        out("EDITOR environment variable is not set. using {} as default."
            .format(DEFAULT_EDITOR), Fore.YELLOW)
    os.system('{} {}'.format(editor, file_path))

def calc_message_lines(message: str) -> int:# TODO
    lines_to_clear = 0
    separator = ''
    columns = os.get_terminal_size().columns
    for char in list(message):
        if char == '\n':
            lines_to_clear += math.floor(len(separator) / columns) + 1
            separator = ''
        else:
            separator += char
    return lines_to_clear

def main():

    chat_history = []
    chat_history_index = -1
    save_file_name = ''
    chat = ''
    chat_load = ''
    message_history = ''
    message = ''

    parser = argparse.ArgumentParser(
           prog = 'gpt-tool',
            description = 'A command line tool for using OpenAI\'s ChatGPT.\n' +
            'https://github.com/apstamp45/gpt-tool/',
            epilog = COMMANDS_HELP,
            formatter_class=RawTextHelpFormatter
            )
    parser.add_argument('-l', '--load-chat', type = str, metavar = 'file',
                        help = 'Loads given chat file if present')
    parser.add_argument('-L', '--edit-chat', type = str, metavar = 'chat-file',
                        help = 'Edits the given chat file in default text editor then quits')
    colorama.init()
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if openai.api_key == '':
        out('Error: your API key is not set.\nYou can place "OPENAI_API_KEY=your OpenAI API key here" ' +
            'in your .bashrc or .zshrc, then run "source ~/.bash(zsh)rc" to reload.',
            Fore.LIGHTRED_EX)
        return

    if not os.path.exists(SAVES_DIRECTORY):
        os.makedirs(SAVES_DIRECTORY)

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
        if (line == ';h'):# HELP
            clear_lines(1)
            out(COMMANDS_HELP, Fore.LIGHTBLUE_EX)

        elif (line == ';z'):# UNDO
            clear_lines(1)
            if message != '':
                message_history = message.strip()
                lines_to_clear = calc_message_lines(message)
                clear_lines(lines_to_clear)
                # print('clear lines: {}'.format(lines_to_clear))
                message = ''
            elif chat_history_index >= 0:
                removed_item = chat_history[chat_history_index]
                chat_history_index -= 1
                chat = get_complete_chat(chat_load, chat_history, chat_history_index, message)
                lines_to_clear = calc_message_lines(removed_item)
                clear_lines(calc_message_lines(removed_item) + 1)
            else:
                out('Undo limit reached.', Fore.YELLOW)

        elif line == ';;': # SEND
            clear_lines(1)
            if internet():
                chat += message.strip() + '\n'
                chat_history_index += 1
                if len(chat_history) > chat_history_index:
                    chat_history[chat_history_index] = message.strip()
                else:
                    chat_history.append(message.strip())
                message = ''
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
                    chat_history_index += 1
                    if len(chat_history) > chat_history_index:
                        chat_history[chat_history_index] = result.strip()
                    else:
                        chat_history.append(result.strip())
                    out(result.strip(), Fore.LIGHTGREEN_EX)
                    message_history = ''
                except openai.error.APIConnectionError:
                    out('Error: There was a problem either with your internet connection, ' +
                        'or with your API key.\nMake sure the OPENAI_API_KEY enviornment ' +
                        'variable is set to your OpenAI API key, and that you have a secure ' +
                        'internet connection', Fore.LIGHTRED_EX, chat_history, chat_history_index)
                    return
                except (openai.error.ServiceUnavailableError, openai.error.RateLimitError):
                    out('WARNING: Something went wrong with the OpenAI server.' +
                        'Perhaps they are overloaded?', Fore.YELLOW, chat_history, chat_history_index)
            else:
                out('It seems that you do not have an internet connection.\n' +
                    'Try reconnecting to the internet and re-sending the message', Fore.YELLOW)

        elif len(split_line) > 0 and split_line[0] == ';s': # SAVE
            clear_lines(1)
            if len(split_line) < 2 and save_file_name == '':
                out('You must provide a filename to save the chat', Fore.YELLOW)
            elif save_file_name == '':
                chat_load = save_chat_file(split_line[1], chat_load, chat_history, chat_history_index, message)
                message = ''
                save_file_name = split_line[1]
                chat_history = []
                chat_history_index = -1
            else:
                chat_load = save_chat_file(save_file_name, chat_load, chat_history, chat_history_index, message)
                message = ''
                chat_history = []
                chat_history_index = -1

        elif len(split_line) > 0 and split_line[0] == ';l':# LOAD
            clear_lines(1)
            if len(split_line) < 2:
                out('You must provide a load file name to load', Fore.YELLOW)
            else:
                temp = load_chat_file(split_line[1])
                if temp != '':
                    chat_load = temp
                    chat = get_complete_chat(chat_load, chat_history, chat_history_index, message)
                    save_file_name = split_line[1]
                    chat_history = []

        elif line == ';L':# EDIT
            clear_lines(1)
            if save_file_name == '':
                out("Cannot open chat file: none was loaded.", Fore.YELLOW)
            else:
                save_chat_file(save_file_name, chat_load, chat_history, chat_history_index, message)
                message = ''
                chat_history = []
                chat_history_index = -1
                edit_file(SAVES_DIRECTORY + save_file_name + '.chat')
                chat_load = load_chat_file(save_file_name)
                chat = get_complete_chat(chat_load, chat_history, chat_history_index, message)

        elif line == ';S':# LIST
            clear_lines(1)
            out('Here is a list of available load file names:', Fore.LIGHTBLUE_EX)
            for file in os.listdir(SAVES_DIRECTORY):
                out(file.removesuffix('.chat'), Fore.LIGHTBLUE_EX)

        elif line == ';x':# CLEAR SCREEN
            clear_lines(1)
            clear_lines(os.get_terminal_size().lines - 1)

        elif line == ';X':# CLEAR CHAT
            clear_lines(1)
            chat = ''
            chat_history_index = -1;
            message = ''
            out('Chat was cleared.', Fore.LIGHTBLUE_EX)

        elif line == ';Z':# REDO
            clear_lines(1)
            if message_history == '':
                if chat_history_index < len(chat_history) - 1:
                    chat_history_index += 1
                    if (chat_history_index % 2 != 0):
                        out(chat_history[chat_history_index], Fore.LIGHTGREEN_EX)
                    else:
                        print(chat_history[chat_history_index])
                    chat = get_complete_chat(chat_load, chat_history, chat_history_index, message)
                else:
                    out('Cannot redo any further.', Fore.YELLOW)
            else:
                message = message_history + '\n'
                message_history = ''
                print(message, end = '')

        else:
            message += line + '\n'

        line = input()

if __name__ == '__main__':
    main()

