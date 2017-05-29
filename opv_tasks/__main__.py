import json
import logging
from docopt import docopt
from .utils import find_task
from opv_directorymanagerclient import DirectoryManagerClient, Protocol
from opv_api_client import RestClient

tasks = ["rotate", "cpfind", "autooptimiser", "stitchable", "stitch", "photosphere", "tiling"]

__doc__ = """ Roate Task, will rotate pictures from a lot

Usage:
    opv-task <task-name> <id> <id-malette> [--db-rest=<str>] [--dir-manager=<str>] [--debug]
    opv-task (-h | --help)

Options:
    -h --help                Show help.
    --db-rest=<str>          API rest server [default: http://localhost:5000]
    --dir-manager=<str>      API for directory manager [default: http://localhost:5001]
    --debug                  Debug mode.

Task are in: run_all, """ + ', '.join(tasks)

def main():
    """Main function."""
    arguments = docopt(__doc__)
    debug = bool(arguments.get('--debug'))

    log_level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    logger = logging.getLogger(__name__)

    dir_manager_client = DirectoryManagerClient(api_base=arguments['--dir-manager'], default_protocol=Protocol.FTP)
    db_client = RestClient(arguments['--db-rest'])

    id_task = (arguments['<id>'], arguments['<id-malette>'])
    task_name = arguments['<task-name>']

    if task_name == "run_all":
        for task in tasks:
            logger.info("Starting task %s" % task)

            out = json.loads(run(dir_manager_client, db_client, task, id_task))
            id_malette = out['id']['id_malette']
            del out['id']['id_malette']
            id_ressource = next(iter(out['id'].values()))
            id_task = (id_ressource, id_malette)

            logger.info("End of task %s" % task)
    else:
        out = run(dir_manager_client, db_client, task_name, id_task)

    print(out)


def run(dm_c, db_c, task_name, id_task):
    """Run task."""
    Task = find_task(task_name)
    if not Task:
        raise Exception('Task %s not found' % task_name)

    task = Task(client_requestor=db_c, opv_directorymanager_client=dm_c)
    return task.run(options={"id": id_task})


if __name__ == "__main__":
    main()
