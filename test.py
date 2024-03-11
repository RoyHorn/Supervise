import os
import sqlite3

def extract_history(history_db):
    c = sqlite3.connect(history_db)
    cursor = c.cursor()
    select_statement = """SELECT 
                        u.url AS URL, 
                        u.title AS Title, 
                        u.visit_count As "Visit Count",
                        strftime('%Y-%m-%d %H:%M:%f', (u.last_visit_time/1000000.0) - 11644473600, 'unixepoch', 'localtime') As "Last Visited Date Time"
                        FROM urls u, visits v 
                        WHERE u.id = v.url;"""
    cursor.execute(select_statement)
    results = cursor.fetchall()
    c.close()
    
    return results

def build_history_string(results, output_file):
    data = extrac

    for url, visit_count in results:
        if url not in visited_urls:
            visited_urls[url] = visit_count
        else:
            visited_urls[url] += visit_count

    with open(output_file, 'a') as file:
        for url, visit_count in visited_urls.items():
            file.write("{0} - {1}\n".format(url, visit_count))

def main():
    # Get the user directory dynamically
    user_dir = os.path.expanduser("~")
    history_db = os.path.join(user_dir, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History')
    output_file = 'history.txt'

    history_data = extract_history(history_db)
    filter_and_write_history(history_data, output_file)

if __name__ == "__main__":
    main()
