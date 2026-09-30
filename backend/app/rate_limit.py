import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class RateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.ip_login_attempts = defaultdict(list)
        self.username_failed_attempts = defaultdict(list)
        self.ip_register_attempts = defaultdict(list)
        self.argon2_concurrent = 0

    def clean_old_entries(self, now):
        # Extremely simple cleanup just for the prototype
        if len(self.ip_login_attempts) > 10000:
            self.ip_login_attempts.clear()
        if len(self.username_failed_attempts) > 10000:
            self.username_failed_attempts.clear()
        if len(self.ip_register_attempts) > 10000:
            self.ip_register_attempts.clear()

    def check_login_rate(self, ip: str, username: str):
        now = time.monotonic()
        with self.lock:
            self.clean_old_entries(now)
            
            # Login allows 10 attempts per minute per client IP
            self.ip_login_attempts[ip] = [t for t in self.ip_login_attempts[ip] if now - t < 60]
            if len(self.ip_login_attempts[ip]) >= 10:
                raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "60"})
            self.ip_login_attempts[ip].append(now)

            # 5 failed attempts per 5 minutes per normalized username
            norm_user = username.strip().lower()
            self.username_failed_attempts[norm_user] = [t for t in self.username_failed_attempts[norm_user] if now - t < 300]
            if len(self.username_failed_attempts[norm_user]) >= 5:
                raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "300"})
                
    def check_register_rate(self, ip: str):
        now = time.monotonic()
        with self.lock:
            self.clean_old_entries(now)
            
            # Registration allows 5 attempts per hour per IP
            self.ip_register_attempts[ip] = [t for t in self.ip_register_attempts[ip] if now - t < 3600]
            if len(self.ip_register_attempts[ip]) >= 5:
                raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "3600"})
            self.ip_register_attempts[ip].append(now)

    def record_failed_login(self, username: str):
        now = time.monotonic()
        norm_user = username.strip().lower()
        with self.lock:
            self.username_failed_attempts[norm_user].append(now)

    def clear_failed_login(self, username: str):
        norm_user = username.strip().lower()
        with self.lock:
            self.username_failed_attempts.pop(norm_user, None)

    def acquire_argon2(self):
        with self.lock:
            if self.argon2_concurrent >= 4:
                raise HTTPException(status_code=429, detail="Server busy", headers={"Retry-After": "5"})
            self.argon2_concurrent += 1

    def release_argon2(self):
        with self.lock:
            self.argon2_concurrent -= 1

limiter = RateLimiter()
