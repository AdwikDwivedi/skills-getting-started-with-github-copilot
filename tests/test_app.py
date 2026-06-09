import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestGetActivities:
    """Test GET /activities endpoint"""
    
    def test_get_activities_returns_list(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_activities_has_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_duplicate_participant_fails(self):
        """Test that duplicate signup returns 400 error"""
        # Sign up first time
        client.post("/activities/Chess%20Club/signup?email=duplicate@mergington.edu")
        
        # Try to sign up again
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_updates_participants_list(self):
        """Test that signup adds participant to the list"""
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Programming Class"]["participants"])
        
        # Sign up new participant
        client.post(
            "/activities/Programming%20Class/signup?email=newcomer@mergington.edu"
        )
        
        # Check updated participant count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Programming Class"]["participants"])
        assert new_count == initial_count + 1


class TestUnregisterFromActivity:
    """Test DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        # First sign up
        client.post(
            "/activities/Art%20Club/signup?email=unregister_test@mergington.edu"
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Art%20Club/unregister?email=unregister_test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_non_registered_participant_fails(self):
        """Test that unregistering non-registered participant returns 400"""
        response = client.delete(
            "/activities/Basketball%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_removes_participant(self):
        """Test that unregister removes participant from list"""
        # Sign up
        client.post(
            "/activities/Debate%20Club/signup?email=remove_test@mergington.edu"
        )
        
        # Get participants before unregister
        response1 = client.get("/activities")
        participants_before = response1.json()["Debate Club"]["participants"]
        assert "remove_test@mergington.edu" in participants_before
        
        # Unregister
        client.delete(
            "/activities/Debate%20Club/unregister?email=remove_test@mergington.edu"
        )
        
        # Check participants after unregister
        response2 = client.get("/activities")
        participants_after = response2.json()["Debate Club"]["participants"]
        assert "remove_test@mergington.edu" not in participants_after


class TestIntegration:
    """Integration tests for signup and unregister flow"""
    
    def test_full_signup_and_unregister_flow(self):
        """Test complete signup and unregister workflow"""
        email = "integration_test@mergington.edu"
        activity = "Science%20Club"
        
        # Check initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Science Club"]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response2 = client.get("/activities")
        after_signup_count = len(response2.json()["Science Club"]["participants"])
        assert after_signup_count == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        response3 = client.get("/activities")
        final_count = len(response3.json()["Science Club"]["participants"])
        assert final_count == initial_count
