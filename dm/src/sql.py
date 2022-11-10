import pymysql
import pandas as pd
from datetime import datetime

class Sql :
    def __init__(self, dbName, comment= "",
                 hostIP='61.98.230.194',
                 userID='root', password='almaden7025!', charset='utf8mb4'):
        self.dbName = dbName
        self.hostIP = hostIP
        self.userID = userID
        self.password = password
        self.charset = charset
        self.conn = None
        self.curs = None
        self.connect()
        # self.sql_alchemy_engine = create_engine(
        #     ("mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8").format
        #                        (userID,
        #                         password,
        #                         hostIP,
        #                         3306,
        #                         dbName),
        #                         encoding='utf-8')

    def connect(self):
        self.conn = pymysql.connect(host=self.hostIP, user=self.userID, password=self.password,
                               db=self.dbName, charset=self.charset)
        self.curs = self.conn.cursor(pymysql.cursors.DictCursor)

    def query(self, query):
        self.curs.execute(query)
        self.conn.commit()
    def close(self):
        self.conn.close()

    def update_one(self,tableName, field, value, field_id, id):
        if type(value) is str :
            value = '"'+value+'"'
        query =f"update {tableName} set {field}={value} where {field_id}={id}"
        self.query(query)

    def select(self, tablename, what="", where="", asDataFrame=False, count=False):
        '''
        e.g. select('tablename', 'id, keyword, title', 'date like "2019%"', True)
        :param tablename: table name
        :param params: field = value or // field like %value%
        :param count:
        :return:
        '''
        if count :
            select_what = "count(*)"
        else :
            if len(what)<1 :
                select_what = "*"
            else :
                select_what = what
        sql = "select %s from %s"%(select_what, tablename)
        if len(where) > 1:
            sql+=" where "+where

        self.curs.execute(sql)
        rows = self.curs.fetchall()
        if count :
            return int(rows[0]['count(*)'])
        else :
            if asDataFrame :
                return pd.DataFrame(rows)
            else :
                return rows

    def check_duplication(self, tablename, **params):
        select_where = " and ".join([k+"="+"'{}'".format(v) if type(v)==str else k+"="+str(v) for k, v in params.items()])
        count = self.select(tablename, where=select_where, count=True)
        if count>0 : return True
        else : return False

    def insert_withoutDuplication(self, tablename, check_list, **params):
        '''
        e.g. insert_withoutDuplication('datatable', ['keyword','url'], keyword = 'abc', url = 'http://', date = '20150305', title = '테스트')
        :param tablename: str
        :param check_list: list
        :param params: dict
        :return: None or id(int)
        '''
        new_params = {}
        for k,v in params.items() :
            if k in check_list :
               new_params[k] = v
        if self.check_duplication(tablename, **new_params) :
            return None
        else:
            return self.insert(tablename, **params)

    def update_multi(self,tablename,update_dict:dict, where_dict:dict):

        update_sql = "update %s set "%(tablename) + ",".join([key+"="+"%s" for key in update_dict.keys()])
        where_sql = "where " + "and".join([key+"="+"%s" for key in where_dict.keys()])
        sql = update_sql +' '+where_sql
        update_set_value = list(update_dict.values())
        where_value = list(where_dict.values())
        value = update_set_value + where_value
        self.curs.execute(sql,value)
        self.conn.commit()

    def insert(self, tablename, **params):
        '''
        e.g. insert('datatable', date = '20150305', title = '테스트')
        :param tablename: str
        :param params: dict
        :return: id(int)
        '''
        len_params = len(params)
        sql = "insert into %s("%(tablename)
        for k in params.keys() :
            sql += str(k)+","
        sql = sql[:-1]+") values("
        for i in range(len_params) :
            sql += "%s"+","
        sql = sql[:-1]+")"
        v = tuple(params.values())
        self.curs.execute(sql, v)
        row_id = self.curs.lastrowid
        self.conn.commit()
        return row_id


    def get_now_datetime(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')