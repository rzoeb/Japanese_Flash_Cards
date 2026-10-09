"""Offline tests for the Gemini 3.x update (no network, no real keys). Run from the repo root: python -m pytest -q"""
import base64, datetime as dt, io, json, logging, os, sys, time, types as pytypes
from pathlib import Path

import httpx
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["PYTHON_DOTENV_DISABLED"] = "1"  # app.py calls load_dotenv(override=True); never read a local .env in tests
for k in ("IS_LOCAL_DEV", "GOOGLE_GEMINI_API_KEY", "LLMWHISPERER_API_KEY", "LLMWHISPERER_BASE_URL_V2", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
    os.environ.pop(k, None)

import app  # noqa: E402
from google.genai import errors, types  # noqa: E402

LOG = logging.getLogger("test"); LOG.addHandler(logging.NullHandler()); LOG.propagate = False
CFG = app.load_model_config()


# ---------- fakes ----------
class FakeFiles:
    def __init__(self): self.calls = []
    def upload(self, **kw): self.calls.append(("upload", kw)); raise AssertionError("Files API must not be used")
    def list(self, **kw): self.calls.append(("list", kw)); raise AssertionError("Files API must not be used")
    def delete(self, **kw): self.calls.append(("delete", kw)); raise AssertionError("Files API must not be used")

class FakeModels:
    def __init__(self, responder): self.responder, self.calls = responder, []
    def generate_content(self, **kw): self.calls.append(kw); return self.responder(kw)

def fake_client(responder):
    c = pytypes.SimpleNamespace(); c.files = FakeFiles(); c.models = FakeModels(responder); return c

def ok_response(payload: dict, prompt=1000, cand=50, thoughts=200):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=json.dumps(payload, ensure_ascii=False))]),
                                    finish_reason=types.FinishReason.STOP)],
        usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=prompt, candidates_token_count=cand,
                                                                  thoughts_token_count=thoughts, total_token_count=prompt + cand + thoughts))

def jpeg_part():
    buf = io.BytesIO(); Image.new("RGB", (32, 32), "white").save(buf, "JPEG")
    return {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}


# ---------- registry ----------
def test_registry_default_and_no_dead_models():
    g = CFG["pricing"]["google"]
    assert g["default_model"] == "gemini-3.8-flash" and g["default_model"] in g["models"]
    for dead in ("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.5-flash-8b-latest"):
        assert dead not in g["models"]
    for mid, info in g["models"].items():
        assert info.get("family") in ("gemini-3", "gemini-2.5"), mid
        assert "input" in info or "input_less_than_200k_prompt" in info, mid
    assert "gemini-2.0-flash" not in (ROOT / "app.py").read_text(encoding="utf-8")

def test_price_schedule_switches_on_2027_01_01():
    info = app.get_google_model_info(CFG, "gemini-3.8-flash")
    assert app.resolve_model_pricing(info, dt.date(2026, 12, 31))["input"] == 0.75
    p = app.resolve_model_pricing(info, dt.date(2027, 1, 1)); assert (p["input"], p["output"]) == (1.5, 7.5)


# ---------- generation config ----------
def test_gemini3_config_has_no_temperature_and_sets_thinking_level():
    c = app.build_generation_config("gemini-3.8-flash", CFG, app.SuitabilityResponse, "sys", "suitability")
    assert c.temperature is None and c.response_schema is None
    assert c.response_mime_type == "application/json" and c.response_json_schema["type"] == "object"
    assert c.thinking_config.thinking_level == types.ThinkingLevel.MEDIUM  # medium (the 3.8 Flash default) for both calls
    assert c.automatic_function_calling.disable is True  # no tools, so no SDK function-calling loop
    c2 = app.build_generation_config("gemini-3.8-flash", CFG, app.FlashcardResponse, "sys", "flashcards")
    assert c2.thinking_config.thinking_level == types.ThinkingLevel.MEDIUM

def test_no_minimal_thinking_where_unsupported():
    models = CFG["pricing"]["google"]["models"]
    for mid in ("gemini-3.8-flash", "gemini-3.1-pro-preview"):  # 'minimal' errors on 3.8 Flash and is unsupported on 3.1 Pro (docs)
        assert "minimal" not in models[mid]["thinking_levels"].values(), mid

def test_gemini25_keeps_temperature_and_no_thinking_level():
    c = app.build_generation_config("gemini-2.5-flash-lite", CFG, app.SuitabilityResponse, "sys", "suitability")
    assert c.temperature == 0.1 and c.thinking_config is None


