import json
import logging
from docopt import docopt
from .utils import find_task
from opv_directorymanagerclient import DirectoryManagerClient, Protocol
from opv_api_client import RestClient

# tasks = ["rotate", "cpfind", "autooptimiser", "stitchable", "stitch", "photosphere", "tiling"]
tasks = ["rotate", "cpfind", "autooptimiser", "stitchable", "stitch", "photosphere", "tiling"]

__doc__ = """ Task executor, will execute some task with input datas.

Usage:
    opv-task <task-name> <input-data> [--db-rest=<str>] [--dir-manager=<str>] [--debug]
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

    # id_task = (arguments['<id>'], arguments['<id-malette>'])
    inputData = json.loads(arguments['<input-data>'])
    task_name = arguments['<task-name>']

    if task_name == "run_all":
        for task in tasks:
            logger.info("Starting task %s" % task)

            lastTaskReturn = run(dir_manager_client, db_client, task, inputData)
            logger.debug("TaskReturn : " + lastTaskReturn.toJSON())

            if not lastTaskReturn.isSuccess():
                logger.error("Last task executed failled with following error : " + lastTaskReturn.error)
                break
            inputData = lastTaskReturn.outputData

            logger.info("End of task %s" % task)
    else:
        lastTaskReturn = run(dir_manager_client, db_client, task_name, inputData)
        logger.debug("TaskReturn : " + lastTaskReturn.toJSON())

        if not lastTaskReturn.isSuccess():
            logger.error("Last task executed failled with following error : " + lastTaskReturn.error)

def run(dm_c, db_c, task_name, inputData):
    """
    Run task.
    Return a TaskReturn.
    """
    Task = find_task(task_name)
    if not Task:
        raise Exception('Task %s not found' % task_name)

    task = Task(client_requestor=db_c, opv_directorymanager_client=dm_c)
    return task.run(options=inputData)


if __name__ == "__main__":
    main()
