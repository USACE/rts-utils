[README](../../README.md)
# Go Support Program, cavi.exe

The `cavi.exe` support program works in conjunction with CAVI scripts to provide `https` connectivity with modern webservers.  Making http(s) requests within the CAVI environment, and other Jython environments, does not provide modern SSL/TLS protocol.  Jython scripting within these environments hands-off web requests to the Go executable, with inputs, and the program returns requesting information back to the Jython parent process to finish its work.

## Sub Commands

Currently, `cavi.exe` provides two subcommands, `grid` and `extract`.  Interacting with the `Cumulus` API is requested using the `grid` subcommand and proper inputs.  Interacting with the `water` API to extract watershed data is done with `extract` subcommand and proper inputs.

## Sub Command Inputs

All subcommands provide the user a couple ways to provide inputs to the running program, switches and standard input.