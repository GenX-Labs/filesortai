import ollama

# ---------------------------------------------------------------------------
# Model configuration
# Using gemma4:e4b for everything (images and text).
# ---------------------------------------------------------------------------
MODEL = "gemma4:e4b"


def _build_messages(file_data: dict, prompt: str) -> list:
    """Build the messages list for ollama.chat based on file type."""
    if file_data["type"] == "image":
        return [{
            "role": "user",
            "content": prompt,
            "images": [file_data["content"]]
        }]
    else:
        # Put the document content FIRST, and the prompt/instructions LAST.
        full_prompt = f"File content:\n{file_data['content']}\n\n---\n{prompt}"
        return [{"role": "user", "content": full_prompt}]


def _parse_result(response: dict, folders: list[str]) -> str:
    """Extract and fuzzy-match the model's answer against known folders."""
    result = response["message"]["content"].strip()

    # Print the raw output to your terminal so you can see if the model is hallucinating
    print(f"\n[DEBUG] Model output: {result}")

    # Clean up — model sometimes adds quotes or punctuation
    result = result.strip('"\'\.,\n')

    for folder in folders:
        if result.lower() in folder.lower() or folder.lower() in result.lower():
            return folder

    return "unsorted"


def classify(file_data: dict, filename: str, folders: list[str]) -> str:
    folder_list = "\n".join(f"- {f}" for f in folders)
    prompt = f"""You are a file organizer.
Choose the SINGLE best folder from the list for this file.
Reply with ONLY the folder name, nothing else.
If none fit, reply: unsorted

Filename: {filename}

Available folders:
{folder_list}
"""

    messages = _build_messages(file_data, prompt)

    try:
        response = ollama.chat(model=MODEL, messages=messages)
        print(f"[classifier] Used model: {MODEL}")
        return _parse_result(response, folders)

    except Exception as err:
        print(f"[classifier] Model '{MODEL}' failed: {err}")
        return "unsorted"
