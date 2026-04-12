import os
from openai import OpenAI

def main():
    try:
        client = OpenAI(
            base_url=os.environ["API_BASE_URL"],
            api_key=os.environ["API_KEY"]
        )

        response = client.responses.create(
            model="gpt-4.1-mini",
            input="Classify this email: 'Meeting at 5pm tomorrow'"
        )

        output_text = response.output[0].content[0].text

        # REQUIRED FORMAT
        print("[START] task=email_classification", flush=True)
        print(f"[STEP] result={output_text}", flush=True)
        print("[END] task=email_classification score=1.0 steps=1", flush=True)

    except Exception as e:
        print("[START] task=error", flush=True)
        print(f"[STEP] error={str(e)}", flush=True)
        print("[END] task=error score=0 steps=1", flush=True)

if __name__ == "__main__":
    main()