package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const helperVersion = "rts-utils CWBI helper 2026-09-18-v2"

// Supplied over stdin by the Jython CAC bridge, never written to disk or logs.
var apiToken string

type filename string
type payload struct {
	After       string   `json:"datetime_start"`
	Before      string   `json:"datetime_end"`
	WatershedID string   `json:"watershed_id"`
	ProductID   []string `json:"product_id"`
}
type updateStatus struct {
	ID       string `json:"id"`
	Status   string `json:"status"`
	Progress int    `json:"progress"`
	File     string `json:"file"`
}

func safeURL(raw string) string {
	u, err := url.Parse(raw)
	if err != nil {
		return "invalid URL"
	}
	u.User, u.RawQuery, u.Fragment = nil, "", ""
	return u.String()
}
func tokenOrigin(u *url.URL) bool {
	return u.Scheme == "https" && u.Host == "cumulus.cwbi.mil"
}

func request(method, raw string, body io.Reader) (*http.Response, error) {
	req, err := http.NewRequest(method, raw, body)
	if err != nil {
		return nil, fmt.Errorf("cannot construct %s request to %s", method, safeURL(raw))
	}
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if apiToken != "" && tokenOrigin(req.URL) {
		req.Header.Set("Authorization", "Bearer "+apiToken)
	}
	client := &http.Client{Timeout: 30 * time.Second, CheckRedirect: func(next *http.Request, via []*http.Request) error {
		if len(via) >= 10 {
			return fmt.Errorf("too many redirects; possible login redirect")
		}
		if !tokenOrigin(next.URL) {
			next.Header.Del("Authorization")
		}
		return nil
	}}
	resp, err := client.Do(req)
	if err != nil {
		if e, ok := err.(*url.Error); ok {
			err = e.Err
		}
		return nil, fmt.Errorf("%s %s: connection failed: %v", method, safeURL(raw), err)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		resp.Body.Close()
		hint := ""
		switch resp.StatusCode {
		case 401:
			hint = "; authentication is required or the session expired"
		case 403:
			hint = "; access denied (network/access policy or account permission); browser login alone is not used by this helper"
		case 404:
			hint = "; API route not found"
		case 407:
			hint = "; proxy authentication required"
		}
		return nil, fmt.Errorf("%s %s: HTTP %d%s", method, safeURL(raw), resp.StatusCode, hint)
	}
	if strings.Contains(strings.ToLower(resp.Header.Get("Content-Type")), "text/html") {
		resp.Body.Close()
		return nil, fmt.Errorf("%s %s: received an HTML website/login page instead of API data", method, safeURL(raw))
	}
	return resp, nil
}

func readJSONResponse(resp *http.Response) ([]byte, error) {
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if !json.Valid(b) {
		return nil, fmt.Errorf("%s: response was not valid JSON (possibly a login or proxy page)", safeURL(resp.Request.URL.String()))
	}
	return b, nil
}
func (us *updateStatus) getStatus(u string) error {
	b, err := getResponseBody(u)
	if err != nil {
		return err
	}
	return json.Unmarshal(b, us)
}
func (us *updateStatus) postPayload(u string, p payload) error {
	data, err := json.Marshal(p)
	if err != nil {
		return err
	}
	resp, err := request("POST", u, bytes.NewReader(data))
	if err != nil {
		return err
	}
	b, err := readJSONResponse(resp)
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, us); err != nil {
		return err
	}
	if us.ID == "" {
		return fmt.Errorf("%s: response did not contain a download ID", safeURL(u))
	}
	return nil
}
func checkService(u string) (*http.Response, error) {
	return (&http.Client{Timeout: 30 * time.Second}).Get(u)
}
func getResponse(u string) (*http.Response, error) { return request("GET", u, nil) }
func getResponseBody(u string) ([]byte, error) {
	resp, err := getResponse(u)
	if err != nil {
		return nil, err
	}
	return readJSONResponse(resp)
}
func (fn *filename) downloadDss(u, d string) error {
	resp, err := request("GET", u, nil)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if strings.Contains(strings.ToLower(resp.Header.Get("Content-Type")), "json") {
		return fmt.Errorf("%s: received JSON instead of a DSS download", safeURL(u))
	}
	f, err := os.CreateTemp(d, "cumulus_*.dss")
	if err != nil {
		return err
	}
	_, copyErr := io.Copy(f, resp.Body)
	closeErr := f.Close()
	if copyErr != nil {
		os.Remove(f.Name())
		return copyErr
	}
	if closeErr != nil {
		os.Remove(f.Name())
		return closeErr
	}
	*fn = filename(f.Name())
	return nil
}
