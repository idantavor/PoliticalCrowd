import logging

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
logging.basicConfig(format=FORMAT)

def getLogger(name, is_debug=False):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if is_debug else logging.INFO)
    return logger


# class LEVEL(enum.Enum):
#     D="debug"
#     W="warning"
#     E="error"
#
#
#
#
# def log(msg,lvl:LEVEL):
#     # Get the previous frame in the stack, otherwise it would
#     # be this function!!!
#     func = inspect.currentframe().f_back.f_code
#     # Dump the message + the name of this function to the log.
#     logging.debug("%s: %s in %s:%i" % (
#         msg,
#         func.co_name,
#         func.co_filename,
#         func.co_firstlineno
#     ))



