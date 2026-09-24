package main

import (
	"encoding/json"
	"flag"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"testing"
)

type mockTransport func(*http.Request) (*http.Response, error)

func (f mockTransport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func response(r *http.Request, body string) *http.Response {
	return &http.Response{StatusCode: 200, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(body)), Request: r}
}

func TestAllowableHosts(t *testing.T) {
	for _, host := range []string{"cumulus.cwbi.mil", "cumulus-api.corps.cloud", "github.com"} {
		if err := allowableHost(host); err != nil {
			t.Errorf("%s: %v", host, err)
		}
	}
	for _, host := range []string{"cumulus.cwbi.mil/api", "https://cumulus.cwbi.mil", "unapproved.example"} {
		if allowableHost(host) == nil {
			t.Errorf("unexpectedly allowed %s", host)
		}
	}
}

// Exercise JSON input and the same main() request construction used by cavi.exe.
// All HTTP requests are intercepted in memory; no external network is used.
func TestGetRequests(t *testing.T) {
	for _, tc := range []struct{ host, endpoint, want string }{
		{"cumulus.cwbi.mil", "watersheds", "/api/watersheds"},
		{"cumulus.cwbi.mil", "products", "/api/products"},
		{"cumulus.cwbi.mil", "api/products", "/api/products"},
		{"cumulus.cwbi.mil", "/api/watersheds", "/api/watersheds"},
		{"cumulus-api.corps.cloud", "products", "/products"},
	} {
		t.Run(tc.host+"/"+tc.endpoint, func(t *testing.T) {
			oldFlags, oldArgs, oldIn, oldOut, oldTransport := flag.CommandLine, os.Args, os.Stdin, os.Stdout, http.DefaultTransport
			t.Cleanup(func() {
				flag.CommandLine, os.Args, os.Stdin, os.Stdout, http.DefaultTransport = oldFlags, oldArgs, oldIn, oldOut, oldTransport
			})
			flag.CommandLine = flag.NewFlagSet("cavi", flag.ContinueOnError)
			os.Args = []string{"cavi"}
			input, err := os.CreateTemp(t.TempDir(), "input")
			if err != nil {
				t.Fatal(err)
			}
			defer input.Close()
			if err := json.NewEncoder(input).Encode(map[string]string{"Host": tc.host, "Scheme": "https", "Subcommand": "get", "Endpoint": tc.endpoint}); err != nil {
				t.Fatal(err)
			}
			if _, err := input.Seek(0, 0); err != nil {
				t.Fatal(err)
			}
			output, err := os.CreateTemp(t.TempDir(), "output")
			if err != nil {
				t.Fatal(err)
			}
			defer output.Close()
			os.Stdin, os.Stdout = input, output
			var requests []string
			http.DefaultTransport = mockTransport(func(r *http.Request) (*http.Response, error) {
				if r.URL.Host != tc.host {
					t.Errorf("unexpected host %s", r.URL.Host)
				}
				requests = append(requests, r.URL.Path)
				return response(r, `[]`), nil
			})
			main()
			if len(requests) != 1 || requests[0] != tc.want {
				t.Fatalf("requests = %v; want only %s (no website-root request)", requests, tc.want)
			}
			if _, err := output.Seek(0, 0); err != nil {
				t.Fatal(err)
			}
			body, err := io.ReadAll(output)
			if err != nil || string(body) != "[]" {
				t.Fatalf("output = %q, error = %v", body, err)
			}
		})
	}
}

// Verify the download submission, status poll and returned file URL together.
func TestGridDownloadRoutes(t *testing.T) {
	for _, tc := range []struct{ host, endpoint, prefix string }{
		{"cumulus.cwbi.mil", "deprecated/anonymous_downloads", "/api"},
		{"cumulus.cwbi.mil", "api/deprecated/anonymous_downloads", "/api"},
		{"cumulus-api.corps.cloud", "deprecated/anonymous_downloads", ""},
	} {
		t.Run(tc.host+"/"+tc.endpoint, func(t *testing.T) {
			oldTransport := http.DefaultTransport
			t.Cleanup(func() { http.DefaultTransport = oldTransport })
			t.Setenv("TMP", t.TempDir())
			t.Setenv("TEMP", t.TempDir())
			var requests []string
			http.DefaultTransport = mockTransport(func(r *http.Request) (*http.Response, error) {
				requests = append(requests, r.Method+" "+r.URL.String())
				switch len(requests) {
				case 1:
					return response(r, `{"id":"test-download"}`), nil
				case 2:
					return response(r, `{"status":"SUCCESS","progress":100,"file":"https://files.example/result.dss"}`), nil
				default:
					return response(r, "mock DSS contents"), nil
				}
			})
			u := url.URL{Scheme: "https", Host: tc.host, Path: apiEndpoint(tc.host, tc.endpoint)}
			result, err := grid(u, payload{WatershedID: "test-watershed", ProductID: []string{"test-product"}}, 2)
			if err != nil {
				t.Fatal(err)
			}
			want := []string{
				"POST https://" + tc.host + tc.prefix + "/deprecated/anonymous_downloads",
				"GET https://" + tc.host + tc.prefix + "/downloads/test-download",
				"GET https://files.example/result.dss",
			}
			if strings.Join(requests, "\n") != strings.Join(want, "\n") {
				t.Fatalf("requests = %v; want %v", requests, want)
			}
			data, err := os.ReadFile(strings.TrimPrefix(result, "dssfile::"))
			if err != nil || string(data) != "mock DSS contents" {
				t.Fatalf("download = %q, error = %v", data, err)
			}
		})
	}
}
