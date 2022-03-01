package main

import (
	"log"
	"net/url"
	"time"

	"github.com/pkg/errors"
)

func grid(f flagOptions, url url.URL, p payload) (string, error) {
	// get auth token
	// auth, err := getResponseBody(authserver)
	// if err != nil {
	// 	return "", err
	// }

	var dssfilepath string

	var us updateStatus
	if err := us.postPayload(url.String(), p); err != nil {
		return dssfilepath, err
	} else {
		log.Println("Download ID:", us.ID)
		log.Println("Payload: ", p)
	}

	url.Path = url.Path + "/" + us.ID

	log.Println("Endpoint/ID: " + url.Path)
	timeout := time.Duration(int(time.Second) * int(f.Timeout))
	var fn filename
	for start := time.Now(); time.Since(start) < timeout; {
		us.getStatus(url.String())
		log.Printf("ID: %s\tStatus: %s\tProgress: %d\tFile: %s", us.ID, us.Status, us.Progress, us.File)
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
