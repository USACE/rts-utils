package main

import (
	"encoding/json"
	"flag"
	"io"
	"net/http"
	"os"
	"strings"
	"testing"
)

func TestAuthenticatedGridMain(t *testing.T) {
	oldFlags, oldArgs, oldIn, oldOut, oldTransport, oldToken := flag.CommandLine, os.Args, os.Stdin, os.Stdout, http.DefaultTransport, apiToken
	t.Cleanup(func() {
		flag.CommandLine, os.Args, os.Stdin, os.Stdout, http.DefaultTransport, apiToken = oldFlags, oldArgs, oldIn, oldOut, oldTransport, oldToken
	})
	t.Setenv("TMP", t.TempDir())
	t.Setenv("TEMP", t.TempDir())
	flag.CommandLine = flag.NewFlagSet("cavi", flag.ContinueOnError)
	os.Args = []string{"cavi"}
	in, err := os.CreateTemp(t.TempDir(), "in")
	if err != nil {
		t.Fatal(err)
	}
	defer in.Close()
	out, err := os.CreateTemp(t.TempDir(), "out")
	if err != nil {
		t.Fatal(err)
	}
	defer out.Close()
	json.NewEncoder(in).Encode(map[string]interface{}{"Host": "cumulus.cwbi.mil", "Scheme": "https", "Subcommand": "grid", "Endpoint": "api/deprecated/anonymous_downloads", "Auth": "test-token-not-real", "ID": "watershed", "Products": []string{"product"}, "Timeout": 2})
	in.Seek(0, 0)
	os.Stdin, os.Stdout = in, out
	var calls []string
	http.DefaultTransport = mockTransport(func(r *http.Request) (*http.Response, error) {
		calls = append(calls, r.Method+" "+r.URL.String())
		if r.URL.Host == "cumulus.cwbi.mil" && r.Header.Get("Authorization") != "Bearer test-token-not-real" {
			t.Error("API request missing bearer token")
		}
		if r.URL.Host != "cumulus.cwbi.mil" && r.Header.Get("Authorization") != "" {
			t.Error("token leaked to file server")
		}
		switch len(calls) {
		case 1:
			return response(r, `{"id":"job"}`), nil
		case 2:
			return response(r, `{"status":"SUCCESS","progress":100,"file":"https://files.example/result.dss"}`), nil
		default:
			return response(r, "DSS test data"), nil
		}
	})
	main()
	want := "POST https://cumulus.cwbi.mil/api/downloads\nGET https://cumulus.cwbi.mil/api/downloads/job\nGET https://files.example/result.dss"
	if strings.Join(calls, "\n") != want {
		t.Fatalf("wrong authenticated flow: %v", calls)
	}
	out.Seek(0, 0)
	result, _ := io.ReadAll(out)
	if !strings.HasPrefix(string(result), "dssfile::") {
		t.Fatalf("wrong output: %q", result)
	}
}

func TestHTTPFailuresAreActionable(t *testing.T) {
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	for _, status := range []int{401, 403, 404, 407, 500} {
		http.DefaultTransport = mockTransport(func(r *http.Request) (*http.Response, error) {
			resp := response(r, `{"secret":"do-not-print"}`)
			resp.StatusCode = status
			return resp, nil
		})
		_, err := getResponseBody("https://cumulus.cwbi.mil/api/products?token=do-not-print")
		if err == nil || !strings.Contains(err.Error(), "HTTP ") || strings.Contains(err.Error(), "do-not-print") {
			t.Fatalf("bad HTTP diagnostic: %v", err)
		}
	}
	http.DefaultTransport = mockTransport(func(r *http.Request) (*http.Response, error) {
		resp := response(r, "<html>Login</html>")
		resp.Header.Set("Content-Type", "text/html")
		return resp, nil
	})
	if _, err := getResponseBody("https://cumulus.cwbi.mil/api/products"); err == nil || !strings.Contains(err.Error(), "login page") {
		t.Fatalf("HTML not diagnosed: %v", err)
	}
	var us updateStatus
	if err := us.postPayload("https://cumulus.cwbi.mil/api/downloads", payload{}); err == nil {
		t.Fatal("HTML POST response accepted")
	}
	if err := us.getStatus("https://cumulus.cwbi.mil/api/downloads/job"); err == nil {
		t.Fatal("status failure not propagated")
	}
}

func TestRedirectDoesNotLeakToken(t *testing.T) {
	oldTransport, oldToken := http.DefaultTransport, apiToken
	t.Cleanup(func() { http.DefaultTransport, apiToken = oldTransport, oldToken })
	apiToken = "test-token-not-real"
	for _, target := range []string{"https://other.cumulus.cwbi.mil/login", "https://files.example/file", "http://cumulus.cwbi.mil/login"} {
		calls := 0
		http.DefaultTransport = mockTransport(func(r *http.Request) (*http.Response, error) {
			calls++
			if calls == 1 {
				if r.Header.Get("Authorization") == "" {
					t.Error("initial token missing")
				}
				resp := response(r, "")
				resp.StatusCode = 302
				resp.Header.Set("Location", target)
				return resp, nil
			}
			if r.Header.Get("Authorization") != "" {
				t.Errorf("token leaked to %s", target)
			}
			return response(r, `[]`), nil
		})
		if _, err := getResponseBody("https://cumulus.cwbi.mil/api/products"); err != nil {
			t.Fatal(err)
		}
		if calls != 2 {
			t.Errorf("unexpected redirect calls %d", calls)
		}
	}
}
