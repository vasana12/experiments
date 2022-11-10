import logging
from datetime import datetime, timezone, timedelta
from src.utils import get_project_root
from src.sql import Sql
timezone_kst = timezone(timedelta(hours=9))


# class IdFilter(logging.Filter):
#     def filter(self, record):
#         record.trace_id = trace_id if trace_id is not None else "null"
#         return True

class LogManager:
    def __init__(self, sys_level="DEBUG", db_level="INFO", file_level="DEBUG", filename=None, cls_type=None):
            """
            Parameters
            ----------
            sys_level : FATAL, CRITICAL, ERROR, WARN, INFO, DEBUG, NOTSET - 시스템 출력 레벨
            file_level : FATAL, CRITICAL, ERROR, WARN, INFO, DEBUG, NOTSET - 파일 출력 레벨
            db_level : FATAL, CRITICAL, ERROR, WARN, INFO, DEBUG, NOTSET - 디비 출력 레벨
            """

            self.project_dir = get_project_root()
            self._logger = None
            db_level = db_level.upper()
            sys_level = sys_level.upper()
            file_level = file_level.upper()

            level_info = {"NO":1000 ,"TEST": 100, 'FATAL': 50, 'CRITICAL': 50, 'ERROR': 40, 'WARN': 30, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10,
                             'NOTSET': 0}

            FORMAT = '%(thread)s\t%(levelname)s\t%(asctime)s\t%(module)s.%(funcName)s\t%(message)s\t%(trace_id)s\t%(status)s'
            #Todo: status -> excetpion , message 에 에러에 대한 설명

            def timetz(*args):
                return datetime.now(tz).timetuple()

            def switch_level(level):
                try:
                    level = level_info[level]
                except:
                    return logging.DEBUG
                else:
                    return level
            tz = timezone_kst
            logging.Formatter.converter = timetz
            # logger.addFilter(IdFilter())

            ### Stream handler(syslog)
            # logging.basicConfig(format=FORMAT)
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False

            # 로그를 콘솔에 출력하는 Handler
            stream_handler = StreamHandler()
            stream_handler.setLevel(switch_level(sys_level))
            STREAM_FORMAT = FORMAT
            stream_log_formatter = logging.Formatter(STREAM_FORMAT)
            stream_handler.setFormatter(stream_log_formatter)
            logger.addHandler(stream_handler)

            # 로그를 DB에 저장하는 Handler
            db_handler = DatabaseHandler()
            db_handler.setLevel(switch_level(db_level))
            DB_FORMAT = FORMAT
            db_log_formatter = logging.Formatter(DB_FORMAT)
            db_handler.setFormatter(db_log_formatter)
            logger.addHandler(db_handler)

            ##File handler
            if not file_level == "NO":
                filename = f"{self.project_dir}/log_script/{filename}_{datetime.now().strftime('%Y-%m-%d')}.log" if filename is not None else f"{self.project_dir}/nope.log"
                file_handler = logging.FileHandler(filename=filename, mode="a")
                file_handler.setLevel(switch_level(file_level))
                file_log_formatter = logging.Formatter(FORMAT)
                file_handler.setFormatter(file_log_formatter)
                logger.addHandler(file_handler)

            # Todo: config 파일 만들어서 하나의 모듈에서 class 별 logging 을 control 할 수 있도록 해야함
            # ex: config 파일 만들어서 하나의 모듈에서 class 별 logging 을 control 할 수 있도록 해야함
            # logger_config = {"instagram_scraper":
            #                      {
            #                          "sys_level": "DEBUG",
            #                          "file_level": "INFO",
            #                          "db_level": "ERROR"
            #                      },
            #                  "main":
            #                      {
            #                          "sys_level": "DEBUG",
            #                          "file_level": "INFO",
            #                          "db_level": "WARNING"
            #                      },}
            self._logger = logger


    @property
    def logger(self):
        # class InitFilter(logging.Filter):
        #     def filter(self, record):
        #         record.trace_id = None
        #         record.error_type = None
        #         return True
        # self._logger.addFilter(InitFilter())
        return self._logger

    def set_logger_id(self, trace_id):
        class IdFilter(logging.Filter):
            def filter(self, record):
                record.trace_id = trace_id
                return True
        self._logger.addFilter(IdFilter())

    def set_logger_service_name(self, service_name):
        class ServiceNameFilter(logging.Filter):
            def filter(self, record):
                record.service_name = service_name
                return True
        self._logger.addFilter(ServiceNameFilter())
# class FileHandler(logging.FileHandler, logging.StreamHandler):
#     def emit(self, record):
#         from model import Log, LogStatus
#
#         if "trace_id" not in record.__dict__.keys():
#             record.trace_id = None
#
#         if "status" not in record.__dict__.keys():
#             record.status = {"code": 200, "description": "success"}
#
#         self.format(record)
#         """
#         Emit a record.
#
#         If the stream was not opened because 'delay' was specified in the
#         constructor, open it before calling the superclass's emit.
#         """
#         if self.stream is None:
#             self.stream = self._open()
#         logging.StreamHandler.emit(self, record)

class StreamHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        if "table_name" not in record.__dict__.keys():
            record.table_name = "log"
        if "trace_id" not in record.__dict__.keys():
            record.trace_id = None
        if "service_name" not in record.__dict__.keys():
            record.service_name = None
        if "status" not in record.__dict__.keys():
            record.status = None
        logging.StreamHandler.emit(self, record)

class DatabaseHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        try:
            self.sql = Sql(dbName="instag")
        except:
            self.sql = Sql(dbName="instag")

    def emit(self, record):
        if "table_name" not in record.__dict__.keys():
            record.table_name = "log"

        if "trace_id" not in record.__dict__.keys():
            record.trace_id = None

        if "service_name" not in record.__dict__.keys():
            record.service_name = None

        if "status" not in record.__dict__.keys():
            record.status = None

        self.format(record)
        document = {
                    "asctime": datetime.now(),
                    "levelname": record.levelname,
                    "module": record.module,
                    "funcName": record.funcName,
                    "lineno": record.lineno,
                    "message": record.message,
                    "trace_id": record.trace_id,
                    "thread_id": record.thread,
                    "service_name": record.service_name,
                    "status": record.status
                    }
        try:
            print("here")
            self.sql.insert(record.table_name, **document)
        except:
            self.sql = Sql(dbName="instag")

# if __name__ == '__main__':
#     logger = logging.getLogger('kjyggg')     # logger name 선언
#     logger.setLevel(logging.DEBUG)              # logger level 설정
#     dbHandler = DatabaseHandler()           # database handler 선언
#     logger.addHandler(dbHandler)            # database hanlder 추가
#     logger.debug("debug message")               # debug 메세지 작성
#     logger.info("info message")                 # info 메세지 작성
#     logger.warning("warning message")           # warning 메세지 작성
#     logger.critical("critical message")         # critical 메세지 작성