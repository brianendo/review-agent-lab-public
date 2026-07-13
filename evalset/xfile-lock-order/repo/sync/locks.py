"""Global locks guarding the two shared account maps."""
import threading

accounts_lock = threading.Lock()
audit_lock = threading.Lock()
