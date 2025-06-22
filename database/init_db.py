import sqlite3

def create_student_table():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            branch TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Table 'students' created successfully.")

def show_data_user():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    
    if rows:
        print("user Data:")
        for row in rows:
            print(f"Name: {row[0]}, Mail ID: {row[1]}, password: {row[2]}")
    else:
        print("No data found in the 'students' table.")
    
    conn.close()

def update_users():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = 'phani'")  # Example ID to delete
    conn.commit()
    # c.execute(f"PRAGMA table_info('users')")
    # headers = [col[1] for col in c.fetchall()]
    # print(headers)
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    
    if rows:
        print("user Data:")
        for row in rows:
            print(f"User Name:    {row[0]}, Mail ID:     {row[1]}, Password:   {row[2]}")
    else:
        print("No data found in the 'students' table.")
    
    conn.close()

def show_data_students():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    rows = c.fetchall()
    
    if rows:
        print("user Data:")
        for row in rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Class: {row[2]}, Branch: {row[3]}")
    else:
        print("No data found in the 'students' table.")
    
    conn.close()

def update_student():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = 'S201025'")  # Example ID to delete
    conn.commit()
    c.execute("SELECT * FROM students")
    rows = c.fetchall()
    
    if rows:
        print("user Data:")
        for row in rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Class: {row[2]}, Branch: {row[3]}")
    else:
        print("No data found in the 'students' table.")
    
    conn.close()


def view_subject_table(class_name='3F', subject='AI'):
    table_name = f"{class_name.upper()}_{subject.upper()}"

    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()

    try:
        c.execute(f"DROP TABLE IF EXISTS '{table_name}'")  # Clear the table
        conn.commit()
        print(f"✅ Cleared data from table '{table_name}'")
        c.execute(f"SELECT * FROM '{table_name}'")
        rows = c.fetchall()

        if rows:
            # Get column headers dynamically
            c.execute(f"PRAGMA table_info('{table_name}')")
            headers = [col[1] for col in c.fetchall()]

            print(f"\n📘 Data in table {table_name}:")
            print(" | ".join(headers))
            print("-" * 60)
            for row in rows:
                print(" | ".join(str(val) for val in row))
        else:
            print(f"No data in table '{table_name}'")

    except sqlite3.OperationalError as e:
        print(f"❌ Error: {e}")

    conn.close()

    
    conn.close()



if __name__ == '__main__':
    # create_student_table()
    update_users()
