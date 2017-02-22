""" Roate Task, will rotate pictures from a lot

Usage:
    opv-task <task-name> <id> [--db-rest=<str>] [--dir-manager=<str>] [--debug]
    opv-task (-h | --help)

Options:
    -h --help                Show help.
    --db-rest=<str>          API rest server [default: http://localhost:5000]
    --dir-manager=<str>      API for directory manager [default: http://localhost:5001]
    --debug                  Debug mode.

Task are in: rotate, cpfind, autooptimiser, stitchable, tiling...
"""
import logging
from docopt import docopt
from opv_directorymanagerclient import DirectoryManagerClient, Protocol
from potion_client import Client
from pprint import pprint

from .utils import find_task

def main():
    arguments = docopt(__doc__)
    debug = bool(arguments.get('--debug'))

    log_level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    dir_manager_client = DirectoryManagerClient(api_base=arguments['--dir-manager'], default_protocol=Protocol.FTP)
    db_client = Client(arguments['--db-rest'])

    Task = find_task(arguments['<task-name>'])
    if not Task:
        logging.getLogger().error('Task %s not found' % arguments['<task-name>'])
        return

    task = Task(client_requestor=db_client, opv_directorymanager_client=dir_manager_client)
    pprint(task.run(options={"id": arguments['<id>']}))

if __name__ == "__main__":
    main()
