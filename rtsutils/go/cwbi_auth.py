"""CAC sign-in for Cumulus using the RTS Windows certificate key manager.

Uses the CWBI direct X509 grant used by the HEC Java Cumulus client.
Tokens stay in memory and are passed to cavi.exe through its stdin pipe.
"""
import json
import threading
import time
try:
    from urllib import urlencode
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlencode, urlparse

API_ROOT = "https://cumulus.cwbi.mil/api"
TOKEN_HOSTS = ("identityc.sec.usace.army.mil",)
_lock = threading.RLock()
_token = None
_expires_at = 0
_ssl_context = None


def _validate_token_url(value):
    parsed = urlparse(value)
    if (parsed.scheme != "https" or parsed.hostname not in TOKEN_HOSTS
            or parsed.port not in (None, 443) or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or parsed.path != "/auth/realms/cwbi/protocol/openid-connect/token"):
        raise RuntimeError("The API returned an unexpected identity-provider URL; sign-in stopped.")
    return value


def _make_ssl_context(with_cac):
    from java.security import KeyStore
    from javax.net.ssl import SSLContext, TrustManagerFactory, KeyManager
    from jarray import array

    # Use Windows' installed trust roots, keeping normal TLS verification on.
    roots = KeyStore.getInstance("Windows-ROOT")
    roots.load(None, None)
    trust = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm())
    trust.init(roots)
    keys = None
    if with_cac:
        try:
            from hec.serversuite import CwmsCacUtil
            key = CwmsCacUtil.getKeyManager(None)
        except ImportError:
            from mil.army.usace.hec.cwms.http.client.auth import CacKeyManagerUtil
            key = CacKeyManagerUtil.createKeyManager()
        if key is None:
            raise RuntimeError("No CAC certificate was selected. Insert your CAC and retry.")
        keys = array([key], KeyManager)
    context = SSLContext.getInstance("TLS")
    context.init(keys, trust.getTrustManagers(), None)
    return context


def _request_json(address, context, form=None):
    from java.net import URL
    from java.lang import String
    connection = URL(address).openConnection()
    connection.setSSLSocketFactory(context.getSocketFactory())
    connection.setConnectTimeout(30000)
    connection.setReadTimeout(60000)
    connection.setInstanceFollowRedirects(False)
    connection.setRequestProperty("Accept", "application/json")
    try:
        if form is not None:
            connection.setRequestMethod("POST")
            connection.setDoOutput(True)
            connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
            output = connection.getOutputStream()
            try:
                output.write(String(urlencode(form)).getBytes("UTF-8"))
            finally:
                output.close()
        status = connection.getResponseCode()
        if status < 200 or status >= 300:
            raise RuntimeError("CAC sign-in request to {} returned HTTP {}. "
                               "Check CAC selection, network access, and Cumulus account permission.".format(address, status))
        if "text/html" in str(connection.getContentType()).lower():
            raise RuntimeError("CAC sign-in received a web login page instead of a token response.")
        stream = connection.getInputStream()
        try:
            body = str(String(stream.readAllBytes(), "UTF-8"))
        finally:
            stream.close()
        try:
            return json.loads(body)
        except ValueError:
            raise RuntimeError("CAC sign-in received an invalid JSON response.")
    finally:
        connection.disconnect()


def get_access_token(force=False):
    global _token, _expires_at, _ssl_context
    with _lock:
        if not force and _token and time.time() < _expires_at:
            return _token
        _token = None
        configuration = _request_json(API_ROOT + "/identity-provider/configuration",
                                      _make_ssl_context(False))
        endpoint = _validate_token_url(configuration.get("token_endpoint", ""))
        print("Cumulus: signing in with CAC. Complete any certificate/PIN prompt.")
        if _ssl_context is None:
            _ssl_context = _make_ssl_context(True)
        response = _request_json(endpoint, _ssl_context, {
            "client_id": "cumulus", "grant_type": "password",
            "username": "", "password": "", "scope": "openid profile"
        })
        token = response.get("access_token")
        if not isinstance(token, type("")):
            # json.loads returns unicode strings in Jython/Python 2.
            try:
                valid = isinstance(token, basestring)
            except NameError:
                valid = False
            if not valid:
                raise RuntimeError("CAC sign-in did not return an access token.")
        if not token or "\r" in token or "\n" in token:
            raise RuntimeError("CAC sign-in did not return a valid access token.")
        _expires_at = time.time() + max(0, int(response.get("expires_in", 60)) - 30)
        _token = token
        return _token
