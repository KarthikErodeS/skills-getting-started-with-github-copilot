"""
Tests for the Mergington High School Activities API

This module contains comprehensive tests for the FastAPI application including:
- Unit tests for validation logic
- Integration tests for all API endpoints
- Tests using the AAA (Arrange-Act-Assert) pattern with pytest fixtures
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient instance for making requests to the app.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture that resets the activities database to known initial state before
    and after each test to ensure test isolation.
    """
    # Initial state with sample data
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for interschool tournaments",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["lucas@mergington.edu", "ava@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and sculpture techniques",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater performances and acting workshops",
            "schedule": "Mondays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["noah@mergington.edu", "mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and critical thinking skills",
            "schedule": "Tuesdays and Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 14,
            "participants": ["alexander@mergington.edu"]
        },
        "STEM Research Lab": {
            "description": "Explore science and engineering through hands-on experiments",
            "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
            "participants": ["grace@mergington.edu", "benjamin@mergington.edu"]
        }
    }
    
    # Clear and reset activities to initial state
    activities.clear()
    activities.update(initial_activities)
    
    yield
    
    # Cleanup after test: reset to initial state
    activities.clear()
    activities.update(initial_activities)


# ============================================================================
# UNIT TESTS - Testing validation logic in isolation
# ============================================================================

class TestValidationLogic:
    """Unit tests for the validation logic used by endpoints."""
    
    def test_activity_not_found_for_nonexistent_activity(self, client, reset_activities):
        """
        Arrange: Request signup for activity that doesn't exist
        Act: Make POST request to signup endpoint
        Assert: Returns 404 status code with "Activity not found" message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_duplicate_signup_validation(self, client, reset_activities):
        """
        Arrange: Student already signed up for Chess Club
        Act: Attempt to sign up same student again
        Assert: Returns 400 status with "Student already signed up" message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_activity_full_validation(self, client, reset_activities):
        """
        Arrange: Fill an activity to max capacity
        Act: Attempt to sign up another student
        Assert: Returns 400 status with "Activity is full" message
        """
        # Arrange - Fill STEM Research Lab to capacity (max=12, current=2)
        activity_name = "STEM Research Lab"
        
        # Add 10 more participants to reach capacity (2 already there)
        for i in range(10):
            activities[activity_name]["participants"].append(f"student{i}@mergington.edu")
        
        new_email = "extra.student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]
    
    def test_remove_student_not_enrolled(self, client, reset_activities):
        """
        Arrange: Attempt to remove student not signed up for activity
        Act: Make DELETE request for student not in participants list
        Assert: Returns 400 status with "Student not signed up for this activity"
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"  # Not in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_remove_from_nonexistent_activity(self, client, reset_activities):
        """
        Arrange: Attempt to remove student from activity that doesn't exist
        Act: Make DELETE request for nonexistent activity
        Assert: Returns 404 status with "Activity not found" message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


# ============================================================================
# INTEGRATION TESTS - Testing endpoints end-to-end
# ============================================================================

class TestGetActivitiesEndpoint:
    """Integration tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Request all activities
        Act: Make GET request to /activities
        Assert: Response contains all 9 activities with correct structure
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify all 9 activities are returned
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "STEM Research Lab" in data
    
    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        """
        Arrange: Request activities
        Act: Make GET request to /activities
        Assert: Each activity has required fields (description, schedule, max_participants, participants)
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_contains_participants(self, client, reset_activities):
        """
        Arrange: Request activities (Chess Club has 2 initial participants)
        Act: Make GET request to /activities
        Assert: Participants list is populated correctly
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Integration tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_new_student_success(self, client, reset_activities):
        """
        Arrange: New student not yet signed up for Programming Class
        Act: Make POST request to signup endpoint
        Assert: Student is added successfully (200 status, message returned)
        """
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in activities[activity_name]["participants"]
    
    def test_signup_multiple_students_success(self, client, reset_activities):
        """
        Arrange: Multiple new students signing up for same activity
        Act: Make multiple POST requests for different students
        Assert: All students are added successfully
        """
        # Arrange
        activity_name = "Art Studio"
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act & Assert - Sign up each student
        for email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
            assert email in activities[activity_name]["participants"]
        
        # Verify all students are in the activity
        assert len(activities[activity_name]["participants"]) == 4  # 1 initial + 3 new
    
    def test_signup_response_message_format(self, client, reset_activities):
        """
        Arrange: New student signing up for Basketball Team
        Act: Make POST request to signup endpoint
        Assert: Response contains formatted message with student email and activity name
        """
        # Arrange
        activity_name = "Basketball Team"
        email = "newplayer@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        message = response.json()["message"]
        assert email in message
        assert activity_name in message


class TestRemoveEndpoint:
    """Integration tests for DELETE /activities/{activity_name}/remove endpoint."""
    
    def test_remove_student_success(self, client, reset_activities):
        """
        Arrange: Student currently signed up for Chess Club
        Act: Make DELETE request to remove endpoint
        Assert: Student is removed successfully (200 status)
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]
    
    def test_remove_updates_participant_list(self, client, reset_activities):
        """
        Arrange: Tennis Club has 2 participants
        Act: Remove one participant
        Assert: Participant count decreases and specific user is gone
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "lucas@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email not in activities[activity_name]["participants"]
    
    def test_remove_multiple_students(self, client, reset_activities):
        """
        Arrange: Activity with multiple participants
        Act: Remove multiple participants sequentially
        Assert: Each removal succeeds and participant count decreases correctly
        """
        # Arrange
        activity_name = "Drama Club"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act - Remove both students
        response1 = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": "noah@mergington.edu"}
        )
        response2 = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": "mia@mergington.edu"}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count - 2
    
    def test_remove_response_message_format(self, client, reset_activities):
        """
        Arrange: Student signed up for Debate Team
        Act: Make DELETE request to remove endpoint
        Assert: Response contains formatted message with student email and activity name
        """
        # Arrange
        activity_name = "Debate Team"
        email = "alexander@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        message = response.json()["message"]
        assert email in message
        assert activity_name in message


# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================

class TestEndToEndWorkflows:
    """Integration tests for complete user workflows."""
    
    def test_signup_then_remove_workflow(self, client, reset_activities):
        """
        Arrange: Student wants to sign up then change mind
        Act: Sign up for activity, then remove
        Assert: Both operations succeed and student is removed
        """
        # Arrange
        activity_name = "Gym Class"
        email = "athlete@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Signup succeeded
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert - Remove succeeded
        assert remove_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
    
    def test_cannot_signup_after_already_signed_up(self, client, reset_activities):
        """
        Arrange: Student signs up for activity
        Act: Attempt to sign up for same activity again
        Assert: First signup succeeds, second fails with duplicate error
        """
        # Arrange
        activity_name = "Programming Class"
        email = "duplicate@mergington.edu"
        
        # Act - First signup (should succeed)
        first_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Second signup (should fail)
        second_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 400
        assert "already signed up" in second_response.json()["detail"]
