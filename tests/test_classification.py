from app.classification import classify_error, classify_response


def test_ok_response():
    assert classify_response(200, {}, "<html>fine</html>") == "ok"


def test_rate_limited():
    assert classify_response(429, {}, "too many requests") == "rate_limited"


def test_blocked_403():
    assert classify_response(403, {}, "forbidden") == "blocked_403"


def test_captcha_challenge_detected_in_body():
    body = '<div class="g-recaptcha" data-sitekey="..."></div>'
    assert classify_response(403, {}, body) == "captcha_challenge"


def test_cloudflare_challenge():
    headers = {"cf-ray": "abc123", "server": "cloudflare"}
    body = "Checking your browser before accessing"
    assert classify_response(503, headers, body) == "bot_challenge_cloudflare"


def test_server_error():
    assert classify_response(500, {}, "internal error") == "server_error"


def test_redirect():
    assert classify_response(302, {}, "") == "redirect"


class FakeTimeoutError(Exception):
    pass


class FakeConnectError(Exception):
    pass


class FakeProxyError(Exception):
    pass


def test_classify_timeout_error():
    assert classify_error(FakeTimeoutError("timed out")) == "timeout"


def test_classify_connect_error():
    assert classify_error(FakeConnectError("connection refused")) == "connection_error"


def test_classify_proxy_error():
    assert classify_error(FakeProxyError("bad proxy")) == "proxy_error"
