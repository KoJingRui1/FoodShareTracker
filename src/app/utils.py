# app/utils.py
import logging
import shutil
import datetime
import os
import re

try:
    import bcrypt
except ImportError:
    bcrypt = None

def init_logger(log_file="src/data/foodshare.log"):
    """Configures the root logger to write to a file."""
    # Ensure folder exists if log_file is inside a subfolder
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Configure basic logging. Set the level to INFO.
    # Set the format to include a timestamp, level name, and message.
    # Set the output file (handler).
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a' # Append to the log file
    )
    print(f"Logging configured. Outputting to {log_file}")

def backup_data(data_path="src/data/data.json", backup_dir="src/data/backups"):
    """Creates a timestamped backup of the main data file."""
    # Check if the backup directory exists, and create it if it doesn't.
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Create a timestamp string (e.g., YYYY-MM-DD_HH-MM-SS).
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"foodshare_backup_{timestamp}.json"
    backup_filepath = os.path.join(backup_dir, backup_filename)
    
    try:
        # Use shutil.copy() to copy the data_path to the backup_filepath.
        shutil.copy(data_path, backup_filepath)
        # Use the logging module to record this event.
        logging.info(f"Data successfully backed up to {backup_filepath}")
        return True
    except Exception as e:
        # Log any errors that occur during the backup process.
        logging.error(f"Failed to create backup: {e}")
        return False

# Name Validation
def validate_name(name, min_length=2, max_length=50):
    """
    Validates a person's or organization's name.
    
    Rules:
    - Must be a string.
    - Stripped length must be between min_length (default 2) and max_length (default 50).
    - Can only contain alphabetic characters, spaces, hyphens (-), apostrophes ('), and periods (.).
    - Must contain at least one alphabetic letter.
    - Must not contain digits or unexpected special characters.
    
    Returns:
        tuple[bool, str]: (is_valid, reason_message)
    """
    if not isinstance(name, str):
        return False, "Name must be a string."
    
    cleaned = name.strip()
    if not cleaned:
        return False, "Name cannot be empty."
    
    if len(cleaned) < min_length:
        return False, f"Name must be at least {min_length} characters long."
    
    if len(cleaned) > max_length:
        return False, f"Name cannot exceed {max_length} characters."
    
    if not re.match(r"^[a-zA-Z\s'\-\.]+$", cleaned):
        return False, "Name can only contain alphabetic letters, spaces, hyphens, periods, and apostrophes."
    
    if not re.search(r"[a-zA-Z]", cleaned):
        return False, "Name must contain at least one alphabetic character."
    
    return True, "Name is valid."

def valid_name(name, min_length=2, max_length=50):
    """
    Convenience helper function that returns True if name is valid, else False.
    """
    is_valid, _ = validate_name(name, min_length=min_length, max_length=max_length)
    return is_valid

# Password Validation
def validate_password(password, min_length=6, max_length=128, require_digit=True, require_letter=True, require_upper=False):
    """
    Validates user password complexity.
    
    Rules:
    - Must be a string.
    - Length must be between min_length (default 6) and max_length (default 128).
    - Must contain at least one letter (if require_letter is True).
    - Must contain at least one numeric digit (if require_digit is True).
    - Must contain at least one uppercase letter (if require_upper is True).
    
    Returns:
        tuple[bool, str]: (is_valid, reason_message)
    """
    if not isinstance(password, str):
        return False, "Password must be a string."
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    
    if len(password) > max_length:
        return False, f"Password cannot exceed {max_length} characters."
    
    if require_letter and not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    
    if require_digit and not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    
    if require_upper and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    
    return True, "Password is valid."

def valid_password(password, min_length=6, max_length=128, require_digit=True, require_letter=True, require_upper=False):
    """
    Convenience helper function that returns True if password is valid, else False.
    """
    is_valid, _ = validate_password(
        password,
        min_length=min_length,
        max_length=max_length,
        require_digit=require_digit,
        require_letter=require_letter,
        require_upper=require_upper
    )
    return is_valid

# Bcrypt Password Hashing and Hardening
def is_bcrypt_hash(stored_hash):
    """Checks whether a string is a valid bcrypt hash signature."""
    if not isinstance(stored_hash, str):
        return False
    return stored_hash.startswith(("$2a$", "$2b$", "$2y$"))

def hash_password(password):
    """
    Hashes a plain-text password using bcrypt with automatic salt generation.
    Returns the decoded string representation suitable for JSON persistence.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")
    if bcrypt is not None:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        # Fallback to standard library sha256 if bcrypt is unavailable
        import hashlib
        return "$sha256$" + hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password, stored_hash):
    """
    Verifies a plain-text password against a stored bcrypt hash.
    Also supports legacy plain-text passwords for backward compatibility.
    """
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    # 1. Bcrypt hash check
    if is_bcrypt_hash(stored_hash):
        if bcrypt is not None:
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
            except Exception:
                return False
        return False

    # 2. SHA256 fallback check
    if stored_hash.startswith("$sha256$"):
        import hashlib
        expected = "$sha256$" + hashlib.sha256(password.encode("utf-8")).hexdigest()
        return stored_hash == expected

    # 3. Plain text fallback (for legacy accounts)
    return password == stored_hash