# ---------- preview / legacy models ----------
def test_preview_and_legacy_models_are_labelled_with_access_notes():
    for mid, info in CFG["pricing"]["google"]["models"].items():
        if "preview" in mid:
            assert "preview" in info["label"].lower() and "paid" in info["access_note"].lower(), mid
        if info["family"] == "gemini-2.5":
            assert "legacy" in info["label"].lower() and info.get("access_note"), mid
        assert info.get("access_note", "").isascii(), mid

def test_pro_preview_uses_200k_tiers_and_pricing_ignores_metadata():
    p = app.resolve_model_pricing(app.get_google_model_info(CFG, "gemini-3.1-pro-preview"))
    assert (p["input_less_than_200k_prompt"], p["output_less_than_200k_prompt"]) == (2.0, 12.0)
    assert all(isinstance(v, (int, float)) for v in p.values())  # no label / access_note / thinking_levels leaking in

def test_4xx_on_legacy_model_adds_access_hint():
    def boom(kw): raise errors.ClientError(403, {"error": {"code": 403, "message": "denied", "status": "PERMISSION_DENIED"}})
    r = app.call_google_llm_structured_output_text(fake_client(boom), "gemini-2.5-pro", "sys", ["p"], app.SuitabilityResponse, LOG, CFG)
    assert r["error"].startswith("Gemini API error 403") and "Legacy model" in r["error"]


# ---------- call function ----------
def test_inline_images_no_files_api_and_cost_includes_thoughts():
    client = fake_client(lambda kw: ok_response({"is_suitable": "Yes", "reason": "ok"}, prompt=1_000_000, cand=100_000, thoughts=100_000))
    r = app.call_google_llm_structured_output_text(client, "gemini-3.8-flash", "sys", [jpeg_part(), "prompt"],
                                                   app.SuitabilityResponse, LOG, CFG, call_kind="suitability")
    assert r["error"] is None and r["data"]["is_suitable"] == "Yes"
    assert client.files.calls == []
    part0 = client.models.calls[0]["contents"][0]
    assert isinstance(part0, types.Part) and part0.inline_data.mime_type == "image/jpeg"
    assert r["output_tokens"] == 200_000  # candidates + thoughts
    expected = 1.0 * app.resolve_model_pricing(app.get_google_model_info(CFG, "gemini-3.8-flash"))["input"] + \
               0.2 * app.resolve_model_pricing(app.get_google_model_info(CFG, "gemini-3.8-flash"))["output"]
    assert abs(r["cost"] - expected) < 1e-9

def test_blocked_prompt_reports_reason():
    blocked = types.GenerateContentResponse(candidates=[], prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason="SAFETY"))
    r = app.call_google_llm_structured_output_text(fake_client(lambda kw: blocked), "gemini-3.8-flash", "sys", ["p"],
                                                   app.SuitabilityResponse, LOG, CFG, call_kind="suitability")
    assert "SAFETY" in r["error"] and "has no attribute 'get'" not in r["error"]

def test_api_error_is_reported_not_raised():
    def boom(kw): raise errors.ClientError(404, {"error": {"code": 404, "message": "model not found", "status": "NOT_FOUND"}})
    r = app.call_google_llm_structured_output_text(fake_client(boom), "gemini-x", "sys", ["p"], app.SuitabilityResponse, LOG, CFG)
    assert r["error"].startswith("Gemini API error 404 NOT_FOUND")

def test_schema_violation_is_an_error():
    r = app.call_google_llm_structured_output_text(fake_client(lambda kw: ok_response({"wrong": 1})), "gemini-3.8-flash", "sys", ["p"],
                                                   app.SuitabilityResponse, LOG, CFG)
    assert r["error"] and r["data"] is None


# ---------- SDK-level retry (real google-genai client, mocked HTTP) ----------
def test_client_retries_429_then_succeeds():
    built = app.build_genai_client("FAKE_KEY")
    ho = built._api_client._http_options
    assert ho.timeout == 180_000 and ho.retry_options.attempts == 4
    assert {429, 503} <= set(ho.retry_options.http_status_codes)
    calls = []
    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, json={"error": {"code": 429, "message": "RESOURCE_EXHAUSTED", "status": "RESOURCE_EXHAUSTED"}})
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": "{\"is_suitable\":\"Yes\",\"reason\":\"ok\"}"}]}, "finishReason": "STOP"}]})
    fast = ho.retry_options.model_copy(update={"initial_delay": 0.01, "max_delay": 0.02})
    from google import genai
    client = genai.Client(api_key="FAKE_KEY", http_options=types.HttpOptions(retry_options=fast, httpx_client=httpx.Client(transport=httpx.MockTransport(handler))))
    r = app.call_google_llm_structured_output_text(client, "gemini-3.8-flash", "sys", ["p"], app.SuitabilityResponse, LOG, CFG, call_kind="suitability")
    assert len(calls) == 2 and r["error"] is None


