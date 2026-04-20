import requests
import time
import threading
import os

class RemoteControl:
    def __init__(self, firebase_url=None, classroom_code=None):
        # 優先讀取傳入參數，否則讀取環境變數
        self.firebase_url = (firebase_url or os.getenv("FIREBASE_URL", "")).rstrip('/')
        self.classroom_code = classroom_code or os.getenv("CLASSROOM_CODE", "")
        if not self.firebase_url or not self.classroom_code:
            raise ValueError("Firebase URL and Classroom Code must be provided either as arguments or environment variables.")
        self.status = "UNLOCKED"
        self.is_active = False
        self._thread = None
        self.callback = None
        self.event_callback = None
        self.students_callback = None
        self.session = requests.Session()
        self.last_event_timestamp = 0

    def start(self, callback, event_callback=None, students_callback=None, start_message="Remote Control Started"):
        """ Start polling the firebase status """
        self.callback = callback
        self.event_callback = event_callback
        self.students_callback = students_callback
        self.is_active = True
        print(start_message)
        self._thread = threading.Thread(target=self._poll_status)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self.is_active = False
        if hasattr(self, 'session'):
            self.session.close()

    def _poll_status(self):
        url = f"{self.firebase_url}/classrooms/{self.classroom_code}.json"
        while self.is_active:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        if 'status' in data:
                            new_status = data['status']
                            if new_status != self.status:
                                self.status = new_status
                                if self.callback:
                                    self.callback(self.status)
                        
                        if 'last_event' in data:
                            event = data['last_event']
                            timestamp = event.get('timestamp', 0)
                            if timestamp > self.last_event_timestamp:
                                self.last_event_timestamp = timestamp
                                if self.event_callback:
                                    self.event_callback(
                                        event.get('type'), 
                                        event.get('payload'),
                                        event.get('target', 'ALL'),
                                        event.get('targetDisplay', '全班')
                                    )
                        
                        if 'students' in data:
                            if self.students_callback:
                                self.students_callback(data['students'])
                elif response.status_code == 404:
                    print(f"Classroom {self.classroom_code} not found.")
            except Exception as e:
                print(f"Remote poll error: {e}")
            
            time.sleep(5) # Poll every 5 seconds

if __name__ == "__main__":
    # Test
    def my_callback(status):
        print(f"Status changed to: {status}")

    # Example instantiation requiring FIREBASE_URL and CLASSROOM_CODE to be set
    # RC = RemoteControl()
    # RC.start(my_callback, start_message="FocusGuard Service Started!")
    
    # Alternatively pass directly for test:
    # RC = RemoteControl("https://focusguard-demo.firebaseio.com", "TEST101")
    # RC.start(my_callback)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    # RC.stop()
