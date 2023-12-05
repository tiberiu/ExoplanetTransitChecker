import threading
import time
import sys

from frontend import FrontendThread
from backend import BackendThread

if __name__ == "__main__":
    frontend_thread = FrontendThread()
    backend_thread = BackendThread()

    frontend_thread.set_backend_thread(backend_thread)
    backend_thread.set_frontend_thread(frontend_thread)

    backend_thread.start()
    frontend_thread.start()

    frontend_thread.join()

    sys.exit()
