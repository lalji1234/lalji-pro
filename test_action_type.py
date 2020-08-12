import unittest
import pyodbc
import psycopg2
import datetime
from config_parser import get_config
from migration_config import SCHEMA_MAP


class TestDBConnection(unittest.TestCase):
    def setUp(self):
        # connection for mssql server
        source_db_config = get_config("SOURCE_DATABASE_CREDENTIALS")
        mssql_connection = pyodbc.connect('Driver='+source_db_config["driver"]+';'
                                         'Server='+source_db_config["server"]+';'
                                         'Database='+source_db_config["database"]+';'
                                         'password='+source_db_config["password"]+';'
                                        # 'uid=' + source_db_config["username"] + ';'
                                         )
        self.mssql_cursor = mssql_connection.cursor()

        # connection for postgresql server
        target_db_config = get_config("TARGET_DATABASE_CREDENTIALS")
        psql_connection = psycopg2.connect(user=target_db_config["user"],
                                               password=target_db_config["password"],
                                               host=target_db_config["host"],
                                               port=target_db_config["port"],
                                               database=target_db_config["database"])
        self.psql_cursor = psql_connection.cursor()
        self.mssql_query = "select top % s  * from filesystem"
        # top % s
        self.mssql_attributes = '10'
        self.mssql_data = []
        self.mssql_cursor.execute(self.mssql_query % self.mssql_attributes)
        columns = [column[0] for column in self.mssql_cursor.description]
        for row in self.mssql_cursor.fetchall():
            self.mssql_data.append(dict(zip(columns, row)))

    def test_file_records(self):
        table_name = 'filesystem'
        schema_map = SCHEMA_MAP[table_name]
        for rec in self.mssql_data:
            print(rec)
            for new_table_name, field_map, pkey in schema_map:
                print(field_map)
                query = "select * from %s where %s=%s"
                # query = "select id, is_active, is_orphan, encode(md5, 'hex'), encode(sha256, 'hex') from file where id=%s"
                print(rec)
                attributes = (new_table_name, field_map, rec[pkey])
                print(query % attributes)
                self.psql_cursor.execute(query % attributes)
                columns = [column[0] for column in self.psql_cursor.description]
                res = self.psql_cursor.fetchall()[0]
                psql_data = dict(zip(columns, res))
                print(psql_data)
                for key, value in field_map.items():
                    if key.endwith('_ms5'):
                        continue
                    print(key, value)
                    mssql_val = rec[key]
                    psql_val = psql_data[value]
                    # if key.endwith('_ms5'):
                    #     continue
                    if isinstance(mssql_val, datetime.datetime):
                        self.assertEqual(mssql_val.strftime('%Y-%m-%d %H:%M:%S.%f'),
                                         psql_val.strftime('%Y-%m-%d %H:%M:%S.%f'))
                    else:
                        self.assertEqual(mssql_val, psql_val)



if __name__ == '__main__':
    unittest.main()
