import subprocess
from properties import java, simian

""" Checks that Simian tool is working correctly """

file_path1 = r"./test/file3.js"
file_path2 = r"./test/file4.js"

# Define the Simian command
# prog_lang could be used for the languages referred to here: https://simian.quandarypeak.com/docs/
cpd_command = f'"{java}" -jar "{simian}" -defaultLanguage=text -threshold=1 {file_path1} {file_path2}'

print(cpd_command + '\n')
# Run the command and capture the output
output = subprocess.run(cpd_command, shell=True, text=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# If simian finished with error
if output.returncode == 2:
   print("Error using Simian")
   

# If no code clones detected, continue
elif output.returncode == 0:
   print("No clones detected")

else:
   result = 'Found' + output.stdout.decode('utf-8').split('Found')[-1]
   print(result)
