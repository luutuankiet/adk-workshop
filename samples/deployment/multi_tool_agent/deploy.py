from vertexai import agent_engines
from multi_tool_agent.agent import root_agent

remote_app = agent_engines.create(
    agent_engine=root_agent,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "dotenv>=0.9.9",
        "email-validator>=2.2.0",
        "google-adk",
        "google-apps-chat",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "google-cloud",
        "google-cloud-aiplatform[adk,agent-engines]>=1.93.0",
        "google-cloud-firestore",
        "langchain-google-vertexai>=2.0.23",
        "vertexai",
    ],
)


import vertexai

PROJECT_ID = "joon-sandbox"
LOCATION = "asia-southeast1"
STAGING_BUCKET = "gs://your-google-cloud-storage-bucket"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)
