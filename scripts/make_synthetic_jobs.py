import sys
import os
import csv
import json
import random
import logging
import argparse
from pathlib import Path
from typing import List, Dict

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.config import settings, BASE_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("make_synthetic_jobs")

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
OUTPUT_CSV = RAW_DATA_DIR / "jobs.csv"

ROLE_DOMAINS = [
    {
        "category": "Backend Engineering",
        "titles": [
            "Python Backend Engineer", "Senior FastAPI Developer", "Django Software Engineer",
            "Golang Microservices Engineer", "Java Spring Boot Developer", "Node.js Backend Developer",
            "Staff API Platform Engineer", "Junior Backend Developer"
        ],
        "tech_pool": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "REST APIs", "gRPC", "Kafka", "AWS"]
    },
    {
        "category": "Frontend Engineering",
        "titles": [
            "React Frontend Developer", "Senior TypeScript Engineer", "Vue.js Web Developer",
            "Next.js Full Stack Frontend Engineer", "UI/UX Software Engineer", "Junior Frontend Developer",
            "Lead Web Application Architect"
        ],
        "tech_pool": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Next.js", "Redux", "GraphQL", "Vite"]
    },
    {
        "category": "Full Stack Engineering",
        "titles": [
            "Full Stack Python/React Developer", "Senior Full Stack Engineer", "MERN Stack Developer",
            "Software Engineer - Full Stack", "Lead Full Stack Developer"
        ],
        "tech_pool": ["Python", "JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "MongoDB", "Docker", "Tailwind CSS"]
    },
    {
        "category": "Data Engineering",
        "titles": [
            "Data Engineer", "Senior Big Data Engineer", "Analytics Engineer",
            "ETL Pipeline Developer", "Lead Cloud Data Engineer"
        ],
        "tech_pool": ["Python", "SQL", "Apache Spark", "Airflow", "BigQuery", "Snowflake", "dbt", "Kafka", "PostgreSQL", "AWS"]
    },
    {
        "category": "Data Science & Machine Learning",
        "titles": [
            "Machine Learning Engineer", "Senior AI Engineer", "Data Scientist",
            "NLP Research Engineer", "Computer Vision Engineer", "MLOps Engineer"
        ],
        "tech_pool": ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "Hugging Face", "MLflow", "Vector Databases", "Pandas", "NumPy", "Docker"]
    },
    {
        "category": "DevOps & Cloud Infrastructure",
        "titles": [
            "DevOps Engineer", "Site Reliability Engineer (SRE)", "Cloud Infrastructure Engineer",
            "Platform Engineer", "Senior Kubernetes Administrator"
        ],
        "tech_pool": ["Kubernetes", "Docker", "Terraform", "AWS", "GCP", "CI/CD", "GitHub Actions", "Prometheus", "Grafana", "Linux", "Bash"]
    },
    {
        "category": "QA & Test Automation",
        "titles": [
            "QA Automation Engineer", "Senior Software Development Engineer in Test (SDET)",
            "Quality Assurance Analyst", "Test Automation Lead"
        ],
        "tech_pool": ["Python", "Pytest", "Selenium", "Cypress", "Playwright", "Postman", "CI/CD", "Jira", "API Testing"]
    },
    {
        "category": "Product & Technical Management",
        "titles": [
            "Technical Product Manager", "Product Manager - AI Platform", "Associate Product Manager",
            "Engineering Manager", "Scrum Master & Agile Coach"
        ],
        "tech_pool": ["Agile", "Scrum", "Jira", "SQL", "Product Strategy", "User Stories", "Roadmap Planning", "Data Analytics"]
    }
]

LOCATIONS = [
    "Remote", "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA",
    "Boston, MA", "Chicago, IL", "Denver, CO", "London, UK", "Toronto, Canada",
    "Bangalore, India", "Berlin, Germany"
]

EXPERIENCE_LEVELS = ["Entry Level", "Mid-Level", "Senior", "Lead", "Staff"]

