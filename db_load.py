import pandas as pd
import numpy as np
import ibm_db
import json
from datetime import datetime


class DbAction:
    """
    This class is for acting with db2
    """

    def __init__(self, filename):
        self.filename = filename

        self.driver = None
        self.database = None
        self.hostname = None
        self.port = None
        self.protocol = None
        self.login = None
        self.password = None

        self._load_params()
        self.conn = self._connect()

    def _load_params(self):
        """
        Set params for db connection
        :return:
        """
        with open(self.filename, 'r') as f:
            params = json.loads(f.read())

        self.driver = params['driver']
        self.database = params['database']
        self.hostname = params['hostname']
        self.port = params['port']
        self.protocol = params['protocol']
        self.login = params['login']
        self.password = params['password']

    def _connect(self):
        """
        Connection for databasae
        :return:
        """
        dsn = (
            "DRIVER={0};"
            "DATABASE={1};"
            "HOSTNAME={2};"
            "PORT={3};"
            "PROTOCOL={4};"
            "UID={5};"
            "PWD={6};").format(self.driver, self.database, self.hostname, self.port,
                               self.protocol, self.login, self.password)
        try:
            conn = ibm_db.connect(dsn, "", "")
            print("Connected to database")
            return conn
        except Exception:
            print("\nERROR: Unable to connect to the \'" + self.database + "\' server.")
            print("error: ", ibm_db.conn_errormsg())
            exit(-1)

    def select(self, query):
        """
        Extract a query
        :param query:
        :return:
        """

        stmt = ibm_db.exec_immediate(self.conn, query)
        dictionary = ibm_db.fetch_assoc(stmt)

        data = []
        while dictionary is not False:
            data.append(dictionary)
            dictionary = ibm_db.fetch_assoc(stmt)
        print('Request is done')
        return pd.DataFrame.from_records(data)

    def delete(self, query):
        """
         Extract a query
         :param query:
         :return:
         """
        ibm_db.exec_immediate(self.conn, query)

        print("Table is cleared")

    def insert(self, df, database, _table,
               collist=('ADDRESS', 'TYPE_PP', 'COMPANY_NAME',
                        'LAT', 'LON', 'REGION', 'DATE_OF_LOADING',
                        'DATE_OF_LOADING_FIRST'),

               sql_tuple=('ADDRESS', 'TYPE_PP', 'COMPANY_NAME',
                          'LAT', 'LON', 'REGION', 'DATE_OF_LOADING',
                          'DATE_OF_LOADING_FIRST'
                          )):

        """
        Insert data from df into table
        :param df: Dataframe
        :param database:  database name
        :param _table:  table
        :param collist:  dataframe_columns
        :param sql_tuple:  columns in sql
        :return:
        """

        cols = ", ".join(sql_tuple)

        df.loc[df.LAT.isin(['', ' ', None, np.nan, np.inf, -np.inf]), 'LAT'] = 0
        df.loc[df.LON.isin(['', ' ', None, np.nan, np.inf, -np.inf]), 'LON'] = 0

        tuple_of_tuples = tuple([tuple(x) for x in
                                 df[list(collist)].values])

        db_name = database + "." + _table

        sql = "insert into {0} ({1}) values(?,?, ?,?, ?,?,?, ?);".format(db_name, cols)

        stmt = ibm_db.prepare(self.conn, sql)

        try:
            ibm_db.execute_many(stmt, tuple_of_tuples)
        except Exception:

            print("\nERROR: Unable to connect to the \'" + self.database + "\' server.")
            print("error: ", ibm_db.conn_errormsg())
            exit(-1)

    def merge_dataframe_diff(self, target_df, source_df):

        target_df['DATE_OF_LOADING'] = target_df['DATE_OF_LOADING'].astype('datetime64[ns]')
        source_df['DATE_OF_LOADING'] = source_df['DATE_OF_LOADING'].astype('datetime64[ns]')
        full_df = target_df.append(source_df)

        full_df['ADDRESS'] = full_df['ADDRESS'].str.replace(', Москва', '')
        full_df['ADDRESS'] = full_df['ADDRESS'].str.replace('Москва', '')

        full_df.loc[full_df['REGION'] == 'Москва', 'ADDRESS'] += ', Москва'

        full_df['DATE_OF_LOADING'] = full_df['DATE_OF_LOADING'].astype('datetime64[ns]')
        adr_date_dict = {i[0]: i[1] for i in target_df[['ADDRESS', 'DATE_OF_LOADING_FIRST']].values}

        new_df = (full_df
                  .reset_index(drop=True)
                  .sort_values('DATE_OF_LOADING', ascending=False)
                  #.drop_duplicates(subset=['ADDRESS', 'TYPE_PP'], keep='first'))
                  .drop_duplicates(subset=['ADDRESS', 'TYPE_PP'], keep='first'))

        curr_date = datetime.today().strftime('%Y-%m-%d')

        new_df['DATE_OF_LOADING_FIRST'] = new_df \
            .apply(lambda x: adr_date_dict[x['ADDRESS']] if x['ADDRESS'] in adr_date_dict else curr_date, axis=1)
        new_df.drop(['ID_OFFICE'], axis=1, inplace=True)

        new_df['DATE_OF_LOADING'] = new_df['DATE_OF_LOADING'].astype('datetime64[ns]')
        new_df['DATE_OF_LOADING_FIRST'] = new_df['DATE_OF_LOADING_FIRST'].astype('datetime64[ns]')

        return new_df


if __name__ == '__main__':
    pass
    df_all = pd.read_excel("output/result_Ozon, пункты выдачи.xlsx")
    db_conn = DbAction('config_db.json')
    for region in df_all.REGION.unique():
        if region in ['Санкт-Петербург']:
            continue
        df_new = df_all[df_all.REGION == region].drop_duplicates(subset=['ADDRESS'], keep='first')

        type_of_points = df_new['TYPE_PP'].values[0]
        type_of_company_name = df_new['COMPANY_NAME'].values[0]
        type_of_company_region = df_new['REGION'].values[0]

        df = db_conn.select(
            'SELECT * FROM  DATA_SCIENCE.PARSER_DELIVERY_POINTS WHERE TYPE_PP=\'{0}\' AND COMPANY_NAME=\'{1}\' AND REGION=\'{2}\'' \
                .format(type_of_points, type_of_company_name, type_of_company_region))

        if len(df) == 0:
            df_insert = df_new
        else:
            df_insert = db_conn.merge_dataframe_diff(df, df_new)

        db_conn.delete(
            "DELETE from DATA_SCIENCE.PARSER_DELIVERY_POINTS WHERE TYPE_PP=\'{0}\' AND COMPANY_NAME=\'{1}\' AND REGION=\'{2}\'  ".format(
                type_of_points, type_of_company_name, type_of_company_region))

        db_conn.insert(df_insert, "DATA_SCIENCE",
                       "PARSER_DELIVERY_POINTS")