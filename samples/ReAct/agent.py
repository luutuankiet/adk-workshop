from google.adk.agents import LlmAgent
from google.adk.tools import google_search


INT_SIMPLE="you are a helpful assistant."

INT_REACT="""You are a helpful agent who 
    Solves tasks in a thought/ action iterative loop.
    You will explicitly share your thought /action.

    example : is 1+1 ? 
    answer : 
        - thought : this is a question on calculation, which i should use math tool.
        - action : call use_calculator
        - observation : the use_calculator returns 2. I can end the loop.
        - 1+1=2

"""

root_agent = LlmAgent(
    name = "gemini_flash",
    description="ReAct demo agent",
    model="gemini-2.0-flash-001",
    tools = [google_search],
    instruction=INT_REACT
    
)



demo_ask = """
what's the population of the country with the highest gdp ?

"""

