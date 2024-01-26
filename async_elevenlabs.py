import os
import json
import base64
from typing import Iterator, Literal
import websockets
from websockets.sync.client import connect

OutputFormat = Literal[
    "mp3_44100_64",
    "mp3_44100_96",
    "mp3_44100_128",
    "mp3_44100_192",
    "pcm_16000",
    "pcm_22050",
    "pcm_24000",
    "pcm_44100",
    "ulaw_8000",
]

def generate(
    text: Iterator[str],
    voice_id: str,
    stream: bool = True,
    output_format: OutputFormat = "mp3_44100_128",
    latency: int = 1,
) -> Iterator[bytes]:
    if not stream:
        raise NotImplementedError("Non-streaming mode not implemented in this simplified version.")

    WSS_PATH = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?output_format={output_format}&optimize_streaming_latency={latency}"
    HEADERS = {"xi-api-key": os.environ.get("ELEVEN_API_KEY")}

    BOS = json.dumps({"text": " ", "try_trigger_generation": True})
    EOS = json.dumps({"text": ""})

    with connect(WSS_PATH, additional_headers=HEADERS) as websocket:
        websocket.send(BOS)

        for text_chunk in text:
            data = {"text": text_chunk, "try_trigger_generation": True}
            websocket.send(json.dumps(data))
            try:
                data = json.loads(websocket.recv(1e-4))
                if data.get("audio"):
                    yield base64.b64decode(data["audio"])
            except TimeoutError:
                pass

        websocket.send(EOS)

        while True:
            try:
                data = json.loads(websocket.recv())
                if data.get("audio"):
                    yield base64.b64decode(data["audio"])
            except websockets.exceptions.ConnectionClosed:
                break
