import logging


def _init():
  log = logging.getLogger()

  if log.handlers:
    for handle in log.handlers:
      log.removeHandler(handle)
  logging.basicConfig(level=logging.INFO)
  return log


log = _init()
