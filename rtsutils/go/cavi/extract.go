package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"net/url"
	"os"
)

func extract(url url.URL) {

	resp, err := getResponse(url.String())
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error - %s", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	reader := bufio.NewReader(resp.Body)
	buffer := &bytes.Buffer{}

	for {
		line, err := reader.ReadBytes('\n')
		if err == io.EOF {
			break
		}
		line = bytes.TrimSpace(line)
		buffer.Write(line)
		os.Stdout.WriteString(string(line))
	}
}
