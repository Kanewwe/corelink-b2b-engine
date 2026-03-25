import pytest
import auth as auth_module
from models import Session as SessionModel

def test_create_session(db_session, mock_user):
    """Test creating a session for a user."""
    session = auth_module.create_session(db_session, mock_user, ip_address="127.0.0.1")
    assert session.user_id == mock_user.id
    assert session.ip_address == "127.0.0.1"
    assert session.id is not None
    
    # Verify DB state
    db_session.refresh(mock_user)
    assert mock_user.last_login_at is not None

def test_get_session(db_session, mock_user):
    """Test retrieving a valid session."""
    session = auth_module.create_session(db_session, mock_user)
    
    retrieved = auth_module.get_session(db_session, session.id)
    assert retrieved is not None
    assert retrieved.id == session.id

def test_get_session_expired(db_session, mock_user, mocker):
    """Test that expired sessions are not returned."""
    session = auth_module.create_session(db_session, mock_user)
    
    # Mock is_expired to return True
    mocker.patch.object(SessionModel, 'is_expired', return_value=True)
    
    retrieved = auth_module.get_session(db_session, session.id)
    assert retrieved is None

def test_delete_session(db_session, mock_user):
    """Test deleting a session."""
    session = auth_module.create_session(db_session, mock_user)
    
    success = auth_module.delete_session(db_session, session.id)
    assert success is True
    
    retrieved = auth_module.get_session(db_session, session.id)
    assert retrieved is None
