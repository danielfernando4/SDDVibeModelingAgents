def extract_added_lines(old_content: str, new_content: str) -> str:
    old_lines = set(old_content.splitlines())
    new_lines = new_content.splitlines()
    added = [line for line in new_lines if line.strip() and line not in old_lines]
    result = "\n".join(added)
    if len(result) > 3000:
        result = result[:3000] + "\n... (diff truncado)"
    return result
