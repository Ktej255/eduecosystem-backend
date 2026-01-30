from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tests.utils.utils import get_superuser_token_headers
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.models.adaptive_learning import Concept, ConceptDependency, GranularityType, MasteryStatus, StudentMastery

def test_create_concept(client: TestClient, db: Session) -> None:
    # Manual Superuser setup
    from app.tests.utils.utils import random_email
    from app.tests.utils.user import authentication_token_from_email
    from app.models.user import User

    email = random_email()
    # 1. Get token (creates user with password="password")
    superuser_token_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # 2. Upgrade to Superuser
    user = db.query(User).filter(User.email == email).first()
    user.is_superuser = True
    db.add(user)
    db.commit()
    
    data = {"title": "Fractions", "subject": "Math", "difficulty_level": 3}
    response = client.post(
        f"{settings.API_V1_STR}/adaptive-learning/concepts", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200, f"Error: {response.text}"
    content = response.json()
    assert content["title"] == data["title"]
    assert "id" in content

def test_create_dependency(client: TestClient, db: Session) -> None:
    from app.tests.utils.utils import random_email
    from app.tests.utils.user import authentication_token_from_email
    from app.models.user import User
    
    email = random_email()
    # 1. Get token (creates user)
    superuser_token_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # 2. Upgrade
    user = db.query(User).filter(User.email == email).first()
    user.is_superuser = True
    db.add(user)
    db.commit()

    # Create two concepts
    concept1 = Concept(title="Parent", subject="Test")
    concept2 = Concept(title="Child", subject="Test")
    db.add(concept1)
    db.add(concept2)
    db.commit()
    db.refresh(concept1)
    db.refresh(concept2)
    
    data = {
        "parent_id": str(concept1.id),
        "child_id": str(concept2.id),
        "strength": 0.9
    }
    response = client.post(
        f"{settings.API_V1_STR}/adaptive-learning/dependencies", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200, f"Error: {response.text}"
    content = response.json()
    assert content["status"] == "created"

def test_interaction_flow(client: TestClient, db: Session) -> None:
    # Create user and get headers
    # Note: create_random_user uses a random password, but authentication_token_from_email defaults to "password".
    # We must ensure they match. 
    # authentication_token_from_email creates the user if not exists with password="password".
    # create_random_user uses a random string.
    # So we should use authentication_token_from_email directly with a new email to create the user and get token.
    from app.tests.utils.utils import random_email
    email = random_email()
    normal_user_token_headers = authentication_token_from_email(
        client=client, email=email, db=db
    )
    
    # 1. Setup Concept
    concept = Concept(title="BKT Test Concept", subject="Math")
    db.add(concept)
    db.commit()
    db.refresh(concept)
    
    # 2. Log Interaction (Correct, Fast -> High Mastery)
    data = {
        "question_id": "q1",
        "associated_concept_id": str(concept.id),
        "is_correct": True,
        "time_taken_ms": 2000,
        "hesitation_detected": False,
        "backspaces_count": 0
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/adaptive-learning/interaction", headers=normal_user_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert "mastery_probability" in content
    assert content["mastery_probability"] > 0.6
    
    # 3. Log Interaction (Correct, Hesitant -> Lower increase)
    data = {
        "question_id": "q2",
        "associated_concept_id": str(concept.id),
        "is_correct": True,
        "time_taken_ms": 15000,
        "hesitation_detected": True,
        "backspaces_count": 2
    }
    response = client.post(
        f"{settings.API_V1_STR}/adaptive-learning/interaction", headers=normal_user_token_headers, json=data
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["mastery_probability"] > 0.8
    assert content["mastery_status"] == "Green"

def test_content_generation(client: TestClient, db: Session) -> None:
    from app.tests.utils.utils import random_email
    email = random_email()
    # We need a user
    user_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # Setup Concept
    concept = Concept(title="Generation Test", subject="AI")
    db.add(concept)
    db.commit()
    db.refresh(concept)
    
    # 1. Generate Content (Red State - Default)
    # We mock the Gemini Service response to avoid real API calls and cost
    from unittest.mock import patch
    
    mock_response = '''
    {
        "question_text": "What is AI?",
        "options": ["A) Magic", "B) Linear Algebra", "C) Biology", "D) None"],
        "correct_option_index": 1,
        "explanation": "It is basically math."
    }
    '''
    
    with patch("app.services.gemini_service.GeminiService.generate_text", return_value=mock_response) as mock_generate:
        data = {
            "concept_id": str(concept.id),
            "interaction_context": {"hesitation_detected": False, "is_correct": False}
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/adaptive-learning/generate", headers=user_headers, json=data
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        content = response.json()
        assert "question_text" in content
        assert content["strategy_used"] == "remedial_with_hint" # Red + Incorrect -> Remedial

def test_node_locking(client: TestClient, db: Session) -> None:
    from app.tests.utils.utils import random_email
    from app.tests.utils.user import authentication_token_from_email
    from app.models.user import User
    
    email = random_email()
    # 1. Get token
    user_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # 2. Setup Chain: Concept A -> Concept B
    from app.models.adaptive_learning import Concept, ConceptDependency
    
    parent = Concept(title="Parent Lock", subject="Test")
    child = Concept(title="Child Lock", subject="Test")
    db.add(parent)
    db.add(child)
    db.commit()
    db.refresh(parent)
    db.refresh(child)
    
    dep = ConceptDependency(parent_concept_id=parent.id, child_concept_id=child.id)
    db.add(dep)
    db.commit()
    
    # 3. Check Map (Should be Locked initially because Parent mastery is 0 < 0.5 default? 
    # Actually, if no mastery record exists, it defaults to 0.0, so Locked.
    
    response = client.get(
        f"{settings.API_V1_STR}/adaptive-learning/knowledge-map", headers=user_headers
    )
    assert response.status_code == 200
    data = response.json()
    
    nodes = {n["label"]: n for n in data["nodes"]}
    assert nodes["Child Lock"]["is_locked"] == True, "Child should be locked if parent is unvisited (Red)"
    assert nodes["Parent Lock"]["is_locked"] == False, "Root node should be unlocked"
    
    # 4. Master Parent
    # Log interaction to make parent Green
    interaction_data = {
        "associated_concept_id": str(parent.id),
        "is_correct": True,
        "time_taken_ms": 1000,
        "hesitation_detected": False
    }
    # Log multiple times to ensure high probability
    for _ in range(10):
        client.post(
            f"{settings.API_V1_STR}/adaptive-learning/interaction", headers=user_headers, json=interaction_data
        )
        
    # 5. Check Map Again (Should be Unlocked)
    response = client.get(
        f"{settings.API_V1_STR}/adaptive-learning/knowledge-map", headers=user_headers
    )
    data = response.json()
    nodes = {n["label"]: n for n in data["nodes"]}
    
    # Check Parent State (Debug if fails)
    print(f"Parent Mastery: {nodes['Parent Lock']['mastery_probability']}")
    print(f"Child Locked Status: {nodes['Child Lock']['is_locked']}")
    
    assert nodes["Child Lock"]["is_locked"] == False, f"Child should be unlocked after parent is mastered. Parent Mastery: {nodes['Parent Lock']['mastery_probability']}"

def test_interaction_recommendation(client: TestClient, db: Session) -> None:
    from app.tests.utils.utils import random_email
    from app.tests.utils.user import authentication_token_from_email
    from app.models.adaptive_learning import Concept, ConceptDependency
    
    email = random_email()
    user_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # 1. Setup Chain: Weak Parent -> Child
    parent = Concept(title="Weak Parent", subject="Test")
    child = Concept(title="Difficult Child", subject="Test")
    db.add(parent)
    db.add(child)
    db.commit()
    db.refresh(parent)
    db.refresh(child)
    
    dep = ConceptDependency(parent_concept_id=parent.id, child_concept_id=child.id)
    db.add(dep)
    db.commit()
    
    # 2. Fail on Child interaction
    interaction_data = {
        "associated_concept_id": str(child.id),
        "is_correct": False,
        "time_taken_ms": 5000,
        "hesitation_detected": True
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/adaptive-learning/interaction", headers=user_headers, json=interaction_data
    )
    
    assert response.status_code == 200
    content = response.json()
    
    # 3. Check for Recommendation
    assert content["recommendation"] is not None
    assert content["recommendation"]["type"] == "review_prerequisite"
    assert content["recommendation"]["concept_id"] == str(parent.id)

def test_counseling_service(client: TestClient, db: Session) -> None:
    from app.tests.utils.utils import random_email
    from app.tests.utils.user import authentication_token_from_email
    from app.models.adaptive_learning import Concept
    from unittest.mock import patch
    
    email = random_email()
    user_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # 1. Setup Concept
    concept = Concept(title="Counseling Test", subject="Psychology")
    db.add(concept)
    db.commit()
    db.refresh(concept)
    
    # 2. Simulate Frustration (Incorrect + Hesitant)
    for _ in range(2):
        interaction_data = {
            "associated_concept_id": str(concept.id),
            "is_correct": False,
            "time_taken_ms": 15000,
            "hesitation_detected": True
        }
        client.post(
            f"{settings.API_V1_STR}/adaptive-learning/interaction", headers=user_headers, json=interaction_data
        )
        
    # 3. Request Counseling
    # Mock LLM
    with patch("app.services.gemini_service.GeminiService.generate_text", return_value='"Keep going! You can do it."') as mock_generate:
        response = client.post(
            f"{settings.API_V1_STR}/adaptive-learning/counsel", 
            headers=user_headers, 
            json={"concept_id": str(concept.id)}
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        content = response.json()
        
        # 4. Verify Sentiment Analysis
        assert content["detected_emotion"] == "frustration"
        assert content["message"] == "Keep going! You can do it."
        assert content["concept_id"] == str(concept.id)