COMPANIES = [
    "NovaTech Systems", "Apex Data Labs", "CloudVanguard", "ByteWave Digital",
    "Synthetix AI", "Nexus Global Health", "Beacon Financial Tech", "Horizon Platforms",
    "Quantum Insights", "Velocity Robotics", "BluePeak Analytics", "Pulse Interactive",
    "Terraform Networks", "Crestline Media", "Aegis CyberSec", "Kinetix Commerce",
    "Starlight Mobile", "Prism Cloud", "Vertex Software", "HyperScale Computing",
    "Argon Stream", "Solstice Health", "Northstar FinTech", "OmniLogic",
    "Datacraft Labs", "Skyline AI", "Ironclad Systems", "Elevate Tech",
    "Vanguard Logistics", "CipherSecure", "InfiniCloud", "NextGen Mobility",
    "Cobalt Media", "AeroTech Innovations", "Triton Systems", "Luminary Data",
    "Catalyst Payments", "Aura Intelligence", "Strata Cloud", "Centric Software"
]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=15))
def generate_job_batch_with_llm(client: genai.Client, domain: Dict, count: int) -> List[Dict]:
    """Uses Gemini to generate realistic, cohesive job descriptions for a domain."""
    prompt = f"""Generate exactly {count} distinct and realistic synthetic job postings for the '{domain['category']}' category.
Return the output strictly as a JSON list of objects with the following keys for each job:
- "title": Job title (choose from or similar to: {', '.join(domain['titles'])})
- "company": A realistic tech company name
- "location": Location or Remote
- "experience_level": One of: Entry Level, Mid-Level, Senior, Lead
- "skills": Comma-separated key technical skills (include some of: {', '.join(domain['tech_pool'])})
- "description": A thorough 3-4 paragraph job description explaining the role, core responsibilities, key qualifications, and tech stack.

Make each job posting realistic and detailed.
"""
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        )
    )
    data = json.loads(response.text)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "jobs" in data:
        return data["jobs"]
    return []

def generate_procedural_fallback(domain: Dict, count: int) -> List[Dict]:
    """Generates realistic structured jobs locally without API calls if needed."""
    jobs = []
    for _ in range(count):
        title = random.choice(domain["titles"])
        company = random.choice(COMPANIES)
        location = random.choice(LOCATIONS)
        exp = random.choice(EXPERIENCE_LEVELS)
        sampled_skills = random.sample(domain["tech_pool"], min(len(domain["tech_pool"]), random.randint(4, 7)))
        skills_str = ", ".join(sampled_skills)
        
        desc = (
            f"About the Role:\n"
            f"{company} is looking for a passionate {title} to join our growing team. "
            f"In this role, you will design, build, and maintain scalable systems and collaborate closely with cross-functional partners.\n\n"
            f"Key Responsibilities:\n"
            f"- Architect and develop robust solutions using {skills_str}.\n"
            f"- Collaborate with product managers, designers, and fellow engineers to deliver high-impact features.\n"
            f"- Write clean, maintainable, and well-tested code with comprehensive unit and integration tests.\n"
            f"- Participate in code reviews, technical design discussions, and system architecture evaluations.\n\n"
            f"Requirements:\n"
            f"- Demonstrated hands-on experience in {sampled_skills[0]} and {sampled_skills[1]}.\n"
            f"- Strong understanding of software engineering fundamentals, design patterns, and database design.\n"
            f"- Experience with version control (Git), CI/CD pipelines, and agile software development methodologies.\n"
            f"- Excellent problem-solving skills and effective written and verbal communication."
        )
        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "experience_level": exp,
            "skills": skills_str,
            "description": desc
        })
    return jobs

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic job postings dataset.")
    parser.add_argument("--count", type=int, default=500, help="Target number of jobs to generate (default: 500)")
    parser.add_argument("--use-llm", action="store_true", help="Use Gemini LLM to enrich descriptions (requires GEMINI_API_KEY)")
    args = parser.parse_args()

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_count = args.count
    logger.info(f"Targeting {target_count} synthetic jobs...")

    jobs: List[Dict] = []
    per_domain = target_count // len(ROLE_DOMAINS) + 1

    client = None
    if args.use_llm and settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("Using Gemini to generate rich synthetic job postings...")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini client: {e}. Falling back to procedural generation.")

    for domain in ROLE_DOMAINS:
        logger.info(f"Generating jobs for {domain['category']}...")
        domain_jobs = []
        if client:
            try:
                # Generate in batches of 15-20 to avoid token limits
                batch_size = 15
                needed = per_domain
                while needed > 0:
                    current_batch = min(needed, batch_size)
                    batch_res = generate_job_batch_with_llm(client, domain, current_batch)
                    domain_jobs.extend(batch_res)
                    needed -= len(batch_res)
            except Exception as e:
                logger.warning(f"LLM generation failed for {domain['category']}: {e}. Using procedural fallback.")
                domain_jobs.extend(generate_procedural_fallback(domain, per_domain - len(domain_jobs)))
        else:
            domain_jobs = generate_procedural_fallback(domain, per_domain)

        jobs.extend(domain_jobs)

    # Trim to exact target count
    jobs = jobs[:target_count]

    # Save to CSV
    fieldnames = ["title", "company", "location", "experience_level", "skills", "description"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for j in jobs:
            writer.writerow({
                "title": j.get("title", "").strip(),
                "company": j.get("company", "").strip(),
                "location": j.get("location", "").strip(),
                "experience_level": j.get("experience_level", "").strip(),
                "skills": j.get("skills", "").strip(),
                "description": j.get("description", "").strip()
            })

    logger.info(f"SUCCESS: Generated {len(jobs)} synthetic job postings saved to {OUTPUT_CSV}")
    logger.info("NOTE: This dataset is synthetically generated for demonstration and evaluation.")

if __name__ == "__main__":
    main()
