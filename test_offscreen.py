import sys
import os
import subprocess

# 设置环境变量用于远程或无GUI环境
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

print("Testing main.py with offscreen mode...")
result = subprocess.run([sys.executable, 'main.py'], capture_output=True, text=True, timeout=10)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)