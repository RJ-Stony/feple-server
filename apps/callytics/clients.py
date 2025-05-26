"""
apps/callytics/clients.py

이 파일은 Callytics 모델 서버에 오디오 파일과 메타데이터를 전송하고,
반환된 JSON 응답을 파싱하여 다음 단계(태스크)로 전달하기 위한 HTTP 클라이언트 함수를 정의합니다.

<설정 안내>
- settings.py에 다음 값을 추가해주세요.
    CALLYTICS_URL = os.getenv("CALLYTICS_URL")  # 예: http://192.168.0.10:8000/predict

<사용 예시>
  from apps.callytics.clients import call_callytics
  result = call_callytics("/path/to/audio.wav", {"topic_name": "상담"})
"""

import requests
from django.conf import settings


def call_callytics(audio_path: str, metadata: dict) -> dict:
    """
    Callytics API에 오디오 파일과 메타데이터를 전송하여
    분석 결과 JSON을 받아 리턴합니다.

    :param audio_path: 분석할 오디오 파일의 파일 시스템 경로
    :param metadata:   모델에 전달할 메타데이터 딕셔너리
    :return:           API에서 반환한 JSON 결과
    """
    with open(audio_path, "rb") as f:
        files = {"audio": f}
        # metadata는 추후에 구조보고 결정해야할 듯
        data = {"metadata": metadata}
        resp = requests.post(
            settings.CALLYTICS_URL,
            files=files,
            data=data,
            timeout=120
        )
    resp.raise_for_status()
    return resp.json()