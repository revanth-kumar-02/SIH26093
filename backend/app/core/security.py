import uuid

def generate_session_id() -> str:
    """Generate a server-side UUIDv4 for a victim interaction session."""
    return str(uuid.uuid4())

def generate_message_id() -> str:
    """Generate a unique ID for a chat message."""
    return f"msg_{uuid.uuid4().hex[:12]}"
