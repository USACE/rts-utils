package main

import (
	"log"
	"net/url"
	"time"

	"github.com/pkg/errors"
)

func grid(url url.URL, p payload, t int, tk string) (string, error) {

	var dssfilepath string

	var us updateStatus
	if err := us.postPayload(url.String(), p, tk); err != nil {
		return dssfilepath, err
	} else {
		log.Println("Download ID:", us.ID)
		log.Println("Payload: ", p)
	}

	url.Path = url.Path + "/" + us.ID

	log.Println("Endpoint/ID: " + url.Path)
	timeout := time.Duration(int(time.Second) * int(t))
	var fn filename
	for start := time.Now(); time.Since(start) < timeout; {
		us.getStatus(url.String())
		if us.Status == "FAILED" {
			return "", errors.New("Status: FAILED")
		}
		log.Printf("ID: %-40s Status: %-12s Progress: %-6d File: %s", us.ID, us.Status, us.Progress, us.File)
		if us.Status == "SUCCESS" && us.Progress >= 100 && us.File != "" {
			if err := fn.downloadDss(us.File, ""); err != nil {
				return dssfilepath, err
			}
			log.Println("File downloaded to:", fn)
			dssfilepath := "dssfile::" + string(fn)
			return dssfilepath, nil
		} else {
			time.Sleep(1 * time.Second)
		}
	}

	return dssfilepath, errors.New("No grids produced")
}
