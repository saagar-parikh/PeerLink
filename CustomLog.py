# CustomLog.py
# Implemented by Allan Nesathurai (anesathu@andrew.cmu.edu)
import logging

def addLoggingLevel(levelName, levelNum, methodName=None):
    # https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

# need to add logging level before including it in the custom formatter 
addLoggingLevel("HEARTBEAT", 51)
addLoggingLevel("STATE", 52)
addLoggingLevel("SEND", 53)
addLoggingLevel("RECEIVE", 54)
addLoggingLevel("RECEIVE_D", 55)


class CustomFormatter(logging.Formatter):
    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    grey = "\x1b[38;20m"
    
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    bold_green = "\x1b[32;1m"
    yellow = "\x1b[33;20m"
    bold_yellow = "\x1b[33;1m"
    blue = "\x1b[34;20m"
    bold_blue = "\x1b[34;1m"
    purple = "\x1b[35;20m"
    bold_purple = "\x1b[35;1m" 
    cyan = "\x1b[36;20m"
    bold_cyan = "\x1b[36;1m" 
    white = "\x1b[37;20m"
    bold_white = "\x1b[37;1m" 

    strike = "\x1b[9m"

    reset = "\x1b[0m"
    # format = "|%(levelname)-8s| PID: %(process)d (%(filename)s:%(lineno)d) [%(asctime)s.%(msecs)03d] %(message)s"
    format = "|%(levelname)-10s| [%(asctime)s.%(msecs)03d] "
    msg = "%(message)s"
    # %(thread)d
    # %(threadName)s
    level=logging.DEBUG

    FORMATS = {
        logging.DEBUG: grey + format + msg + reset,
        logging.INFO: grey + format + msg + reset,
        logging.WARNING: yellow + format + msg + reset,
        logging.ERROR: red + format + msg + reset,
        logging.CRITICAL: bold_red + format + msg + reset,
        logging.HEARTBEAT: bold_green + format + msg + reset,
        logging.STATE: green + format + msg + reset,
        logging.SEND: cyan + format + msg + reset,
        logging.RECEIVE: bold_cyan + format + msg + reset,
        logging.RECEIVE_D: bold_cyan + format + strike + msg + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%H:%M:%S")
        return formatter.format(record)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger = logging.getLogger("18749")
# change the minimum logging level here 
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)
logger.addHandler(ch)

# logger.addHandler(logging.FileHandler("debug.log"))

if __name__ == '__main__':
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
    logger.heartbeat("heartbeat message")
    logger.state("state message")
    logger.send("send message")
    logger.receive("receive message")
    logger.receive_d("receive message duplicate")