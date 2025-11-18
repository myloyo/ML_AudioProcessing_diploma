import os
import asyncio
import json
import torch
import numpy as np
import soundfile as sf
from fastapi import FastAPI
from aioboto3 import Session
from kafka import KafkaConsumer, KafkaProducer
from threading import Thread

# ====================================================
# ENVIRONMENT VARIABLES
# ====================================================
KAFKA_BROKERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audio")

TOPIC_PREPARED = "job.prepared"
TOPIC_COMPLETED = "job.completed"
TOPIC_FAILED = "job.failed"

# ====================================================
# FASTAPI app
# ====================================================
app = FastAPI(title="ML Service", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

# ====================================================
# Fake ML model (PyTorch)
# ====================================================
class DummyModel(torch.nn.Module):
    def forward(self, x):
        # Возвращает немного "изменённый" звук
        return x * 0.5

model = DummyModel()

# ====================================================
# MinIO async client
# ====================================================
session = Session()

async def download_from_minio(storage_key: str, local_path: str):
    async with session.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
    ) as s3:
        await s3.download_file(MINIO_BUCKET, storage_key, local_path)

async def upload_to_minio(local_path: str, storage_key: str):
    async with session.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
    ) as s3:
        await s3.upload_file(local_path, MINIO_BUCKET, storage_key)

# ====================================================
# ML task handler
# ====================================================
async def process_job(job: dict, producer: KafkaProducer):
    job_id = job["job_id"]
    input_key = job["input_key"]
    output_key = job["output_key"]

    print(f"[ML] Received job {job_id}")

    try:
        # 1. Download
        input_path = f"/tmp/{job_id}_input.wav"
        output_path = f"/tmp/{job_id}_output.wav"

        print("[ML] Downloading file from MinIO...")
        await download_from_minio(input_key, input_path)

        # 2. Read audio
        audio, sr = sf.read(input_path)
        audio_tensor = torch.tensor(audio, dtype=torch.float32)

        # 3. Run fake model
        print("[ML] Running inference...")
        output_audio = model(audio_tensor).detach().numpy()

        # 4. Save result
        sf.write(output_path, output_audio, sr)

        # 5. Upload to MinIO
        print("[ML] Uploading result...")
        await upload_to_minio(output_path, output_key)

        # 6. Send completed event
        msg = {"job_id": job_id, "status": "completed", "output_key": output_key}
        producer.send(TOPIC_COMPLETED, json.dumps(msg).encode("utf-8"))

        print(f"[ML] Completed job {job_id}")

    except Exception as e:
        print(f"[ML] ERROR: {e}")
        msg = {"job_id": job_id, "status": "failed", "error": str(e)}
        producer.send(TOPIC_FAILED, json.dumps(msg).encode("utf-8"))

# ====================================================
# Kafka listener
# ====================================================
def start_kafka_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    consumer = KafkaConsumer(
        TOPIC_PREPARED,
        bootstrap_servers=KAFKA_BROKERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id="ml_service_group",
        auto_offset_reset="earliest"
    )

    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKERS)

    print("[ML] Kafka listener started...")

    for message in consumer:
        job = message.value
        loop.run_until_complete(process_job(job, producer))

# ====================================================
# Background thread for Kafka
# ====================================================
def start_background_kafka_thread():
    t = Thread(target=start_kafka_listener, daemon=True)
    t.start()

# ====================================================
# Startup event
# ====================================================
@app.on_event("startup")
async def startup_event():
    print("[ML] Starting background Kafka listener...")
    start_background_kafka_thread()
    print("[ML] Ready to process tasks!")

