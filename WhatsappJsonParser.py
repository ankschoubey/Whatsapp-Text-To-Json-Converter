import argparse
import json
import os.path
import re
import sys
from functools import lru_cache
from pprint import pprint

import constants
import helper


class WhatappToJson(object):

    def __init__(self):
        pass

    @staticmethod
    def get_device_specific_metas(device: str):
        return constants.devices[device]['delimeter_format'], constants.devices[device]['attachment_tag'], constants.devices[device]['attachment_delimeters']

    @staticmethod
    def format(text: str, device: str = 'iphone'):
        """ Formats String of chat into JSON.

        Arguments:
            text {str} -- formats chat string
        
        Keyword Arguments:
            device {str} -- either 'android' or 'iphone' (default: {'iphone'})
        
        Returns:
            dict -- {
                        'device': device,
                        'attachment_extensions': list(attachment_extensions),
                        'participants': list(participants),
                        'chats': output
                    }
        """

        delimiter_format, attachment_format, attachment_delimiters = WhatappToJson.get_device_specific_metas(
            device=device)
        
        participants = set()
        attachment_extensions = set()

        output = []
        for i in text.split('\n'):
            splitted = re.split(delimiter_format, i)

            if len(splitted) == 1:  # Continuation of last message
                output[-1]['message'] += '\n'+i
                continue

            line = {
                'date': splitted[0],
                'sender': splitted[1],
                'message': ''.join(splitted[2:]),
                'type': 'conversation'
            }

            try:
                line['date'] = helper.get_date(
                    line['date'], device).strftime(constants.devices['iphone']['date_format'])
            except:  # if not in date format then it is continuation of last message
                output[-1]['message'] += '\n'+i
                continue
                
            if len(splitted) == 2 and line['message'] == '':  # Whatsapp Meta
                line['message'] = line['sender']
                del line['sender']
                line['type'] = 'whatsapp meta'
            elif line['message'].endswith(attachment_format):
                file_name, * \
                    meta = re.split(attachment_delimiters,
                                    line['message'])[:-1]
                extention = file_name[file_name.rfind('.')+1:].strip()
                line['type'] = 'attachment'
                line['message'] = ''
                line['attachment'] = {
                    'file_name': file_name,
                    'meta': '' if len(meta) == 0 else meta[0],
                    'extention': extention
                }
                attachment_extensions.add(extention)

            sender = line.get('sender', False)

            if sender:
                participants.add(sender)
            output.append(line)

        return {
            'device': device,
            'attachment_extensions': list(attachment_extensions),
            'participants': list(participants),
            'chats': output
        }

    @staticmethod
    def formatFile(source: str, destination: str = None, device: str = 'iphone'):
        """Reads in a file and then sends to formatFunction
        
        Arguments:
            source {str} -- file path of source chat file
        
        Keyword Arguments:
            destination {str} -- destination of file if file is to be exported as json (default: {None})
            device {str} -- either 'android' or 'iphone' (default: {'iphone'})
        
        Returns:
            dict -- same as that of format function
        """

        text = ''
        with open(source) as f:
            text = f.read()

        output = WhatappToJson.format(text, device=device)

        if destination is not None:
            with open(destination, 'w') as file:
                file.write(json.dumps(output, ensure_ascii=False, indent=2))
        return output
    
def getCommandLineArguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True,
        help="chat text file")
    ap.add_argument("-d", "--device", required=True,
        help="can be 'iphone' or 'android'")
    ap.add_argument("-s", "--save", required=False,
        help="path of file/direction to save json, 'default' would be same as text file name in same directory")
    ap.add_argument('-v','--verbose', action='store_const',
                    const=True, default=False,
                    help='Verbose (Print output)')
    args = vars(ap.parse_args())

    file_path: str = args.get('file')
    device: str = args.get('device').lower()
    destination: str = args.get('save')
    verbose: str = args.get('verbose')

    if not os.path.isfile(file_path):
        ap.error('Could not find '+file_path)
    if not file_path.endswith('.txt'):
        ap.error('File does not end with .txt: '+file_path)

    if destination and  os.path.isdir(destination):
        destination = os.path.join(destination, file_path[:-4])
    if destination and destination.lower().strip() == 'default':
        destination = os.path.dirname(file_path) + file_path[:-4]
    if destination and not destination.endswith('.json'):
        destination +='.json'
    

    if device not in ['iphone','android']:
        ap.error('device can be either \'iphone\' or \'android\'. Others are not supported yet.')
    
    return file_path, device, destination, verbose

if __name__ == "__main__":
    file_path, device, destination, verbose = getCommandLineArguments()
    output = WhatappToJson().formatFile(source=file_path, destination=destination, device=device)
    if verbose:
        pprint(output)
