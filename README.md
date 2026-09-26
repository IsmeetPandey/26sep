# RunLedger

Local-first execution receipts for reproducible CLI runs.

RunLedger records the command, working directory, Git HEAD when available, explicitly selected environment variables, declared input/output SHA-256 digests, start/end timestamps, duration, and exit code.

It does not capture stdout/stderr, dump the whole environment, or require a service.

## Install

Requires Python 3.10+.

~~~bash
python -m pip install -e .
~~~

## Use

~~~bash
runledger --receipt receipt.json \
  --env PYTHON_VERSION \
  --input src/input.txt \
  --output build/output.bin \
  -- python -m your_tool
~~~

The child process is launched without a shell. Declared paths must remain inside the selected working directory. A failing child still produces a receipt and RunLedger returns the child's exit code.

## Security

Only named environment variables are recorded. Paths are constrained to the working directory. File hashing is streaming. No network service is required.

RunLedger is an execution receipt, not a cryptographic supply-chain attestation system. For stronger provenance guarantees, use established attestation frameworks.

## Development

~~~bash
python -m unittest discover -s tests -v
PYTHONPATH=. python -m runledger.cli --help
~~~

License: MIT.
