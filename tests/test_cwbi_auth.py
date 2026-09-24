"""Offline checks run with the same Jython 2.7 runtime bundled with RTS."""
import imp
import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pkg = types.ModuleType("rtsutils")
pkg.__path__ = [os.path.join(ROOT, "rtsutils")]
pkg.null = None
sys.modules["rtsutils"] = pkg
from rtsutils import go
from rtsutils.go import cwbi_auth as auth


class CacBridgeTests(unittest.TestCase):
    def setUp(self):
        self.context = auth._make_ssl_context
        self.request = auth._request_json
        self.clock = auth.time
        self.invoke = go._invoke
        self.get_token = auth.get_access_token
        auth._token = None
        auth._expires_at = 0
        auth._ssl_context = None
        auth._make_ssl_context = lambda with_cac: with_cac
        auth.time = types.ModuleType("test_clock")
        auth.time.time = lambda: 1000

    def tearDown(self):
        auth._make_ssl_context = self.context
        auth._request_json = self.request
        auth.time = self.clock
        go._invoke = self.invoke
        auth.get_access_token = self.get_token
        auth._token = None

    def test_token_grant_and_memory_cache(self):
        calls = []
        def request(url, context, form=None):
            calls.append((url, context, form))
            if form is None:
                return {"token_endpoint": "https://identityc.sec.usace.army.mil/auth/realms/cwbi/protocol/openid-connect/token"}
            self.assertTrue(context)
            self.assertEqual(form, {"client_id": "cumulus", "grant_type": "password", "username": "", "password": "", "scope": "openid profile"})
            return {"access_token": u"fake-token-for-test", "expires_in": 300}
        auth._request_json = request
        self.assertEqual(auth.get_access_token(), "fake-token-for-test")
        self.assertEqual(auth.get_access_token(), "fake-token-for-test")
        self.assertEqual(len(calls), 2)
        self.assertFalse(calls[0][1])
        auth.time.time = lambda: 1400
        auth.get_access_token()
        self.assertEqual(len(calls), 4)

    def test_unexpected_identity_host_is_rejected(self):
        for endpoint in ["http://identityc.sec.usace.army.mil/auth/realms/cwbi/protocol/openid-connect/token", "https://evil.example/token", "https://identityc.sec.usace.army.mil:444/auth/realms/cwbi/protocol/openid-connect/token", "https://identityc.sec.usace.army.mil/other"]:
            self.assertRaises(RuntimeError, auth._validate_token_url, endpoint)

    def test_grid_token_is_not_stored_in_caller_configuration(self):
        flags = {"Host": "cumulus.cwbi.mil", "Scheme": "https", "Subcommand": "grid"}
        auth.get_access_token = lambda: "fake-token-for-test"
        captured = []
        def invoke(values, *args):
            captured.append(values)
            return "dssfile::test", ""
        go._invoke = invoke
        self.assertEqual(go.get(flags)[0], "dssfile::test")
        self.assertEqual(captured[0]["Auth"], "fake-token-for-test")
        self.assertNotIn("Auth", flags)

    def test_metadata_does_not_login_unless_denied(self):
        flags = {"Host": "cumulus.cwbi.mil", "Scheme": "https", "Subcommand": "get"}
        calls = []
        def token():
            calls.append("login")
            return "fake-token-for-test"
        auth.get_access_token = token
        go._invoke = lambda *args: ("[]", "")
        self.assertEqual(go.get(flags), ("[]", ""))
        self.assertEqual(calls, [])
        def denied(values, *args):
            return ("[]", "") if values.get("Auth") else ("", "error::GET /api/products: HTTP 401")
        go._invoke = denied
        self.assertEqual(go.get(flags), ("[]", ""))
        self.assertEqual(calls, ["login"])
        self.assertNotIn("Auth", flags)

    def test_connection_error_does_not_prompt_for_cac(self):
        flags = {"Host": "cumulus.cwbi.mil", "Scheme": "https", "Subcommand": "get"}
        auth.get_access_token = lambda: self.fail("CAC requested for network failure")
        go._invoke = lambda *args: ("", "error::connection failed: DNS lookup failed")
        self.assertIn("DNS lookup", go.get(flags)[1])

    def test_java_signin_error_is_reported(self):
        from java.io import IOException
        def token():
            raise IOException("test CAC unavailable")
        auth.get_access_token = token
        result = go.get({"Host":"cumulus.cwbi.mil", "Scheme":"https", "Subcommand":"grid"})
        self.assertIn("error::", result[1])
        self.assertIn("CAC unavailable", result[1])

    def test_runtime_dependencies_exist_in_rts_35(self):
        from java.security import KeyStore
        from javax.net.ssl import SSLContext, TrustManagerFactory
        from hec.serversuite import CwmsCacUtil
        from mil.army.usace.hec.cwms.http.client.auth import CacKeyManagerUtil
        self.assertTrue(hasattr(CwmsCacUtil, "getKeyManager"))
        self.assertTrue(hasattr(CacKeyManagerUtil, "createKeyManager"))
        self.assertIsNotNone(KeyStore.getInstance("Windows-ROOT"))

    def test_jython_can_run_rebuilt_executable(self):
        stdout, stderr = go._invoke({"Host": "invalid.example", "Subcommand": "get"})
        self.assertEqual(stdout, "")
        self.assertIn("2026-09-18-v2", stderr)
        self.assertIn("not allowed", stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