# ---------- image preprocessing ----------
def test_preprocess_outputs_small_jpeg_and_flattens_alpha():
    big = Image.new("RGBA", (4000, 6000), (255, 0, 0, 128))
    out = app.preprocess_image(big, ["google"], LOG, CFG["image_requirements"])
    assert out["media_type"] == "image/jpeg"
    im = Image.open(io.BytesIO(base64.b64decode(out["data"])))
    assert im.format == "JPEG" and max(im.size) <= 3072 and len(base64.b64decode(out["data"])) < 4 * 1024 * 1024


# ---------- upload hardening ----------
@pytest.mark.filterwarnings("error::PIL.Image.DecompressionBombWarning")  # as app.py sets at import; pytest resets filters per test
def test_bomb_png_rejected_quickly_before_decode():
    buf = io.BytesIO(); Image.new("1", (13000, 13000)).save(buf, "PNG"); buf.seek(0)  # 169 MP; mode "1" keeps the test's own memory ~21 MB
    t0 = time.perf_counter()
    with pytest.raises(ValueError, match="MP"):
        app.open_uploaded_image(buf)
    assert time.perf_counter() - t0 < 1.0

def test_only_jpeg_and_png_accepted():
    buf = io.BytesIO(); Image.new("RGB", (16, 16)).save(buf, "GIF"); buf.seek(0)
    with pytest.raises(ValueError, match="Only JPEG and PNG"):
        app.open_uploaded_image(buf)

def test_pixel_limits_admit_phone_jpegs_but_not_big_pngs():
    app.check_image_limits("JPEG", 8064, 6048)        # 48 MP phone photo: allowed
    app.check_image_limits("JPEG", 12000, 9000)       # 108 MP: allowed (decoded at reduced scale)
    with pytest.raises(ValueError): app.check_image_limits("PNG", 8064, 6048)
    with pytest.raises(ValueError): app.check_image_limits("JPEG", 16320, 12240)  # 200 MP

def test_oversize_file_rejected():
    big = io.BytesIO(b"\xff\xd8" + b"\0" * (app.MAX_UPLOAD_MB * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="limit is"):
        app.open_uploaded_image(big)

def test_too_many_files_rejected():
    with pytest.raises(ValueError, match="at most"):
        app.generate_japanese_flashcards(uploaded_images=[io.BytesIO()] * (app.MAX_FILES_PER_RUN + 1))


# ---------- cards table ----------
@pytest.mark.parametrize("response", [
    app.FlashcardResponse(flashcards=[app.FlashcardEntry(kanji='迷う [道に～]', furigana="まよう", english_translation_and_notes='lose one\'s way, "get lost"\nline 2')]),
    app.KanjiFlashcardResponse(flashcards=[app.KanjiFlashcardEntry(kanji="学", readings="ガク | まな-ぶ", english_translation_and_notes="study, learning", example_words_and_sentences='学校 (がっこう), "school"')]),
    app.GrammarFlashcardResponse(flashcards=[app.GrammarFlashcardEntry(grammar_point="～ながら", english_explanation_and_notes='although, "while"', example_sentences="A。| B。")]),
])
def test_csv_to_table_rows_round_trip(response):
    rows = app.flashcards_csv_to_rows(app.convert_flashcard_response_to_csv(response))
    assert rows == [list(card.model_dump().values()) for card in response.flashcards]


# ---------- code hygiene ----------
def test_llm_prompts_compiles_without_warnings_and_prompt_unchanged():
    import warnings, LLM_Prompts
    src = (ROOT / "LLM_Prompts.py").read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(src, "LLM_Prompts.py", "exec")
    assert '""while \\~ing""' in LLM_Prompts.flashcard_answer_grammar_example_1  # runtime string keeps the backslash

def test_no_star_import_and_no_bare_except():
    import ast
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    assert not any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names) for n in ast.walk(tree))
    assert not any(isinstance(n, ast.ExceptHandler) and n.type is None for n in ast.walk(tree))


# ---------- photo metadata ----------
def photo_with_metadata(orientation=6):
    exif = Image.Exif(); exif[0x0112] = orientation
    exif.get_ifd(0x8825).update({1: "N", 2: (0.0, 0.0, 0.0), 3: "E", 4: (0.0, 0.0, 0.0)})  # fake GPS block (0, 0)
    buf = io.BytesIO()
    Image.effect_noise((600, 400), 64).convert("RGB").save(
        buf, "JPEG", exif=exif, comment=b"PRIVATE", xmp=b"<x:xmpmeta>PRIVATE</x:xmpmeta>", quality=85)
    buf.write(b"APPENDED-PRIVATE")  # like a motion-photo trailer after the end of the image
    buf.seek(0)
    return buf

