import re
with open('tests/test_api_and_ocr.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'monkeypatch.setattr(api_main, \"AsyncResult\"' in line:
        new_lines.append('    monkeypatch.setattr(api_main, \"AsyncResult\", lambda task_id, app: FakeResult())\n')
        new_lines.append('    monkeypatch.setattr(api_main, \"redis_client\", FakeRedis())\n\n')
        new_lines.append('    response = api_main.get_task_result(\"task-abc\")\n\n')
        new_lines.append('    assert response.model_dump() == expected_body\n\n')
        skip = True
    elif skip and 'def test_process_image_with_pipeline_handles_prediction_failure' in line:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('tests/test_api_and_ocr.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
