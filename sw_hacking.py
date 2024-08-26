# ensure that equations of the solidworks files are exported to .txt

# the way you backdoor into rebuilding solidworks geometry is by using win32 VBA in Python (every SolidWorks command is translated this way, so we use it like an API)
# great article about this: https://mason-landry.hashnode.dev/automating-solidworks-using-python-492b15303db3 

import subprocess as sb
import win32com.client
from time import sleep


def startSW():
    ## Starts Solidworks
    SW_PROCESS_NAME = r'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SLDWORKS.exe'
    sb.Popen(SW_PROCESS_NAME)

def shutSW():
    ## Kills Solidworks
    sb.call('Taskkill /IM SLDWORKS.exe /F')

def connectToSW():
    ## With Solidworks window open, connects to application      
    sw = win32com.client.Dispatch("SLDWORKS.Application")
    return sw

def openFile(sw, Path):
    ## With connection established (sw), opens part, assembly, or drawing file            
    f = sw.getopendocspec(Path)
    model = sw.opendoc7(f)
    return model

def updatePrt(model):
    ## Rebuilds the active part, assembly, or drawing (model)
    model.EditRebuild3
    sleep(20)
    model.save()

def update_solidworks_equations(file_path, updates):
    """
    Update the values of global variables in a SolidWorks equations .txt file.

    Parameters:
    - file_path (str): Path to the .txt file containing SolidWorks equations.
    - updates (dict): A dictionary where keys are the global variable names and values are the new values.
    """
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        # Split line by "=" to separate variable name and value/expression
        if "=" in line:
            var, expr = line.split("=", 1)
            var = var.strip().strip('"')  # Remove extra whitespace and quotes if present

            print(f'Checking variable: "{var}"')  # Debug print
            print(f'Available updates: {updates.keys()}')  # Debug print

            # If the variable is in the updates dictionary, update its value
            if var in updates:
                print(f'Updating {var} to {updates[var]}')  # Debug print
                expr = str(updates[var])
            updated_lines.append(f'"{var}" = {expr.strip()}\n')
        else:
            updated_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(updated_lines)
    
def update_sw(file_path, eq_path, var_dict):
    update_solidworks_equations(eq_path, var_dict)
    startSW()
    sw = connectToSW()
    model = openFile(sw, file_path)
    updatePrt(model)
    shutSW()

if __name__ == "__main__":
    update_sw(r"C:\Users\ericp\OneDrive\Desktop\plate_heatsink.SLDPRT", r"C:\Users\ericp\OneDrive\Desktop\equations.txt", {'plate_width':1, 'n_plates':24})