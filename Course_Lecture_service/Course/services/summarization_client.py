import requests
from django.conf import settings


def send_for_summarization(lecture_id: str, text: str) -> None:
    """
    Fire-and-forget request to summarization service.
    """
    url = f"{settings.SUMMARIZATION_SERVICE['base_url']}/lecture-text/"
    payload = {
        'lecture_id': str(lecture_id),
        'text': text
    }

    requests.post(
        url,
        json=payload,
        timeout=settings.SUMMARIZATION_SERVICE['timeout']
    )

def is_summary_ready(lecture_id: str) -> bool:
    """
    Ask summarization service if summary is ready.
    """
    url = f"{settings.SUMMARIZATION_SERVICE['base_url']}/summary/status/{lecture_id}/"

    response = requests.get(
        url,
        timeout=settings.SUMMARIZATION_SERVICE['timeout']
    )

    response.raise_for_status()

    data = response.json()
    return data.get('ready', False)

def get_summary(lecture_id: str) -> dict:
    """
    Fetch summary from summarization service.
    """
    url = f"{settings.SUMMARIZATION_SERVICE['base_url']}/summary/{lecture_id}/"

    response = requests.get(
        url,
        timeout=settings.SUMMARIZATION_SERVICE['timeout']
    )

    response.raise_for_status()
    return response.json()

