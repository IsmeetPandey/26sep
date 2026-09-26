# Security

RunLedger executes the command supplied by the user and therefore should only be used with commands the user trusts.

The child process is not invoked through a shell. Environment capture is explicit and limited to names passed with --env. Receipts and source files are not uploaded anywhere.

Please report suspected security issues privately rather than publishing exploit details in an issue.
