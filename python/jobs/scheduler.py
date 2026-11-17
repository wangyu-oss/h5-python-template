import logging
import os
import sys
import threading
import time

logger = logging.getLogger('jobs')
_started = False


def start():
    global _started
    joined = ' '.join(sys.argv)
    if any(cmd in joined for cmd in ('test', 'migrate', 'makemigrations', 'shell', 'collectstatic', 'seed_demo')):
        return
    if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        return
    if _started:
        return
    _started = True

    def loop():
        while True:
            try:
                from jobs.tasks import run_due
                run_due()
            except Exception:
                logger.exception('job loop failed')
            time.sleep(60)

    threading.Thread(target=loop, name='h5-jobs', daemon=True).start()
    logger.info('in-process scheduler started')
