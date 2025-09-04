import os, time, base64, requests, sys

GEN_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
OP_URL  = "https://operation.api.cloud.yandex.net/operations/{}"

# Берём значения из переменных окружения
IAM_TOKEN = os.environ.get("IAM_TOKEN", "")
FOLDER_ID = os.environ.get("FOLDER_ID", "")

PROMPT = ("Фотореалистичный жёлтый электросамокат на мокрой городской улице во время дождя, "
          "крупный план; мягкое боке огней на фоне, капли дождя в воздухе и на корпусе, "
          "влажные отражения на асфальте, контрастная палитра, 4k.")

def start(prompt):
    if not IAM_TOKEN or not FOLDER_ID:
        raise RuntimeError("Нет IAM_TOKEN или FOLDER_ID в окружении")
    r = requests.post(
        GEN_URL,
        headers={
            "Authorization": f"Bearer {IAM_TOKEN}",
            "x-folder-id": FOLDER_ID,
            "Content-Type": "application/json"
        },
        json={
            "modelUri": f"art://{FOLDER_ID}/yandex-art/latest",
            "messages": [{"text": prompt}],
            "generationOptions": {"mimeType": "image/png"}
        },
        timeout=60
    )
    r.raise_for_status()
    return r.json()["id"]

def poll(op_id, timeout=240):
    t0 = time.time()
    hdr = {"Authorization": f"Bearer {IAM_TOKEN}"}
    while time.time() - t0 < timeout:
        rr = requests.get(OP_URL.format(op_id), headers=hdr, timeout=30)
        rr.raise_for_status()
        data = rr.json()
        if data.get("done"):
            if "error" in data:
                raise RuntimeError(data["error"].get("message", str(data["error"])))
            return data["response"]["image"]
        time.sleep(2)
    raise TimeoutError("Истекло время ожидания")

def main():
    print("Запускаю генерацию…")
    op_id = start(PROMPT)
    img_b64 = poll(op_id)
    with open("result.png", "wb") as f:
        f.write(base64.b64decode(img_b64))
    print("Готово: result.png")

if __name__ == "__main__":
    main()
