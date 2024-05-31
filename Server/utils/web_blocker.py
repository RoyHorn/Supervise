import platform
import sqlite3
import re
import os

class WebBlocker:
    """
    The `WebBlocker` class provides functionality to manage a hosts file for blocking websites.
    
    The class has the following methods:
    
    - `get_hosts_file_location()`: Returns the location of the hosts file based on the operating system.
    - `get_sites()`: Reads the hosts file and extracts the list of blocked websites.
    - `update_file()`: Updates the hosts file with the current list of blocked websites.
    - `add_website(domain)`: Adds a new website to the block list and updates the hosts file.
    - `remove_website(domain)`: Removes a website from the block list and updates the hosts file.
    - `extract_history(history_db)`: Extracts the browsing history from the Chrome browser's history database.
    - `build_history_string()`: Builds a dictionary of the browsing history.
    """
    
    def __init__(self):
        self.path = self.get_hosts_file_location()
        self.redirect = '127.0.0.1'
        self.blocked_sites = self.get_sites()

    def get_hosts_file_location(self) -> str:
        """
        Returns the location of the hosts file based on the operating system.
        
        This method checks the current operating system and returns the appropriate file path for the hosts file.
        It supports Windows, Linux, and macOS (Darwin) operating systems.
        If the operating system is not supported, it raises an OSError exception.
        
        Returns:
            str: The file path of the hosts file.
        
        Raises:
            OSError: If the operating system is not supported.
        """
        system = platform.system()
        if system == "Windows":
            return r'C:\Windows\System32\drivers\etc\hosts'
        elif system == "Linux" or system == "Darwin":
            return '/etc/hosts'
        else:
            raise OSError("Unsupported operating system")

    def get_sites(self) -> list:
        """
        Gets the list of blocked websites from the hosts file.
        
        This method reads the contents of the hosts file and extracts the URLs of the blocked websites. It returns a list of these URLs.
        
        Returns:
            list: A list of blocked website URLs.
        """
        with open(self.path,'r') as f:
            raw_data = f.read()

            if len(raw_data)>0:
                # Split the raw data into lines
                lines = raw_data.strip().split('\n')

                # Extract URLs from each line
                urls = [line.split()[1] for line in lines]
                print(urls)
                return urls
        
        return []

    def update_file(self):
        """
        Updates the hosts file by writing the blocked websites and their redirect address to the file.
        
        This method iterates through the list of blocked websites stored in `self.blocked_sites` and writes each one to the hosts file, prefixed with the redirect address `self.redirect`.
        This effectively blocks access to the listed websites by redirecting them to the specified address.
        """
        
        f = open(self.path, 'w')
        for domain in self.blocked_sites:
            f.write(f'\n{self.redirect}  {domain}    #added using Supervise.')
        f.close()

    def add_website(self, domain: str):
        """
        Adds a website to the block list and updates the hosts file to reflect the change.
        
        Args:
            domain (str): The domain of the website to be added to the block list.
        
        This method appends the provided domain to the `self.blocked_sites` list, and then calls the `update_file()` method to write the updated block list to the hosts file.
        """
        # Strip the URL from the https:// at the beginning if it exists, and from the / at the end
        stripped_domain = re.search(r'(?<=://)([^/]+)', domain).group(0)
        domain = stripped_domain if stripped_domain is not None else domain

        self.blocked_sites.append(domain)
        self.update_file()

    def remove_website(self, domain: str):
        """
        Removes a website from the block list and updates the hosts file to reflect the change.
        
        Args:
            domain (str): The domain of the website to be removed from the block list.
        
        This method removes the provided domain from the `self.blocked_sites` list, and then calls the `update_file()` method to write the updated block list to the hosts file.
        """

        domain = re.search(r'(?<=://)([^/]+)', domain).group(0)
        
        if domain in self.blocked_sites:
            self.blocked_sites.remove(domain)
            self.update_file()

    def extract_history(self, history_db: str) -> list[tuple]:
        """
        Extracts the browsing history from the Chrome browser's SQLite database and returns a list of tuples containing the URL, title, and last visited date/time for the 20 most recent visits.
        
        This function first closes the Chrome browser to gain access to the database file, then connects to the SQLite database and executes a SQL query to retrieve the desired history data.
        The results are then returned as a list of tuples.
        
        Args:
            history_db (str): The file path to the Chrome browser's SQLite history database.
        
        Returns:
            list of tuples: A list of tuples containing the URL, title, and last visited date/time for the 20 most recent visits.
        """
        # Close chrome in order to access its database
        os.system("taskkill /f /im chrome.exe")

        c = sqlite3.connect(history_db)
        cursor = c.cursor()
        select_statement = """SELECT
                                DISTINCT u.url AS URL, 
                                u.title AS Title, 
                                -- Convert the Unix timestamp to a human-readable date and time format
                                strftime('%m-%d-%Y %H:%M', (u.last_visit_time/1000000.0) - 11644473600, 'unixepoch', 'localtime') AS "Last Visited Date Time"
                            FROM
                                urls u,
                                visits v 
                            WHERE
                                u.id = v.url
                            ORDER BY
                                u.last_visit_time DESC -- Order by last visited time in descending order
                            LIMIT 20;
                            """
        cursor.execute(select_statement)
        results = cursor.fetchall()
        c.close()

        # Open chrome again
        os.system("start \"\" https://www.google.com")
        
        return results
        
    def build_history_string(self) -> dict[str, str]:
        """
        Builds a dictionary of the user's browsing history, where the keys are the last visited date and time concatenated with the page title, and the values are the corresponding URLs.
        
        This method first retrieves the Chrome browser's SQLite history database file path, then calls the `extract_history()` method to extract the 20 most recent browsing history entries. The resulting list of tuples is then used to construct the `browsing_history` dictionary, where the key is a string containing the last visited date and time, and the title, and the value is the corresponding URL.
        
        Returns:
            browsing_histoyry (dict[str, str]): A dictionary of the user's browsing history, where the keys are the last visited date and time concatenated with the page title, and the values are the corresponding URLs.
        """
        # Get the user directory dynamically
        user_dir = os.path.expanduser("~")
        history_db = os.path.join(user_dir, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History')

        # Extract the history data
        history_data = self.extract_history(history_db)

        # Build the browsing history dictionary
        browsing_history = {}
        for url, title, last_visit_time in history_data:
            browsing_history[f"{last_visit_time} - {title}"] = url

        return browsing_history
