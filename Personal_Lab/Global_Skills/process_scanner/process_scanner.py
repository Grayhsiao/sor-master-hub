import psutil
import datetime
import argparse
import sys
import os

def list_procs(output_filename):
    print("列出所有正在執行的程序...")
    try:
        # 確保輸出的目錄存在
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(f"Time: {datetime.datetime.now()}\n")
            f.write("-" * 50 + "\n")
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    line = f"PID: {proc.info['pid']} | Name: {proc.info['name']} | Exe: {proc.info['exe']}\n"
                    f.write(line)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        print(f"已將程序列表儲存至 {os.path.abspath(output_filename)}")
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan and list running processes.")
    parser.add_argument("--output_filename", type=str, default="running_processes.txt", help="Output file path for the process list.")
    args = parser.parse_args()
    
    list_procs(args.output_filename)
