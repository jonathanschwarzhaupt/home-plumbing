from pydantic import Field, AliasChoices, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider


class PydanticAIConfig(BaseSettings):
    """Class for configuring pydantic ai"""

    api_key: str = Field(
        description="The API key to use with anthropic models",
        validation_alias=AliasChoices("api_key", "anthropic_api_key"),
    )

    model_config = SettingsConfigDict(env_file="pydanticai.env")


def get_comdirect_transaction_categorization_agent(
    config: PydanticAIConfig,
    output_type: BaseModel,
    instructions: str = """
        You are a very knowledgeable personal finance assistant.
        Your speciality lies in: 
        * determening the category of a financial transactions
        * providing a concise description of a financial transaction better than the original
        given the details of the transactions.
    """,
) -> Agent:
    """Constructs a financial transaction agent based on PydanticAIConfig"""

    model = AnthropicModel(
        "claude-3-5-sonnet-latest", provider=AnthropicProvider(config.api_key)
    )

    return Agent(model=model, instructions=instructions, output_type=output_type)
