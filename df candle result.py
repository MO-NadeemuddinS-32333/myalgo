# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 16:53:30 2025

@author: USER
"""

import time
import pandas as pd




# Initialize an empty list to store results
result_list = []

starttime = time.time()
timeout = time.time() + 60 * 60 * 1  # 60 seconds * 60 meaning the script will run for 1 hour

while time.time() <= timeout:
    try:
        print("passthrough at ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        
        # Collect the results from the main function
        result = main()  # Assume `main()` returns a dictionary
        
        # Append the result to the list
        result_list.append(result)
        
        # Sleep for the remaining time to complete 5-minute intervals (300 seconds)
        time.sleep(300 - ((time.time() - starttime) % 300.0))  # 300 second interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        break

# After the loop, convert the result_list (list of dictionaries) into a DataFrame
df = pd.DataFrame(result_list)

# If needed, save the DataFrame to a CSV file
df.to_csv('result_output.csv', index=False)

print(df)
