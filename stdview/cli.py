import os
import argparse

from .app import app, stdconf

def main():

    parser = argparse.ArgumentParser(description="STD Viewer")

    parser.add_argument('-d', '--dir', dest='basepath', type=str, default='.', help='Directory to browse')
    parser.add_argument('-p', '--port', dest='port', type=int, default=5567, help='Port to use')
    parser.add_argument('-a', '--all', dest='show_all', action='store_true', help='Show all files')
    parser.add_argument('-i', '--inline-previews', dest='inline_previews', action='store_true', help='Enable inline image previews in directory listings')

    parser.add_argument('--debug', dest='debug', action='store_true', help='Debug mode')

    parser.add_argument('-s', '--secret', dest='secret', type=str, default=os.urandom(24), help='Secret key')

    # TODO: option to listen for external requests
    # TODO: option to set access tokens

    args, others = parser.parse_known_args()

    app.config['stdview']['basepath'] = args.basepath
    app.config['stdview']['show_all'] = args.show_all
    app.config['stdview']['inline_previews'] = args.inline_previews

    app.secret_key = args.secret

    app.run(port=args.port, debug=args.debug)