def scan_data(jpeg):
    start = jpeg.find(b"\xff\xda")
    return jpeg[start:jpeg.find(b"\xff\xd9", start) + 2]

def test_strip_metadata_keeps_image_data_and_orientation():
    src = photo_with_metadata().getvalue()
    out = app.strip_image_metadata(src, orientation=6)
    assert scan_data(out) == scan_data(src)  # compressed image data, byte for byte
    a, b = Image.open(io.BytesIO(src)), Image.open(io.BytesIO(out))
    assert a.size == b.size and a.tobytes() == b.tobytes()  # identical pixels
    exif = b.getexif()
    assert dict(exif) == {0x0112: 6} and not exif.get_ifd(0x8825)  # orientation only, no GPS
    assert b"PRIVATE" not in out and "xmp" not in b.info and "comment" not in b.info

def test_strip_metadata_png_keeps_pixels():
    from PIL import PngImagePlugin
    info = PngImagePlugin.PngInfo(); info.add_text("Comment", "PRIVATE")
    buf = io.BytesIO(); Image.new("RGBA", (50, 40), (0, 0, 0, 0)).save(buf, "PNG", pnginfo=info)
    src = buf.getvalue()
    out = app.strip_image_metadata(src)
    assert b"PRIVATE" not in out
    assert Image.open(io.BytesIO(out)).tobytes() == Image.open(io.BytesIO(src)).tobytes()

def test_gemini_copy_has_no_metadata_and_stays_upright():
    img = app.open_uploaded_image(photo_with_metadata())
    gem = base64.b64decode(app.preprocess_image(img, ["google"], LOG, CFG["image_requirements"])["data"])
    assert b"Exif" not in gem and b"PRIVATE" not in gem  # fails without `img_copy.info = {}` (comment)
    assert Image.open(io.BytesIO(gem)).size == (400, 600)


# ---------- end-to-end pipeline with fakes (Gemini + LLMWhisperer) ----------
class FakeUpload(io.BytesIO):
    name = "page.jpg"

def test_pipeline_end_to_end_with_fakes(monkeypatch):
    seq = iter([ok_response({"is_suitable": "Yes", "reason": "ok"}),
                ok_response({"flashcards": [{"kanji": "先輩", "furigana": "せんぱい", "english_translation_and_notes": "senior"}]})])
    client = fake_client(lambda kw: next(seq))
    monkeypatch.setattr(app, "build_genai_client", lambda key: client)
    whisper_calls, ocr_streams = [], []
    class FakeWhisper:
        def __init__(self, **kw): whisper_calls.append(("init", kw))
        def whisper(self, **kw):
            ocr_streams.append(kw["stream"].getvalue())
            whisper_calls.append(("whisper", {k: v for k, v in kw.items() if k != "stream"}))
            return {"status_code": 200, "extraction": {"result_text": "先輩 せんぱい senior"}}
    monkeypatch.setattr(app, "LLMWhispererClientV2", FakeWhisper)
    photo = photo_with_metadata().getvalue()  # fake GPS, comment, XMP and appended data
    buf = FakeUpload(photo)
    kwargs = dict(uploaded_images=[buf], prompt_template="Vocabulary", use_examples=False)
    import inspect
    if "gemini_api_key" in inspect.signature(app.generate_japanese_flashcards).parameters:  # app_public
        kwargs.update(gemini_api_key="FAKE_GEMINI_KEY_123", llmwhisperer_api_key="FAKE_LLMW_KEY_123")
    else:  # main reads keys from env/secrets
        monkeypatch.setenv("GOOGLE_GEMINI_API_KEY", "FAKE_GEMINI_KEY_123"); monkeypatch.setenv("LLMWHISPERER_API_KEY", "FAKE_LLMW_KEY_123")
        monkeypatch.setenv("IS_LOCAL_DEV", "true")
    cards, notes, stats = app.generate_japanese_flashcards(**kwargs)
    assert cards == '"先輩","せんぱい","senior"', (cards, notes)
    assert stats["cost"] > 0 and client.files.calls == []
    assert [c["model"] for c in client.models.calls] == ["gemini-3.8-flash", "gemini-3.8-flash"]
    init_kw = whisper_calls[0][1]
    assert init_kw["base_url"].startswith("https://llmwhisperer-api.")
    assert whisper_calls[1][1]["mode"] == "form"
    # The OCR service gets the same image data, without the metadata
    sent = ocr_streams[0]
    assert b"PRIVATE" not in sent and not Image.open(io.BytesIO(sent)).getexif().get_ifd(0x8825)
    assert scan_data(sent) == scan_data(photo)
