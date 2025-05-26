"""
apps/callytics/tasks.py

이 파일은 Celery를 활용하여 Callytics 호출 → DB 저장까지의 파이프라인을 비동기로 수행하는 태스크를 정의합니다.

<설정 안내>
- config/celery.py에 Celery 앱이 설정되어 있어야 하며, django_celery_results를 INSTALLED_APPS에 추가해주세요.

<마이그레이션 안내>
- File, Utterance, Topic 모델이 정의된 후
  python manage.py makemigrations callytics
  python manage.py migrate

<사용 예시>
  from apps.callytics.tasks import run_callytics_pipeline
  run_callytics_pipeline.delay("/path/to/audio.wav", {"topic_name": "상담"})
"""
from celery import shared_task
from .clients import call_callytics
from .models import Topic, File, Utterance


@shared_task
def run_callytics_pipeline(audio_path: str, metadata: dict) -> int:
    """
    1) Callytics 호출
    2) Topic, File, Utterance 모델에 결과 저장
    3) 생성된 File.id를 반환
    """
    # API 호출
    result = call_callytics(audio_path, metadata)

    # Topic 객체 생성 또는 조회
    topic_name = metadata.get("topic_name") or result.get("topic")
    topic, _ = Topic.objects.get_or_create(name=topic_name)

    # File 레코드 생성
    file_obj = File.objects.create(
        topic       = topic,
        name        = result["name"],
        extension   = result["extension"],
        path        = audio_path,
        rate        = result["rate"],
        bit_depth   = result["bit_depth"],
        channels    = result["channels"],
        duration    = result["duration"],
        min_freq    = result["min_freq"],
        max_freq    = result["max_freq"],
        rms_loud    = result["rms_loud"],
        zero_cross  = result["zero_cross"],
        spec_cent   = result["spec_cent"],
        spec_bw     = result["spec_bw"],
        spec_flat   = result["spec_flat"],
        rolloff     = result["rolloff"],
        chroma_stft = result["chroma_stft"],
        spec_contr  = result["spec_contr"],
        tonnetz     = result["tonnetz"],
        mfcc        = result["mfcc"],
        summary     = result.get("summary", ""),
        conflict    = result["conflict"],
        silence     = result["silence"],
    )

    # Utterance 레코드 생성
    for utt in result.get("utterances", []):
        Utterance.objects.create(
            file       = file_obj,
            speaker    = utt["speaker"],
            sequence   = utt["sequence"],
            start_time = utt["start_time"],
            end_time   = utt["end_time"],
            content    = utt["content"],
            sentiment  = utt["sentiment"],
            profane    = utt["profane"],
        )

    return file_obj.id