from google.cloud import firestore

# Initialize a single global Firestore client instance to be reused across requests
_db_client = firestore.Client(project="clear-booking-457205-t9", database="(default)")

def get_db() -> firestore.Client:
    """
    Returns the global Firestore client instance.
    """
    return _db_client
