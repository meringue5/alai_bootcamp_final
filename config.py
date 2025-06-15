# 환경 변수 및 설정값 정의
import os

AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT")  # Azure OpenAI 엔드포인트
AOAI_API_KEY = os.getenv("AOAI_API_KEY")  # Azure OpenAI API 키
AOAI_DEPLOY_GPT4O = os.getenv("AOAI_DEPLOY_GPT4O")  # GPT-4O 배포 이름
AOAI_DEPLOY_EMBED_3_LARGE = os.getenv("AOAI_DEPLOY_EMBED_3_LARGE")  # 임베딩 모델 배포 이름
AOAI_API_VERSION = os.getenv("AOAI_API_VERSION", "2024-02-01")  # API 버전

VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "vectorstore")  # 벡터스토어 경로
