import sqlite3
import pandas as pd
import hashlib
import os
import pkgutil
from io import StringIO



DATA_FOLDER_URL = "data/"
DB_SCHEMA_URL = "db_creation_script.sql"
SQLITE_URL = "courses.sqlite"
CSV_FILES_URL = [
    "sql_course_info.csv",
    "sql_course_registration_info.csv",
    "sql_course_run.csv",
    "sql_courses.csv",
    "sql_instructors.csv",
    "sql_learners.csv",
    "sql_online_xacts.csv",
    "sql_superheroes.csv",
    "sql_xacts.csv",
    ]
SOLUTION_CSV = "project_solutions.csv"


def run(sql_query: str) -> pd.DataFrame:
    """
    Run an SQL query on a database
    """
    # Check if db is set up
    __init()

    # Create your connection.
    cnx = sqlite3.connect(SQLITE_URL)

    # Open the connection and run the query
    dataframe = pd.read_sql_query(sql_query, cnx)

    # Close the connection.
    cnx.commit()
    cnx.close()

    # Return the output as Pandas dataframe
    return dataframe


def check(**key_user_sql_query):
    print("-------------------")
    sql_solutions = pd.read_csv(StringIO(pkgutil.get_data(
            __name__, DATA_FOLDER_URL + SOLUTION_CSV).decode("utf-8")), sep=";", header=None)
    sql_sol_dict = dict(zip(sql_solutions.key, sql_solutions.value))

    for key, user_sql_query in key_user_sql_query.items():
        try: 
            if key in sql_sol_dict:
                sql_sol_df = run(sql_sol_dict[key])
                current_sql_df = run(user_sql_query)
                
                # First check if contains the same columns
                if sorted(sql_sol_df.columns.tolist()) != sorted(current_sql_df.columns.tolist()):
                    print("Your SQL query does NOT match our solution. There is a mismatch in columns.")
                else:
                    # Ensure the columns of both dataframes are in the same order
                    sql_sol_df = sql_sol_df[current_sql_df.columns.tolist()]
                    
                    if sql_sol_df.equals(current_sql_df):
                        print("Your SQL query is correct!")
                    else:
                        print("Your SQL query does NOT match our solution. The number of rows is different.")
            else:
                raise QuestionKeyUnknown
        except QuestionKeyUnknown:
            print("The variable name used for the parameter" +
                  " in the check function does not match" + 
                  " any of our solution keys.")
            

class QuestionKeyUnknown(Exception):
    """
    Raised when the variable name does not match
    any of the keys we've defined for our question-
    solution pairs.
    """
    pass


def __init():
    """
    (Re-)creates the database
    """
    if "SQLITE_DB_HASH" in os.environ:
        if os.path.isfile(SQLITE_URL):
            hash = __calculate_file_hash(SQLITE_URL)

            if hash != os.environ["SQLITE_DB_HASH"]:
                # Delete db
                __delete_db(SQLITE_URL)

                # Recreate db
                __create_db(DATA_FOLDER_URL, DB_SCHEMA_URL,
                            SQLITE_URL, CSV_FILES_URL)
        else:
            # Create db
            __create_db(DATA_FOLDER_URL, DB_SCHEMA_URL,
                        SQLITE_URL, CSV_FILES_URL)
    else:
        # Delete db
        __delete_db(SQLITE_URL)

        # Create db
        __create_db(DATA_FOLDER_URL, DB_SCHEMA_URL, SQLITE_URL, CSV_FILES_URL)

        # Set hash to env variable
        os.environ["SQLITE_DB_HASH"] = __calculate_file_hash(SQLITE_URL)


def __calculate_file_hash(file_url: str) -> str:
    """
    Calculate the hash of given file
    """
    BUF_SIZE = 60000  # read in ~60kb chunks
    blake2b = hashlib.blake2b()

    with open(file_url, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            blake2b.update(data)

    return blake2b.hexdigest()


def __create_db(data_folder: str, db_schema_url: str, sqlite_url: str, csv_files_url: list):
    """
    (Re-)create the database from scratch using SQL and CSV scripts.
    """
    db_schema_string = pkgutil.get_data(
        __name__, data_folder + db_schema_url).decode("utf-8")

    conn = sqlite3.connect(sqlite_url)
    c = conn.cursor()
    c.executescript(db_schema_string)

    conn.commit()

    # Remove "sql_" and ".csv" from csv_files
    table_names = [file.replace("sql_", "").replace(".csv", "")
                   for file in csv_files_url]

    for csv_file, table_name in zip(csv_files_url, table_names):
        df = pd.read_csv(StringIO(pkgutil.get_data(
            __name__, data_folder + csv_file).decode("utf-8")))
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()

    conn.close()


def __delete_db(file_url: str):
    """
    Delete the database
    """
    try:
        os.remove(file_url)
    except FileNotFoundError:
        pass