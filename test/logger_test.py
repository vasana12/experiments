from manager import m_log
from setting import *


m_log_obj = m_log.LogManager(sys_level="DEBUG", db_level="INFO", file_level="NO", filename=None)

if __name__ == '__main__':
    ### logger 객체 생성
    logger = m_log_obj.logger
    ### logger 의 trace_id 설정
    m_log_obj.set_logger_id(str('id:1234'))
    logger.info("test")
    logger.info("test", extra={"exception": "test", "table_name": "log_trace"})

