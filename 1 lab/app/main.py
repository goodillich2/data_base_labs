import os
import sys
import time
import psycopg2
import pandas as pd
import csv


# Database connection details
db_name = 'DB_lab_1'
db_user = 'postgres'
db_pass = '2509'
db_host = 'localhost'
db_port = '5432'


def detect_encoding(filename):
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252']  # list of encodings to try
    for encoding in encodings:
        try:
            with open(filename, encoding=encoding) as f:
                csv_reader = csv.reader(f)
                next(csv_reader)  # skip header row
                return encoding
        except UnicodeDecodeError:
            continue
    # if none of the encodings work, raise an exception
    raise ValueError(f"Could not detect encoding of file '{filename}'")

def lowercase_columns(df):
    # Convert all columns to lowercase using the str.lower() method
    df.columns = df.columns.str.lower()

    # Return the DataFrame with lowercase column names
    return df

def drop_table(table_name):
    cur = conn.cursor()
    drop_table_query = f"DROP TABLE IF EXISTS {table_name}" 
    cur.execute(drop_table_query)  
    conn.commit()

def connect_bd():
    print('Try connect with DB')
    for _ in range(20):
        try:
            connect = psycopg2.connect(database=db_name, user=db_user, password=db_pass, host=db_host, port=db_port)
            print('Connect successful\n')
            return connect
        except:
            print('DB is unavailable, please wait a moment')
            time.sleep(5)

    print('The database is currently unavailable, please try again later')
    sys.exit()  # якщо база даних дуже довго не відповідає



def change_type_df(df):
    df = df.astype(str)
    df = lowercase_columns(df)
    df['birth'] = df['birth'].astype(int)
    
    
    for col in df.columns:
        if 'ball' in col or 'scale' in col:
            try:
                df[col] = df[col].str.replace(',', '.').astype(float)
            except KeyError:
                pass      
    return df


def create_table(table_name, file_names):
    """Create table if not exists"""

    cur = conn.cursor()
    
    dfs = []
    for file_name in file_names:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files_folder_path = os.path.join(current_dir, '..', 'files')
        file_path = files_folder_path + '/' + file_name
        encoding_F = detect_encoding(file_path)
        df = pd.read_csv(file_path, delimiter=';', encoding=encoding_F, nrows=1)
        df.columns = df.columns.str.lower() # convert column names to lowercase
        dfs.append(df)


    df = pd.concat(dfs, axis=1)
    df = df.loc[:, ~df.columns.duplicated()]

 
    print(df.head(10))
    df = change_type_df(df)

    column_types = []

    column_types.append("year INTEGER")    
    for column in df.columns:
        column_type = df[column].dtype
        if column_type == 'int64':
            column_types.append(f"{column} INTEGER")
        elif column_type == 'float64':
            column_types.append(f"{column} FLOAT")
        else:
            column_types.append(f"{column} TEXT")
        
    columns = ", ".join(column_types)
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
    cur.execute(create_table_query)
    conn.commit()



def add_unique_constraint(table_name, unique_col_name):
    """Add unique constraint to table"""
    cur = conn.cursor()
    cur.execute(f"ALTER TABLE {table_name} ADD CONSTRAINT unique_constraint UNIQUE ({unique_col_name})")
    conn.commit()


def insert(col_names, rows):
    global conn
    global cursor

    try:
        cursor.executemany("INSERT INTO zno ({}) VALUES ({}) ON CONFLICT DO NOTHING".format(
                ', '.join(col_names), ', '.join(['%s']*len(col_names))), rows)
        conn.commit()
        return
    except:
        print('DB is unavailable, please wait a moment')
        time.sleep(5)

        conn = connect_bd()
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO zno ({}) VALUES ({}) ON CONFLICT DO NOTHING".format(
                ', '.join(col_names), ', '.join(['%s']*len(col_names))), rows)
        conn.commit()

def insert_data(filename, year, encoding_F):
    """Insert data from CSV file into table"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_folder_path = os.path.join(current_dir, '..', 'files')
    filename = files_folder_path + '/' + filename
    # encoding_F = detect_encoding(filename)
    print(encoding_F)
    i = 0 #
    col_names = None
    batch_size = 200
    try:
        for chunk in pd.read_csv(filename, delimiter=';', encoding=encoding_F, chunksize=batch_size):

            chunk = change_type_df(chunk)
            
            # Add the "year" parameter to the chunk dataframe
            chunk['year'] = year
            chunk['year'] = chunk['year'].astype(int)


            if col_names is None:
                col_names = chunk.columns.tolist()


            # Get the data types of all columns
            dtypes = chunk.dtypes
             
            # Replace NaN with NULL
            for col in chunk.columns:
                if dtypes[col] == object: 
                    chunk[col] = chunk[col].replace({'nan': None}, inplace=False)   
                else:   
                    chunk[col] = chunk[col].replace({pd.np.nan: None}, inplace=False)   


            rows = [tuple(row) for row in chunk.values]
            insert(col_names, rows)
            
            
            i = i + batch_size #
            print(str(i) + " rows inserted")
            if i >= 1000:
                break
           

    except Exception as e:
        print(f"Error: {str(e)}")
  


    

while True:
    try:
        # Connect to database
        print("conected conection to db")
        conn = connect_bd()
        print("conected to db\n")

        # Create table and add unique constraint
      
        
        drop_table('zno')
        print("table zno dropped\n")

        
        file_names = ['Odata2020File.csv', 'Odata2021File.csv']

        create_table('zno', file_names)
        print("created table zno\n")
        
        add_unique_constraint('zno', 'OUTID')
        print("created unique constraint\n")

        # Insert data from CSV files
       
        insert_data('Odata2020File.csv', 2020, 'Windows-1251')
        insert_data('Odata2021File.csv', 2021, 'utf8')
        print("all data inserted\n")


        # Close database connection
        conn.close()

        # Exit loop if successful
        break

    except psycopg2.OperationalError as err:
        # Connection lost, retry in 5 seconds
        print(err)
        print("Connection lost. Retrying in 5 seconds...")
        time.sleep(5)


print("All good!")




