"""
OpenAI-powered helpdesk assistant.

Uses OPENAI_API_KEY from environment/settings. Never hardcode keys.
Supports any user language (Khmer, Chinese, etc.) by instructing the model
to reply in the same language as the user.
"""
import logging
from typing import List, Dict, Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful IT HelpDesk AI assistant for an internal support system.

Your role:
- Help users write clear tickets, set priorities, attach evidence, and troubleshoot IT issues
- Explain network, software, hardware, login, email, security, and account topics simply
- Give practical, step-by-step guidance

Language rules (very important):
- Detect the language of the user's message automatically
- ALWAYS reply in the SAME language the user used
- Support Khmer (ភាសាខ្មែរ), Chinese (中文), English, Thai, Vietnamese, French, Japanese, Korean, and any other language
- If the user mixes languages, prefer the primary language of their latest message
- Do not force English unless the user writes in English

Style:
- Be concise, friendly, and accurate
- Use markdown (headings, lists, bold) when it helps readability
- For urgent outages or security incidents, tell the user to contact IT support directly
- If you are unsure, say so and suggest how to escalate to a human agent
"""


def is_openai_configured() -> bool:
    return bool(getattr(settings, 'OPENAI_API_KEY', '') or '')


def build_chat_messages(history: List[Dict[str, str]], user_message: str) -> List[Dict[str, str]]:
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for item in history:
        role = item.get('role')
        content = (item.get('content') or '').strip()
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': user_message})
    return messages


def call_openai(
    history: List[Dict[str, str]],
    user_message: str,
    timeout: int = 60,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Call OpenAI Chat Completions API.

    Returns (assistant_text, error_message).
    On success error_message is None; on failure assistant_text is None.
    """
    api_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
    if not api_key:
        return None, (
            'OpenAI API key is not configured. '
            'Set the OPENAI_API_KEY environment variable on the server and redeploy.'
        )

    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini') or 'gpt-4o-mini'
    base = (getattr(settings, 'OPENAI_API_BASE', '') or 'https://api.openai.com/v1').rstrip('/')
    url = f'{base}/chat/completions'

    payload = {
        'model': model,
        'messages': build_chat_messages(history, user_message),
        'temperature': 0.6,
        'max_tokens': 1500,
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.Timeout:
        logger.exception('OpenAI request timed out')
        return None, 'The AI request timed out. Please try again.'
    except requests.RequestException as exc:
        logger.exception('OpenAI request failed: %s', exc)
        return None, 'Could not reach the AI service. Please try again later.'

    if response.status_code == 401:
        return None, (
            'OpenAI rejected the API key (unauthorized). '
            'Check OPENAI_API_KEY on Render and regenerate the key if needed.'
        )
    if response.status_code == 429:
        return None, 'AI rate limit reached. Please wait a moment and try again.'
    if response.status_code >= 400:
        try:
            detail = response.json()
            msg = detail.get('error', {}).get('message') or response.text[:300]
        except Exception:
            msg = response.text[:300]
        logger.error('OpenAI error %s: %s', response.status_code, msg)
        return None, f'AI service error ({response.status_code}): {msg}'

    try:
        data = response.json()
        content = data['choices'][0]['message']['content']
        return (content or '').strip(), None
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.exception('Unexpected OpenAI response shape: %s', exc)
        return None, 'Received an unexpected response from the AI service.'
