from __future__ import annotations

import json

from blogger_agent.gemini import _extract_inline_images, _extract_json


def test_extract_json_from_gemini_text_response() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "title": "Teaching draft",
                                    "labels": ["virology"],
                                    "html": "<h2>Teaching draft</h2>",
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }

    assert _extract_json(payload)["title"] == "Teaching draft"


def test_extract_inline_images_from_gemini_response() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "aGVsbG8=",
                            }
                        }
                    ]
                }
            }
        ]
    }

    assert _extract_inline_images(payload) == [("image/png", "aGVsbG8=")]
