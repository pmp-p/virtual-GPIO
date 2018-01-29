'''
ESP32 upload tool by The Cheaterman
WTFPL license (although it's very much compatible with beerware)
'''

from argparse import ArgumentParser
from os.path import basename
from serial import Serial
from textwrap import dedent
from zlib import compress
import glob

parser = ArgumentParser(
    description=(
        'Upload a file to ESP8266/ESP32 using serial REPL, '
        'requires your ESP32 to currently be running the REPL and not your own program'
    )
)
parser.add_argument(
    'filename',
    type=str,
    help='Full path to source file',
)
parser.add_argument(
    'destination',
    type=str,
    help='Name of target file',
    nargs='?',
)

args = parser.parse_args()

with Serial(glob.glob('/dev/ttyUSB*')[-1], 115200) as esp:
    esp.write('')
    with open(args.filename, 'rb') as source_file:
        esp.write('data = b%r\n' % compress(source_file.read()))
    esp.write(dedent('''
        from zlib import decompress
        with open('%s', 'wb') as target_file:
            target_file.write(decompress(data))
    ''' % (args.destination if args.destination else basename(args.filename))
    ).strip() + '\n')
    esp.write('')
    esp.write('')
    print('Done!')
