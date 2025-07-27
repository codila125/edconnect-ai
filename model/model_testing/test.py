import requests

def get_summary(model, prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    }
    res = requests.post(url, json=payload)
    try:
        return res.json()["response"]
    except Exception as e:
        print("Error in API response:", res.text)
        raise e

def make_prompt(text):
    return f"Summarize the following content:\n\n{text}"

# Load input (can be text, table, or OCR result from image)
input_text = (
    "A hackathon, also known as a codefest, is a social coding event that brings computer programmers and other interested people together to improve upon or build a new software program."
    "The word hackathon is a portmanteau of the words hacker, which means clever programmer, and marathon, an event marked by endurance. "
    "The concept of the hackathon, also called a hack day or hack fest, was born out of the open source community. "
    "The first event labeled a hackathon was the OpenBSD Hackathon in Calgary, Canada, on June 4, 1999."
)

prompt = make_prompt(input_text)

summary_gemma = get_summary("gemma3:12b", prompt)
summary_qwen = get_summary("qwen2.5vl:7b", prompt)

print("Gemma Summary:\n", summary_gemma)
print("\nQwen Summary:\n", summary_qwen)

from bert_score import score

# Human-written reference summary
reference_summary = "A hackathon is a collaborative coding event where programmers and others build or improve software, originating from the open source community, with the first event held in 1999 in Canada."

# Ensure the number of references matches the number of candidates
candidates = [summary_gemma, summary_qwen]
reference = [reference_summary] * len(candidates)

P, R, F1 = score(candidates, reference, lang="en", verbose=True)

print("\n--- BERTScore Evaluation ---")
print(f"Gemma F1: {F1[0].item():.4f}")
print(f"Qwen F1: {F1[1].item():.4f}")

"""AVERAGE F1 BERTScore Evaluation,
Gemma : 0.92694 
Qwen : 0.93272
This suggests that Qwen's summary captures the essence of the input text more effectively than Gemma
"""

