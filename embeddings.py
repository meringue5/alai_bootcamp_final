# 임베딩 모델 관련 함수 정의
from langchain_openai import AzureOpenAIEmbeddings
import config

# Azure OpenAI 임베딩 모델을 반환합니다.
def get_embedding_model() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_endpoint=config.AOAI_ENDPOINT,
        api_key=config.AOAI_API_KEY,
        model=config.AOAI_DEPLOY_EMBED_3_LARGE,
        openai_api_version=config.AOAI_API_VERSION,
    )
