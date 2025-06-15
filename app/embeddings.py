from langchain_openai import AzureOpenAIEmbeddings
from . import config


def get_embedding_model() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_endpoint=config.AOAI_ENDPOINT,
        api_key=config.AOAI_API_KEY,
        model=config.AOAI_DEPLOY_EMBED_3_LARGE,
        openai_api_version=config.AOAI_API_VERSION,
    )
