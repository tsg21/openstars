"""Build a GameDirectory from env vars."""

import os

from openstars.game_directory.base import GameDirectory


def build_game_directory() -> GameDirectory:
    """Construct the configured GameDirectory.

    GAME_DIRECTORY_BACKEND: 'firestore' | 'memory'
    Defaults to 'memory' when STORAGE_BACKEND=memory and GAME_DIRECTORY_BACKEND is unset.
    """
    backend = os.environ.get("GAME_DIRECTORY_BACKEND")
    if not backend:
        storage_backend = os.environ.get("STORAGE_BACKEND", "")
        backend = "memory" if storage_backend == "memory" else "firestore"

    if backend == "memory":
        from openstars.game_directory.memory import InMemoryGameDirectory

        return InMemoryGameDirectory()

    if backend == "firestore":
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        if not project_id:
            raise RuntimeError(
                "FIREBASE_PROJECT_ID must be set when GAME_DIRECTORY_BACKEND=firestore"
            )
        import firebase_admin
        from firebase_admin import firestore as admin_firestore

        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={"projectId": project_id})

        from openstars.game_directory.firestore import FirestoreGameDirectory

        return FirestoreGameDirectory(admin_firestore.client())

    raise RuntimeError(f"Unsupported GAME_DIRECTORY_BACKEND: {backend!r}")
