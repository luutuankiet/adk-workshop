from google.adk.agents import LlmAgent


def get_weather(city: str, current_time: str) -> dict:
    """function to retrieve weather info of a city.

    Args:
        city (str): the name of city to search

    Returns:
        a dictionary containing 2 keys : result and the weather.

    """
    if not current_time: 
        raise Exception
    # wrangle input
    city = city.lower()

    # simluate call api  / do some web fetch to get the weather.
    ####### ...... do something
    # done simulate

    return {
        "result": 'pass',
        "value": '33 degrees celcius and sunny day.'
    }


root_agent = LlmAgent(
    name = "quickstart_agent",
    instruction = "you are a helpful agent",
    model = "gemini-2.0-flash-lite-001",
    tools = [get_weather]
)


