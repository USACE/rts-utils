package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

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

func (us *updateStatus) getStatus(u string) {
	b, err := getResponseBody(u, false)
	if err != nil {
		log.Fatal(err)
	}
	if err := json.Unmarshal(b, us); err != nil {
		log.Fatal(err)
	}

}

func (us *updateStatus) postPayload(u string, p payload, t string) error {
	timeout := time.Duration(time.Second * 10)
	bearer := "Bearer " + t
	client := http.Client{
		Timeout: timeout,
	}
	json_data, err := json.Marshal(p)
	if err != nil {
		return err
	}
	req, err := http.NewRequest("POST", u, bytes.NewBuffer(json_data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", bearer)

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	if err = json.Unmarshal(b, us); err != nil {
		return err
	}
	return nil
}

// checkService
func checkService(u string) (*http.Response, error) {
	timeout := time.Duration(10 * time.Second)
	client := &http.Client{
		Timeout: timeout,
	}
	return client.Get(u)
}

func getResponse(u string) (*http.Response, error) {
	timeout := time.Duration(time.Second * 10)
	client := http.Client{
		Timeout: timeout,
	}
	req, err := http.NewRequest("GET", u, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")

	return client.Do(req)

}

func getResponseBody(u string, tb bool) ([]byte, error) {
	// Make a new request and get the response
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: tb},
	}
	timeout := time.Duration(time.Second * 10)
	client := http.Client{
		Timeout:   timeout,
		Transport: tr,
	}
	req, err := http.NewRequest("GET", u, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	if sc := resp.StatusCode; sc != 200 {
		return nil, fmt.Errorf("response status code %d", sc)
	}

	defer resp.Body.Close()

	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	return b, nil
}

func (fn *filename) downloadDss(url string, d string) error {
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	f, err := os.CreateTemp(d, "cumulus_*.dss")
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, resp.Body)
	if err != nil {
		return err
	}
	(*fn) = filename(f.Name())
	return nil
}
