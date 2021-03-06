from string import find
import subprocess

ORACLE_TABLES_FILTER = """ | grep -v '^$' | grep -v 'rows selected' | grep -v '"""+'\-'*30+"""' | grep -v 'TABLE_NAME' """
ORACLE_TABLES_QUERY= """{0} 2> /dev/null <<< "select table_name from user_tables;" """ + ORACLE_TABLES_FILTER
ORACLE_COLUMNS_FILTER = """ | grep -v '^$' | grep -v 'rows selected' | grep -v '"""+'\-'*30+"""' | grep -v 'COLUMN_NAME' """
ORACLE_COLUMNS_QUERY= """{0} 2> /dev/null <<< "select column_name from user_tab_columns where table_name = '{1}';" """ + ORACLE_COLUMNS_FILTER 

PSQL_TABLES_QUERY= """{0} -c "select tablename from pg_tables where schemaname = 'public'" 2> /dev/null """
PSQL_COLUMNS_QUERY= """{0} -c "select column_name from information_schema.columns where table_name = {1}" 2> /dev/null """
MYSQL_TABLES_QUERY= """{0} -e 'SHOW tables;' 2> /dev/null """
MYSQL_COLUMNS_QUERY= """{0} -e 'SHOW COLUMNS FROM {1}' 2> /dev/null """


def get_table_names(suggest_db):
    get_tables_query, _ = get_db_specific_query_statements(suggest_db)
    query_string = get_tables_query.format(suggest_db)
    tables = check_command_output(query_string)
    db_type = get_db_type(suggest_db)
    if db_type == "mysql":
        return [{"word": table} for table in tables.rstrip().split("\n")[1:]]
    elif db_type == "psql":
        return [{"word": table.strip()} for table in tables.rstrip().split("\n")[2:-1]]
    elif db_type == "oracle":
        return [{"word": table} for table in tables.rstrip().split("\n")[7:-2]]


def get_column_names(suggest_db, word_to_complete):
    if word_to_complete.endswith("."):
        return create_column_name_list(suggest_db, [{"word": word_to_complete[:-1]}], ".")
    else:
        return create_column_name_list(suggest_db, get_table_names(suggest_db))

def get_db_specific_query_statements(suggest_db):
    queries = {
        "oracle_tables": ORACLE_TABLES_QUERY,
        "oracle_columns": ORACLE_COLUMNS_QUERY,
        "psql_tables": PSQL_TABLES_QUERY,
        "psql_columns": PSQL_COLUMNS_QUERY,
        "mysql_tables": MYSQL_TABLES_QUERY,
        "mysql_columns": MYSQL_COLUMNS_QUERY
    }
    db_type = get_db_type(suggest_db)
    return (queries[db_type + "_tables"], queries[db_type + "_columns"])

def get_db_type(suggest_db):
    db_type = suggest_db.split(" ")[0]
    if find(db_type,"sqlplus") != 0:
        return db_type
    else:
        return "oracle"

def check_command_output(query_string):
    #return subprocess.check_output(query_string, shell=True)
    try:
        ret = subprocess.check_output(query_string, shell=True, executable="/bin/bash")
    except subprocess.CalledProcessError, e:
        print("subprocess error:\n", e.output)
        ret = None

    return ret

def create_column_name_list(suggest_db, tables, prefix=""):
    table_cols = []
    db_type = get_db_type(suggest_db)
    for table in tables:
        table = table["word"]
        query_string = get_db_specific_query_statements(suggest_db)[1].format(suggest_db, table)
        columns = check_command_output(query_string)
        if db_type == "mysql":
            table_cols.extend([{"word": prefix + column.split("\t")[0], "menu": table, "dup": 1} for column in columns.rstrip().split("\n")[1:]])
        elif db_type == "psql":
            table_cols.extend([{"word": prefix + column.strip(), "menu": table, "dup": 1} for column in columns.rstrip().split("\n")[2:-1]])
        elif db_type == "oracle":
            table_cols.extend([{"word": prefix + column.strip(), "menu": table, "dup": 1} for column in columns.rstrip().split("\n")[7:-2]])
    return table_cols

if __name__ == "__main__":
    print(get_table_names('sqlplus64 "gjzspt/12345678@192.168.21.249/gjzs"'))
    print(get_column_names('sqlplus64 "gjzspt/12345678@192.168.21.249/gjzs"','T_DGAP_RESOURCE.'))
    print(get_column_names('sqlplus64 "gjzspt/12345678@192.168.21.249/gjzs"','QRTZ_LOCKS.'))
