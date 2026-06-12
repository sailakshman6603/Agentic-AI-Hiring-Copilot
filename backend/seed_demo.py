import sys
import os
from uuid import uuid4

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.config.database import SessionLocal, engine
from app.infrastructure.db.models import Base, OrganizationModel, UserModel, ResumeModel, CandidateModel
from app.infrastructure.security.auth import get_password_hash

def seed_demo_data():
    print("Connecting to database...")
    db = SessionLocal()
    
    try:
        # 1. Check if organization exists or create it
        org = db.query(OrganizationModel).filter(OrganizationModel.name == "Demo Corp").first()
        if not org:
            org = OrganizationModel(name="Demo Corp")
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created demo organization: Demo Corp ({org.id})")
        else:
            print(f"Using existing organization: Demo Corp ({org.id})")

        # 2. Define user roles
        users_to_create = [
            {
                "email": "admin@democorp.com",
                "password": "password123",
                "role": "admin"
            },
            {
                "email": "recruiter@democorp.com",
                "password": "password123",
                "role": "recruiter"
            },
            {
                "email": "candidate@democorp.com",
                "password": "password123",
                "role": "candidate"
            }
        ]

        # 3. Create users
        for u_data in users_to_create:
            existing = db.query(UserModel).filter(UserModel.email == u_data["email"]).first()
            if not existing:
                hashed_pwd = get_password_hash(u_data["password"])
                user = UserModel(
                    email=u_data["email"],
                    password_hash=hashed_pwd,
                    role=u_data["role"],
                    organization_id=org.id
                )
                db.add(user)
                db.commit()
                print(f"Created {u_data['role']} account: {u_data['email']}")
            else:
                print(f"{u_data['role'].capitalize()} account already exists: {u_data['email']}")

        # 4. Create a dummy candidate resume for quick matching demo
        candidate_user = db.query(UserModel).filter(UserModel.email == "candidate@democorp.com").first()
        existing_resume = db.query(ResumeModel).filter(ResumeModel.filename == "alex_developer_resume.pdf").first()
        
        if not existing_resume:
            resume = ResumeModel(
                id=uuid4(),
                filename="alex_developer_resume.pdf",
                file_path="./uploads/demo_resume.pdf",
                raw_text="Alex Developer. email: candidate@democorp.com. Skills: Python, FastAPI, Postgres, React. Experience: 3 years building backend applications.",
                parsed_data={
                    "personal_info": {
                        "first_name": "Alex",
                        "last_name": "Developer",
                        "email": "candidate@democorp.com",
                        "phone": "+1-555-0100"
                    },
                    "skills": ["Python", "FastAPI", "Postgres", "React"],
                    "experience": [
                        {
                            "company": "SaaS Ventures",
                            "role": "Software Developer",
                            "duration": "3 years",
                            "description": "Designed APIs using Python and FastAPI. Managed Postgres databases."
                        }
                    ],
                    "education": [
                        {
                            "institution": "State University",
                            "degree": "B.S. Software Engineering",
                            "year": "2020"
                        }
                    ]
                },
                organization_id=org.id
            )
            db.add(resume)
            db.commit()
            
            # Link to candidate table
            candidate = CandidateModel(
                first_name="Alex",
                last_name="Developer",
                email="candidate@democorp.com",
                phone="+1-555-0100",
                resume_id=resume.id,
                organization_id=org.id
            )
            db.add(candidate)
            db.commit()
            print("Seeded sample Candidate CV for Alex Developer successfully.")
            
            # Index resume into Qdrant for semantic search matching
            try:
                from app.infrastructure.search.qdrant_store import qdrant_store
                from app.infrastructure.ai.embedding_service import embedding_service
                
                # Generate embedding
                indexing_text = "Skills: Python, FastAPI, Postgres, React. Experience: Software Developer at SaaS Ventures building APIs."
                resume_vector = embedding_service.get_embedding(indexing_text)
                
                metadata = {
                    "organization_id": str(org.id),
                    "candidate_id": str(candidate.id),
                    "first_name": "Alex",
                    "last_name": "Developer",
                    "email": "candidate@democorp.com",
                    "skills": ["Python", "FastAPI", "Postgres", "React"],
                    "parsed_data": resume.parsed_data
                }
                
                qdrant_store.upsert_resume(
                    resume_id=resume.id,
                    vector=resume_vector,
                    metadata=metadata
                )
                print("Indexed Alex Developer CV in Qdrant Vector database.")
            except Exception as vector_err:
                print(f"Skipping vector index: {vector_err} (running fallback database mode)")
        
        print("\nDemo Seed Completed successfully!")
        print("="*40)
        print("Organization Name: Demo Corp")
        print("1. Admin Login     -> User: admin@democorp.com     / Pass: password123")
        print("2. Recruiter Login -> User: recruiter@democorp.com / Pass: password123")
        print("3. Candidate Login -> User: candidate@democorp.com / Pass: password123")
        print("="*40)

    except Exception as e:
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
