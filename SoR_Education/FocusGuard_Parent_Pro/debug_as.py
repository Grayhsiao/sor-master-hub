import subprocess

script = '''
if application "Google Chrome" is running then
    tell application "Google Chrome" to return (title of active tab of front window) & "|||" & (URL of active tab of front window)
else if application "Safari" is running then
    tell application "Safari" to return (name of current tab of front window) & "|||" & (URL of current tab of front window)
else
    return ""
end if
'''

r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
print(f"STDOUT: {r.stdout}")
print(f"STDERR: {r.stderr}")
print(f"RETURNCODE: {r.returncode}")
